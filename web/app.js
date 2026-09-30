/* =========================================================
   LocalLLM — Yerel RAG Asistanı · arayüz mantığı
   Bağımlılık yok, dış istek yok. Her şey localhost üzerinde.
   ========================================================= */
(() => {
"use strict";

/* ---------------------------------------------------------
   Diller
   --------------------------------------------------------- */
const I18N = {
  tr: {
    "brand.sub": "Yerel RAG Asistanı",
    "sidebar.newChat": "Yeni sohbet",
    "sidebar.history": "Geçmiş",
    "nav.chat": "Sohbet", "nav.docs": "Belgeler", "nav.settings": "Ayarlar",
    "pill.offline": "Çevrimdışı",
    "welcome.title": "Belgelerinize sorun",
    "welcome.sub": "Sorularınız cihazınızdaki belgelerden yanıtlanır. İnternet bağlantısı gerekmez, hiçbir veri dışarı çıkmaz.",
    "composer.ph": "Belgelerinize bir soru sorun…",
    "composer.hint": "Enter ile gönder · Shift+Enter yeni satır",
    "docs.dzTitle": "Dosyaları buraya sürükleyin",
    "docs.dzSub": "veya tıklayıp seçin — .txt .md .pdf .docx .csv .json",
    "docs.addNote": "Not ekle", "docs.reindex": "Yeniden indeksle",
    "drawer.title": "Kaynak",
    "stat.docs": "belge", "stat.chunks": "parça", "stat.dim": "boyut", "stat.embed": "gömme",
    "docs.empty": "Henüz belge yok. Yukarıdan dosya yükleyerek başlayın.",
    "docs.deleted": "Belge silindi", "docs.confirmDelete": "silinsin mi?",
    "docs.uploaded": "belge indekslendi", "docs.indexing": "İndeksleniyor…",
    "docs.reindexed": "Yeniden indeksleme tamamlandı",
    "docs.notePrompt": "Not başlığı (dosya adı):", "docs.noteBody": "Not içeriğini yapıştırın:",
    "hist.empty": "Henüz sohbet yok",
    "status.checking": "Kontrol ediliyor…",
    "status.online": "Model bağlı", "status.offline": "Model bulunamadı",
    "status.noModel": "Model yüklü değil", "status.noModelSub": "sunucu açık, model indirin",
    "status.offlineSub": "Alıntı modu etkin",
    "msg.copy": "Kopyala", "msg.copied": "Kopyalandı", "msg.retry": "Yeniden sor",
    "meta.sec": "sn", "meta.score": "benzerlik",
    "gate.rejected": "belge dışı", "gate.verified": "doğrulandı",
    "gate.extractive": "alıntı modu", "gate.empty_index": "indeks boş",
    "gate.reindexing": "yeniden indeksleniyor", "gate.smalltalk": "sohbet", "gate.no_live_data": "anlık veri yok", "gate.general": "genel bilgi",
    "set.model": "Dil modeli", "set.modelSub": "Foundry Local, Ollama, LM Studio veya OpenAI uyumlu herhangi bir yerel sunucu.",
    "set.provider": "Sağlayıcı", "set.baseUrl": "Sunucu adresi",
    "set.detect": "Otomatik bul", "set.modelName": "Model adı",
    "set.modelNameDesc": "Boş bırakırsanız sunucudaki ilk sohbet modeli kullanılır.",
    "set.temp": "Yaratıcılık (temperature)", "set.maxTokens": "En fazla kelime birimi",
    "set.thinking": "Düşünme modu", "set.thinkingDesc": "qwen3 gibi modeller cevaptan önce uzun bir düşünme bloğu üretir. Açarsanız kaliteyi biraz artırabilir ama cevap çok yavaşlar ve token bütçesi dolarsa yarıda kesilebilir.",
    "set.prompt": "Sistem talimatı", "set.promptDesc": "Modelin nasıl davranacağını belirler.",
    "set.embed": "Gömme (embedding)", "set.embedSub": "Belgelerin anlamsal aramaya dönüştürülme yöntemi.",
    "set.embedProvider": "Yöntem", "set.embedModel": "Uç nokta modeli",
    "set.embedLocal": "Yerel model adı",
    "set.retrieval": "Erişim", "set.retrievalSub": "Her soruda kaç parça getirileceği ve parçaların boyutu.",
    "set.topK": "Getirilecek parça (top-K)", "set.chunkSize": "Parça boyutu (karakter)",
    "set.overlap": "Parça örtüşmesi", "set.reindexNote": "Parça ayarlarını değiştirdikten sonra yeniden indeksleyin.",
    "set.gate": "Alaka kapısı", "set.gateSub": "Benzerlik düşükse model hiç çalıştırılmaz; böylece uydurma cevap üretilmez.",
    "set.gateOn": "Alaka kapısı etkin",
    "set.reject": "Bu değerin altını reddet", "set.verify": "Bu değerin altını modele doğrulat",
    "set.general": "Genel bilgiyle cevapla",
    "set.generalDesc": "Kapalıyken asistan yalnızca belgelerinize dayanır; bulamazsa \"bilmiyorum\" der. Açtığınızda, belgelerde bulunamayan sorularda model kendi genel bilgisiyle cevap verir. Bu cevaplar kaynak göstermez ve üstlerinde \"belgelerinize dayanmıyor\" notu çıkar. Anlık veri (hava, döviz, saat) isteyen sorular yine cevaplanmaz.",
    "set.appearance": "Görünüm", "set.theme": "Tema", "set.language": "Dil",
    "set.showScores": "Benzerlik puanlarını göster",
    "set.fallback": "Yedeğe düşme nedeni",
    "set.system": "Sistem bilgisi", "set.reset": "Varsayılanlara dön",
    "set.saved": "Ayarlar kaydedildi", "set.resetDone": "Ayarlar sıfırlandı",
    "set.reindexRec": "Gömme yöntemi değişti — belgeleri yeniden indeksleyin.",
    "set.setup": "Yerel model nasıl kurulur?",
    "set.step1": "Microsoft Foundry Local'ı kurun (winget ile):",
    "set.step2": "Bir sohbet modeli indirin (Türkçe için qwen3-4b önerilir):",
    "set.step3": "Modeli belleğe yükleyin:",
    "set.step4": "Bu sayfaya dönüp \"Otomatik bul\" düğmesine basın.",
    "detect.found": "Yerel sunucu bulundu", "detect.none": "Çalışan yerel sunucu bulunamadı",
    "err.generic": "Bir hata oluştu",
    "sugg1t": "Özet", "sugg1": "Belgelerdeki ana konuları özetle",
    "sugg2t": "Tanım", "sugg2": "En önemli kavramı açıkla",
    "sugg3t": "Karşılaştırma", "sugg3": "İki yaklaşımı karşılaştır",
    "sugg4t": "Adımlar", "sugg4": "Süreci adım adım anlat",
  },
  en: {
    "brand.sub": "Local RAG Assistant",
    "sidebar.newChat": "New chat",
    "sidebar.history": "History",
    "nav.chat": "Chat", "nav.docs": "Documents", "nav.settings": "Settings",
    "pill.offline": "Offline",
    "welcome.title": "Ask your documents",
    "welcome.sub": "Answers come from files on this device. No internet needed and nothing ever leaves your machine.",
    "composer.ph": "Ask a question about your documents…",
    "composer.hint": "Enter to send · Shift+Enter for a new line",
    "docs.dzTitle": "Drag files here",
    "docs.dzSub": "or click to pick — .txt .md .pdf .docx .csv .json",
    "docs.addNote": "Add note", "docs.reindex": "Reindex",
    "drawer.title": "Source",
    "stat.docs": "documents", "stat.chunks": "chunks", "stat.dim": "dimensions", "stat.embed": "embedding",
    "docs.empty": "No documents yet. Upload a file above to get started.",
    "docs.deleted": "Document removed", "docs.confirmDelete": "— delete it?",
    "docs.uploaded": "documents indexed", "docs.indexing": "Indexing…",
    "docs.reindexed": "Reindexing finished",
    "docs.notePrompt": "Note title (file name):", "docs.noteBody": "Paste the note content:",
    "hist.empty": "No chats yet",
    "status.checking": "Checking…",
    "status.online": "Model connected", "status.offline": "No model found",
    "status.noModel": "No model loaded", "status.noModelSub": "server up, download a model",
    "status.offlineSub": "Excerpt mode active",
    "msg.copy": "Copy", "msg.copied": "Copied", "msg.retry": "Ask again",
    "meta.sec": "s", "meta.score": "similarity",
    "gate.rejected": "out of scope", "gate.verified": "verified",
    "gate.extractive": "excerpt mode", "gate.empty_index": "empty index",
    "gate.reindexing": "reindexing", "gate.smalltalk": "chat", "gate.no_live_data": "no live data", "gate.general": "general knowledge",
    "set.model": "Language model", "set.modelSub": "Foundry Local, Ollama, LM Studio or any OpenAI-compatible local server.",
    "set.provider": "Provider", "set.baseUrl": "Server address",
    "set.detect": "Auto-detect", "set.modelName": "Model name",
    "set.modelNameDesc": "Leave empty to use the first chat model on the server.",
    "set.temp": "Creativity (temperature)", "set.maxTokens": "Max tokens",
    "set.thinking": "Thinking mode", "set.thinkingDesc": "Models like qwen3 emit a long reasoning block before answering. Enabling it may help slightly but is much slower and can truncate the answer.",
    "set.prompt": "System prompt", "set.promptDesc": "Defines how the model behaves.",
    "set.embed": "Embeddings", "set.embedSub": "How documents are turned into semantic search vectors.",
    "set.embedProvider": "Method", "set.embedModel": "Endpoint model",
    "set.embedLocal": "Local model name",
    "set.retrieval": "Retrieval", "set.retrievalSub": "How many chunks each question pulls in, and how big they are.",
    "set.topK": "Chunks per query (top-K)", "set.chunkSize": "Chunk size (characters)",
    "set.overlap": "Chunk overlap", "set.reindexNote": "Reindex after changing chunk settings.",
    "set.gate": "Relevance gate", "set.gateSub": "When similarity is low the model is never called, so nothing gets made up.",
    "set.gateOn": "Relevance gate enabled",
    "set.reject": "Reject below", "set.verify": "Verify with model below",
    "set.general": "Answer from general knowledge",
    "set.generalDesc": "When off, the assistant relies only on your documents and says \"I don't know\" otherwise. When on, questions not found in your documents are answered from the model's own knowledge, without citations and with a clear \"not based on your documents\" note. Live-data questions (weather, rates, time) are still declined.",
    "set.appearance": "Appearance", "set.theme": "Theme", "set.language": "Language",
    "set.showScores": "Show similarity scores",
    "set.fallback": "Fallback reason",
    "set.system": "System info", "set.reset": "Restore defaults",
    "set.saved": "Settings saved", "set.resetDone": "Settings reset",
    "set.reindexRec": "Embedding method changed — please reindex your documents.",
    "set.setup": "How to set up a local model",
    "set.step1": "Install Microsoft Foundry Local (via winget):",
    "set.step2": "Download a chat model (qwen3-4b works well for Turkish):",
    "set.step3": "Load the model into memory:",
    "set.step4": "Come back here and press \"Auto-detect\".",
    "detect.found": "Local server found", "detect.none": "No running local server found",
    "err.generic": "Something went wrong",
    "sugg1t": "Summary", "sugg1": "Summarise the main topics in the documents",
    "sugg2t": "Definition", "sugg2": "Explain the most important concept",
    "sugg3t": "Comparison", "sugg3": "Compare two approaches",
    "sugg4t": "Steps", "sugg4": "Walk through the process step by step",
  },
};

let LANG = "tr";
const t = (key) => (I18N[LANG] && I18N[LANG][key]) || I18N.tr[key] || key;

/* ---------------------------------------------------------
   Kısayollar
   --------------------------------------------------------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const el = (tag, cls, html) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (html != null) node.innerHTML = html;
  return node;
};
const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const state = {
  settings: {},
  status: null,
  conversationId: null,
  messages: [],
  busy: false,
  abort: null,
  view: "chat",
};

/* ---------------------------------------------------------
   API
   --------------------------------------------------------- */
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

/* ---------------------------------------------------------
   Bildirim
   --------------------------------------------------------- */
function toast(message, kind = "") {
  const node = el("div", `toast ${kind}`, `<i class="bar"></i><span>${esc(message)}</span>`);
  $("#toasts").appendChild(node);
  setTimeout(() => {
    node.classList.add("out");
    setTimeout(() => node.remove(), 250);
  }, 3400);
}

/* ---------------------------------------------------------
   Markdown (küçük, güvenli)
   --------------------------------------------------------- */
function markdown(src) {
  const blocks = [];
  let text = esc(src || "");

  // kod blokları
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    blocks.push(`<pre><button class="copy-code" data-copy>${esc(t("msg.copy"))}</button><code>${code.replace(/\n$/, "")}</code></pre>`);
    return ` B${blocks.length - 1} `;
  });
  // satır içi kod
  text = text.replace(/`([^`\n]+)`/g, (_, code) => {
    blocks.push(`<code>${code}</code>`);
    return ` B${blocks.length - 1} `;
  });

  const lines = text.split("\n");
  const out = [];
  let list = null, para = [], quote = [];

  const flushPara = () => { if (para.length) { out.push(`<p>${para.join("<br>")}</p>`); para = []; } };
  const flushList = () => { if (list) { out.push(`</${list}>`); list = null; } };
  const flushQuote = () => { if (quote.length) { out.push(`<blockquote>${quote.join("<br>")}</blockquote>`); quote = []; } };
  const flushAll = () => { flushPara(); flushList(); flushQuote(); };

  for (const raw of lines) {
    const line = raw.trimEnd();

    if (!line.trim()) { flushAll(); continue; }

    let match;
    if ((match = line.match(/^(#{1,4})\s+(.*)$/))) {
      flushAll();
      const level = Math.min(match[1].length + 1, 4);
      out.push(`<h${level}>${inline(match[2])}</h${level}>`);
      continue;
    }
    if (/^\s*([-*_])\s*\1\s*\1[\s-*_]*$/.test(line)) { flushAll(); out.push("<hr>"); continue; }
    // metin önce kaçışlandığı için ">" burada "&gt;" olarak gelir
    if ((match = line.match(/^\s*(?:>|&gt;)\s?(.*)$/))) { flushPara(); flushList(); quote.push(inline(match[1])); continue; }
    if ((match = line.match(/^\s*[-*+]\s+(.*)$/))) {
      flushPara(); flushQuote();
      if (list !== "ul") { flushList(); out.push("<ul>"); list = "ul"; }
      out.push(`<li>${inline(match[1])}</li>`);
      continue;
    }
    if ((match = line.match(/^\s*\d+[.)]\s+(.*)$/))) {
      flushPara(); flushQuote();
      if (list !== "ol") { flushList(); out.push("<ol>"); list = "ol"; }
      out.push(`<li>${inline(match[1])}</li>`);
      continue;
    }
    flushList(); flushQuote();
    para.push(inline(line));
  }
  flushAll();

  let html = out.join("");
  html = html.replace(/ B(\d+) /g, (_, i) => blocks[+i]);
  return html;
}

function inline(s) {
  return s
    .replace(/\*\*\*([^*]+)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/(^|[\s(])_([^_\n]+)_/g, "$1<em>$2</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

/* ---------------------------------------------------------
   Dil / tema
   --------------------------------------------------------- */
function applyLanguage(lang) {
  LANG = I18N[lang] ? lang : "tr";
  document.documentElement.lang = LANG;
  $$("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
  $$("[data-i18n-ph]").forEach((node) => { node.placeholder = t(node.dataset.i18nPh); });
  $("#langBtn").textContent = LANG.toUpperCase();
  $("#viewTitle").textContent = t(`nav.${state.view}`);
  renderSuggestions();
  renderStatus();
  if (state.view === "settings") renderSettings();
  if (state.view === "docs") loadDocuments();
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme === "light" ? "light" : "dark";
}

/* ---------------------------------------------------------
   Görünümler
   --------------------------------------------------------- */
function showView(view) {
  state.view = view;
  $$(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${view}`));
  $("#viewTitle").textContent = t(`nav.${view}`);
  document.body.classList.remove("nav-open");
  if (view === "docs") loadDocuments();
  if (view === "settings") renderSettings();
  if (view === "chat") setTimeout(() => $("#input").focus(), 80);
}

