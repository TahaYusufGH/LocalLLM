# Gömme (Embedding) ve Vektör Arama

Gömme, bir metin parçasının anlamını temsil eden sayı dizisidir. Benzer anlamlı metinler
vektör uzayında birbirine yakın konumlanır. Bu sayede "anahtar kelime" eşleşmesi olmadan da
anlamsal arama yapılabilir.

## Kosinüs Benzerliği

İki vektör arasındaki açının kosinüsü, o iki metnin anlamsal yakınlığının ölçüsü olarak
kullanılır. Değer -1 ile 1 arasındadır; 1'e yaklaştıkça metinler birbirine daha benzerdir.
Vektörler birim uzunluğa normalize edilirse kosinüs benzerliği basit bir nokta çarpımına
indirgenir.

## SQLite ile Vektör Deposu

Küçük veri kümeleri için ayrı bir vektör veritabanına ihtiyaç yoktur. SQLite tek dosyalık,
sunucusuz bir veritabanıdır ve metin parçalarıyla birlikte gömme vektörlerini de saklayabilir.
Vektörler ikili (blob) biçimde tutulur; arama sırasında hepsi belleğe okunup kaba kuvvet
yöntemiyle karşılaştırılır. Binlerce parçaya kadar bu yaklaşım fazlasıyla hızlıdır.

## Parçalama (Chunking) Stratejisi

Belgeler doğrudan değil, parçalar hâlinde indekslenir. İyi bir parça bir ile üç paragraf
uzunluğundadır. Parçalar arasında bir miktar örtüşme bırakmak, cümlenin ortasından bölünen
bilgilerin kaybolmasını önler. Parça çok büyük olursa alakasız bilgi de bağlama girer;
çok küçük olursa bağlam kopar.
