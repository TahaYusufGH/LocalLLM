# LocalLLM — Yerel RAG Asistanı

Kendi belgelerinize soru soran, **tamamen çevrimdışı** çalışan bir bilgi asistanı.
Sorular cihazınızda gömülür, cevaplar cihazınızdaki bir dil modeliyle üretilir.
Hiçbir veri dışarı çıkmaz; uygulama yalnızca `127.0.0.1` üzerinde konuşur.

Bu proje, *"One-Month Project Plan: Local RAG AI Assistant with Microsoft Foundry Local"*
planındaki mimariyi (Foundry Local + RAG + SQLite vektör deposu + alaka kapısı) uygular
ve planın "Seçenek B/C" olarak bıraktığı web arayüzünü hayata geçirir.

---

## Hızlı başlangıç

```bash
baslat.bat
```

İlk çalıştırmada sanal ortam kurulur, bağımlılıklar yüklenir, `documents/` klasörü
indekslenir ve tarayıcı <http://127.0.0.1:8765> adresinde açılır.

Elle çalıştırmak isterseniz:

```bash
python -m pip install -r requirements.txt
```

```bash
python main.py
```

Yerel bir dil modeli kurulu olmasa bile uygulama açılır: bu durumda **alıntı modunda**
çalışır ve sorunuza en uygun belge bölümlerini kaynaklarıyla birlikte gösterir.

---

## Yerel dil modelini bağlama

Uygulama, OpenAI uyumlu HTTP arayüzü sunan her yerel çalıştırıcıyla konuşur ve
açık olan portları kendisi tarar (Foundry Local, Ollama, LM Studio, llama.cpp).

Microsoft Foundry Local ile (sürüm 0.10+):

```bash
winget install Microsoft.FoundryLocal
```

```bash
foundry server start
```

```bash
foundry model download qwen3-4b
```

```bash
foundry model load qwen3-4b
```

Ardından **Ayarlar → Dil modeli → Otomatik bul** düğmesine basın.

> **Dinamik port:** Foundry Local sabit bir port kullanmaz (ör. `http://127.0.0.1:50084`).
> Uygulama adresi `foundry server status -o json` çıktısından okur, bu yüzden elle
> port yazmanız gerekmez. Adresi görmek isterseniz aynı komutu siz de çalıştırabilirsiniz.

> **Model seçimi:** Türkçe belgeler için `qwen3-4b` belirgin biçimde daha iyi sonuç verir;
> `qwen3-1.7b` daha hızlı, `phi-3.5-mini` ise plan belgesinde adı geçen modeldir.

> **İnternet:** Yalnızca ilk model indirmesi internet ister. İndirme bittikten sonra
> hem model hem uygulama tamamen çevrimdışı çalışır.

---

## Nasıl çalışır?

```
Soru
  ↓
[1] Gömme         soru bir vektöre dönüşür (aksanlar katlanır: "parcalama" = "parçalama")
  ↓
[2] Melez arama   anlamsal (kosinüs) + sözlüksel (BM25) sıralama RRF ile birleştirilir
  ↓
[3] Alaka kapısı  puan düşükse model hiç çalıştırılmaz
  ↓
[4] Zenginleştirme  en iyi K parça "BAĞLAM" olarak isteme eklenir
  ↓
[5] Üretim        yerel LLM cevabı akış hâlinde üretir, kaynaklar [1] [2] ile gösterilir
```

### Neden melez arama?

Saf anlamsal arama, sorudaki kelimenin metinde birebir geçtiği durumları
şaşırtıcı biçimde kaçırabiliyor. "Kaç kademesi vardır?" sorusunda "Üç Kademeli
Karar" başlıklı parça anlamsal sıralamada 10., BM25 sıralamasında 3. çıkıyor.
İki sıralama Reciprocal Rank Fusion ile birleştirilince parça bağlama giriyor
ve cevap doğru oluyor.

BM25 tarafı Türkçe için kelimeleri 5 harfe kırpar: "kademesi" ve "kademeli"
aynı köke iner. Gösterilen benzerlik yüzdesi her zaman anlamsal (kosinüs)
puandır, böylece eşiklerin anlamı değişmez.

### Alaka kapısı (üç kademe)

Modele "bilmiyorsan söyle" demek küçük modellerde çoğu zaman yetmez, bu yüzden karar
istemde değil **kodda** verilir:

| En iyi benzerlik | Davranış |
|---|---|
| eşiğin altında | Model hiç çağrılmaz, doğrudan "bu bilgi belgelerimde yok" |
| iki eşik arasında | Modele önce "bu metin yeter mi?" diye sorulur, hayırsa reddedilir |
| üst eşiğin üstünde | Doğrudan cevap üretilir |

Eşikler gömme yöntemine göre otomatik seçilir ve **Ayarlar → Alaka kapısı**
bölümünden değiştirilebilir. Her cevabın altında gerçek benzerlik puanı görünür,
böylece eşikleri kendi belgelerinize göre ölçerek ayarlayabilirsiniz.

Doğrulama adımı modele **yalnızca en alakalı parçayı** gösterir. Tüm bağlam
verildiğinde alakasız parçalar küçük modeli şaşırtıyor: ölçümde tüm bağlamla
doğruluk 1/5 iken tek parçayla 5/5 çıktı.

### Sohbet şeridi

Alaka kapısı yalnızca belgelere benzerliğe bakar. "Merhaba nasılsın" belgelerle
%18 benzeştiği için kapsam dışı bir soru sanılıp reddediliyordu — oysa bu bir
soru değil, sohbet. Selamlaşma, teşekkür, vedalaşma ve "sen kimsin / ne
yapabilirsin" türü mesajlar artık erişime hiç girmeden, modele gitmeden
0,03 sn'de cevaplanır. Kalıp eşleşmesi bilerek dar tutulmuştur: 8 kelimeden
uzun mesajlar ve belgelere dair gerçek sorular RAG hattına gider.

