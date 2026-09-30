"""RAG hattı: erişim (retrieve) → alaka kapısı (gate) → üretim (generate)."""
from __future__ import annotations

import re
import threading
from typing import Any, Dict, Iterator, List, Optional

from . import config, llm, smalltalk, store
from .embeddings import get_embedder

REFUSAL = {
    "tr": "Bu bilgi belgelerimde yok. Sorunuzu farklı ifade edebilir ya da ilgili belgeyi "
          "**Belgeler** sekmesinden ekleyebilirsiniz.",
    "en": "I couldn't find this in my documents. Try rephrasing, or add the relevant file "
          "from the **Documents** tab.",
}

EMPTY_INDEX = {
    "tr": "Henüz indekslenmiş belge yok. **Belgeler** sekmesinden dosya yükleyip "
          "*Yeniden indeksle* deyin.",
    "en": "No documents are indexed yet. Upload files in the **Documents** tab and run "
          "*Reindex*.",
}

VERIFY_PROMPT = (
    "Aşağıdaki METİN, SORU'yu cevaplamak için kullanılabilir bilgi içeriyor mu?\n"
    "Sadece EVET ya da HAYIR yaz, başka hiçbir şey yazma.\n\n"
    "METİN:\n{context}\n\nSORU: {question}\n\nCevap:"
)

# Modelin bağlamdan cevabına kopyaladığı kaynak başlıklarını yakalar.
LEAKED_HEADER_RE = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?\[?[ \t]*KAYNAK[ \t]+\d+.*$",
    re.MULTILINE | re.IGNORECASE,
)


def clean_answer(text: str) -> str:
    """Cevaba sızmış bağlam başlıklarını ve oluşan boşlukları temizler.

    İstemde "başlıkları kopyalama" demek küçük modellerde her zaman
    tutmuyor; bu yüzden temizlik istemde değil kodda garanti altına alınır.
    """
    cleaned = LEAKED_HEADER_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _request_reindex(settings: Dict[str, Any]) -> bool:
    """Arka planda yeniden indekslemeyi başlatır (sunucu tarafından sağlanır)."""
    try:
        from .server import request_reindex

        return request_reindex(settings)
    except Exception:
        return False


def build_context(hits: List[Dict[str, Any]]) -> str:
    """Bağlamı, modelin taklit edip cevaba kopyalamayacağı bir biçimde kurar."""
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(
            f"### KAYNAK {i} — {hit['doc_name']}\n{hit['text']}\n### KAYNAK {i} SONU"
        )
    return "\n\n".join(blocks)


