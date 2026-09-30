"""Selamlaşma ve "sen kimsin" türü mesajlar için sohbet şeridi.

Alaka kapısı yalnızca belgelere benzerliğe bakar; "merhaba nasılsın" bu ölçüde
düşük puan aldığı için kapsam dışı bir soru sanılıp reddediliyordu. Oysa bu bir
soru değil, sohbet. Bu modül böyle mesajları erişimden önce yakalar ve modele
hiç gitmeden anında cevaplar — alıntı modunda da çalışır.

Eşleşme bilerek dar tutulmuştur: uzun cümleler ve belgelere dair gerçek sorular
buraya düşmez, RAG hattına gider.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .embeddings import fold

PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)

# Mesajın tamamı bunlardan biriyse (kısa, tek başına anlamlı kalıplar)
EXACT = {
    "greeting": {
        "merhaba", "merhabalar", "selam", "selamlar", "selamun aleykum",
        "gunaydin", "iyi gunler", "iyi aksamlar", "hey", "alo",
        "hi", "hello", "hey there", "good morning", "good evening",
    },
    "howareyou": {"naber", "ne haber", "nasilsin", "nasilsiniz", "napiyorsun"},
    "thanks": {"tesekkurler", "tesekkur ederim", "sagol", "sag ol", "sagolun",
               "eyvallah", "tesekkurs", "thanks", "thank you", "ty"},
    "bye": {"gorusuruz", "hosca kal", "hoscakal", "bay bay", "baybay",
            "iyi geceler", "bye", "goodbye", "see you"},
    "identity": {"kimsin", "sen kimsin", "nesin", "sen nesin", "adin ne",
                 "yardim", "help", "who are you", "what are you"},
}

# Mesajın içinde geçmesi yeterli (yalnızca kısa mesajlarda denenir)
CONTAINS = {
    "howareyou": ("nasilsin", "nasilsiniz", "how are you"),
    "thanks": ("tesekkur", "sag ol", "sagol", "thank"),
    "identity": ("ne yapabilirsin", "neler yapabilirsin", "ne ise yararsin",
                 "ne ise yariyorsun", "kendini tanit", "what can you do",
                 "sen kimsin", "who are you"),
    "greeting": ("merhaba", "selam", "gunaydin"),
}

MAX_WORDS = 8  # bundan uzun mesajlar gerçek soru sayılır


def normalize(text: str) -> str:
    return PUNCT_RE.sub(" ", fold(text).lower()).strip()


def detect(text: str) -> Optional[str]:
    """Mesajın sohbet kalıbı türünü döndürür, yoksa None."""
    normalized = " ".join(normalize(text).split())
    if not normalized:
        return None

    for kind, phrases in EXACT.items():
        if normalized in phrases:
            return kind

    if len(normalized.split()) > MAX_WORDS:
        return None

    # "ne yapabilirsin" gibi yetenek soruları selamlamadan önce gelmeli
    for kind in ("identity", "thanks", "howareyou", "greeting"):
        for phrase in CONTAINS.get(kind, ()):
            if phrase in normalized:
                return kind
    return None


def _doc_line(documents: List[str], lang: str) -> str:
    if not documents:
        return ("Şu an hiç belge indekslenmemiş — **Belgeler** sekmesinden dosya ekleyebilirsiniz."
                if lang == "tr" else
                "No documents are indexed yet — add files from the **Documents** tab.")
    shown = ", ".join(f"`{name}`" for name in documents[:5])
    more = f" (+{len(documents) - 5})" if len(documents) > 5 else ""
    return (f"Şu an {len(documents)} belge indeksli: {shown}{more}."
            if lang == "tr" else
            f"{len(documents)} documents are indexed: {shown}{more}.")


def reply(kind: str, lang: str, documents: List[str]) -> str:
    tr = lang != "en"
    docs = _doc_line(documents, "tr" if tr else "en")

    if kind == "greeting":
        return ("Merhaba! Ben belgelerinizden cevap veren yerel bir asistanım. "
                f"{docs}\n\nBu belgelerle ilgili ne öğrenmek istersiniz?"
                if tr else
                f"Hello! I'm a local assistant that answers from your documents. {docs}"
                "\n\nWhat would you like to know?")

    if kind == "howareyou":
        return ("İyiyim, teşekkürler — tamamen cihazınızda çalışıyorum, "
                f"internete hiç çıkmıyorum. {docs}\n\nSormak istediğiniz bir şey var mı?"
                if tr else
                "I'm well, thanks — I run entirely on your machine and never go online. "
                f"{docs}\n\nAnything you'd like to ask?")

    if kind == "thanks":
        return ("Rica ederim! Başka bir sorunuz olursa buradayım."
                if tr else "You're welcome! I'm here if you need anything else.")

    if kind == "bye":
        return ("Görüşmek üzere! Sohbetiniz cihazınızda kayıtlı kalıyor."
                if tr else "See you! Your chat stays saved on this machine.")

    # identity
    return (
        "Ben **LocalLLM**, tamamen çevrimdışı çalışan bir belge asistanıyım.\n\n"
        "- Sorunuzu belgelerinizde arar, bulduğum bölümleri kaynak göstererek cevaplarım.\n"
        "- Cevap belgelerde yoksa uydurmam, açıkça \"bilmiyorum\" derim.\n"
        "- Hiçbir veri cihazınızdan çıkmaz.\n\n"
        f"{docs}\n\n**Belgeler** sekmesinden yeni dosya ekleyebilirsiniz."
        if tr else
        "I'm **LocalLLM**, a fully offline document assistant.\n\n"
        "- I search your documents and answer with citations to the passages I used.\n"
        "- If the answer isn't in your documents I say so instead of making something up.\n"
        "- No data ever leaves this machine.\n\n"
        f"{docs}\n\nYou can add files from the **Documents** tab."
    )


# Canlı veri gerektiren, hiçbir belgede bulunamayacak sorular. Bunlar erişimi
# engellemez; yalnızca kapı zaten reddettiğinde daha dürüst bir mesaj verilir.
LIVE_DATA_HINTS = (
    "hava durumu", "hava nasil", "hava nasıl", "sicaklik kac", "yagmur yagacak",
    "saat kac", "bugun gunlerden", "hangi gundeyiz", "tarih nedir",
    "dolar kac", "euro kac", "doviz kuru", "altin fiyat", "borsa",
    "mac skoru", "kim kazandi", "son dakika", "haberler",
    "weather", "what time is it", "today's date", "stock price", "exchange rate",
)


def needs_live_data(text: str) -> bool:
    normalized = " ".join(normalize(text).split())
    return any(hint in normalized for hint in (normalize(h) for h in LIVE_DATA_HINTS))


def live_data_reply(lang: str) -> str:
    return (
        "Bunu bilemem: internete hiç çıkmıyorum ve cihazınızdaki belgelerde "
        "güncel hava durumu, saat, döviz veya haber gibi anlık bilgiler yok. "
        "Belge eklemek de bunu değiştirmez.\n\n"
        "Belgelerinizle ilgili bir şey sorarsanız kaynak göstererek cevaplarım."
        if lang != "en" else
        "I can't know that: I never go online, and live information like weather, "
        "time, exchange rates or news isn't in your documents. Adding a document "
        "won't change that.\n\nAsk me something about your documents and I'll answer "
        "with citations."
    )


def handle(text: str, lang: str, documents: List[str]) -> Optional[Dict[str, Any]]:
    """Sohbet kalıbıysa hazır cevabı döndürür, değilse None."""
    kind = detect(text)
    if not kind:
        return None
    return {"kind": kind, "text": reply(kind, lang, documents)}
