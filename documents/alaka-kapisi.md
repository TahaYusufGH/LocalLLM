# Alaka Kapısı (Relevance Gating)

Alaka kapısı, modelin belgelerde olmayan bir soruya uydurma cevap vermesini engelleyen
kod tabanlı bir karar mekanizmasıdır. Modele "bilmiyorsan söyle" demek çoğu zaman yeterli
olmaz; küçük modeller bu talimatı göz ardı edebilir. Bu yüzden karar, istemin içinde değil
kodun içinde verilir.

## Üç Kademeli Karar

Sistem, en yüksek benzerlik puanına bakarak üç farklı davranış sergiler. Puan alt eşiğin
altındaysa model hiç çalıştırılmaz ve doğrudan "bu bilgi belgelerimde yok" cevabı döner.
Puan iki eşik arasındaysa modele önce kısa bir doğrulama sorusu sorulur: bu bağlam bu soruyu
cevaplamaya yeter mi? Cevap hayırsa yine reddedilir. Puan üst eşiğin üzerindeyse doğrudan
cevap üretilir.

## Eşikler Nasıl Belirlenir?

Eşik değerleri kullanılan gömme modeline göre değişir. Doğru yöntem, bilinen sorularla
gerçek benzerlik puanlarını ölçmek ve iki grubun arasındaki boşluğu eşik olarak seçmektir.
Cevaplanabilir sorular genellikle yüksek puan alırken, alakasız sorular belirgin biçimde
düşük puan alır.

## Faydası

Bu yaklaşımın iki faydası vardır. Birincisi doğruluk: sistem bilmediğini söyler. İkincisi
hızdır: alakasız sorular için model hiç çalıştırılmadığı için cevap anında döner.