/* ---------------------------------------------------------
   Durum çubuğu
   --------------------------------------------------------- */
async function refreshStatus() {
  try {
    state.status = await api("/api/status");
  } catch (_) { state.status = null; }
  renderStatus();
  renderIndexProgress();
}

function renderStatus() {
  const dot = $("#statusDot"), title = $("#statusTitle"), sub = $("#statusSub"), pill = $("#modelPill");
  const status = state.status;
  if (!status) {
    dot.className = "dot"; title.textContent = t("status.checking"); sub.textContent = "—";
    pill.textContent = "—";
    return;
  }
  $("#docBadge").textContent = status.index.documents ?? 0;

  if (status.llm.online && status.llm.ready) {
    dot.className = "dot on";
    title.textContent = t("status.online");
    sub.textContent = `${status.llm.provider} · ${shortModel(status.llm.model)}`;
    pill.textContent = shortModel(status.llm.model);
    pill.title = `${status.llm.provider} — ${status.llm.base_url}`;
  } else if (status.llm.online) {
    // Sunucu ayakta ama hiçbir model yüklü değil
    dot.className = "dot warn";
    title.textContent = t("status.noModel");
    sub.textContent = `${status.llm.provider} · ${t("status.noModelSub")}`;
    pill.textContent = t("status.noModel");
    pill.title = status.llm.base_url;
  } else {
    dot.className = "dot warn";
    title.textContent = t("status.offline");
    sub.textContent = t("status.offlineSub");
    pill.textContent = t("status.offlineSub");
    pill.title = "";
  }
}

