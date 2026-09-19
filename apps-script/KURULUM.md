# Apps Script kurulumu

Dashboard'ı Google Sheets üzerinden çalıştırmak ve **dashboard içinden veri
eklemek** için gereken adımlar. Tek seferlik.

## Neden bu yol

GitHub Pages statik dosya sunucusudur — veri kabul edemez. `design.md` §0 ve
§10 zaten Apps Script ortamını hedefler, yani bu proje şirket standardına
geri dönmüş olur. Ek olarak veri repodan çıkar: herkese açık depoda üretim
verisi kalmaz.

## 1 — Google Sheet oluştur

Yeni bir Google E-Tablo aç. Adı önemli değil; URL'deki kimliği not et:

```
https://docs.google.com/spreadsheets/d/BURADAKI_KIMLIK/edit
```

## 2 — Apps Script projesini bağla

E-Tablo içinde **Uzantılar → Apps Script**. Açılan projeye bu klasördeki
dosyaları yükle.

`clasp` ile (önerilen):

```bash
npm install -g @google/clasp
clasp login
cd apps-script
clasp create --type sheets --title "DMF Daily" --rootDir .
clasp push
```

Elle: düzenleyicide `Kod.gs`, `Toplama.gs` dosyalarını ve `index.html`,
`styles.html` HTML dosyalarını aynı adlarla oluşturup içerikleri yapıştır.

> `index.html` ve `styles.html` **üretilen** dosyalardır — elle düzenleme.
> Kaynak `generate_dashboard.py`; değişiklikten sonra `python3
> generate_dashboard.py --gas` çalıştırıp tekrar push et.

## 3 — Sekmeleri oluştur

Düzenleyicide `kurulum` fonksiyonunu seçip bir kez **Çalıştır**. Dört sekme
başlıklarıyla açılır: `Uretim`, `Durus`, `Cycle`, `SMF`.

Apps Script projesi E-Tabloya bağlı değilse, **Proje Ayarları → Komut Dosyası
Özellikleri**'ne `SHEET_ID` = E-Tablo kimliği ekle.

## 4 — Mevcut veriyi taşı

```bash
DMF_EXCEL=/yol/DMF_Daily_Followup.xlsx python3 tools/excel_to_csv.py
```

`sheets-csv/` altında dört CSV üretilir. Her birini ilgili sekmeye aktar:
**Dosya → İçe aktar → Yükle**, ayırıcı virgül, *mevcut sayfayı değiştir*.
Başlık satırını koru.

Excel elinde yoksa `python3 tools/datajson_to_csv.py` duruş ve SMF
geçmişini mevcut `dashboard/data.json` içinden çıkarır; **üretim geçmişi
yalnız Excel'den gelebilir.**

## 5 — Web uygulaması olarak yayınla

**Dağıt → Yeni dağıtım → Web uygulaması**

| Ayar | Değer |
|---|---|
| Yürütme | Web uygulamasına erişen kullanıcı |
| Erişim | Şirket alan adındaki herkes |

Verilen `/exec` adresi yeni dashboard linkidir.

## Kullanım

Dashboard'a **Veri Girişi** sekmesi gelir: vardiya üretimi, duruş kaydı,
SMF günlüğü ve cycle time. Kayıt eklenince grafikler kendiliğinden yenilenir.

Doğrulama **sunucu tarafında** yapılır — tarayıcıdaki kontroller yalnız hızlı
geri bildirim içindir:

- Tarih `YYYY-AA-GG`, geçerli ve gelecekte değil
- Hat bilinen dokuz hattan biri, vardiya A/B/C
- Aynı tarih + vardiya + hat için **ikinci üretim kaydı reddedilir** (TRP'yi bozar)
- Aynı güne ikinci SMF kaydı reddedilir
- Duruş süresi 0.1–1440 dk
- Cycle time'da aynı hat + referans varsa **güncellenir**, yeni satır açılmaz

Her satıra kaydeden e-postası ve zaman damgası yazılır.

## Notlar

- Okunan veri 6 saat önbelleklenir; **her yazmada önbellek temizlenir**, yani
  eklediğin kayıt anında görünür.
- Yazmalar `LockService` ile sıraya alınır — iki kişi aynı anda eklerse satır
  ezilmez.
- Düzeltme/silme dashboard'dan yapılmaz; E-Tablo üzerinden düzenlenir.
  (Önbellek en geç 6 saat içinde yenilenir; hemen görmek için bir kayıt
  ekleyip silmek yerine `verileriGetir(true)` çalıştırılabilir.)
