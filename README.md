# Yapay Zeka Destekli Maden Ekipman İzleme ve Arıza Tahmin Sistemi

ÇankaYazılım — TEKNOFEST 2026 Maden Teknolojileri Yarışması (Takım ID: 951354)

## Klasör Yapısı

| Klasör | İçerik |
|---|---|
| `proje/digital_twin-main/` | **Çalışan sistem** — backend, simülatör, ML modelleri, dashboard, Docker altyapısı. Başlatma: `docker compose up -d` sonra `.venv/bin/python -m uvicorn main:app --port 8000` |
| `sunum/` | Yarışma sunumları (yarı final sunumu: `...(11).pptx`) |
| `dokumanlar/` | Yarışma şartnamesi, ön değerlendirme raporu, Sandvik LH517i / TH551i teknik spec PDF'leri, literatür (makaleler + yazılar) |
| `veri/` | TeknoFest Türk Altın jeofizik/sondaj veri seti |

Kaggle kestirimci bakım veri seti (arıza oranı referansı): `proje/digital_twin-main/data/predictive_maintenance.csv`