const shortModel = (name) => {
  if (!name) return "—";
  return name.length > 30 ? name.slice(0, 28) + "…" : name;
};

/* ---------------------------------------------------------
   Sohbet
   --------------------------------------------------------- */
function renderSuggestions() {
  const box = $("#suggestions");
  if (!box) return;
  box.innerHTML = "";
  [1, 2, 3, 4].forEach((i) => {
    const text = t(`sugg${i}`);
    const button = el("button", "suggestion", `<b>${esc(t(`sugg${i}t`))}</b>${esc(text)}`);
    button.addEventListener("click", () => { $("#input").value = text; send(); });
    box.appendChild(button);
  });
}

function clearChat() {
  $("#chatInner").innerHTML = "";
  const welcome = el("div", "welcome");
  welcome.id = "welcome";
  welcome.innerHTML = `
    <div class="welcome-mark">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a3 3 0 0 0-3 3v.2A2.8 2.8 0 0 0 6.5 9v.3A3 3 0 0 0 5 12a3 3 0 0 0 1.5 2.6v.4A2.8 2.8 0 0 0 9 17.8V18a3 3 0 0 0 6 0v-.2a2.8 2.8 0 0 0 2.5-2.8v-.4A3 3 0 0 0 19 12a3 3 0 0 0-1.5-2.7V9A2.8 2.8 0 0 0 15 6.2V6a3 3 0 0 0-3-3Z"/>
        <path d="M12 8v8M9.5 10.5h5M9.5 13.5h5"/>
      </svg>
    </div>
    <h2 data-i18n="welcome.title">${esc(t("welcome.title"))}</h2>
    <p data-i18n="welcome.sub">${esc(t("welcome.sub"))}</p>
    <div class="suggestions" id="suggestions"></div>`;
  $("#chatInner").appendChild(welcome);
  renderSuggestions();
}

