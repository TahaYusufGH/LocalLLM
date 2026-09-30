"""FastAPI sunucusu — yalnızca 127.0.0.1 üzerinde dinler, dış ağa çıkmaz."""
from __future__ import annotations

import json
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, embeddings, ingest, llm, rag, store
from .config import DOCS_DIR, WEB_DIR

app = FastAPI(title="LocalLLM — Yerel RAG Asistanı", version="1.0.0")

_index_lock = threading.Lock()
_index_state: Dict[str, Any] = {"running": False, "current": 0, "total": 0, "file": "", "done": True}


# --------------------------------------------------------------------------
# modeller
# --------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
    history: List[Dict[str, str]] = []
    save: bool = True


class SettingsPatch(BaseModel):
    values: Dict[str, Any]


class TitlePatch(BaseModel):
    title: str


class TextDoc(BaseModel):
    name: str
    text: str


# --------------------------------------------------------------------------
# başlangıç
# --------------------------------------------------------------------------

@app.on_event("startup")
def _startup() -> None:
    store.init()
    settings = config.load()
    if store.stats()["chunks"] == 0 and ingest.scan_documents_folder():
        threading.Thread(target=_run_reindex, args=(settings,), daemon=True).start()
    else:
        # Gömme modelini ve model sunucusu aramasını arka planda ısıt:
        # ilk soru anında cevaplansın.
        threading.Thread(target=_warmup, args=(settings,), daemon=True).start()


def _warmup(settings: Dict[str, Any]) -> None:
    try:
        embeddings.get_embedder(settings).embed_one("hazırlık")
    except Exception:
        pass
    try:
        llm.resolve_endpoint(settings)
    except Exception:
        pass


def request_reindex(settings: Optional[Dict[str, Any]] = None) -> bool:
    """Arka planda yeniden indeksleme başlatır; zaten sürüyorsa False döner."""
    if _index_state.get("running"):
        return False
    threading.Thread(target=_run_reindex, args=(settings or config.load(),),
                     daemon=True).start()
    return True


def _run_reindex(settings: Dict[str, Any]) -> Dict[str, Any]:
    def progress(current: int, total: int, name: str) -> None:
        _index_state.update({"running": True, "current": current, "total": total,
                             "file": name, "done": False})

    with _index_lock:
        _index_state.update({"running": True, "current": 0, "total": 0, "file": "", "done": False})
        try:
            embedder = embeddings.get_embedder(settings)
            result = ingest.reindex_all(embedder, settings, progress)
            _index_state.update({"running": False, "done": True, "result": result})
            return result
        except Exception as exc:
            _index_state.update({"running": False, "done": True, "error": str(exc)})
            raise


# --------------------------------------------------------------------------
# durum & ayarlar
# --------------------------------------------------------------------------

@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    settings = config.load()
    model_status = llm.status(settings)
    embedder = embeddings.get_embedder(settings, probe=False)
    reject, verify = config.gate_thresholds(settings, embedder.kind)
    return {
        "llm": model_status,
        "embedder": {**embedder.info(), "fallback_reason": embeddings.last_error()},
        "index": store.stats(),
        "indexing": _index_state,
        "gate": {"reject_below": reject, "verify_below": verify,
                 "enabled": bool(settings.get("gate_enabled", True))},
        "offline": True,
        "docs_dir": str(DOCS_DIR),
    }


@app.get("/api/settings")
def api_get_settings() -> Dict[str, Any]:
    return {"settings": config.load(), "defaults": config.DEFAULTS}


@app.post("/api/settings")
def api_set_settings(patch: SettingsPatch) -> Dict[str, Any]:
    before = config.load()
    updated = config.save(patch.values)
    embed_changed = any(
        before.get(k) != updated.get(k)
        for k in ("embed_provider", "embed_model", "embed_local_model")
    )
    if embed_changed:
        embeddings.clear_cache()
    if before.get("llm_base_url") != updated.get("llm_base_url") or \
       before.get("llm_provider") != updated.get("llm_provider"):
        llm.invalidate()
    return {"settings": updated, "reindex_recommended": embed_changed}


@app.post("/api/settings/reset")
def api_reset_settings() -> Dict[str, Any]:
    embeddings.clear_cache()
    llm.invalidate()
    return {"settings": config.reset()}


@app.post("/api/detect")
def api_detect() -> Dict[str, Any]:
    llm.invalidate()
    embeddings.clear_cache()
    settings = config.load()
    found = llm.resolve_endpoint(settings)
    if not found:
        return {"found": False, "message": "Çalışan bir yerel model sunucusu bulunamadı."}
    config.save({"llm_base_url": found["base_url"]})
    return {"found": True, "endpoint": found, "status": llm.status(config.load())}


# --------------------------------------------------------------------------
# belgeler
# --------------------------------------------------------------------------

