"""SQLite tabanlı yerel vektör deposu ve sohbet geçmişi.

Tek bir dosya (``data/knowledge.db``) her şeyi tutar: belgeler, parçalar,
gömme vektörleri ve sohbetler. Vektör araması küçük veri kümeleri için
kaba kuvvet kosinüs benzerliğiyle yapılır (proje planındaki yaklaşım).
"""
from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import DB_PATH

_write_lock = threading.Lock()
_matrix_cache: Dict[str, Any] = {"version": -1, "matrix": None, "rows": []}
_lexical_cache: Dict[str, Any] = {"version": -1, "index": None}
_version = 0

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    source      TEXT,
    kind        TEXT,
    bytes       INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at  REAL
);
CREATE TABLE IF NOT EXISTS chunks (
    id         TEXT PRIMARY KEY,
    doc_id     TEXT NOT NULL,
    ordinal    INTEGER NOT NULL,
    text       TEXT NOT NULL,
    embedding  BLOB NOT NULL,
    dim        INTEGER NOT NULL,
    model      TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    title      TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE TABLE IF NOT EXISTS messages (
    id       TEXT PRIMARY KEY,
    conv_id  TEXT NOT NULL,
    role     TEXT NOT NULL,
    content  TEXT NOT NULL,
    sources  TEXT,
    created_at REAL,
    FOREIGN KEY (conv_id) REFERENCES conversations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def _bump() -> None:
    global _version
    _version += 1


# --------------------------------------------------------------------------
# meta
# --------------------------------------------------------------------------

def get_meta(key: str, default: str = "") -> str:
    with connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(key: str, value: str) -> None:
    with _write_lock, connect() as conn:
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


# --------------------------------------------------------------------------
# belgeler & parçalar
# --------------------------------------------------------------------------

def add_document(name: str, source: str, kind: str, size: int,
                 chunks: List[str], vectors: np.ndarray, model: str) -> str:
    doc_id = uuid.uuid4().hex
    now = time.time()
    payload = [
        (uuid.uuid4().hex, doc_id, i, text,
         vectors[i].astype(np.float32).tobytes(), int(vectors.shape[1]), model)
        for i, text in enumerate(chunks)
    ]
    with _write_lock, connect() as conn:
        conn.execute(
            "INSERT INTO documents(id, name, source, kind, bytes, chunk_count, created_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (doc_id, name, source, kind, size, len(chunks), now),
        )
        conn.executemany(
            "INSERT INTO chunks(id, doc_id, ordinal, text, embedding, dim, model)"
            " VALUES(?,?,?,?,?,?,?)",
            payload,
        )
    _bump()
    return doc_id


def list_documents() -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, source, kind, bytes, chunk_count, created_at"
            " FROM documents ORDER BY created_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def document_by_name(name: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE name = ?", (name,)).fetchone()
    return dict(row) if row else None


def delete_document(doc_id: str) -> bool:
    with _write_lock, connect() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    _bump()
    return cursor.rowcount > 0


def clear_all() -> None:
    with _write_lock, connect() as conn:
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM documents")
    _bump()


def stats() -> Dict[str, Any]:
    with connect() as conn:
        docs = conn.execute("SELECT COUNT(*) AS c FROM documents").fetchone()["c"]
        chunks = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()["c"]
        dim_row = conn.execute("SELECT dim, model FROM chunks LIMIT 1").fetchone()
    return {
        "documents": docs,
        "chunks": chunks,
        "dim": dim_row["dim"] if dim_row else 0,
        "model": dim_row["model"] if dim_row else "",
    }


def _load_matrix() -> Tuple[Optional[np.ndarray], List[Dict[str, Any]]]:
    global _matrix_cache
    if _matrix_cache["version"] == _version and _matrix_cache["matrix"] is not None:
        return _matrix_cache["matrix"], _matrix_cache["rows"]

    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.doc_id, c.ordinal, c.text, c.embedding, c.dim, c.model,"
            " d.name AS doc_name FROM chunks c JOIN documents d ON d.id = c.doc_id"
            " ORDER BY d.created_at DESC, c.ordinal"
        ).fetchall()

    if not rows:
        _matrix_cache = {"version": _version, "matrix": None, "rows": []}
        return None, []

    dim = rows[0]["dim"]
    usable = [r for r in rows if r["dim"] == dim]
    matrix = np.vstack([np.frombuffer(r["embedding"], dtype=np.float32) for r in usable])
    meta = [
        {"id": r["id"], "doc_id": r["doc_id"], "ordinal": r["ordinal"],
         "text": r["text"], "doc_name": r["doc_name"], "model": r["model"]}
        for r in usable
    ]
    _matrix_cache = {"version": _version, "matrix": matrix, "rows": meta}
    return matrix, meta