const ASSISTANT_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a3 3 0 0 0-3 3v.2A2.8 2.8 0 0 0 6.5 9v.3A3 3 0 0 0 5 12a3 3 0 0 0 1.5 2.6v.4A2.8 2.8 0 0 0 9 17.8V18a3 3 0 0 0 6 0v-.2a2.8 2.8 0 0 0 2.5-2.8v-.4A3 3 0 0 0 19 12a3 3 0 0 0-1.5-2.7V9A2.8 2.8 0 0 0 15 6.2V6a3 3 0 0 0-3-3Z"/><path d="M12 8v8M9.5 10.5h5M9.5 13.5h5"/></svg>`;

function addMessage(role, content, sources, meta) {
  $("#welcome")?.remove();
  const wrap = el("div", `msg ${role}`);
  const avatar = el("div", "avatar", role === "assistant" ? ASSISTANT_ICON : "S");
  if (role === "user") avatar.textContent = "S";
  const body = el("div", "bubble-wrap");
  const bubble = el("div", "bubble");
  bubble.innerHTML = role === "assistant" ? markdown(content || "") : esc(content).replace(/\n/g, "<br>");
  body.appendChild(bubble);
  wrap.append(avatar, body);
  $("#chatInner").appendChild(wrap);

  // Boş balon akış için yer tutucudur; ekleri akış bitince decorate() kurar.
  if (role === "assistant" && content) decorate(body, content, sources, meta);
  scrollDown();
  return { wrap, body, bubble };
}

/** Balonun altındaki kaynak, meta/araç satırlarını sıfırdan kurar. */
function decorate(body, content, sources, meta) {
  while (body.children.length > 1) body.lastElementChild.remove();
  if (sources && sources.length) body.appendChild(buildSources(sources));
  if (meta) body.appendChild(buildMeta(meta));
  body.appendChild(buildTools(content));
}

function buildSources(sources) {
  const box = el("div", "sources");
  sources.forEach((source) => {
    const chip = el("button", "src-chip");
    const score = state.settings.show_scores !== false
      ? `<span class="score">${Math.round(source.score * 100)}%</span>` : "";
    chip.innerHTML = `<span class="n">${source.n}</span><span class="name">${esc(source.doc_name)}</span>${score}`;
    chip.addEventListener("click", () => openDrawer(source));
    box.appendChild(chip);
  });
  return box;
}

function buildMeta(meta) {
  const row = el("div", "meta-line");
  const chips = [];
  if (meta.gate && meta.gate !== "answer") {
    chips.push(`<span class="meta-chip gate-${meta.gate}">${esc(t(`gate.${meta.gate}`) || meta.gate)}</span>`);
  }
  if (meta.model) chips.push(`<span class="meta-chip">${esc(shortModel(meta.model))}</span>`);
  if (meta.elapsed != null) chips.push(`<span class="meta-chip">${meta.elapsed} ${esc(t("meta.sec"))}</span>`);
  if (state.settings.show_scores !== false && meta.best_score != null) {
    chips.push(`<span class="meta-chip">${esc(t("meta.score"))} ${Math.round(meta.best_score * 100)}%</span>`);
  }
  row.innerHTML = chips.join("");
  return row;
}

function buildTools(content) {
  const tools = el("div", "msg-tools");
  const copy = el("button", "", `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>${esc(t("msg.copy"))}`);
  copy.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(content); toast(t("msg.copied"), "ok"); } catch (_) {}
  });
  tools.appendChild(copy);
  return tools;
}

