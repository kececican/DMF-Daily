# design.md — Valeo Dashboard Tasarım Sistemi
### (Marka kimliği + Material 3 Expressive uyarlaması, tek tutarlı doküman)

> Bu dosya, uygulamanın nasıl görüneceğini anlatan tek "tarif kağıdı"dır.
> Hem Claude Design'a (görünüm keşfi için) hem Claude Code'a (gerçek dosyalara
> uygularken) referans olarak verilir.
>
> **M3E notu:** Material 3 Expressive'in resmî bir web/CSS implementasyonu yoktur
> (yeni şekiller/motion yalnızca Figma + Jetpack Compose'da). Bu doküman M3E'nin
> görsel dilini **saf CSS token'larıyla** uygular — Google Apps Script'in HTML Service
> ortamında (build adımı yok, iframe sandbox) hiçbir dış bağımlılık gerekmeden çalışsın
> diye. Yani bu, M3E'ye **sadık bir uyarlamadır**, birebir Google implementasyonu değil.
> M3E'den yalnızca işe yarayan kısımlar alınmıştır.

---

## 0. ÖNEMLİ — Bu bir Google Apps Script uygulamasıdır (DOKUNMA LİSTESİ)

Bu proje Google Apps Script (GAS) üzerinde çalışır ve `HtmlService` ile servis edilir.
Tasarımı yenilerken aşağıdakiler **kesinlikle değiştirilmemeli** — bunlar uygulamanın
"çalışan" kısmıdır, sadece görünüm değişecek:

- Tüm `google.script.run.*` çağrıları (aynen kalacak)
- `<?= ... ?>`, `<?!= ... ?>` ve `<? ... ?>` scriptlet etiketleri (GAS şablon motoru)
- JavaScript'in kullandığı element `id` değerleri
- Form alanlarının `name` özellikleri (bunlar arka uca gider)
- `onclick`, `onchange` vb. olay bağlantıları
- `withSuccessHandler` / `withFailureHandler` blokları

**Yalnızca** HTML yapısının görünümü, CSS/stiller ve sınıf (class) isimleri
yenilenebilir. İşlevi sağlayan hiçbir bağ koparılmaz.

---

## 1. Marka Kimliği & Kullanım Bağlamı

Valeo — **şirket içi çalışanların** her gün kullandığı kurumsal bir dashboard.
Kimlik: **kurumsal ve güvenilir, ama ölçülü şekilde sıcak (welcoming).**
Aşırı oyuncu değil; çalışanın gün boyu rahat kullanacağı, göze hitap eden, verimli araç.

- **Kullanıcı:** şirket içi çalışanlar → verimlilik ve okunaklılık önce gelir.
- **Ton:** profesyonel, net, düzenli; küçük yumuşak dokunuşlarla davetkâr.
- **His:** ferah ama verimli. Tablo ve listeler net okunmalı, gün boyu göz yormamalı.
- **Logo:** Valeo logosu açık zeminde net kullanılır, etrafında yeterli boşluk.

### M3E tasarım ilkeleri (bu dashboard'ın uyduğu)
- **Containment (kapsama):** Her mantıksal grup, yuvarlak köşeli ve tonal olarak
  ayrışan bir kapsayıcıda durur. Yapı boşlukla değil, renk/şekil ile kurulur.
- **Layered surfaces (katmanlı yüzeyler):** Derinlik gölgeyle değil, yüzey tonu
  farklarıyla verilir (`surface-container` seviyeleri).
- **Expressive shape:** Kartlarda ve kapsayıcılarda cömert köşe yuvarlaklığı.
- **Ölçülü motion:** Geçişler "emphasized" eğrilerle; yaylı zıplama sadece küçük
  detaylarda, abartısız (kurumsal his için M3E'nin fazla oyuncu tarafı törpülendi).
- **Semantik renk:** Tüm renkler rollerle tanımlıdır; tek seed değişince tema döner.

---

## 2. Renk Sistemi (Valeo markası → M3 rolleri)

Kaynak marka paleti aynen korunur; M3 semantik rolleri bunların üzerine eşlenir.
Bazı tonlar (container'lar, surface rampaları, açık temada okunur yeşil) marka
renklerinden **türetilmiştir** ve `(türetilmiş)` olarak işaretlidir.

### 2.1 Marka token'ları (değişmez kaynak — palet görselinden birebir)

```css
:root {
  --brand-navy:        #253442; /* Koyu lacivert */
  --brand-green:       #82E600; /* Valeo yeşili — imza aksan */
  --brand-blue:        #2D85B9; /* Mavi (açık) */
  --brand-blue-dark:   #1E5A7C; /* Mavi (koyu) */
  --brand-gray-light:  #E4EAED; /* Gri (açık) */
  --brand-gray-mid:    #93ADBC; /* Gri (orta) */
  --brand-slate:       #4B6A7C; /* Slate */
}
```

**Rol atama mantığı (KARAR: okunaklılık önce)**
- **Primary = Lacivert.** Ana etkileşim rengi; butonlar laciverttir. Açık temada dolu
  buton `navy #253442` + beyaz metin (çok yüksek kontrast, rahat AAA). Koyu temada
  zemin zaten lacivert olduğundan primary `blue #2D85B9`'a döner + beyaz metin.
- **Bilgi / link = Mavi.** `blue-dark #1E5A7C` bağlantı ve bilgi vurgusu için. `blue
  #2D85B9` üstüne beyaz metin ~4.05:1 (sınırda) → geniş buton dolgusu yapma.
- **Tertiary / aksan = Valeo yeşili `#82E600`.** Marka imzası ama **nokta vurgu** olarak:
  aktif göstergeler, kilit KPI, grafik highlight'ı. Üzerine **her zaman koyu lacivert
  metin** (~8:1); **beyaz metin asla**. Geniş dolgu yapma, göz yorar.
- **Secondary = Slate `#4B6A7C`.** Destekleyici mavi-gri, tonal butonlar.
- **Nötr:** metin lacivert/`gray-light`, ikincil metin/çizgi `gray-mid`.

### 2.2 Açık (light) tema

```css
:root, [data-theme="light"] {
  /* Primary (lacivert — sakin/kurumsal buton) */
  --md-sys-color-primary:               #253442; /* brand-navy */
  --md-sys-color-on-primary:            #FFFFFF;
  --md-sys-color-primary-container:     #CDE7F5; /* (türetilmiş) açık mavi */
  --md-sys-color-on-primary-container:  #06263A; /* (türetilmiş) */

  /* Bilgi / link = mavi (butonda değil, vurgu/bağlantıda) */
  --md-sys-color-info:                  #1E5A7C; /* brand-blue-dark */
  --md-sys-color-on-info:               #FFFFFF;

  /* Secondary (slate) */
  --md-sys-color-secondary:             #4B6A7C;
  --md-sys-color-on-secondary:          #FFFFFF;
  --md-sys-color-secondary-container:   #D6E3EC; /* (türetilmiş) */
  --md-sys-color-on-secondary-container:#0C2530; /* (türetilmiş) */

  /* Tertiary / aksan (Valeo yeşili) */
  --md-sys-color-tertiary:              #4C6B00; /* (türetilmiş) açık zeminde okunur yeşil */
  --md-sys-color-on-tertiary:           #FFFFFF;
  --md-sys-color-tertiary-container:    #C7F27A; /* (türetilmiş) açık yeşil dolgu */
  --md-sys-color-on-tertiary-container: #1B2600; /* (türetilmiş) */

  /* Durum */
  --md-sys-color-error:                 #BA1A1A;
  --md-sys-color-on-error:              #FFFFFF;
  --md-sys-color-error-container:       #FFDAD6;
  --md-sys-color-on-error-container:    #410002;
  --dash-color-success:                 #2E6B4F; /* (türetilmiş) */
  --dash-color-success-container:       #C7ECD6; /* (türetilmiş) */
  --dash-color-warning:                 #8A5A00; /* (türetilmiş) */
  --dash-color-warning-container:       #FBE7C2; /* (türetilmiş) */

  /* Surface & katmanlar (soğuk gri rampası) */
  --md-sys-color-surface:                    #F7FAFB; /* (türetilmiş) — sayfa zemini */
  --md-sys-color-surface-container-lowest:   #FFFFFF;
  --md-sys-color-surface-container-low:      #EEF3F5; /* (türetilmiş) — kart zemini */
  --md-sys-color-surface-container:          #E4EAED; /* brand-gray-light */
  --md-sys-color-surface-container-high:     #DBE3E8; /* (türetilmiş) */
  --md-sys-color-surface-container-highest:  #D2DDE3; /* (türetilmiş) */

  /* Metin & kenarlık */
  --md-sys-color-on-surface:            #1A2733; /* (türetilmiş) lacivere yakın */
  --md-sys-color-on-surface-variant:    #41525E; /* (türetilmiş) ikincil metin */
  --md-sys-color-outline:               #71818B; /* (türetilmiş) */
  --md-sys-color-outline-variant:       #C1CDD3; /* (türetilmiş) ince çizgi */

  /* Dostane takma adlar (kolaylık) */
  --row-hover: rgba(130,230,0,0.08);
}
```

### 2.3 Koyu (dark) tema

```css
[data-theme="dark"] {
  /* Primary (koyu temada mavi — lacivert zemine karışmasın diye) */
  --md-sys-color-primary:               #2D85B9; /* brand-blue */
  --md-sys-color-on-primary:            #FFFFFF;
  --md-sys-color-primary-container:     #1E5A7C; /* brand-blue-dark */
  --md-sys-color-on-primary-container:  #CDE7F5; /* (türetilmiş) */

  /* Bilgi / link */
  --md-sys-color-info:                  #7FC0E6; /* (türetilmiş) koyuda açık mavi */
  --md-sys-color-on-info:               #06263A;

  /* Secondary */
  --md-sys-color-secondary:             #93ADBC; /* brand-gray-mid */
  --md-sys-color-on-secondary:          #14242E; /* (türetilmiş) */
  --md-sys-color-secondary-container:   #33505F; /* (türetilmiş) */
  --md-sys-color-on-secondary-container:#D6E3EC; /* (türetilmiş) */

  /* Tertiary / aksan — dark zeminde ham Valeo yeşili parlar */
  --md-sys-color-tertiary:              #82E600; /* brand-green */
  --md-sys-color-on-tertiary:           #253442; /* brand-navy — üzerine lacivert metin */
  --md-sys-color-tertiary-container:    #3C5500; /* (türetilmiş) */
  --md-sys-color-on-tertiary-container: #C7F27A; /* (türetilmiş) */

  /* Durum */
  --md-sys-color-error:                 #FFB4AB;
  --md-sys-color-on-error:              #690005;
  --md-sys-color-error-container:       #93000A;
  --md-sys-color-on-error-container:    #FFDAD6;
  --dash-color-success:                 #7FD1A6; /* (türetilmiş) */
  --dash-color-success-container:       #1E4535; /* (türetilmiş) */
  --dash-color-warning:                 #E9B44C; /* (türetilmiş) */
  --dash-color-warning-container:       #4A3A12; /* (türetilmiş) */

  /* Surface & katmanlar — brand-navy #253442 çevresinden türetildi */
  --md-sys-color-surface:                    #1B2831; /* (türetilmiş) — sayfa zemini */
  --md-sys-color-surface-container-lowest:   #16212B; /* (türetilmiş) */
  --md-sys-color-surface-container-low:      #202D37; /* (türetilmiş) — kart zemini */
  --md-sys-color-surface-container:          #253442; /* brand-navy */
  --md-sys-color-surface-container-high:     #2E3E4D; /* (türetilmiş) */
  --md-sys-color-surface-container-highest:  #384A5A; /* (türetilmiş) */

  /* Metin & kenarlık */
  --md-sys-color-on-surface:            #E4EAED; /* brand-gray-light */
  --md-sys-color-on-surface-variant:    #93ADBC; /* brand-gray-mid */
  --md-sys-color-outline:               #6E8794; /* (türetilmiş) */
  --md-sys-color-outline-variant:       #3A4C58; /* (türetilmiş) */

  --row-hover: rgba(130,230,0,0.12);
}

/* İşletim sistemi koyu tercihini, kullanıcı elle seçim yapmadıysa uygula */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    /* Yukarıdaki [data-theme="dark"] bloğunun aynısı geçerli olur.
       Pratikte: aşağıdaki toggle JS'i sayfa açılışında data-theme'i
       OS tercihine göre kurar; bu media query yedek güvencedir. */
  }
}
```

### 2.4 Tema toggle (KARAR: elle seçim + OS varsayılanı)

Üst barın sağında güneş/ay ikonlu bir toggle bulunur. Varsayılan olarak işletim
sistemi tercihini izler; kullanıcı elle değiştirebilir ve seçimi `localStorage`'da
saklanır. Erişilebilir olsun (klavyeyle seçilebilir, `aria-label`).

```html
<script>
  (function () {
    var saved = localStorage.getItem('valeo-theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    window.toggleTheme = function () {
      var cur = document.documentElement.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('valeo-theme', next);
    };
  })();
</script>
```

> Kural: Kodun hiçbir yerinde renk sabit (`#FFFFFF` gibi) yazılmaz — **her zaman**
> ilgili `var(--md-sys-color-*)` rolü kullanılır. Metin daima ilgili `on-*` rolüyle.

### 2.5 Grafik serisi paleti

Tablo/grafik ağırlıklı uygulama için, birbirinden net ayrılan ve markayla uyumlu sıra.
İlk seride yeşil vurgu, sonra maviler; 5'ten fazla seri gerekirse 6–7 ek tonları.

```css
:root {
  --chart-1: #82E600; /* Valeo yeşili — ana/kilit seri */
  --chart-2: #2D85B9; /* mavi açık */
  --chart-3: #4B6A7C; /* slate */
  --chart-4: #1E5A7C; /* mavi koyu */
  --chart-5: #93ADBC; /* gri orta */
  --chart-6: #2AA39A; /* teal (ek — 6. seri) */
  --chart-7: #5B6B9E; /* indigo (ek — 7. seri) */
}
```

**Kullanım kuralları**
- Sayfa zemini `surface`; kart zemini `surface-container-low` / `-container`.
- Üst üste binen paneller yükseldikçe daha yüksek container seviyesi.
- Yeşili büyük dolgu değil **nokta vurgu** olarak kullan.
- Renk körlüğü için: rengi tek ayırt edici yapma; çizgi tipi/desen/etiketle destekle.
- Riskli çiftler: beyaz metin `#2D85B9` üstünde (açık temada dolgu yapma); yeşil metin
  beyaz zeminde (kullanma — açık temada `tertiary` koyu yeşildir).

---

## 3. Tipografi (KARAR: Montserrat + Lato, M3 ölçeğine oturtulmuş)

M3'ün tip **ölçeği** (roller) korunur; typeface olarak marka fontları kullanılır.
- **Montserrat (600/700):** Display, Headline, Title — başlıklar ve büyük sayılar.
- **Lato (400/700):** Body, Label — gövde, tablo, buton, chip, rozet.
- Google Fonts'tan yüklenir; erişilemezse `system-ui`'ye düş.

```css
:root {
  --font-brand: 'Montserrat', system-ui, sans-serif; /* başlıklar */
  --font-plain: 'Lato', system-ui, sans-serif;        /* gövde */
}
```

| Rol            | Boyut / satır | Ağırlık | Font       | Nerede |
|----------------|---------------|---------|------------|--------|
| Display Small  | 36 / 44 px    | 700     | Montserrat | Büyük tek KPI sayısı |
| Headline Small | 24 / 32 px    | 600     | Montserrat | Bölüm başlığı |
| Title Large    | 22 / 28 px    | 600     | Montserrat | Kart başlığı |
| Title Medium   | 16 / 24 px    | 600     | Montserrat | Alt başlık, tablo başlığı |
| Body Large     | 16 / 24 px    | 400     | Lato       | Genel metin |
| Body Medium    | 14 / 20 px    | 400     | Lato       | Tablo hücresi, açıklama |
| Label Large    | 14 / 20 px    | 700     | Lato       | Buton, chip, sekme |
| Label Small    | 11 / 16 px    | 700     | Lato       | Rozet, üst etiket |

---

## 4. Şekil (köşe yarıçapı)

M3E cömert yuvarlaklıktan yana. Ölçek:

```css
:root {
  --md-sys-shape-corner-none:  0px;
  --md-sys-shape-corner-xs:    4px;
  --md-sys-shape-corner-sm:    8px;
  --md-sys-shape-corner-md:    10px;  /* input/select — hap değil */
  --md-sys-shape-corner-lg:    12px;  /* kartların varsayılanı (biraz sertleştirildi) */
  --md-sys-shape-corner-xl:    20px;  /* büyük paneller, diyaloglar (sertleştirildi) */
  --md-sys-shape-corner-full:  9999px;/* buton, chip, avatar */
}
```

**KARAR (dengeli):**
- **Birincil butonlar & filtre chip'leri:** `full` (hap) — M3E imzası, welcoming.
- **Metin/veri girişi inputları & select'ler:** `md` (10px) — hap input tuhaf durur,
  okunaklılık için orta yuvarlaklık.
- **Tablo içi küçük eylem butonları:** kompakt, `sm`–`md`; tıklama alanı yine ≥40px.
- **Metrik/grafik kartları:** `lg` (12px) — fazla yuvarlak değil, ölçülü.
- **Sayfa çapında ana paneller:** `xl` (20px).

---

## 5. Elevation / yüzey katmanları

Gölgeyi minimumda tut; derinliği **tonal** ver (yüzey tonu farkıyla).

| Katman              | Yüzey token'ı              | Gölge |
|---------------------|----------------------------|-------|
| Sayfa zemini        | `surface`                  | yok |
| Kart (durgun)       | `surface-container-low`    | yok / çok hafif |
| Kart (hover)        | `surface-container`        | hafif |
| Yüzen menü / dialog | `surface-container-high`   | orta |

```css
:root {
  --md-sys-elevation-1: 0 1px 2px rgba(0,0,0,.10);
  --md-sys-elevation-2: 0 2px 6px rgba(0,0,0,.12);
  --md-sys-elevation-3: 0 4px 12px rgba(0,0,0,.14);
}
```

> Koyu temada gölge yerine ince `outline-variant` kenar tercih et.

---

## 6. Spacing & grid

```css
:root {
  --dash-space-1: 4px;
  --dash-space-2: 8px;
  --dash-space-3: 12px;
  --dash-space-4: 16px;  /* kart iç dolgusu varsayılan */
  --dash-space-6: 24px;  /* kartlar arası boşluk */
  --dash-space-8: 32px;
}
```

- Dashboard grid: `display: grid; gap: var(--dash-space-6);`
- Duyarlı kolon: `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));`
- Kart iç dolgusu `var(--dash-space-4)`; başlık altı `var(--dash-space-3)`.

---

## 7. Motion (M3E — ölçülü)

```css
:root {
  --md-sys-motion-duration-short:  200ms;
  --md-sys-motion-duration-medium: 350ms;
  --md-sys-motion-duration-long:   500ms;

  --md-sys-motion-easing-standard:   cubic-bezier(0.2, 0, 0, 1);
  --md-sys-motion-easing-emphasized: cubic-bezier(0.2, 0, 0, 1);
  --md-sys-motion-easing-spring:     cubic-bezier(0.34, 1.30, 0.7, 1); /* hafif, ölçülü zıplama */
}
```

- Hover/press geri bildirimi: `short` + `standard`.
- Kart giriş / panel açılış: `medium` + `emphasized`; yaylı `spring` yalnızca küçük
  detaylarda (kurumsal his için abartma).
- `prefers-reduced-motion: reduce` altında tüm süreleri `0ms`/`1ms` yap.

---

## 8. Bileşen Kuralları

### Tablolar & listeler (BU UYGULAMANIN KALBİ — en çok özen buraya)
- Başlık satırı: Title Medium, `on-surface-variant`, zemin `surface-container`,
  yapışkan (sticky) olabilir ki uzun listede başlıklar hep görünür kalsın.
- Satır yüksekliği yoğun veri için 40–48px; hücre dolgusu ~10px 14px. Okunaklılık > sıkışıklık.
- Satır ayırıcı: 1px `outline-variant`.
- **Zebra yerine hover** tercih et: satır hover'da `var(--row-hover)` (hafif yeşilimsi).
- Sıralama okları, sayfalama, satır sayısı net ve sade.
- Sayısal sütunlar sağa, metin sola hizalı. Yatay taşmada kaydırma sorunsuz çalışsın.

### Metrik (KPI) kartı
- Zemin `surface-container-low`, köşe `lg`, dolgu `space-4`.
- Üst etiket: Label Small, `on-surface-variant`.
- Ana sayı: Display Small, `on-surface` (kilit KPI'da yeşil `tertiary` vurgu olabilir).
- Değişim rozeti: Label Small; artış `success`, azalış `error` (ikon + renk birlikte).

### Grafik kapsayıcısı
- Metrik kartıyla aynı yüzey ve köşe; başlık Title Large.
- Grafik renkleri §2.5 seri sırasını izler.
- Eksen/ızgara çizgileri `outline-variant`; eksen etiketleri `on-surface-variant`.

### Butonlar
- **Dolu (birincil):** zemin `primary`, metin `on-primary`, köşe `full`, yükseklik Label Large.
- **Tonal (ikincil):** zemin `secondary-container`, metin `on-secondary-container`, köşe `full`.
- **Metin (text):** şeffaf zemin, metin `primary`.
- **Aksan (nadir/kilit eylem):** zemin `tertiary-container`, metin `on-tertiary-container`.
- **Tehlikeli:** zemin `error`, metin `on-error`.
- Tablo içi küçük eylem butonları kompakt; tıklama hedefi ≥40px.

### Chip / filtre
- Köşe `full`; seçili durumda zemin `secondary-container` + `on-secondary-container` metin.

### Formlar & inputlar
- Zemin `surface-container-lowest`, kenar `outline-variant`, köşe `md` (10px), dolgu 10px 12px.
- Etiket üstte: Label Large, `on-surface-variant`.
- Focus'ta 2px `primary` halka.
- Hata: kenar `error` + altında küçük `error` metin.

### Bildirim / uyarı kutuları & rozetler
- Başarı → `dash-color-success-container` zemin + `dash-color-success` kenar/metin.
- Uyarı → `dash-color-warning-container` + `dash-color-warning`.
- Hata → `error-container` + `on-error-container`.
- Bilgi → `primary-container` + `on-primary-container`.
- Durumu renk + ikon/etiketle birlikte belirt (renk tek başına anlam taşımasın).

### Navigasyon
- Geniş ekran: sol **navigation rail** (ikon + Label Small).
- Dar ekran: alt **navigation bar**. Aktif öğe `secondary-container` göstergeli.

---

## 9. Dashboard Layout Deseni

```
┌───────────────────────────────────────────────┐
│  Top app bar (surface, başlık + tema toggle)   │
├───────┬───────────────────────────────────────┤
│ nav   │  [KPI] [KPI] [KPI] [KPI]   ← auto-fit  │
│ rail  │  ┌─────────────┐ ┌──────────────────┐  │
│       │  │ Grafik kartı│ │ Grafik kartı     │  │
│       │  └─────────────┘ └──────────────────┘  │
│       │  ┌──────────────────────────────────┐  │
│       │  │ Veri tablosu kartı               │  │
│       │  └──────────────────────────────────┘  │
└───────┴───────────────────────────────────────┘
```

---

## 10. Google Apps Script'e Özel Notlar

- **Ortak stil dosyası:** Tüm token'ları ve stilleri `styles.html` adlı bir include
  parçasında topla; ana HTML'lerin `<head>`'inde `<?!= include('styles'); ?>` ile çağır.
  `.gs` tarafına gerekiyorsa şu yardımcıyı ekle:
  `function include(f){ return HtmlService.createHtmlOutputFromFile(f).getContent(); }`
- **Build yok:** Saf CSS token; harici bileşen kütüphanesi gerekmez (varsayılan tercih).
- **iframe sandbox:** Uygulama iframe içinde çalışır; gerekiyorsa
  `createHtmlOutput(...).setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)`.
- **Sunucu çağrıları:** Veri çekişi `google.script.run.withSuccessHandler(...)` ile;
  yüklenirken kart yerine **skeleton** (`surface-container-low` zemin + hafif shimmer) göster.
- **Font:** Montserrat + Lato'yu Google Fonts CDN ile yükle; erişilemezse `system-ui`.
- **Bağımlılık riski:** Hazır M3E web bileşenleri resmî/Google-onaylı değildir ve iframe
  içinde ESM yükleme davranışı ayrıca test gerektirir. Varsayılan: bu dokümandaki saf CSS.

---

## 11. Erişilebilirlik

- Metin/zemin kontrastı en az WCAG AA (normal metin 4.5:1). `on-*` rolleri bunu sağlar.
- Yeşil aksan üstüne **daima** koyu lacivert metin; yeşil üstüne beyaz metin yok.
- Etkileşimli her öğede görünür **focus** halkası: 2px `primary`.
- Renk tek başına anlam taşımasın (durumları ikon/etiketle de belirt).
- Dokunma hedefi en az 48×48px (tablo içi kompakt butonlarda ≥40px).
- `prefers-reduced-motion` ve `prefers-color-scheme` desteklensin; tema toggle'ı OS'i ezebilir.

---

## 12. Genel His — Yap / Kaçın

**Yap:**
- Tabloları net, hizalı, okunaklı yap — en çok kullanılan yer burası.
- Yeşili nokta vurgu olarak kullan (birincil eylem mavi; yeşil = kilit KPI/aktif/grafik).
- Derinliği tonal yüzeylerle ver; gölgeyi minimumda tut.
- Cömert yuvarlaklık + ölçülü motion ile welcoming ama kurumsal dur.
- Her iki temada da kontrastın yeterli olduğundan emin ol.
- Renkleri hep `var(--md-sys-color-*)` rolüyle kullan (tema toggle için şart).

**Kaçın:**
- Yeşili geniş dolgu yapmak veya üstüne beyaz metin koymak (okunmaz).
- Aşırı oyuncu/zıplayan motion (bu bir iş aracı).
- Renkleri sabit hex yazmak — hep semantik token.
- Zebra + ağır gölge; sıkışık ya da gereksiz devasa boşluklu yerleşim.
- Palet dışına çıkmak; çok fazla renk.
```
