# Literatür Araştırması & Sektör İstatistikleri
### ÇankaYazılım — AI Destekli Maden Ekipman İzleme ve Arıza Tahmin Sistemi
**Yarı Final Sunumu için kaynaklı veri derlemesi** · Hazırlanma: 27 Haziran 2026

> Bu belge, sunumun **Problem (slayt 4)**, **Çözüm/Yöntem (5–6)** ve **Özgünlük & Yerlilik (9)** slaytlarına doğrudan girecek, kaynak gösterilebilir verileri içerir. Tüm rakamlar uluslararası sektör raporları ve akademik kaynaklardan alınmıştır. Slaytta kullanırken yanına atıf numarasını koyacağız.

---

## BLOK A — Problem Gerçek ve Pahalı (Slayt 4)

### A1. Plansız duruşun maliyeti
- Ultra sınıf maden kamyonlarında (haul truck) plansız duruş **saatte 5.000–20.000 $** kayıp üretim; kritik varlıklarda **saatte 130.000 $'a** kadar çıkabiliyor. [1]
- Acil/baskı altında yapılan onarımlar, planlı bakımdan **3–5 kat** (uç durumda zincirleme gecikmelerle **15 kata** kadar) daha pahalı. [1]
- Bir maden kamyonu yılda ortalama **8,7 gün** plansız duruş yaşıyor. [1]
- Endüstri genelinde plansız ekipman arızası ortalama maliyeti **saatte ~260.000 $** (tüm sektörler). [5]

### A2. Reaktif vs. kestirimci bakım dengesi
- Dünya standartındaki madenler **%20'nin altında reaktif bakım** hedefliyor; yani işin büyük kısmı planlı/kestirimci olmalı. [2]
- McKinsey: ağır sanayide plansız duruş, **toplam bakım maliyetinin %25–40'ını** oluşturuyor — madencilik bu aralığın üst ucunda. [2]
- PwC & Mainnovation (280 sanayi şirketi): yalnızca **%11'i** en yüksek kestirimci bakım olgunluğuna ulaşmış; üçte ikisi en alt basamakta. → Pazarda büyük boşluk var. [2]

### A3. Bakımın işletme maliyetindeki (OPEX) payı
- Bakım faaliyetleri bir madenin **toplam işletme maliyetinin %30–60'ını** oluşturuyor. [3]

### A4. MTBF / MTTR / Kullanılabilirlik (availability)
- Kullanılabilirlik: dünya standartı maden kamyonlarında **%92–94**, kepçe/ekskavatörde %90–92; **sektör ortalaması ise %72–78** (büyük iyileştirme fırsatı). [4]
- MTBF (arızalar arası ortalama süre): ekskavatör/yükleyicide sektör ortalaması **400–600 saat**, kestirimci bakımla dünya standartı **800+ saat**. [4]
- MTTR (ortalama tamir süresi): en iyi operasyonlarda **6 saatin altı**, sektör ortalaması **12–18 saat**. Fark, analitik platformun olası kök nedeni ve parça listesini önceden çıkarmasından geliyor — teknisyen teşhise vakit harcamıyor. [4]
- Sistematik dijital bakım, 10 makinelik filoda yılda **85.000–135.000 $ tasarruf** sağlıyor. [4]

### A5. İş Sağlığı & Güvenliği (İSG)
- Bir incelemede 775 ölümlü maden kazasının **597'si (%77) bir maden ekipmanı/makinesiyle ilişkili** bulundu. [6]
- En ağır yaralanmaların **%40'tan fazlası** makine/ekipmana "çarpma" veya "kapılma" sınıfında. [7]
- **Türkiye:** DİSK İşçi Sağlığı ve Güvenliği Meclisi 2024 raporuna göre madencilik işkolunda **75 işçi** hayatını kaybetti. [8]