function scrollDown() {
  const scroller = $("#chatScroll");
  scroller.scrollTop = scroller.scrollHeight;
}

async function send(question) {
  if (state.busy) { stop(); return; }
  const input = $("#input");
  const text = (question ?? input.value).trim();
  if (!text) return;

  input.value = "";
  input.style.height = "auto";
  addMessage("user", text);
  state.messages.push({ role: "user", content: text });

  const { body, bubble } = addMessage("assistant", "");
  bubble.innerHTML = `<div class="typing"><i></i><i></i><i></i></div>`;

  setBusy(true);
  const controller = new AbortController();
  state.abort = controller;

  let answer = "", sources = [], meta = null, first = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        question: text,
        conversation_id: state.conversationId,
        history: state.messages.slice(0, -1).slice(-6),
      }),
    });
    if (!response.ok || !response.body) throw new Error(response.statusText);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        let event;
        try { event = JSON.parse(payload); } catch (_) { continue; }

        if (event.type === "conversation") {
          if (state.conversationId !== event.id) { state.conversationId = event.id; loadConversations(); }
        } else if (event.type === "sources") {
          sources = event.sources || [];
        } else if (event.type === "status") {
          bubble.innerHTML = `<div class="typing"><i></i><i></i><i></i></div><small style="color:var(--text-3)">${esc(event.text)}</small>`;
        } else if (event.type === "delta") {
          if (first) { bubble.innerHTML = ""; first = false; }
          answer += event.text;
          bubble.innerHTML = markdown(answer) + '<span class="cursor"></span>';
          scrollDown();
        } else if (event.type === "done") {
          meta = event.meta || {};
          if (event.content) answer = event.content;
        } else if (event.type === "error") {
          throw new Error(event.message || t("err.generic"));
        }
      }
    }
  } catch (error) {
    if (error.name !== "AbortError") {
      answer = answer || `⚠️ ${error.message || t("err.generic")}`;
      toast(error.message || t("err.generic"), "err");
    }
  }

  bubble.innerHTML = markdown(answer);
  decorate(body, answer, sources, meta);
  state.messages.push({ role: "assistant", content: answer });
  setBusy(false);
  scrollDown();
  refreshStatus();
}

function stop() {
  state.abort?.abort();
  setBusy(false);
}

function setBusy(busy) {
  state.busy = busy;
  document.body.classList.toggle("busy", busy);
}

/* ---------------------------------------------------------
   Kaynak paneli
   --------------------------------------------------------- */
function openDrawer(source) {
  const ext = (source.doc_name.split(".").pop() || "txt").slice(0, 4);
  $("#drawerBody").innerHTML = `
    <div class="drawer-doc">
      <div class="doc-icon">${esc(ext)}</div>
      <div>
        <strong>${esc(source.doc_name)}</strong>
        <span>${t("nav.docs")} · #${source.ordinal + 1}</span>
      </div>
    </div>
    <div class="meta-line" style="margin-bottom:4px">
      <span>${esc(t("meta.score"))}: <b>${Math.round(source.score * 100)}%</b></span>
    </div>
    <div class="score-bar"><i style="width:${Math.max(3, Math.min(100, source.score * 100))}%"></i></div>
    <div class="chunk-text">${esc(source.text)}</div>`;
  $("#drawer").classList.add("open");
}

/* ---------------------------------------------------------
   Sohbet geçmişi
   --------------------------------------------------------- */
async function loadConversations() {
  let items = [];
  try { items = (await api("/api/conversations")).conversations; } catch (_) {}
  const list = $("#historyList");
  list.innerHTML = "";
  if (!items.length) {
    list.appendChild(el("div", "history-empty", esc(t("hist.empty"))));
    return;
  }
  items.forEach((item) => {
    const row = el("button", "hist-item" + (item.id === state.conversationId ? " active" : ""));
    row.innerHTML = `<span>${esc(item.title || t("sidebar.newChat"))}</span>
      <i class="del" title="Sil"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg></i>`;
    row.addEventListener("click", (event) => {
      if (event.target.closest(".del")) {
        api(`/api/conversations/${item.id}`, { method: "DELETE" }).then(() => {
          if (state.conversationId === item.id) newChat();
          loadConversations();
        });
        return;
      }
      openConversation(item.id);
    });
    list.appendChild(row);
  });
}

async function openConversation(id) {
  state.conversationId = id;
  state.messages = [];
  $("#chatInner").innerHTML = "";
  showView("chat");
  const { messages } = await api(`/api/conversations/${id}`);
  messages.forEach((message) => {
    addMessage(message.role, message.content, message.sources, null);
    state.messages.push({ role: message.role, content: message.content });
  });
  if (!messages.length) clearChat();
  loadConversations();
}

function newChat() {
  state.conversationId = null;
  state.messages = [];
  clearChat();
  showView("chat");
  loadConversations();
}

/* ---------------------------------------------------------
   Belgeler
   --------------------------------------------------------- */
const formatBytes = (bytes) => {
  if (!bytes) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
};

async function loadDocuments() {
  let data;
  try { data = await api("/api/documents"); } catch (_) { return; }
  const stats = data.stats || {};
  $("#docBadge").textContent = stats.documents ?? 0;

  $("#statRow").innerHTML = [
    `<div class="stat"><b>${stats.documents ?? 0}</b><span>${esc(t("stat.docs"))}</span></div>`,
    `<div class="stat"><b>${stats.chunks ?? 0}</b><span>${esc(t("stat.chunks"))}</span></div>`,
    `<div class="stat"><b>${stats.dim ?? 0}</b><span>${esc(t("stat.dim"))}</span></div>`,
  ].join("");

  const list = $("#docList");
  list.innerHTML = "";
  if (!data.documents.length) {
    list.appendChild(el("div", "empty", esc(t("docs.empty"))));
    return;
  }
  data.documents.forEach((doc) => {
    const card = el("div", "doc-card");
    card.innerHTML = `
      <div class="doc-icon">${esc((doc.kind || "txt").slice(0, 4))}</div>
      <div class="doc-info">
        <strong>${esc(doc.name)}</strong>
        <span>${doc.chunk_count} ${esc(t("stat.chunks"))} · ${formatBytes(doc.bytes)}</span>
      </div>
      <button class="icon-btn" title="Sil">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>
      </button>`;
    card.querySelector("button").addEventListener("click", async () => {
      if (!confirm(`"${doc.name}" ${t("docs.confirmDelete")}`)) return;
      await api(`/api/documents/${doc.id}`, { method: "DELETE" });
      toast(t("docs.deleted"), "ok");
      loadDocuments(); refreshStatus();
    });
    list.appendChild(card);
  });
}