STEM_LEN = 5  # Türkçe eklemeli bir dil: "kademesi" ve "kademeli" aynı köke iner


_folded_stopwords: Optional[set] = None


def _terms(text: str) -> List[str]:
    global _folded_stopwords
    from .embeddings import STOPWORDS, TOKEN_RE, fold

    if _folded_stopwords is None:
        # Metin katlanarak işlendiği için durak kelimeler de katlanmalı,
        # aksi hâlde "için" listede olmasına rağmen "icin" elenmez.
        _folded_stopwords = {fold(word).lower() for word in STOPWORDS}

    out = []
    for token in TOKEN_RE.findall(fold(text).lower()):
        if len(token) < 2 or token in _folded_stopwords:
            continue
        out.append(token[:STEM_LEN])
    return out


def _load_lexical() -> Optional[Dict[str, Any]]:
    """BM25 için ters indeks kurar (sürüm değişince yeniden üretilir)."""
    global _lexical_cache
    if _lexical_cache["version"] == _version and _lexical_cache["index"] is not None:
        return _lexical_cache["index"]

    _, rows = _load_matrix()
    if not rows:
        _lexical_cache = {"version": _version, "index": None}
        return None

    postings: Dict[str, Dict[int, int]] = {}
    lengths = np.zeros(len(rows), dtype=np.float32)
    for i, row in enumerate(rows):
        terms = _terms(row["text"])
        lengths[i] = len(terms) or 1
        for term in terms:
            postings.setdefault(term, {})
            postings[term][i] = postings[term].get(i, 0) + 1

    total = len(rows)
    idf = {
        term: math.log(1 + (total - len(docs) + 0.5) / (len(docs) + 0.5))
        for term, docs in postings.items()
    }
    index = {"postings": postings, "idf": idf, "lengths": lengths,
             "avgdl": float(lengths.mean()), "total": total}
    _lexical_cache = {"version": _version, "index": index}
    return index


def bm25_scores(query_text: str, k1: float = 1.5, b: float = 0.75) -> Optional[np.ndarray]:
    """Sorgu için tüm parçaların BM25 puanını döndürür.

    IDF ağırlığı sayesinde soruda geçen nadir bir kelime ("kademe") uzun bir
    parçanın içinde bile öne çıkar; saf anlamsal aramanın kaçırdığı tam
    kelime eşleşmeleri böyle yakalanır.
    """
    index = _load_lexical()
    if not index:
        return None
    scores = np.zeros(index["total"], dtype=np.float32)
    avgdl, lengths = index["avgdl"] or 1.0, index["lengths"]
    for term in set(_terms(query_text)):
        docs = index["postings"].get(term)
        if not docs:
            continue
        weight = index["idf"][term]
        for doc_index, freq in docs.items():
            norm = 1 - b + b * (lengths[doc_index] / avgdl)
            scores[doc_index] += weight * (freq * (k1 + 1)) / (freq + k1 * norm)
    return scores


