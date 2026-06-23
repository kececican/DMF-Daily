# DMF Daily — Üretim Takip Dashboard

VALEO DMF montaj hatlarının günlük üretim, TRP ve duruş verilerini görselleştiren interaktif web dashboard'u.

## Hatlar

| Grup | Hatlar |
|---|---|
| DMF Montaj | DMF1, DMF2, DMF3, DMF4 |
| PFW Alt Montaj | PFW1, PFW2, PFW3, PFW4 |
| ITL | ITL |

## Dashboard Ekranları

| Ekran | İçerik |
|---|---|
| **KPI Özet** | Hat bazında toplam üretim, TRP, rework, iskarta kartları + aylık üretim grafikleri |
| **Üretim Trendi** | Haftalık üretim adedi ve TRP trendi — hat bazında filtrelenebilir |
| **Duruş Analizi** | Duruş sebebi pareto, hat bazında toplam duruş, aylık stacked dağılım |
| **Duruş Detay** | 1000+ kayıt — hat / sebep / vardiya / metin filtreli tablo |

## TRP Hesaplama

```
TRP = Vardiya Toplam Üretim / Teorik Maksimum
Teorik Maksimum = (480 dk × 60 sn) / Cycle Time (sn)
```

| Hat | Cycle Time |
|---|---|
| DMF1 | 47 sn |
| DMF2 | 49 sn |
| DMF3 | 46 sn |
| DMF4 | 47 sn |
| PFW1–4 | 50 sn |
| ITL | 56 sn |

## Kurulum & Kullanım

### Gereksinimler

```bash
pip install openpyxl
```

### Dashboard Güncelleme

Excel dosyası güncellendiğinde:

```bash
python3 generate_dashboard.py
```

`dashboard/index.html` dosyası yeniden üretilir.

### Dashboard'u Açma

`dashboard/index.html` dosyasını herhangi bir tarayıcıda açın.  
(Chart.js CDN üzerinden yüklenir — internet bağlantısı gerekir)

## Dosya Yapısı

```
DMF-Daily/
├── generate_dashboard.py   # Excel → HTML dönüştürücü
└── dashboard/
    └── index.html          # Tek dosya, standalone dashboard
```

## Veri Kaynakları

| Sayfa | İçerik |
|---|---|
| DMF1–4 | Saat bazında üretim, vardiya toplam, duruş dakikaları |
| PFW1–4 | Alt montaj üretim ve duruş verileri |
| ITL | ITL hattı üretim ve TRP |
| Duruş Süre&Sebep | Kategorili duruş kayıt defteri (1000+ satır) |
| CYCLE | Hat ve referans bazında cycle time tablosu |