async function uploadFiles(files) {
  if (!files.length) return;
  const form = new FormData();
  [...files].forEach((file) => form.append("files", file));
  showProgress(true, t("docs.indexing"), 30);
  try {
    const result = await api("/api/documents/upload", { method: "POST", body: form });
    showProgress(false);
    if (result.errors?.length) result.errors.forEach((e) => toast(`${e.name}: ${e.error}`, "err"));
    if (result.saved?.length) toast(`${result.saved.length} ${t("docs.uploaded")}`, "ok");
    loadDocuments(); refreshStatus();
  } catch (error) {
    showProgress(false);
    toast(error.message || t("err.generic"), "err");
  }
}

function showProgress(visible, label = "", percent = 0) {
  const box = $("#indexProgress");
  box.hidden = !visible;
  if (visible) {
    $("#progressFill").style.width = `${percent}%`;
    $("#progressLabel").textContent = label;
  }
}

async function reindex() {
  $("#reindexBtn").disabled = true;
  showProgress(true, t("docs.indexing"), 5);
  try {
    await api("/api/reindex", { method: "POST" });
    await pollIndexing();
    toast(t("docs.reindexed"), "ok");
  } catch (error) {
    toast(error.message || t("err.generic"), "err");
  }
  showProgress(false);
  $("#reindexBtn").disabled = false;
  loadDocuments(); refreshStatus();
}

async function pollIndexing() {
  for (;;) {
    await new Promise((r) => setTimeout(r, 500));
    let status;
    try { status = await api("/api/reindex/status"); } catch (_) { return; }
    const percent = status.total ? Math.round((status.current / status.total) * 100) : 8;
    showProgress(true, `${status.file || ""} ${status.total ? `(${status.current}/${status.total})` : ""}`.trim() || t("docs.indexing"), percent);
    if (!status.running) return;
  }
}

function renderIndexProgress() {
  const indexing = state.status?.indexing;
  if (indexing?.running && state.view === "docs") {
    const percent = indexing.total ? Math.round((indexing.current / indexing.total) * 100) : 8;
    showProgress(true, `${indexing.file || ""}`.trim() || t("docs.indexing"), percent);
  }
}

/* ---------------------------------------------------------
   Ayarlar
   --------------------------------------------------------- */
function field(label, control, desc) {
  return `<div class="field"><label>${esc(label)}</label>${control}${desc ? `<div class="desc">${esc(desc)}</div>` : ""}</div>`;
}

