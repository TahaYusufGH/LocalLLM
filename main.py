"""LocalLLM — Yerel RAG Asistanı başlatıcısı.

Kullanım:
    python main.py                # sunucuyu başlat ve tarayıcıyı aç
    python main.py --no-browser   # tarayıcı açma
    python main.py --port 8800    # farklı port
    python main.py --reindex      # sadece documents/ klasörünü indeksle ve çık
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser


def _open_browser(url: str, delay: float = 1.5) -> None:
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def run_reindex() -> int:
    from app import config, embeddings, ingest, store

    store.init()
    settings = config.load()
    embedder = embeddings.get_embedder(settings)
    print(f"Gomme saglayicisi: {embedder.kind} / {embedder.name} ({embedder.dim} boyut)")

    def progress(current: int, total: int, name: str) -> None:
        print(f"  [{current}/{total}] {name}")

    result = ingest.reindex_all(embedder, settings, progress)
    print(f"\nTamamlandi: {result['indexed']} belge, {result['chunks']} parca.")
    for error in result["errors"]:
        print(f"  HATA {error['name']}: {error['error']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Yerel RAG asistani")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--reindex", action="store_true")
    args = parser.parse_args()

    if args.reindex:
        return run_reindex()

    import uvicorn
    from app.server import app

    url = f"http://{args.host}:{args.port}"
    print("=" * 62)
    print("  LocalLLM - Yerel RAG Asistani")
    print(f"  Arayuz : {url}")
    print("  Durum  : cevrimdisi calisir, hicbir veri disari gonderilmez")
    print("  Durdur : Ctrl+C")
    print("=" * 62)

    if not args.no_browser:
        threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
