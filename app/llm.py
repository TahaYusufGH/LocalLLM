"""Yerel dil modeli istemcisi.

Foundry Local, Ollama, LM Studio, llama.cpp gibi araçların hepsi OpenAI uyumlu
bir HTTP arayüzü sunar. Bu modül tek bir istemciyle hepsini konuşturur ve
çalışan bir sunucuyu otomatik bulmayı dener. Tüm istekler ``localhost``
üzerinedir; internet erişimi kullanılmaz.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import requests

# (etiket, taban adres) — yaygın yerel sunucu portları.
# Windows'ta "localhost" önce IPv6 (::1) denendiği için her bağlantıya ~2 sn
# ekliyor; bu yüzden her yerde doğrudan 127.0.0.1 kullanılır.
CANDIDATE_ENDPOINTS = [
    ("foundry", "http://127.0.0.1:5273/v1"),
    ("foundry", "http://127.0.0.1:5272/v1"),
    ("ollama", "http://127.0.0.1:11434/v1"),
    ("lmstudio", "http://127.0.0.1:1234/v1"),
    ("llamacpp", "http://127.0.0.1:8080/v1"),
    ("custom", "http://127.0.0.1:8000/v1"),
]

# Bağlantılar yeniden kullanılsın diye tek oturum (keep-alive).
SESSION = requests.Session()


def normalize_url(url: str) -> str:
    """Adresi 127.0.0.1'e sabitler ve /v1 sonekini garantiler."""
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    url = url.replace("://localhost:", "://127.0.0.1:").replace("://[::1]:", "://127.0.0.1:")
    if not url.endswith("/v1") and "/v1" not in url:
        url += "/v1"
    return url

_endpoint_cache: Dict[str, Any] = {"value": None, "at": 0.0, "valid": False}
_cache_lock = threading.Lock()
CACHE_TTL = 45.0          # olumlu sonuç ömrü
CACHE_TTL_MISS = 60.0     # olumsuz sonuç ömrü (yeniden taramayı sınırlar)


def _list_models(base_url: str, api_key: str = "", timeout: float = 2.0) -> Optional[List[str]]:
    try:
        response = SESSION.get(
            f"{base_url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {api_key or 'local'}"},
            timeout=timeout,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        items = payload.get("data", payload if isinstance(payload, list) else [])
        return [item.get("id") for item in items if isinstance(item, dict) and item.get("id")]
    except Exception:
        return None


def foundry_exe() -> Optional[str]:
    """foundry.exe yolunu bulur.

    Foundry Local bir MSIX paketi olarak kurulduğu için komut yalnızca
    WindowsApps klasöründedir ve etkileşimsiz kabuklarda PATH'te görünmeyebilir.
    """
    found = shutil.which("foundry")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidate = Path(local) / "Microsoft" / "WindowsApps" / "foundry.exe"
        if candidate.exists():
            return str(candidate)
    return None


def _foundry_cli_endpoint(timeout: float = 12.0) -> Optional[str]:
    """Foundry CLI çıktısından servis adresini okumayı dener.

    Sürümler arasında alt komut değiştiği için birkaç varyant denenir.
    Bu çağrı yavaş olabildiğinden yalnızca port taraması başarısız olunca
    ve kısa zaman aşımıyla kullanılır.
    """
    exe = foundry_exe()
    if not exe:
        return None
    # 0.10+ sürümlerde "server status", daha eskilerde "service status".
    # Foundry rastgele bir port seçtiği için (ör. 50084) adres yalnızca
    # buradan öğrenilebilir; sabit port listesi yetmez.
    for args in (["server", "status", "-o", "json"], ["server", "status"],
                 ["service", "status"], ["status"]):
        try:
            result = subprocess.run(
                [exe, *args], capture_output=True, text=True, timeout=timeout,
            )
        except Exception:
            continue
        text = f"{result.stdout}\n{result.stderr}"
        if "Unrecognized command" in text:
            continue

        if "-o" in args:  # yapılandırılmış çıktı: webUrls listesini oku
            try:
                payload = json.loads(result.stdout.strip())
                urls = payload.get("webUrls") or []
                if urls:
                    return normalize_url(urls[0])
            except (json.JSONDecodeError, AttributeError):
                pass

        for token in text.replace(",", " ").split():
            if token.startswith("http://") or token.startswith("https://"):
                return normalize_url(token.rstrip(".,)\"'"))
    return None


def _foundry_sdk_endpoint(alias: str) -> Optional[Dict[str, str]]:
    try:
        from foundry_local import FoundryLocalManager  # type: ignore
    except Exception:
        return None
    try:
        manager = FoundryLocalManager(alias or "phi-3.5-mini")
        info = manager.get_model_info(alias) if alias else None
        return {
            "base_url": normalize_url(manager.endpoint),
            "api_key": getattr(manager, "api_key", "") or "",
            "model": getattr(info, "id", "") if info else "",
        }
    except Exception:
        return None