@app.get("/api/documents")
def api_documents() -> Dict[str, Any]:
    documents = store.list_documents()
    known = {d["name"] for d in documents}
    pending = [p.name for p in ingest.scan_documents_folder() if p.name not in known]
    return {"documents": documents, "pending": pending, "stats": store.stats(),
            "supported": sorted(ingest.SUPPORTED)}


@app.post("/api/documents/upload")
async def api_upload(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    settings = config.load()
    embedder = embeddings.get_embedder(settings)
    saved, errors = [], []
    for upload in files:
        name = Path(upload.filename or "belge.txt").name
        if Path(name).suffix.lower() not in ingest.SUPPORTED:
            errors.append({"name": name, "error": "Desteklenmeyen dosya türü."})
            continue
        target = DOCS_DIR / name
        try:
            with target.open("wb") as handle:
                shutil.copyfileobj(upload.file, handle)
            saved.append(ingest.index_file(target, embedder, settings))
        except Exception as exc:
            errors.append({"name": name, "error": str(exc)})
        finally:
            await upload.close()
    store.set_meta("embedder", embedder.name)
    store.set_meta("embedder_kind", embedder.kind)
    return {"saved": saved, "errors": errors, "stats": store.stats()}


@app.post("/api/documents/text")
def api_add_text(doc: TextDoc) -> Dict[str, Any]:
    settings = config.load()
    embedder = embeddings.get_embedder(settings)
    name = Path(doc.name or "not.md").name
    if not Path(name).suffix:
        name += ".md"
    target = DOCS_DIR / name
    target.write_text(doc.text, encoding="utf-8")
    result = ingest.index_file(target, embedder, settings)
    return {"saved": [result], "errors": [], "stats": store.stats()}


@app.delete("/api/documents/{doc_id}")
def api_delete_document(doc_id: str, remove_file: bool = True) -> Dict[str, Any]:
    documents = {d["id"]: d for d in store.list_documents()}
    document = documents.get(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")
    store.delete_document(doc_id)
    if remove_file and document.get("source"):
        path = Path(document["source"])
        try:
            if path.is_file() and DOCS_DIR in path.parents:
                path.unlink()
        except OSError:
            pass
    return {"ok": True, "stats": store.stats()}


@app.post("/api/reindex")
def api_reindex() -> Dict[str, Any]:
    if not request_reindex():
        return {"started": False, "message": "İndeksleme zaten sürüyor."}
    time.sleep(0.15)
    return {"started": True}


@app.get("/api/reindex/status")
def api_reindex_status() -> Dict[str, Any]:
    return dict(_index_state)


# --------------------------------------------------------------------------
# sohbet
# --------------------------------------------------------------------------

@app.get("/api/conversations")
def api_conversations() -> Dict[str, Any]:
    return {"conversations": store.list_conversations()}


@app.post("/api/conversations")
def api_new_conversation() -> Dict[str, Any]:
    return {"conversation": store.create_conversation()}


@app.get("/api/conversations/{conv_id}")
def api_conversation(conv_id: str) -> Dict[str, Any]:
    return {"messages": store.list_messages(conv_id)}


@app.patch("/api/conversations/{conv_id}")
def api_rename(conv_id: str, patch: TitlePatch) -> Dict[str, Any]:
    store.rename_conversation(conv_id, patch.title.strip()[:80] or "Yeni sohbet")
    return {"ok": True}


@app.delete("/api/conversations/{conv_id}")
def api_delete_conversation(conv_id: str) -> Dict[str, Any]:
    store.delete_conversation(conv_id)
    return {"ok": True}


@app.post("/api/search")
def api_search(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = (payload.get("q") or "").strip()
    if not question:
        return {"hits": []}
    settings = config.load()
    try:
        found = rag.retrieve(question, settings)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return found


def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.post("/api/chat")
def api_chat(request: ChatRequest) -> StreamingResponse:
    settings = config.load()
    conv_id = request.conversation_id

    def generate():
        nonlocal conv_id
        if request.save:
            if not conv_id:
                conv_id = store.create_conversation(request.question.strip()[:60] or "Yeni sohbet")["id"]
            elif not store.list_messages(conv_id):
                store.rename_conversation(conv_id, request.question.strip()[:60] or "Yeni sohbet")
            store.add_message(conv_id, "user", request.question)
            yield _sse({"type": "conversation", "id": conv_id})

        sources: List[Dict[str, Any]] = []
        started = time.time()
        try:
            for event in rag.answer_stream(request.question, request.history, settings):
                if event["type"] == "sources":
                    sources = event["sources"]
                if event["type"] == "done":
                    event["meta"]["elapsed"] = round(time.time() - started, 2)
                    if request.save and conv_id:
                        store.add_message(conv_id, "assistant", event["content"], sources)
                yield _sse(event)
        except Exception as exc:  # beklenmeyen hata
            yield _sse({"type": "error", "message": str(exc)})
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# --------------------------------------------------------------------------
# arayüz
# --------------------------------------------------------------------------

@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"ok": True})


app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
