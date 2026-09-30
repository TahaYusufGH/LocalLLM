"""Uygulama ayarları — data/settings.json içinde saklanır, tamamen yereldir."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "documents"
WEB_DIR = ROOT / "web"
DB_PATH = DATA_DIR / "knowledge.db"
SETTINGS_PATH = DATA_DIR / "settings.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_SYSTEM_PROMPT = (
    "Sen yerel bir bilgi asistanısın. Yalnızca sana verilen BAĞLAM bölümündeki "
    "bilgileri kullanarak cevap ver.\n"
    "Kurallar:\n"
    "1. Cevabı bağlamda bulamazsan açıkça 'Bu bilgi belgelerimde yok.' de, tahmin etme.\n"
    "2. Doğrudan cevapla. Soruyu tekrarlama, aynı cümleyi iki kez yazma.\n"
    "3. Bilgiyi hangi kaynaktan aldığını cümle sonunda [1], [2] şeklinde belirt.\n"
    "4. 'KAYNAK 1', '### KAYNAK' gibi bağlam başlıklarını cevabına kopyalama.\n"
    "5. Kullanıcının sorduğu dilde cevap ver."
)

DEFAULTS: Dict[str, Any] = {
    # --- Dil modeli (LLM) ---
    "llm_provider": "auto",          # auto | foundry | ollama | custom | none
    "llm_base_url": "",              # örn. http://localhost:5273/v1
    "llm_model": "",                 # örn. Phi-3.5-mini-instruct-generic-cpu
    "llm_api_key": "",
    "temperature": 0.2,
    "max_tokens": 800,
    # Düşünen modellerde (qwen3) düşünme bloğu token bütçesini tüketip
    # cevabı kesebildiği için varsayılan olarak kapalıdır.
    "thinking": False,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,

    # --- Gömme (embedding) ---
    "embed_provider": "auto",        # auto | endpoint | local | hash
    "embed_model": "qwen3-embedding-0.6b",
    "embed_local_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",

    # --- Erişim (retrieval) ---
    "top_k": 6,
    "chunk_size": 700,
    "chunk_overlap": 150,

    # --- Alaka kapısı (relevance gating) ---
    "gate_enabled": True,
    "reject_below": 0.0,             # 0 => gömme sağlayıcısına göre otomatik
    "verify_below": 0.0,
    # Kapı reddettiğinde modelin kendi genel bilgisiyle cevaplamasına izin ver.
    # Kapalıyken asistan yalnızca belgelere dayanır (varsayılan davranış).
    "general_knowledge": False,

    # --- Arayüz ---
    "language": "tr",                # tr | en
    "theme": "dark",                 # dark | light
    "show_scores": True,
}

# Gömme sağlayıcısına göre önerilen eşik değerleri.
GATE_PRESETS = {
    "hash": {"reject_below": 0.10, "verify_below": 0.20},
    "local": {"reject_below": 0.30, "verify_below": 0.45},
    "endpoint": {"reject_below": 0.50, "verify_below": 0.65},
}

_lock = threading.Lock()
_cache: Dict[str, Any] | None = None


def load() -> Dict[str, Any]:
    global _cache
    with _lock:
        if _cache is None:
            data = dict(DEFAULTS)
            if SETTINGS_PATH.exists():
                try:
                    stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                    data.update({k: v for k, v in stored.items() if k in DEFAULTS})
                except (json.JSONDecodeError, OSError):
                    pass
            _cache = data
        return dict(_cache)


def save(patch: Dict[str, Any]) -> Dict[str, Any]:
    global _cache
    current = load()
    for key, value in patch.items():
        if key in DEFAULTS:
            current[key] = value
    with _lock:
        _cache = current
        SETTINGS_PATH.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return dict(current)


def reset() -> Dict[str, Any]:
    return save(dict(DEFAULTS))


def gate_thresholds(settings: Dict[str, Any], embed_kind: str) -> tuple[float, float]:
    """Ayarlarda 0 bırakılmışsa gömme türüne uygun varsayılanı döndürür."""
    preset = GATE_PRESETS.get(embed_kind, GATE_PRESETS["hash"])
    reject = settings.get("reject_below") or preset["reject_below"]
    verify = settings.get("verify_below") or preset["verify_below"]
    if verify < reject:
        verify = reject
    return float(reject), float(verify)