def resolve_endpoint(settings: Dict[str, Any], probe: bool = True) -> Optional[Dict[str, Any]]:
    """Kullanılabilir yerel model sunucusunu bulur.

    Sıra: elle girilen adres → Foundry SDK → bilinen portlar → Foundry CLI.
    """
    provider = settings.get("llm_provider", "auto")
    if provider == "none":
        return None

    manual = normalize_url(settings.get("llm_base_url") or "")
    if manual:
        base = manual
        models = _list_models(base, settings.get("llm_api_key", "")) if probe else []
        if models is not None:
            return {"base_url": base, "provider": provider if provider != "auto" else "custom",
                    "models": models, "api_key": settings.get("llm_api_key", "")}
        if not probe:
            return {"base_url": base, "provider": "custom", "models": [], "api_key": ""}

    with _cache_lock:
        cached = _endpoint_cache["value"]
        valid = _endpoint_cache["valid"]
        age = time.time() - _endpoint_cache["at"]
    # Olumsuz sonuçlar da önbelleğe alınır; aksi hâlde her istek tüm portları tarar.
    if valid and age < (CACHE_TTL if cached else CACHE_TTL_MISS):
        return cached

    found: Optional[Dict[str, Any]] = None

    if provider in ("auto", "foundry"):
        sdk = _foundry_sdk_endpoint(settings.get("llm_model", ""))
        if sdk:
            models = _list_models(sdk["base_url"], sdk["api_key"])
            if models is not None:
                found = {"base_url": sdk["base_url"], "provider": "foundry",
                         "models": models, "api_key": sdk["api_key"]}

    # Port taraması hızlıdır, önce o denenir; CLI sorgusu (yavaş olabilir)
    # yalnızca hiçbir port yanıt vermezse son çare olarak çalıştırılır.
    if not found:
        found = _probe_candidates(provider)

    if not found and provider in ("auto", "foundry"):
        cli = _foundry_cli_endpoint()
        if cli:
            models = _list_models(cli)
            if models is not None:
                found = {"base_url": cli, "provider": "foundry",
                         "models": models, "api_key": ""}

    with _cache_lock:
        _endpoint_cache["value"] = found
        _endpoint_cache["at"] = time.time()
        _endpoint_cache["valid"] = True
    return found


