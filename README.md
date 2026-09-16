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

Üretim iki adıma ayrılmıştır: **veri ayıklama** ve **sunum**.

```
Excel ──(extract_excel.py)──> dashboard/data.json ──(generate_dashboard.py)──> dashboard/index.html
```

`data.json` depoda tutulduğu için **Excel olmadan da** dashboard yeniden
üretilebilir — arayüzde değişiklik yapmak için Excel'e ihtiyaç yoktur.

### 1. Excel → data.json  (yalnız veri değiştiğinde)

```bash
pip install openpyxl
DMF_EXCEL=/yol/DMF_Daily_Followup.xlsx python3 extract_excel.py
```

`DMF_EXCEL` verilmezse `data/DMF_Daily_Followup_New_Version_2026.xlsx` aranır.

### 2. data.json → index.html  (her arayüz değişikliğinde)

```bash
python3 generate_dashboard.py
```

Bu adımın bağımlılığı yoktur — sadece standart kütüphane.

### Dashboard'u Açma

`dashboard/index.html` dosyasını herhangi bir tarayıcıda açın.  
Chart.js ve datalabels eklentisi HTML'in içine gömülüdür — **internet
bağlantısı gerekmez** (`file://`, offline veya kapalı fabrika ağı dahil).

## Arayüz Özellikleri

| Özellik | Davranış |
|---|---|
| **Veri etiketleri** | Tüm grafiklerde kalıcı — hover gerekmez. Üst üste binen etiketler otomatik gizlenir |
| **Light / Dark tema** | Sağ üstteki düğme. Açılış **light**, tercih tarayıcıda hatırlanır |
| **Hat renkleri** | Her tema için ayrı palet — light temada koyulaştırılmış tonlar kullanılır |
| **Grafik kurulumu** | Sekme ilk açıldığında kurulur (gizli canvas'ta boyut hatası olmaz) |

## Dosya Yapısı

```
DMF-Daily/
├── extract_excel.py               # Excel → data.json  (openpyxl gerekir)
├── generate_dashboard.py          # data.json → index.html  (bağımlılıksız)
├── vendor/
│   ├── chart.umd.min.js                 # Chart.js 4.4.0
│   └── chartjs-plugin-datalabels.min.js # datalabels 2.2.0
└── dashboard/
    ├── data.json               # Ayıklanmış veri (Excel'den bağımsız cache)
    └── index.html              # Tek dosya, standalone dashboard
```

## Veri Kaynakları

| Sayfa | İçerik |
|---|---|
| DMF1–4 | Saat bazında üretim, vardiya toplam, duruş dakikaları |
| PFW1–4 | Alt montaj üretim ve duruş verileri |
| ITL | ITL hattı üretim ve TRP |
| Duruş Süre&Sebep | Kategorili duruş kayıt defteri (1000+ satır) |
| CYCLE | Hat ve referans bazında cycle time tablosu |