def search(query_vector: np.ndarray, top_k: int = 4,
           query_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """Anlamsal + sözlüksel aramayı birleştirerek en iyi parçaları döndürür.

    Yalnızca anlamsal arama, sorudaki kelimenin metinde birebir geçtiği
    durumları şaşırtıcı biçimde kaçırabiliyor. Bu yüzden iki sıralama
    Reciprocal Rank Fusion ile birleştirilir. Döndürülen ``score`` alanı
    her zaman anlamsal (kosinüs) benzerliktir; alaka kapısı bu değere göre
    çalıştığı için eşiklerin anlamı değişmez.
    """
    matrix, rows = _load_matrix()
    if matrix is None or not rows:
        return []
    if matrix.shape[1] != query_vector.shape[0]:
        raise ValueError(
            f"Vektör boyutu uyuşmuyor (veritabanı {matrix.shape[1]}, sorgu {query_vector.shape[0]}). "
            "Belgeleri yeniden indekslemeniz gerekiyor."
        )
    query = query_vector.astype(np.float32)
    norm = float(np.linalg.norm(query)) or 1.0
    dense = matrix @ (query / norm)
    top_k = max(1, min(top_k, len(rows)))

    dense_order = np.argsort(-dense)
    chosen = dense_order[:top_k]

    if query_text:
        lexical = bm25_scores(query_text)
        if lexical is not None and float(lexical.max()) > 0:
            chosen = _fuse(dense_order, np.argsort(-lexical), top_k, len(rows))

    return [
        {**rows[int(i)], "score": round(float(dense[int(i)]), 4)}
        for i in chosen
    ]


def _fuse(dense_order: np.ndarray, lexical_order: np.ndarray,
          top_k: int, total: int, k: int = 20) -> List[int]:
    """Reciprocal Rank Fusion: iki sıralamayı tek listede birleştirir.

    ``k`` klasik olarak 60 alınır ama bu değer binlerce sonuç için tasarlanmıştır;
    birkaç düzine parçalık yerel bir koleksiyonda sıralar arası farkı yok ederek
    sıralamayı düzleştirir. Bu yüzden daha keskin bir k kullanılır.
    """
    pool = min(total, max(top_k * 5, 25))
    points: Dict[int, float] = {}
    for rank, index in enumerate(dense_order[:pool]):
        points[int(index)] = points.get(int(index), 0.0) + 1.0 / (k + rank + 1)
    for rank, index in enumerate(lexical_order[:pool]):
        points[int(index)] = points.get(int(index), 0.0) + 1.0 / (k + rank + 1)
    ranked = sorted(points, key=lambda i: -points[i])
    return ranked[:top_k]


def all_chunks() -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.doc_id, c.ordinal, c.text, d.name AS doc_name, d.source, d.kind"
            " FROM chunks c JOIN documents d ON d.id = c.doc_id ORDER BY d.created_at, c.ordinal"
        ).fetchall()
    return [dict(row) for row in rows]


def replace_embeddings(items: List[Tuple[str, bytes, int, str]]) -> None:
    """(chunk_id, blob, dim, model) listesiyle gömmeleri toplu günceller."""
    with _write_lock, connect() as conn:
        conn.executemany(
            "UPDATE chunks SET embedding = ?, dim = ?, model = ? WHERE id = ?",
            [(blob, dim, model, cid) for cid, blob, dim, model in items],
        )
    _bump()


# --------------------------------------------------------------------------
# sohbetler
# --------------------------------------------------------------------------

def create_conversation(title: str = "Yeni sohbet") -> Dict[str, Any]:
    conv_id = uuid.uuid4().hex
    now = time.time()
    with _write_lock, connect() as conn:
        conn.execute(
            "INSERT INTO conversations(id, title, created_at, updated_at) VALUES(?,?,?,?)",
            (conv_id, title, now, now),
        )
    return {"id": conv_id, "title": title, "created_at": now, "updated_at": now}


def list_conversations(limit: int = 100) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT c.id, c.title, c.created_at, c.updated_at,"
            " (SELECT COUNT(*) FROM messages m WHERE m.conv_id = c.id) AS message_count"
            " FROM conversations c ORDER BY c.updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def rename_conversation(conv_id: str, title: str) -> None:
    with _write_lock, connect() as conn:
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))


def delete_conversation(conv_id: str) -> None:
    with _write_lock, connect() as conn:
        conn.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))


def add_message(conv_id: str, role: str, content: str,
                sources: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    msg_id = uuid.uuid4().hex
    now = time.time()
    with _write_lock, connect() as conn:
        conn.execute(
            "INSERT INTO messages(id, conv_id, role, content, sources, created_at)"
            " VALUES(?,?,?,?,?,?)",
            (msg_id, conv_id, role, content,
             json.dumps(sources or [], ensure_ascii=False), now),
        )
        conn.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id))
    return {"id": msg_id, "role": role, "content": content, "sources": sources or [], "created_at": now}


def list_messages(conv_id: str) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, role, content, sources, created_at FROM messages"
            " WHERE conv_id = ? ORDER BY created_at",
            (conv_id,),
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["sources"] = json.loads(item.get("sources") or "[]")
        except json.JSONDecodeError:
            item["sources"] = []
        out.append(item)
    return out