Ret mesajı da soruya göre ayrışır. Hava durumu, saat, döviz kuru gibi **anlık
veri** isteyen sorularda "belge ekleyin" demek yanıltıcı olurdu — eklenecek
belge yok. Bu durumda asistan internete çıkmadığını ve bu bilginin cihazda hiç
bulunmadığını açıkça söyler. Belgelerde olabilecek ama bulunamayan sorularda
ise normal ret mesajı ve belge ekleme önerisi verilir.

### Genel bilgi anahtarı

Varsayılan olarak **kapalıdır**: asistan yalnızca belgelerinize dayanır, bulamazsa
"bilmiyorum" der. Uydurma riski sıfırdır ama modelin bildiği şeyler de kullanılmaz.

**Ayarlar → Alaka kapısı → Genel bilgiyle cevapla** ile açtığınızda, belgelerde
bulunamayan sorular modelin kendi bilgisiyle cevaplanır. Bu cevaplar kaynaklı
cevaplarla karıştırılamaz:

- Metnin başına *"Bu cevap belgelerinize dayanmıyor"* notu konur.
- Kaynak rozetleri ve benzerlik yüzdesi gösterilmez.
- Üstveride `gate` alanı `general` olur, arayüzde **genel bilgi** etiketi çıkar.

Anlık veri (hava, döviz, saat) isteyen sorular anahtar açıkken de cevaplanmaz —
o bilgi hiçbir modelde yok.

### Düşünme modu

qwen3 gibi modeller cevaptan önce uzun bir `<think>` bloğu üretir. Bu blok token
bütçesinin tamamını tüketip cevabı yarıda kesebildiği için **varsayılan olarak
kapalıdır** (`Ayarlar → Dil modeli → Düşünme modu`). Ölçülen fark: aynı soru
düşünme açıkken 17,2 sn sürüp yarıda kesiliyor, kapalıyken 3,0 sn'de doğru
cevap veriyor. Cevaba sızan `<think>` blokları ve kopyalanan bağlam başlıkları
ayrıca kod tarafında temizlenir.

### Gömme seçenekleri

| Yöntem | Açıklama |
|---|---|
| `endpoint` | Foundry Local / Ollama üzerindeki gömme modeli (ör. `qwen3-embedding-0.6b`) |
| `local` | `sentence-transformers` ile cihazda çalışan model (çok dilli, Türkçe için iyi) |
| `hash` | Model gerektirmeyen, saf NumPy sözcük/karakter n-gram gömmesi — her zaman çalışır |

`auto` seçiliyken mevcut indeksin kurulduğu yöntem korunur; böylece sonradan bir model
sunucusu açtığınızda indeks bozulmaz.

---

## Arayüz

- **Sohbet** — akışlı cevaplar, Markdown, kod bloğu kopyalama, sohbet geçmişi
- **Kaynak rozetleri** — her cevabın altında kullanılan belgeler ve benzerlik yüzdesi;
  tıklayınca sağdan açılan panelde modelin gördüğü ham metin parçası görünür
- **Belgeler** — sürükle-bırak yükleme, not ekleme, silme, yeniden indeksleme
- **Ayarlar** — model, gömme, erişim ve kapı ayarları; koyu/açık tema; TR/EN dil değişimi

Klavye: `Enter` gönder · `Shift+Enter` yeni satır · `Ctrl+K` yeni sohbet · `Esc` panelleri kapat

---

## Belge ekleme

`documents/` klasörüne dosya bırakıp **Belgeler → Yeniden indeksle** deyin ya da
doğrudan arayüze sürükleyin.

Desteklenen türler: `.txt` `.md` `.pdf` `.docx` `.csv` `.json` `.log` `.rst`

Belgeler başlıklarına göre bölünür, her bölüm kendi içinde örtüşmeli parçalara
ayrılır. Bu sayede farklı konular tek bir vektörde birbirine karışmaz.

---

## Proje yapısı

```
LocalLLM/
├── app/
│   ├── config.py       ayarlar (data/settings.json)
│   ├── embeddings.py   gömme sağlayıcıları + aksan katlama
│   ├── llm.py          yerel model istemcisi, uç nokta bulma, akış, /no_think
│   ├── store.py        SQLite vektör deposu + BM25 indeksi + sohbet geçmişi
│   ├── ingest.py       belge okuma, başlık duyarlı parçalama, indeksleme
│   ├── smalltalk.py    selamlaşma / "sen kimsin" şeridi
│   ├── rag.py          erişim → alaka kapısı → üretim hattı
│   └── server.py       FastAPI uçları (yalnız 127.0.0.1)
├── web/                arayüz (bağımlılıksız HTML/CSS/JS, dış istek yok)
├── documents/          bilgi tabanı
├── data/knowledge.db   vektörler, belgeler, sohbetler
├── main.py             başlatıcı
└── baslat.bat          Windows tek tık başlatma
```

## Komut satırı

```bash
python main.py --port 8800 --no-browser
```

```bash
python main.py --reindex
```

---

## Gizlilik

- Sunucu yalnızca `127.0.0.1` üzerinde dinler, dışarıya açılmaz.
- Arayüz hiçbir CDN, yazı tipi ya da analiz betiği yüklemez.
- Model çağrıları yalnızca `127.0.0.1` üzerindeki yerel çalıştırıcıya gider.
- Belgeleriniz, vektörleriniz ve sohbetleriniz `data/knowledge.db` dosyasında kalır.
