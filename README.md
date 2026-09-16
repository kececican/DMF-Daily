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

## Tasarım Sistemi

Arayüz `design.md` (Valeo Tasarım Sistemi — Material 3 Expressive uyarlaması)
kurallarına uyar. Renkler **daima** semantik token üzerinden kullanılır;
kodda sabit hex yazılmaz (`design.md` §2.4).

`design.md`'nin §0 ve §10 bölümleri Google Apps Script projeleri içindir; bu
proje statik HTML ürettiğinden o iki bölüm uygulanmaz.

| Özellik | Davranış |
|---|---|
| **Tema** | §2.4 — açılışta işletim sistemi tercihi; kullanıcı seçimi `localStorage['valeo-theme']`'de saklanır |
| **Tipografi** | §3 — Montserrat 600/700 (başlık), Lato 400/700 (gövde). `vendor/fonts/` altından base64 gömülür |
| **Veri etiketleri** | Tüm grafiklerde kalıcı — hover gerekmez. Üst üste binenler otomatik gizlenir |
| **Navigasyon** | §8-9 — geniş ekranda sol rail, dar ekranda alt bar |
| **Seri paleti** | §2.5 — tema başına türetilmiş 9 ton; palet sarmalanırsa ek turlar zeminden uzağa kaydırılır |
| **Tablo** | §8 — yapışkan başlık, zebra yerine hover, sayısal sütunlar sağa hizalı |
| **Erişilebilirlik** | §11 — metin çiftleri WCAG AA (≥4.5:1), grafik serileri ≥3:1, görünür focus halkası, `prefers-reduced-motion` |
| **Grafik kurulumu** | Sekme ilk açıldığında kurulur (gizli canvas'ta boyut hatası olmaz) |

### Paletten sapmalar

`design.md` §2.5 yedi seri rengi tanımlar; bu dashboard'da dokuz hat ve on üç
duruş sebebi var. Palet, dokümanın kendi `(türetilmiş)` yöntemiyle genişletildi
ve §11'in kontrast şartı için tema başına ayrıldı — gerekçeler
`generate_dashboard.py` içinde satır satır yazılı.

## Dosya Yapısı

```
DMF-Daily/
├── extract_excel.py               # Excel → data.json  (openpyxl gerekir)
├── generate_dashboard.py          # data.json → index.html  (bağımlılıksız)
├── design.md                      # Valeo Tasarım Sistemi (M3E uyarlaması)
├── vendor/
│   ├── chart.umd.min.js                 # Chart.js 4.4.0
│   ├── chartjs-plugin-datalabels.min.js # datalabels 2.2.0
│   └── fonts/                           # Montserrat + Lato (woff2, latin & latin-ext)
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