> **Slayt 4 mesajı:** "Plansız ekipman arızası madencilikte hem en büyük gizli maliyet kalemi (bakım = OPEX'in %30–60'ı, plansız duruş bakım maliyetinin %25–40'ı) hem de bir can güvenliği sorunu (ölümlü kazaların %77'si ekipman ilişkili). Buna rağmen şirketlerin yalnızca %11'i olgun kestirimci bakıma geçebilmiş. Biz bu boşluğu yerli bir çözümle kapatıyoruz."

---

## BLOK B — Çözümümüz Bilimsel ve Etkili (Slayt 5–6)

### B1. Kestirimci bakımın kanıtlanmış faydası (gerekçe)
- McKinsey: kestirimci bakım, reaktife kıyasla **bakım maliyetini %18–25 düşürüyor**, **plansız duruşu %30–50 azaltıyor**. [9]
- ROI **10:1 ile 30:1** arasında, 12–18 ayda geri dönüş; uygulayan şirketlerin **%95'i pozitif ROI** bildiriyor. [9]
- Deloitte: zayıf bakım stratejisi tesis kapasitesini **%5–20 düşürüyor**; bir pilot uygulama plansız duruşu **%80 azaltıp varlık başına ~300.000 $ tasarruf** sağladı. [9]

### B2. Isolation Forest (anomali tespiti) — yöntem gerekçesi
- Isolation Forest, **doğrusal zaman karmaşıklığı** ve **minimum hiperparametre** ihtiyacıyla anomali tespitinde güçlü; sağlıklı temel sinyalden sapmaları ayırt etmede özellikle başarılı, gömülü (edge) cihazlarda bile çalışabiliyor. [10]
- Endüksiyon motoru + kaplin düzeneğinde titreşim verisinde **yüksek hassasiyet ve doğrulukla** otomatik anomali tespiti deneysel olarak gösterildi. [11]

### B3. LSTM (kalan faydalı ömür / arıza zamanı tahmini) — yöntem gerekçesi
- LSTM, zaman serisindeki **zamansal bağımlılıkları** yakalamada MLP gibi klasik yöntemleri tutarlı biçimde geçiyor; kalan faydalı ömür (RUL) tahmini için temel mimari. [12]
- Uçak motoru (NASA C-MAPSS) RUL tahmininde yaygın referans; rulman arıza teşhisi + RUL'da hibrit modellerle **%99,9'a varan doğruluk** raporlandı. [13]

> **Yöntem anlatısı:** "Tek model yerine hibrit kuruyoruz: Isolation Forest normal çalışma profilinden anlık sapmayı (anomali) yakalıyor, LSTM ise geçmiş telemetriden arızanın *ne zaman* geleceğini tahmin ediyor. Bu ikisi, literatürde ayrı ayrı kanıtlanmış en güçlü iki yaklaşımın birleşimi."

---

## BLOK C — Rakipler ve Bizim Konumumuz (Slayt 9: Özgünlük & Yerlilik)

### C1. Uluslararası çözümler (hepsi yabancı + kendi markasına kilitli)
| Çözüm | Üretici | Ne yapıyor | Kısıt |
|---|---|---|---|
| **OptiMine + My Sandvik** | Sandvik (İsveç) | LHD yükleyici & delici verisini analiz edip hidrolik/motor arızalarını öngörüyor | Yalnızca Sandvik ekipmanı [14] |
| **Cat MineStar Health** | Caterpillar (ABD) | Binlerce veri kanalını izleyip arızayı önceden tespit, onarım önerisi | Yalnızca Cat ekipmanı [14] |
| **FrontRunner** | Komatsu (Japonya) | Ultra sınıf kamyon + filo yönetimi + kestirimci bakım | Komatsu ekosistemi [14] |
| **Fleet+ / InSite (eski Certiq)** | Epiroc (İsveç) | Telematik, gerçek zamanlı izleme, proaktif bakım planı | Epiroc ekosistemi [15] |