def retrieve(question: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    embedder = get_embedder(settings)
    vector = embedder.embed_one(question)
    hits = store.search(vector, top_k=int(settings.get("top_k", 4)), query_text=question)
    reject, verify = config.gate_thresholds(settings, embedder.kind)
    # Melez sıralamada ilk sıra en yüksek kosinüs puanına sahip olmayabilir;
    # alaka kapısı her zaman en yüksek anlamsal benzerliğe bakar.
    return {
        "hits": hits,
        "embedder": embedder.info(),
        "best": max((h["score"] for h in hits), default=0.0),
        "reject_below": reject,
        "verify_below": verify,
    }


def _verify_with_model(question: str, context: str, settings: Dict[str, Any]) -> bool:
    try:
        answer = llm.chat(
            [{"role": "user", "content": VERIFY_PROMPT.format(context=context, question=question)}],
            settings, temperature=0.0, max_tokens=24,
        )
    except Exception:
        return True  # model yoksa kapıyı kapatma
    normalized = answer.strip().lower()
    return not (normalized.startswith("hayır") or normalized.startswith("hayir")
                or normalized.startswith("no"))


GENERAL_SYSTEM_PROMPT = {
    "tr": "Sen yardımcı bir asistansın. Kullanıcının sorusunu kendi genel bilginle, "
          "kısa ve doğru biçimde cevapla. Emin olmadığın bir konuda emin olmadığını "
          "açıkça söyle, uydurma. Kullanıcının sorduğu dilde cevap ver.",
    "en": "You are a helpful assistant. Answer the question from your own general "
          "knowledge, concisely and accurately. If you are unsure, say so plainly "
          "instead of guessing. Reply in the user's language.",
}

GENERAL_NOTICE = {
    "tr": "*Bu cevap belgelerinize dayanmıyor — modelin genel bilgisinden geliyor.*\n\n",
    "en": "*This answer is not based on your documents — it comes from the model's "
          "general knowledge.*\n\n",
}


def _general_knowledge_stream(question: str, history: Optional[List[Dict[str, str]]],
                              settings: Dict[str, Any], lang: str, meta: Dict[str, Any],
                              stop_flag: Optional[threading.Event]) -> Iterator[Dict[str, Any]]:
    """Kapı reddettiğinde modelin kendi bilgisiyle cevaplar (isteğe bağlı).

    Cevap belgelere dayanmadığı için hem metnin başına açık bir not konur hem de
    üstveride ``gate`` alanı ``general`` olarak işaretlenir; arayüz bunu ayrı bir
    etiketle gösterir. Böylece kaynaklı cevapla karıştırılamaz.
    """
    notice = GENERAL_NOTICE[lang if lang in GENERAL_NOTICE else "tr"]
    messages: List[Dict[str, str]] = [
        {"role": "system",
         "content": GENERAL_SYSTEM_PROMPT[lang if lang in GENERAL_SYSTEM_PROMPT else "tr"]}
    ]
    for turn in (history or [])[-4:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    meta["gate"] = "general"
    # Belge benzerliği bu cevapla ilgisiz; "belgelerinize dayanmıyor" notunun
    # yanında benzerlik yüzdesi göstermek kafa karıştırıyor.
    meta.pop("best_score", None)
    # Cevap belgelere dayanmadığı için daha önce gönderilmiş kaynak rozetleri
    # silinir; aksi hâlde "belgelerinize dayanmıyor" notunun altında kaynak
    # listesi görünüyor ve bu çelişkili oluyor.
    yield {"type": "sources", "sources": []}
    yield {"type": "delta", "text": notice}

    collected: List[str] = []
    try:
        for piece in llm.filter_thinking(llm.chat_stream(messages, settings, stop_flag=stop_flag)):
            collected.append(piece)
            yield {"type": "delta", "text": piece}
    except Exception as exc:
        meta["error"] = str(exc)

    answer = "".join(collected).strip()
    if not answer:  # model cevap veremedi → normal ret mesajına dön
        meta["gate"] = "rejected"
        text = REFUSAL[lang if lang in REFUSAL else "tr"]
        yield {"type": "delta", "text": text}
        yield {"type": "done", "content": text, "meta": meta}
        return

    yield {"type": "done", "content": notice + answer, "meta": meta}


def _general_enabled(settings: Dict[str, Any]) -> bool:
    status = llm.status(settings)
    return bool(settings.get("general_knowledge")) and status["online"] and status.get("ready")


def _extractive_answer(hits: List[Dict[str, Any]], lang: str) -> str:
    header = ("Yerel dil modeli çalışmıyor, bu yüzden **alıntı modundayım**: "
              "belgelerinizden en alakalı bölümleri aşağıda görebilirsiniz.\n\n"
              if lang == "tr" else
              "The local language model is not running, so I'm in **excerpt mode**: "
              "here are the most relevant passages from your documents.\n\n")
    parts = [
        f"**[{i}] {hit['doc_name']}**\n\n> {hit['text'][:900].strip()}"
        for i, hit in enumerate(hits, start=1)
    ]
    return header + "\n\n".join(parts)


def answer_stream(question: str, history: Optional[List[Dict[str, str]]] = None,
                  settings: Optional[Dict[str, Any]] = None,
                  stop_flag: Optional[threading.Event] = None) -> Iterator[Dict[str, Any]]:
    """Soruya olay akışı (event stream) üreterek cevap verir."""
    settings = settings or config.load()
    lang = settings.get("language", "tr")
    question = (question or "").strip()

    if not question:
        yield {"type": "done", "content": "", "meta": {"reason": "empty"}}
        return

    # Selamlaşma ve "sen kimsin" türü mesajlar erişime hiç girmez: alaka kapısı
    # bunları belgelere benzemedikleri için reddediyordu.
    chat_reply = smalltalk.handle(question, lang, [d["name"] for d in store.list_documents()])
    if chat_reply:
        yield {"type": "sources", "sources": []}
        yield {"type": "delta", "text": chat_reply["text"]}
        yield {"type": "done", "content": chat_reply["text"],
               "meta": {"gate": "smalltalk", "kind": chat_reply["kind"]}}
        return

    try:
        found = retrieve(question, settings)
    except ValueError as exc:
        # Gömme yöntemi indeksten farklı (ör. kurulum değişti). Kullanıcıyı
        # çıkmaza sokmak yerine yeniden indekslemeyi kendimiz başlatıyoruz.
        started = _request_reindex(settings)
        message = (
            "Gömme yöntemi değiştiği için belgeler yeniden indeksleniyor. "
            "**Belgeler** sekmesinden ilerlemeyi görebilir, işlem bitince sorunuzu "
            "tekrar sorabilirsiniz." if started else str(exc)
        )
        yield {"type": "delta", "text": message}
        yield {"type": "done", "content": message,
               "meta": {"gate": "reindexing", "error": str(exc)}}
        return

    hits: List[Dict[str, Any]] = found["hits"]
    sources = [
        {"n": i + 1, "doc_name": h["doc_name"], "ordinal": h["ordinal"],
         "score": h["score"], "text": h["text"]}
        for i, h in enumerate(hits)
    ]
    meta = {
        "best_score": found["best"],
        "reject_below": found["reject_below"],
        "verify_below": found["verify_below"],
        "embedder": found["embedder"],
        "gate": "answer",
    }

    if not hits:
        yield {"type": "sources", "sources": []}
        if _general_enabled(settings) and not smalltalk.needs_live_data(question):
            yield from _general_knowledge_stream(question, history, settings, lang, meta, stop_flag)
            return
        text = EMPTY_INDEX[lang if lang in EMPTY_INDEX else "tr"]
        meta["gate"] = "empty_index"
        yield {"type": "delta", "text": text}
        yield {"type": "done", "content": text, "meta": meta}
        return

    yield {"type": "sources", "sources": sources}

    gate_on = bool(settings.get("gate_enabled", True))
    best = found["best"]
    context = build_context(hits)

    if gate_on and best < found["reject_below"]:
        meta["gate"] = "rejected"
        # Anlık veri isteyen sorularda "belge ekleyin" demek yanıltıcı olur:
        # eklenecek belge yok, bilgi cihazda hiç bulunmuyor.
        if smalltalk.needs_live_data(question):
            meta["gate"] = "no_live_data"
            text = smalltalk.live_data_reply(lang)
        elif _general_enabled(settings):
            # Anlık veri soruları hariç: model kendi bilgisiyle cevaplayabilir
            yield from _general_knowledge_stream(question, history, settings, lang, meta, stop_flag)
            return
        else:
            text = REFUSAL[lang if lang in REFUSAL else "tr"]
        yield {"type": "delta", "text": text}
        yield {"type": "done", "content": text, "meta": meta}
        return

    status = llm.status(settings)
    if not (status["online"] and status.get("ready")):
        meta["gate"] = "extractive"
        text = _extractive_answer(hits, lang)
        yield {"type": "delta", "text": text}
        yield {"type": "done", "content": text, "meta": meta}
        return

    if gate_on and best < found["verify_below"]:
        yield {"type": "status", "text": "Bağlam doğrulanıyor…" if lang == "tr" else "Verifying context…"}
        # Doğrulama yalnızca en alakalı parçayla yapılır: tüm bağlam
        # verildiğinde alakasız parçalar küçük modeli şaşırtıp iyi cevapları
        # da reddettiriyor (ölçümde 1/5'e karşı 5/5 doğruluk).
        top_chunk = max(hits, key=lambda h: h["score"])["text"]
        if not _verify_with_model(question, top_chunk, settings):
            if _general_enabled(settings) and not smalltalk.needs_live_data(question):
                yield from _general_knowledge_stream(question, history, settings, lang, meta, stop_flag)
                return
            meta["gate"] = "verify_failed"
            text = REFUSAL[lang if lang in REFUSAL else "tr"]
            yield {"type": "delta", "text": text}
            yield {"type": "done", "content": text, "meta": meta}
            return
        meta["gate"] = "verified"

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": settings.get("system_prompt", config.DEFAULT_SYSTEM_PROMPT)}
    ]
    for turn in (history or [])[-6:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({
        "role": "user",
        "content": f"BAĞLAM:\n{context}\n\nSORU: {question}\n\n"
                   "Yalnızca yukarıdaki bağlamı kullanarak cevap ver. "
                   "KAYNAK başlıklarını cevabına kopyalama; atıfları yalnızca "
                   "cümlenin sonunda [1], [2] biçiminde yaz. Doğrudan cevapla, "
                   "aynı cümleyi tekrar etme.",
    })
    meta["model"] = status["model"]
    meta["provider"] = status["provider"]

    collected: List[str] = []
    try:
        stream = llm.filter_thinking(llm.chat_stream(messages, settings, stop_flag=stop_flag))
        for piece in stream:
            collected.append(piece)
            yield {"type": "delta", "text": piece}
    except Exception as exc:
        if collected:
            text = "".join(collected)
            yield {"type": "done", "content": text, "meta": {**meta, "error": str(exc)}}
            return
        meta["gate"] = "extractive"
        text = _extractive_answer(hits, lang)
        yield {"type": "delta", "text": text}
        yield {"type": "done", "content": text, "meta": {**meta, "error": str(exc)}}
        return

    yield {"type": "done", "content": clean_answer("".join(collected)), "meta": meta}
