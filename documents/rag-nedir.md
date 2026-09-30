# RAG (Retrieval-Augmented Generation) Nedir?

RAG, bir dil modelinin cevabını kendi eğitim verisi yerine sizin belgelerinize dayandıran
bir tasarım desenidir. Üç adımdan oluşur: Retrieve (eriş), Augment (zenginleştir) ve
Generate (üret).

## Adım 1: Erişim (Retrieve)

Kullanıcının sorusu bir gömme (embedding) modeliyle sayısal bir vektöre dönüştürülür.
Bu vektör, daha önce indekslenmiş belge parçalarının vektörleriyle karşılaştırılır.
Karşılaştırma genellikle kosinüs benzerliği ile yapılır. En yüksek benzerliğe sahip
ilk K parça seçilir.

## Adım 2: Zenginleştirme (Augment)

Seçilen parçalar, modele gönderilecek istemin (prompt) içine "BAĞLAM" olarak yerleştirilir.
Sistem talimatı modele yalnızca bu bağlamı kullanmasını, bağlamda olmayan bir şey sorulursa
bilmediğini söylemesini bildirir.

## Adım 3: Üretim (Generate)

Dil modeli, zenginleştirilmiş istemi okuyup cevabı üretir. Cevap belgelere dayandığı için
uydurma (halüsinasyon) oranı ciddi biçimde düşer ve kaynak gösterimi mümkün olur.

## RAG'in Avantajları

RAG'in en büyük avantajı, modeli yeniden eğitmeden (fine-tuning yapmadan) yeni bilgi
eklenebilmesidir. Yeni bir belge eklendiğinde yalnızca indeksleme tekrarlanır. Ayrıca
cevapların hangi kaynaktan geldiği izlenebilir, bu da güveni artırır.