function renderSettings() {
  const s = state.settings;
  const status = state.status || { llm: {}, embedder: {}, index: {}, gate: {} };
  const page = $("#settingsPage");

  const providerOptions = [
    ["auto", "Otomatik"], ["foundry", "Foundry Local"], ["ollama", "Ollama"],
    ["custom", "Özel / Custom"], ["none", "Kapalı"],
  ].map(([v, l]) => `<option value="${v}"${s.llm_provider === v ? " selected" : ""}>${l}</option>`).join("");

  const embedOptions = [
    ["auto", "Otomatik"], ["endpoint", "Foundry / uç nokta"],
    ["local", "sentence-transformers"], ["hash", "Yerel hash (modelsiz)"],
  ].map(([v, l]) => `<option value="${v}"${s.embed_provider === v ? " selected" : ""}>${l}</option>`).join("");

  const modelList = (status.llm.models || []).length
    ? `<div class="desc">${status.llm.models.slice(0, 8).map(esc).join(" · ")}</div>` : "";

  page.innerHTML = `
    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9zM9 2v2M15 2v2M9 20v2M15 20v2M2 9h2M2 15h2M20 9h2M20 15h2"/></svg>${esc(t("set.model"))}</h3>
      <p class="card-sub">${esc(t("set.modelSub"))}</p>
      ${field(t("set.provider"), `<select id="set-llm_provider">${providerOptions}</select>`)}
      ${field(t("set.baseUrl"), `<div class="detect-row">
        <input type="text" id="set-llm_base_url" value="${esc(s.llm_base_url || "")}" placeholder="http://localhost:5273/v1">
        <button class="btn ghost" id="detectBtn">${esc(t("set.detect"))}</button></div>`)}
      ${field(t("set.modelName"), `<input type="text" id="set-llm_model" value="${esc(s.llm_model || "")}" placeholder="phi-3.5-mini">${modelList}`, t("set.modelNameDesc"))}
      ${field(t("set.temp"), `<div class="range-row"><input type="range" id="set-temperature" min="0" max="1" step="0.05" value="${s.temperature}"><span class="range-val" data-for="set-temperature">${s.temperature}</span></div>`)}
      ${field(t("set.maxTokens"), `<div class="range-row"><input type="range" id="set-max_tokens" min="128" max="4096" step="32" value="${s.max_tokens}"><span class="range-val" data-for="set-max_tokens">${s.max_tokens}</span></div>`)}
      <div class="field switch">
        <label style="margin:0">${esc(t("set.thinking"))}</label>
        <div class="switch-box${s.thinking ? " on" : ""}" id="set-thinking"></div>
      </div>
      <div class="desc" style="margin:-10px 0 15px">${esc(t("set.thinkingDesc"))}</div>
      ${field(t("set.prompt"), `<textarea class="setting" id="set-system_prompt">${esc(s.system_prompt || "")}</textarea>`, t("set.promptDesc"))}
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18M3 12h18"/></svg>${esc(t("set.embed"))}</h3>
      <p class="card-sub">${esc(t("set.embedSub"))}</p>
      ${field(t("set.embedProvider"), `<select id="set-embed_provider">${embedOptions}</select>`)}
      ${field(t("set.embedModel"), `<input type="text" id="set-embed_model" value="${esc(s.embed_model || "")}" placeholder="qwen3-embedding-0.6b">`)}
      ${field(t("set.embedLocal"), `<input type="text" id="set-embed_local_model" value="${esc(s.embed_local_model || "")}">`)}
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>${esc(t("set.retrieval"))}</h3>
      <p class="card-sub">${esc(t("set.retrievalSub"))}</p>
      ${field(t("set.topK"), `<div class="range-row"><input type="range" id="set-top_k" min="1" max="10" step="1" value="${s.top_k}"><span class="range-val" data-for="set-top_k">${s.top_k}</span></div>`)}
      ${field(t("set.chunkSize"), `<div class="range-row"><input type="range" id="set-chunk_size" min="300" max="2000" step="50" value="${s.chunk_size}"><span class="range-val" data-for="set-chunk_size">${s.chunk_size}</span></div>`)}
      ${field(t("set.overlap"), `<div class="range-row"><input type="range" id="set-chunk_overlap" min="0" max="500" step="25" value="${s.chunk_overlap}"><span class="range-val" data-for="set-chunk_overlap">${s.chunk_overlap}</span></div>`, t("set.reindexNote"))}
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Z"/></svg>${esc(t("set.gate"))}</h3>
      <p class="card-sub">${esc(t("set.gateSub"))}</p>
      <div class="field switch">
        <label style="margin:0">${esc(t("set.gateOn"))}</label>
        <div class="switch-box${s.gate_enabled ? " on" : ""}" id="set-gate_enabled"></div>
      </div>
      ${field(t("set.reject"), `<div class="range-row"><input type="range" id="set-reject_below" min="0" max="0.9" step="0.01" value="${s.reject_below || status.gate.reject_below || 0.1}"><span class="range-val" data-for="set-reject_below">${(s.reject_below || status.gate.reject_below || 0.1).toFixed(2)}</span></div>`)}
      ${field(t("set.verify"), `<div class="range-row"><input type="range" id="set-verify_below" min="0" max="0.95" step="0.01" value="${s.verify_below || status.gate.verify_below || 0.2}"><span class="range-val" data-for="set-verify_below">${(s.verify_below || status.gate.verify_below || 0.2).toFixed(2)}</span></div>`)}
      <div class="field switch" style="margin-top:18px;padding-top:16px;border-top:1px solid var(--border-soft)">
        <label style="margin:0">${esc(t("set.general"))}</label>
        <div class="switch-box${s.general_knowledge ? " on" : ""}" id="set-general_knowledge"></div>
      </div>
      <div class="desc">${esc(t("set.generalDesc"))}</div>
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>${esc(t("set.appearance"))}</h3>
      ${field(t("set.theme"), `<div class="seg" id="seg-theme">
        <button data-value="dark"${s.theme !== "light" ? " class=on" : ""}>Koyu / Dark</button>
        <button data-value="light"${s.theme === "light" ? " class=on" : ""}>Açık / Light</button></div>`)}
      ${field(t("set.language"), `<div class="seg" id="seg-language">
        <button data-value="tr"${s.language !== "en" ? " class=on" : ""}>Türkçe</button>
        <button data-value="en"${s.language === "en" ? " class=on" : ""}>English</button></div>`)}
      <div class="field switch">
        <label style="margin:0">${esc(t("set.showScores"))}</label>
        <div class="switch-box${s.show_scores !== false ? " on" : ""}" id="set-show_scores"></div>
      </div>
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16v-4M12 8h.01"/><circle cx="12" cy="12" r="9"/></svg>${esc(t("set.system"))}</h3>
      <div class="info-grid">
        <div class="info-item"><span>LLM</span><strong>${esc(status.llm.online ? `${status.llm.provider} · ${status.llm.model || t("status.noModel")}` : t("status.offline"))}</strong></div>
        <div class="info-item"><span>${esc(t("stat.embed"))}</span><strong>${esc(status.embedder.kind || "—")} · ${status.embedder.dim || 0}d</strong>${status.embedder.fallback_reason ? `<div class="desc" style="margin-top:4px">${esc(t("set.fallback"))}: ${esc(status.embedder.fallback_reason)}</div>` : ""}</div>
        <div class="info-item"><span>${esc(t("stat.docs"))}</span><strong>${status.index.documents ?? 0} · ${status.index.chunks ?? 0} ${esc(t("stat.chunks"))}</strong></div>
        <div class="info-item"><span>${esc(t("set.baseUrl"))}</span><strong>${esc(status.llm.base_url || "—")}</strong></div>
      </div>
      <div class="field" style="margin-top:16px">
        <button class="btn ghost" id="resetBtn">${esc(t("set.reset"))}</button>
      </div>
    </div>

    <div class="card">
      <h3><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4M8 8l4-4 4 4"/><path d="M20 16v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-2"/></svg>${esc(t("set.setup"))}</h3>
      <div class="setup-steps">
        <div class="setup-step"><div>${esc(t("set.step1"))}<br><code>winget install Microsoft.FoundryLocal</code></div></div>
        <div class="setup-step"><div>${esc(t("set.step2"))}<br><code>foundry model download qwen3-4b</code></div></div>
        <div class="setup-step"><div>${esc(t("set.step3"))}<br><code>foundry model load qwen3-4b</code></div></div>
        <div class="setup-step"><div>${esc(t("set.step4"))}</div></div>
      </div>
    </div>`;

  bindSettings();
}

