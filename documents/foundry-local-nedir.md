# Microsoft Foundry Local Nedir?

Foundry Local, büyük dil modellerini tamamen kullanıcının cihazında çalıştırmayı sağlayan
uçtan uca bir yerel yapay zeka çözümüdür. Hafif bir çalışma zamanı (runtime) ve bir SDK sunar.
Bulut hesabı ya da güçlü bir GPU gerektirmez; modelleri otomatik olarak indirir, yönetir ve
CPU, GPU veya NPU hızlandırmasıyla çalıştırır.

## Temel Özellikler

Foundry Local'ın öne çıkan özellikleri şunlardır: cihaz üzerinde model indirme, donanım
hızlandırmanın otomatik seçilmesi, Python başta olmak üzere birçok dil için kolay kullanımlı
bir SDK ve OpenAI uyumlu bir HTTP arayüzü. Bu sayede uygulamalar hiçbir ağ çağrısı yapmadan
çevrimdışı yapay zeka yetenekleri sunabilir.

## Neden Yerel Çalıştırmalı?

Yerel çalıştırmanın üç büyük avantajı vardır. Birincisi gizliliktir: veriler cihazdan hiç
çıkmaz. İkincisi maliyettir: kullanım başına ücret ödenmez. Üçüncüsü ise erişilebilirliktir:
internet bağlantısı olmayan ortamlarda bile sistem çalışmaya devam eder.

## Desteklenen Platformlar

Foundry Local Windows, macOS ve Linux üzerinde çalışır. Kurulum Windows'ta winget ile,
macOS'ta ise brew ile yapılabilir. Kurulumdan sonra `foundry model run phi-3.5-mini`
komutu küçük bir sohbet modelini indirip başlatır.