**Ortak zayıflık:** Hepsi (a) **yabancı menşeli**, (b) **kendi makine markasına bağımlı**, (c) ham veri/uyarı veriyor ama **operatöre manuelden çözüm sunan bir dil asistanı (RAG) yok.**

### C2. Türkiye'deki çözümler (genel amaçlı, madene/RAG'a özel değil)
- **Cormind, Vardabit, AirGemba, Bakım724** — sıcaklık/titreşim verisi + ML destekli arıza tahmini sunan yerli CMMS / kestirimci bakım platformları. Ancak **maden iş makinelerine özel değiller** ve **RAG tabanlı teknik asistan içermiyorlar.** [16]

### C3. Bizim doldurduğumuz boşluk (özgünlük ifadesi)
Hiçbir rakip şu üçünü aynı anda sunmuyor:
1. **Marka-bağımsız** (Sandvik + Epiroc + Caterpillar park karmaşası olan madenlerde tek sistem),
2. **Hibrit YZ** (Isolation Forest + LSTM birlikte),
3. **RAG teknik asistan** (1600+ sayfa manueli anlamsal arama motoruna çevirip operatöre anlık, manuele dayalı çözüm),
4. ve hepsi **tamamen yerli yazılım** (yabancı bulut/lisans bağımlılığı yok; embedding dahil yerel modelle).

> **Slayt 9 karşılaştırma tablosu** doğrudan C1+C2'den kurulacak; sütunlar: *Marka bağımsız mı? · Hibrit anomali+tahmin mi? · RAG asistan var mı? · Yerli mi?* Bizim satırımız tek "✓ ✓ ✓ ✓".

---

## KAYNAKÇA
[1] MapTrack, "Equipment Downtime Cost Statistics 2026"; Cummins, "Reducing machine downtime in mining" (2021); Heavy Vehicle Inspection, mining uptime brief.
[2] Cryotos, "Reactive to Predictive Maintenance in Mining"; Dingo, "Reduce Reactive Maintenance"; PwC & Mainnovation predictive maintenance maturity survey (280 firma); McKinsey (heavy industry maintenance cost).
[3] Asset Integrity Engineering (AIE), "Maintenance and Spares Optimisation – Mining".
[4] Heavy Vehicle Inspection, "Mining Fleet Uptime"; FleetRabbit; Opsima, "Mining Industry KPIs".
[5] Körber / WorkTrek, predictive maintenance downtime cost (~$260k/hr).
[6] Groves et al., "Analysis of fatalities and injuries involving mining equipment", ScienceDirect (775 ölüm, %77 ekipman ilişkili).
[7] CDC/NIOSH Mining, "Machinery Struck-by Injuries".
[8] DİSK İşçi Sağlığı ve Güvenliği Meclisi, 2024 İş Cinayetleri Raporu (madencilik 75 işçi).
[9] McKinsey & Company; WorkTrek "Predictive Maintenance Cost Savings"; Deloitte Insights, "Industry 4.0 / predictive technologies for asset maintenance".
[10] PyImageSearch, "Predictive Maintenance Using Isolation Forest"; MDPI Sensors 25(21):6610, "Low-Cost IoT-Based Predictive Maintenance Using Vibration".
[11] Springer, "Automatic Anomaly Detection in Vibration Analysis Based on Machine Learning Algorithms".
[12] arXiv:2401.07590, "Remaining Useful Life Prediction for Aircraft Engines using LSTM"; Nature Scientific Reports, predictive maintenance / RUL.
[13] ScienceDirect, "Enhanced fault diagnosis and RUL prediction of rolling bearings using hybrid MLP-LSTM".
[14] Mining Digital, "Top 10 Predictive Maintenance Solutions"; Cat.com, "MineStar Maintenance Solutions".
[15] Epiroc.com, "Certiq / Fleet+ / InSite" telematics.
[16] Cormind, Vardabit, AirGemba, Bakım724 kurumsal kaynakları (yerli kestirimci bakım/CMMS).
