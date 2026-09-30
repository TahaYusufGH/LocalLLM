"""Gömme (embedding) sağlayıcıları.

Üç seçenek vardır ve hepsi internetsiz çalışacak şekilde tasarlanmıştır:

* ``endpoint`` – Foundry Local / Ollama / OpenAI uyumlu yerel bir sunucunun
  ``/embeddings`` ucu (örn. ``qwen3-embedding-0.6b``).
* ``local``    – sentence-transformers ile cihazda çalışan model
  (model daha önce indirilmiş olmalıdır; indirme denemesi yapılmaz).
* ``hash``     – hiçbir modele ihtiyaç duymayan, saf NumPy ile çalışan
  sözcük/karakter n-gram hash gömmesi. Her zaman çalışır, varsayılan yedektir.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import threading
import unicodedata
from typing import Any, Dict, List, Sequence

import numpy as np

TOKEN_RE = re.compile(r"[0-9a-zçğıöşüâîû]+", re.IGNORECASE)

# Türkçe aksan katlama: "Parçalama" ile "Parcalama" aynı vektöre düşsün diye
# hem belgeler hem sorgular gömme öncesi bu tablodan geçirilir. Kullanıcılar
# çoğu zaman Türkçe karakter kullanmadan yazdığı için isabet belirgin artar.
FOLD_MAP = str.maketrans("çğıöşüâîûÇĞİÖŞÜÂÎÛ", "cgiosuaiuCGIOSUAIU")


def fold(text: str) -> str:
    return unicodedata.normalize("NFC", text).translate(FOLD_MAP)

STOPWORDS = {
    # Türkçe
    "ve", "ile", "bir", "bu", "şu", "o", "da", "de", "ki", "mi", "mı", "mu", "mü",
    "için", "gibi", "ama", "fakat", "veya", "ya", "çok", "daha", "en", "her", "ne",
    "olan", "olarak", "ise", "ancak", "kadar", "sonra", "önce", "üzere", "hem",
    # İngilizce
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "been", "with", "as", "at", "by", "it", "this", "that",
    "from", "but", "not", "can", "will", "we", "you", "your",
}


def _tokenize(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1]


class BaseEmbedder:
    kind = "base"
    name = "base"
    dim = 0

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        """Aksanları katlayıp alt sınıfın kodlayıcısına verir."""
        return self._encode([fold(t) for t in texts])

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def info(self) -> Dict[str, Any]:
        return {"kind": self.kind, "name": self.name, "dim": self.dim}


class HashEmbedder(BaseEmbedder):
    """Model gerektirmeyen sözlüksel gömme.

    Sözcük tekilleri, ikilileri ve uzun sözcüklerin karakter 4-gramları
    hash'lenerek sabit boyutlu bir vektöre yansıtılır. Karakter n-gramları
    Türkçe gibi eklemeli dillerde çekim eklerine karşı dayanıklılık sağlar.
    """

    kind = "hash"
    name = "yerel-hash-1024"

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim

    def _features(self, text: str) -> Dict[str, float]:
        tokens = _tokenize(text)
        counts: Dict[str, float] = {}
        content = [t for t in tokens if t not in STOPWORDS]

        for tok in content:
            counts[f"w:{tok}"] = counts.get(f"w:{tok}", 0.0) + 1.0
            if len(tok) >= 5:
                # kök yakınlığı için karakter 4-gramları
                for i in range(len(tok) - 3):
                    key = f"c:{tok[i:i + 4]}"
                    counts[key] = counts.get(key, 0.0) + 0.5

        for a, b in zip(content, content[1:]):
            key = f"b:{a}_{b}"
            counts[key] = counts.get(key, 0.0) + 1.5

        return counts

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for feature, count in self._features(text).items():
                digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
                value = int.from_bytes(digest, "little")
                index = value % self.dim
                sign = 1.0 if (value >> 63) & 1 else -1.0
                out[row, index] += sign * (1.0 + math.log(count)) if count > 1 else sign * count
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


class LocalModelEmbedder(BaseEmbedder):
    """sentence-transformers ile cihaz üzerinde çalışan gömme modeli."""

    kind = "local"

    def __init__(self, model_name: str) -> None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from sentence_transformers import SentenceTransformer  # ağır import, tembel

        try:
            # low_cpu_mem_usage kapatılır: açıkken model "meta" cihazda kurulup
            # sonra kopyalanıyor ve bu yol iş parçacığı güvenli değil
            # ("Cannot copy out of meta tensor" hatası).
            self._model = SentenceTransformer(
                model_name, device="cpu", model_kwargs={"low_cpu_mem_usage": False}
            )
        except TypeError:  # eski sentence-transformers sürümleri
            self._model = SentenceTransformer(model_name, device="cpu")
        self.name = model_name
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        vectors = self._model.encode(
            list(texts), normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype=np.float32)


class EndpointEmbedder(BaseEmbedder):
    """OpenAI uyumlu yerel bir sunucunun /embeddings ucu."""

    kind = "endpoint"

    def __init__(self, base_url: str, model: str, api_key: str = "") -> None:
        from .llm import normalize_url

        self.base_url = normalize_url(base_url)
        self.name = model
        self.api_key = api_key or "local"
        self.dim = len(self.embed(["ölçüm"])[0])

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        from .llm import SESSION

        response = SESSION.post(
            f"{self.base_url}/embeddings",
            json={"model": self.name, "input": list(texts)},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=180,
        )
        response.raise_for_status()
        payload = response.json()
        rows = [item["embedding"] for item in sorted(payload["data"], key=lambda d: d.get("index", 0))]
        matrix = np.asarray(rows, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms


_cache: Dict[str, BaseEmbedder] = {}
_cache_lock = threading.Lock()
# Model kurulumu seri yapılır: aynı anda iki iş parçacığının aynı modeli
# yüklemesi hem belleği iki katına çıkarır hem de torch'ta çökmeye yol açar.
_build_lock = threading.RLock()
_last_error: str = ""


def last_error() -> str:
    return _last_error


def _indexed_kind() -> str:
    """Veritabanındaki parçaların hangi gömme türüyle kurulduğunu döndürür."""
    try:
        from . import store

        if store.stats()["chunks"] == 0:
            return ""
        return store.get_meta("embedder_kind", "")
    except Exception:
        return ""


def get_embedder(settings: Dict[str, Any], probe: bool = True) -> BaseEmbedder:
    """Ayarlara göre gömme sağlayıcısını (gerekirse yedeğe düşerek) döndürür."""
    provider = settings.get("embed_provider", "auto")
    if provider == "auto":
        order = ["endpoint", "local", "hash"]
        # Mevcut indeks hangi yöntemle kurulduysa önce o denenir. Aksi hâlde
        # sonradan bir model sunucusu açıldığında vektör boyutu değişir ve
        # kullanıcı sebepsiz yere yeniden indekslemek zorunda kalır.
        existing = _indexed_kind()
        if existing in order:
            order.remove(existing)
            order.insert(0, existing)
    else:
        order = [provider]

    # Seçim zincirinin sonucu tek anahtarla saklanır; böylece her soruda
    # başarısız olan sağlayıcılar tekrar tekrar denenmez.
    key = (f"{provider}:{settings.get('embed_model')}:"
           f"{settings.get('embed_local_model')}:{settings.get('llm_base_url')}")
    with _cache_lock:
        cached = _cache.get(key)
    if cached is not None:
        return cached

    with _build_lock:
        with _cache_lock:  # kilidi beklerken başka bir iş parçacığı kurmuş olabilir
            cached = _cache.get(key)
        if cached is not None:
            return cached
        return _build(key, order, settings, probe)


def _build(key: str, order: List[str], settings: Dict[str, Any], probe: bool) -> BaseEmbedder:
    global _last_error
    _last_error = ""
    for candidate in order:
        try:
            if candidate == "endpoint":
                from .llm import resolve_endpoint

                endpoint = resolve_endpoint(settings, probe=probe)
                if not endpoint:
                    raise RuntimeError("Yerel model sunucusu bulunamadı.")
                embedder: BaseEmbedder = EndpointEmbedder(
                    endpoint["base_url"], settings.get("embed_model", ""), settings.get("llm_api_key", "")
                )
            elif candidate == "local":
                embedder = LocalModelEmbedder(settings.get("embed_local_model", ""))
            else:
                embedder = HashEmbedder()
        except Exception as exc:  # yedeğe düş
            _last_error = f"{candidate}: {exc}"
            continue

        with _cache_lock:
            _cache[key] = embedder
        return embedder

    fallback = HashEmbedder()
    with _cache_lock:
        _cache[key] = fallback
    return fallback


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()