def _probe_candidates(provider: str) -> Optional[Dict[str, Any]]:
    """Bilinen portları paralel yoklar; ilk yanıt verene bağlanır."""
    targets = [(label, base) for label, base in CANDIDATE_ENDPOINTS
               if provider in ("auto", label, "custom")]
    if not targets:
        return None

    results: Dict[int, Dict[str, Any]] = {}
    lock = threading.Lock()

    def worker(index: int, label: str, base: str) -> None:
        models = _list_models(base, timeout=1.5)
        if models is not None:
            with lock:
                results[index] = {"base_url": base, "provider": label,
                                  "models": models, "api_key": ""}

    threads = [threading.Thread(target=worker, args=(i, label, base), daemon=True)
               for i, (label, base) in enumerate(targets)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    for index in range(len(targets)):  # liste sırası = öncelik sırası
        if index in results:
            return results[index]
    return None


def invalidate() -> None:
    with _cache_lock:
        _endpoint_cache["value"] = None
        _endpoint_cache["at"] = 0.0
        _endpoint_cache["valid"] = False


def pick_model(endpoint: Dict[str, Any], settings: Dict[str, Any]) -> str:
    wanted = (settings.get("llm_model") or "").strip()
    models = endpoint.get("models") or []
    if wanted and (not models or wanted in models):
        return wanted
    if wanted:
        for model in models:  # kısmi eşleşme (ör. "phi-3.5")
            if wanted.lower() in model.lower():
                return model
    # gömme modellerini sohbet için seçme
    chat_models = [m for m in models if "embed" not in m.lower()]
    return (chat_models or models or [""])[0]


class LLMUnavailable(RuntimeError):
    pass


THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"

# "/no_think" yumuşak anahtarını tanıyan model aileleri
NO_THINK_MODELS = ("qwen3", "qwen-3", "qwq")


def apply_thinking_switch(messages: List[Dict[str, str]], model: str,
                          thinking: bool) -> List[Dict[str, str]]:
    """Düşünme kapalıysa son kullanıcı mesajına "/no_think" ekler.

    qwen3 gibi modeller varsayılan olarak uzun bir düşünme bloğu üretir ve bu
    blok token bütçesinin tamamını tüketip cevabı yarıda kesebiliyor. RAG'de
    cevap zaten bağlama dayandığı için düşünme kapalı olması hem çok daha
    hızlı hem de daha güvenilir sonuç veriyor.
    """
    if thinking or not model:
        return messages
    if not any(tag in model.lower() for tag in NO_THINK_MODELS):
        return messages

    patched = [dict(m) for m in messages]
    for message in reversed(patched):
        if message.get("role") == "user":
            if "/no_think" not in message["content"]:
                message["content"] = f"{message['content']} /no_think"
            break
    return patched
_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Tamamlanmış bir cevaptaki düşünme bloklarını atar.

    qwen3 gibi "düşünen" modeller cevabın önüne <think>…</think> bloğu koyar;
    bu blok kullanıcıya gösterilmemeli ve doğrulama adımını bozmamalıdır.
    """
    cleaned = _THINK_RE.sub("", text)
    # kapanış etiketi hiç gelmediyse (kesilmiş cevap) açılıştan sonrasını at
    lowered = cleaned.lower()
    if THINK_OPEN in lowered and THINK_CLOSE not in lowered:
        cleaned = cleaned[: lowered.index(THINK_OPEN)]
    return cleaned.strip()


def filter_thinking(chunks: Iterator[str]) -> Iterator[str]:
    """Akış hâlindeki metinden düşünme bloklarını canlı olarak ayıklar.

    Etiketler parçalara bölünerek gelebildiği için etiket uzunluğu kadar
    metin geride tutulur ve ancak güvenli olduğunda dışarı verilir.
    """
    hold = ""
    inside = False
    keep = max(len(THINK_OPEN), len(THINK_CLOSE))

    for chunk in chunks:
        hold += chunk
        while True:
            low = hold.lower()
            if inside:
                end = low.find(THINK_CLOSE)
                if end == -1:
                    hold = hold[-keep:] if len(hold) > keep else hold
                    break
                hold = hold[end + len(THINK_CLOSE):].lstrip()
                inside = False
                continue
            start = low.find(THINK_OPEN)
            if start == -1:
                if len(hold) > keep:
                    out, hold = hold[:-keep], hold[-keep:]
                    if out:
                        yield out
                break
            if start:
                yield hold[:start]
            hold = hold[start + len(THINK_OPEN):]
            inside = True

    if not inside and hold:
        yield hold


def status(settings: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = resolve_endpoint(settings)
    if not endpoint:
        return {"online": False, "ready": False, "provider": None,
                "base_url": None, "model": None, "models": []}
    model = pick_model(endpoint, settings)
    return {
        "online": True,
        # Sunucu ayakta olabilir ama hiç model yüklü olmayabilir
        # (ör. "foundry server start" çalıştırılıp model indirilmemişse).
        "ready": bool(model),
        "provider": endpoint["provider"],
        "base_url": endpoint["base_url"],
        "model": model,
        "models": endpoint.get("models", []),
    }


def chat(messages: List[Dict[str, str]], settings: Dict[str, Any],
         temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
    endpoint = resolve_endpoint(settings)
    if not endpoint:
        raise LLMUnavailable("Yerel model sunucusu bulunamadı.")
    model = pick_model(endpoint, settings)
    body = {
        "model": model,
        "messages": apply_thinking_switch(messages, model, bool(settings.get("thinking", False))),
        "temperature": settings.get("temperature", 0.2) if temperature is None else temperature,
        "max_tokens": settings.get("max_tokens", 800) if max_tokens is None else max_tokens,
        "stream": False,
    }
    response = SESSION.post(
        f"{endpoint['base_url']}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {endpoint.get('api_key') or 'local'}"},
        timeout=300,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"] or ""
    return strip_thinking(content)


def chat_stream(messages: List[Dict[str, str]], settings: Dict[str, Any],
                stop_flag: Optional[threading.Event] = None) -> Iterator[str]:
    endpoint = resolve_endpoint(settings)
    if not endpoint:
        raise LLMUnavailable("Yerel model sunucusu bulunamadı.")
    model = pick_model(endpoint, settings)
    body = {
        "model": model,
        "messages": apply_thinking_switch(messages, model, bool(settings.get("thinking", False))),
        "temperature": settings.get("temperature", 0.2),
        "max_tokens": settings.get("max_tokens", 800),
        "stream": True,
    }
    with SESSION.post(
        f"{endpoint['base_url']}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {endpoint.get('api_key') or 'local'}"},
        stream=True,
        timeout=600,
    ) as response:
        response.raise_for_status()
        for raw in response.iter_lines(decode_unicode=True):
            if stop_flag is not None and stop_flag.is_set():
                break
            if not raw:
                continue
            line = raw.strip()
            if line.startswith("data:"):
                line = line[5:].strip()
            if not line or line == "[DONE]":
                if line == "[DONE]":
                    break
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            for choice in chunk.get("choices", []):
                piece = (choice.get("delta") or {}).get("content") or ""
                if piece:
                    yield piece