function bindSettings() {
  $$("#settingsPage input[type=range]").forEach((input) => {
    input.addEventListener("input", () => {
      const label = $(`.range-val[data-for="${input.id}"]`);
      if (label) label.textContent = input.step.includes(".") ? (+input.value).toFixed(2) : input.value;
    });
    input.addEventListener("change", () => saveSetting(input.id.replace("set-", ""), +input.value));
  });

  $$("#settingsPage select, #settingsPage input[type=text], #settingsPage textarea").forEach((input) => {
    input.addEventListener("change", () => saveSetting(input.id.replace("set-", ""), input.value));
  });

  $$("#settingsPage .switch-box").forEach((box) => {
    box.addEventListener("click", () => {
      box.classList.toggle("on");
      saveSetting(box.id.replace("set-", ""), box.classList.contains("on"));
    });
  });

  $("#seg-theme")?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-value]");
    if (!button) return;
    $$("#seg-theme button").forEach((b) => b.classList.remove("on"));
    button.classList.add("on");
    applyTheme(button.dataset.value);
    saveSetting("theme", button.dataset.value);
  });

  $("#seg-language")?.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-value]");
    if (!button) return;
    saveSetting("language", button.dataset.value).then(() => applyLanguage(button.dataset.value));
  });

  $("#detectBtn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    const button = event.currentTarget;
    button.disabled = true;
    try {
      const result = await api("/api/detect", { method: "POST" });
      if (result.found) {
        toast(`${t("detect.found")}: ${result.endpoint.base_url}`, "ok");
        state.settings.llm_base_url = result.endpoint.base_url;
      } else {
        toast(t("detect.none"), "warn");
      }
    } catch (error) { toast(error.message, "err"); }
    button.disabled = false;
    await refreshStatus();
    renderSettings();
  });

  $("#resetBtn")?.addEventListener("click", async () => {
    const { settings } = await api("/api/settings/reset", { method: "POST" });
    state.settings = settings;
    applyTheme(settings.theme);
    applyLanguage(settings.language);
    toast(t("set.resetDone"), "ok");
    await refreshStatus();
    renderSettings();
  });
}

let saveTimer = null;
async function saveSetting(key, value) {
  state.settings[key] = value;
  clearTimeout(saveTimer);
  return new Promise((resolve) => {
    saveTimer = setTimeout(async () => {
      try {
        const result = await api("/api/settings", {
          method: "POST", body: JSON.stringify({ values: { [key]: value } }),
        });
        state.settings = result.settings;
        if (result.reindex_recommended) toast(t("set.reindexRec"), "warn");
        else toast(t("set.saved"), "ok");
        refreshStatus();
      } catch (error) { toast(error.message, "err"); }
      resolve();
    }, 260);
  });
}

/* ---------------------------------------------------------
   Olay bağlantıları
   --------------------------------------------------------- */
function bindGlobal() {
  $$(".nav-item").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));
  $("#newChatBtn").addEventListener("click", newChat);
  $("#menuBtn").addEventListener("click", () => document.body.classList.add("nav-open"));
  $("#sidebarClose").addEventListener("click", () => document.body.classList.remove("nav-open"));
  $("#scrim").addEventListener("click", () => document.body.classList.remove("nav-open"));
  $("#drawerClose").addEventListener("click", () => $("#drawer").classList.remove("open"));

  $("#themeBtn").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
    saveSetting("theme", next);
  });
  $("#langBtn").addEventListener("click", () => {
    const next = LANG === "tr" ? "en" : "tr";
    applyLanguage(next);
    saveSetting("language", next);
  });

  const input = $("#input");
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 220)}px`;
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); }
  });
  $("#sendBtn").addEventListener("click", () => send());

  // belge yükleme
  const dropzone = $("#dropzone"), fileInput = $("#fileInput");
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => { uploadFiles(fileInput.files); fileInput.value = ""; });
  ["dragenter", "dragover"].forEach((type) =>
    dropzone.addEventListener(type, (e) => { e.preventDefault(); dropzone.classList.add("over"); }));
  ["dragleave", "drop"].forEach((type) =>
    dropzone.addEventListener(type, (e) => { e.preventDefault(); dropzone.classList.remove("over"); }));
  dropzone.addEventListener("drop", (e) => uploadFiles(e.dataTransfer.files));
  window.addEventListener("dragover", (e) => e.preventDefault());
  window.addEventListener("drop", (e) => e.preventDefault());

  $("#reindexBtn").addEventListener("click", reindex);
  $("#addNoteBtn").addEventListener("click", async () => {
    const name = prompt(t("docs.notePrompt"), "not.md");
    if (!name) return;
    const text = prompt(t("docs.noteBody"), "");
    if (!text) return;
    try {
      await api("/api/documents/text", { method: "POST", body: JSON.stringify({ name, text }) });
      toast(`1 ${t("docs.uploaded")}`, "ok");
      loadDocuments(); refreshStatus();
    } catch (error) { toast(error.message, "err"); }
  });

  // kod bloğu kopyalama
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy]");
    if (!button) return;
    const code = button.parentElement.querySelector("code");
    try { await navigator.clipboard.writeText(code.textContent); button.textContent = t("msg.copied"); } catch (_) {}
    setTimeout(() => { button.textContent = t("msg.copy"); }, 1600);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      $("#drawer").classList.remove("open");
      document.body.classList.remove("nav-open");
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault(); newChat(); $("#input").focus();
    }
  });
}

/* ---------------------------------------------------------
   Başlangıç
   --------------------------------------------------------- */
async function init() {
  bindGlobal();
  try {
    const { settings } = await api("/api/settings");
    state.settings = settings;
    applyTheme(settings.theme);
    applyLanguage(settings.language);
  } catch (_) {
    applyTheme("dark"); applyLanguage("tr");
  }
  clearChat();
  await refreshStatus();
  await loadConversations();
  setInterval(refreshStatus, 15000);
  $("#input").focus();
}

init();
})();
