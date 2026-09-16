#!/usr/bin/env python3
"""DMF Daily — dashboard/data.json → dashboard/index.html renderer.

Sunum katmanı. Veri ayıklama extract_excel.py içinde; bu dosya Excel'e
ihtiyaç duymaz, data.json cache'i yeterlidir.

Görünüm design.md'ye (Valeo Tasarım Sistemi — Material 3 Expressive
uyarlaması) uyar. Renkler daima semantik token üzerinden kullanılır;
kodda sabit hex yazılmaz (design.md §2.4 kuralı).

design.md'nin §0 ve §10 bölümleri Google Apps Script projeleri içindir;
bu proje statik HTML ürettiği için o iki bölüm uygulanmaz.
"""

import os
import json
import base64

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH  = os.path.join(BASE_DIR, 'dashboard', 'data.json')
OUTPUT_PATH = os.path.join(BASE_DIR, 'dashboard', 'index.html')

if not os.path.exists(CACHE_PATH):
    raise SystemExit(
        f"Veri cache'i bulunamadi: {CACHE_PATH}\n"
        f"Once Excel'den uretin:  python3 extract_excel.py"
    )

with open(CACHE_PATH, encoding='utf-8') as f:
    data_json = json.load(f)

print("HTML oluşturuluyor...")

# ── Grafik serisi paleti (design.md §2.5) ────────────────────────────────────
# §2.5 yedi seri tanımlar; bu dashboard'da dokuz hat var, o yüzden palet aynı
# soğuk/marka ailesinde iki tonla genişletildi — design.md'nin kendi
# "(türetilmiş)" yöntemiyle aynı mantık.
#
# §11 her iki temada da kontrast şart koşuyor. §2.5'teki tek düz liste koyu
# lacivert zemin için seçilmiş; açık zeminde yeşil ve gri-orta okunmuyor.
# design.md'nin kendisi de aynı sorunu §2.2'de çözüyor (tertiary açık temada
# #4C6B00'a düşüyor), o yüzden seri paleti de tema başına türetildi.
# Hue kimliği ve §2.5 sırası korundu: yeşil, açık mavi, slate, koyu mavi,
# gri-orta, teal, indigo, (+ mor, kiremit).
CHART_SERIES_DARK = [
    '#82E600',  # chart-1  Valeo yeşili (ham — koyu zeminde parlar)
    '#4FA3D4',  # chart-2  mavi açık      (türetilmiş: #2D85B9 açıldı)
    '#93ADBC',  # chart-3  gri orta       (brand-gray-mid)
    '#2D85B9',  # chart-4  mavi           (brand-blue)
    '#C3D3DC',  # chart-5  gri açık       (türetilmiş)
    '#3FBFB3',  # chart-6  teal           (türetilmiş: #2AA39A açıldı)
    '#8B99CC',  # chart-7  indigo         (türetilmiş: #5B6B9E açıldı)
    '#C08AD4',  # chart-8  mor            (türetilmiş — 8. seri)
    '#E0964A',  # chart-9  kiremit        (türetilmiş — 9. seri)
]
CHART_SERIES_LIGHT = [
    '#4C6B00',  # chart-1  yeşil          (design.md §2.2'deki açık-tema yeşili)
    '#2D85B9',  # chart-2  mavi açık      (brand-blue)
    '#4B6A7C',  # chart-3  slate          (brand-slate)
    '#1E5A7C',  # chart-4  mavi koyu      (brand-blue-dark)
    '#5E7C8C',  # chart-5  gri orta       (türetilmiş: #93ADBC koyulaştırıldı)
    '#1E7A72',  # chart-6  teal           (türetilmiş)
    '#4A5889',  # chart-7  indigo         (türetilmiş)
    '#8A4F9E',  # chart-8  mor            (türetilmiş — 8. seri)
    '#A35A1E',  # chart-9  kiremit        (türetilmiş — 9. seri)
]

HATLAR = data_json['meta']['hatlar']
HAT_COLORS_DARK  = {h: CHART_SERIES_DARK[i % len(CHART_SERIES_DARK)]
                    for i, h in enumerate(HATLAR)}
HAT_COLORS_LIGHT = {h: CHART_SERIES_LIGHT[i % len(CHART_SERIES_LIGHT)]
                    for i, h in enumerate(HATLAR)}

data_js       = json.dumps(data_json, ensure_ascii=False, indent=2)
hat_dark_js   = json.dumps(HAT_COLORS_DARK)
hat_light_js  = json.dumps(HAT_COLORS_LIGHT)
series_dark_js  = json.dumps(CHART_SERIES_DARK)
series_light_js = json.dumps(CHART_SERIES_LIGHT)


# ── Gömülü varlıklar ─────────────────────────────────────────────────────────
def _inline_js(fname, cdn_fallback):
    """vendor/ altındaki kütüphaneyi HTML'e göm; yoksa CDN etiketine düş."""
    path = os.path.join(BASE_DIR, 'vendor', fname)
    try:
        with open(path, encoding='utf-8') as fh:
            body = fh.read().replace('</script>', '<\\/script>')
        return '<script>\n' + body + '\n  </script>'
    except FileNotFoundError:
        return f'<script src="{cdn_fallback}"></script>'


# design.md §3 Montserrat + Lato ister, §10 ise Google Fonts CDN'i önerir.
# Bu dashboard CDN'siz çalışmak zorunda (kapalı fabrika ağı, file://), o yüzden
# font dosyaları base64 olarak gömülür — marka fontu ve çevrimdışı çalışma
# birlikte korunur. Dosyalar yoksa §3'teki system-ui yedeğine düşülür.
_UNICODE_RANGE = {
    'latin': ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,"
              "U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,"
              "U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
    'latin-ext': ("U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,"
                  "U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,"
                  "U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
}
# (Türkçe: ı latin'de; ş ğ İ Ç Ö Ü latin-ext'te — ikisi de gömülür.)
_FONT_FACES = [
    ('Montserrat', 600, 'montserrat-latin-600.woff2',     'latin'),
    ('Montserrat', 600, 'montserrat-latin-ext-600.woff2', 'latin-ext'),
    ('Montserrat', 700, 'montserrat-latin-700.woff2',     'latin'),
    ('Montserrat', 700, 'montserrat-latin-ext-700.woff2', 'latin-ext'),
    ('Lato',       400, 'lato-latin-400.woff2',           'latin'),
    ('Lato',       400, 'lato-latin-ext-400.woff2',       'latin-ext'),
    ('Lato',       700, 'lato-latin-700.woff2',           'latin'),
    ('Lato',       700, 'lato-latin-ext-700.woff2',       'latin-ext'),
]


def build_font_css():
    out, missing = [], []
    for family, weight, fname, subset in _FONT_FACES:
        path = os.path.join(BASE_DIR, 'vendor', 'fonts', fname)
        if not os.path.exists(path):
            missing.append(fname)
            continue
        with open(path, 'rb') as fh:
            b64 = base64.b64encode(fh.read()).decode('ascii')
        out.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');"
            "unicode-range:%s}" % (family, weight, b64, _UNICODE_RANGE[subset])
        )
    if missing:
        print(f"  ! font eksik ({len(missing)}) — system-ui yedeğine düşülecek")
    return '\n    '.join(out)


chart_tag = '\n  '.join([
    _inline_js('chart.umd.min.js',
               'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'),
    _inline_js('chartjs-plugin-datalabels.min.js',
               'https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js'),
])
font_css = build_font_css()

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DMF Daily – Üretim Dashboard</title>
  <script>
    /* design.md §2.4 — OS tercihi varsayılan, kullanıcı seçimi localStorage'da.
       Render'dan önce çalışır ki açılışta tema atlaması olmasın. */
    (function(){{
      var saved=null; try{{saved=localStorage.getItem('valeo-theme');}}catch(e){{}}
      var prefersDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', saved || (prefersDark?'dark':'light'));
    }})();
  </script>
  {chart_tag}
  <style>
    {font_css}

    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

    /* ══ design.md §2.2 — Açık (light) tema ══════════════════════════════ */
    :root,[data-theme="light"]{{
      --md-sys-color-primary:               #253442;
      --md-sys-color-on-primary:            #FFFFFF;
      --md-sys-color-primary-container:     #CDE7F5;
      --md-sys-color-on-primary-container:  #06263A;
      --md-sys-color-info:                  #1E5A7C;
      --md-sys-color-on-info:               #FFFFFF;
      --md-sys-color-secondary:             #4B6A7C;
      --md-sys-color-on-secondary:          #FFFFFF;
      --md-sys-color-secondary-container:   #D6E3EC;
      --md-sys-color-on-secondary-container:#0C2530;
      --md-sys-color-tertiary:              #4C6B00;
      --md-sys-color-on-tertiary:           #FFFFFF;
      --md-sys-color-tertiary-container:    #C7F27A;
      --md-sys-color-on-tertiary-container: #1B2600;
      --md-sys-color-error:                 #BA1A1A;
      --md-sys-color-on-error:              #FFFFFF;
      --md-sys-color-error-container:       #FFDAD6;
      --md-sys-color-on-error-container:    #410002;
      --dash-color-success:                 #2E6B4F;
      --dash-color-success-container:       #C7ECD6;
      --dash-color-warning:                 #8A5A00;
      --dash-color-warning-container:       #FBE7C2;
      --md-sys-color-surface:                    #F7FAFB;
      --md-sys-color-surface-container-lowest:   #FFFFFF;
      --md-sys-color-surface-container-low:      #EEF3F5;
      --md-sys-color-surface-container:          #E4EAED;
      --md-sys-color-surface-container-high:     #DBE3E8;
      --md-sys-color-surface-container-highest:  #D2DDE3;
      --md-sys-color-on-surface:            #1A2733;
      --md-sys-color-on-surface-variant:    #41525E;
      --md-sys-color-outline:               #71818B;
      --md-sys-color-outline-variant:       #C1CDD3;
      --row-hover: rgba(130,230,0,0.08);
      --dash-shadow-1: var(--md-sys-elevation-1);
    }}

    /* ══ design.md §2.3 — Koyu (dark) tema ═══════════════════════════════ */
    [data-theme="dark"]{{
      --md-sys-color-primary:               #2D85B9;
      --md-sys-color-on-primary:            #FFFFFF;
      --md-sys-color-primary-container:     #1E5A7C;
      --md-sys-color-on-primary-container:  #CDE7F5;
      --md-sys-color-info:                  #7FC0E6;
      --md-sys-color-on-info:               #06263A;
      --md-sys-color-secondary:             #93ADBC;
      --md-sys-color-on-secondary:          #14242E;
      --md-sys-color-secondary-container:   #33505F;
      --md-sys-color-on-secondary-container:#D6E3EC;
      --md-sys-color-tertiary:              #82E600;
      --md-sys-color-on-tertiary:           #253442;
      --md-sys-color-tertiary-container:    #3C5500;
      --md-sys-color-on-tertiary-container: #C7F27A;
      --md-sys-color-error:                 #FFB4AB;
      --md-sys-color-on-error:              #690005;
      --md-sys-color-error-container:       #93000A;
      --md-sys-color-on-error-container:    #FFDAD6;
      --dash-color-success:                 #7FD1A6;
      --dash-color-success-container:       #1E4535;
      --dash-color-warning:                 #E9B44C;
      --dash-color-warning-container:       #4A3A12;
      --md-sys-color-surface:                    #1B2831;
      --md-sys-color-surface-container-lowest:   #16212B;
      --md-sys-color-surface-container-low:      #202D37;
      --md-sys-color-surface-container:          #253442;
      --md-sys-color-surface-container-high:     #2E3E4D;
      --md-sys-color-surface-container-highest:  #384A5A;
      --md-sys-color-on-surface:            #E4EAED;
      --md-sys-color-on-surface-variant:    #93ADBC;
      --md-sys-color-outline:               #6E8794;
      --md-sys-color-outline-variant:       #3A4C58;
      --row-hover: rgba(130,230,0,0.12);
      /* §5 — koyu temada gölge yerine ince kenar */
      --dash-shadow-1: none;
    }}

    /* ══ §3 Tipografi · §4 Şekil · §5 Elevation · §6 Spacing · §7 Motion ══ */
    :root{{
      --font-brand:'Montserrat',system-ui,sans-serif;
      --font-plain:'Lato',system-ui,sans-serif;

      --md-sys-shape-corner-none:0px;  --md-sys-shape-corner-xs:4px;
      --md-sys-shape-corner-sm:8px;    --md-sys-shape-corner-md:10px;
      --md-sys-shape-corner-lg:12px;   --md-sys-shape-corner-xl:20px;
      --md-sys-shape-corner-full:9999px;

      --md-sys-elevation-1:0 1px 2px rgba(0,0,0,.10);
      --md-sys-elevation-2:0 2px 6px rgba(0,0,0,.12);
      --md-sys-elevation-3:0 4px 12px rgba(0,0,0,.14);

      --dash-space-1:4px;  --dash-space-2:8px;  --dash-space-3:12px;
      --dash-space-4:16px; --dash-space-6:24px; --dash-space-8:32px;

      --md-sys-motion-duration-short:200ms;
      --md-sys-motion-duration-medium:350ms;
      --md-sys-motion-duration-long:500ms;
      --md-sys-motion-easing-standard:cubic-bezier(0.2,0,0,1);
      --md-sys-motion-easing-emphasized:cubic-bezier(0.2,0,0,1);
      --md-sys-motion-easing-spring:cubic-bezier(0.34,1.30,0.7,1);
    }}

    /* §7 — hareket azaltma tercihi */
    @media(prefers-reduced-motion:reduce){{
      *,*::before,*::after{{animation-duration:1ms!important;transition-duration:1ms!important}}
    }}

    /* ── Tip rolleri (§3) ── */
    .t-display-sm {{font:700 36px/44px var(--font-brand)}}
    .t-headline-sm{{font:600 24px/32px var(--font-brand)}}
    .t-title-lg   {{font:600 22px/28px var(--font-brand)}}
    .t-title-md   {{font:600 16px/24px var(--font-brand)}}
    .t-body-lg    {{font:400 16px/24px var(--font-plain)}}
    .t-body-md    {{font:400 14px/20px var(--font-plain)}}
    .t-label-lg   {{font:700 14px/20px var(--font-plain)}}
    .t-label-sm   {{font:700 11px/16px var(--font-plain);letter-spacing:.4px}}

    body{{
      background:var(--md-sys-color-surface);
      color:var(--md-sys-color-on-surface);
      font:400 14px/20px var(--font-plain);
      -webkit-font-smoothing:antialiased;
    }}

    /* §11 — her etkileşimli öğede görünür focus halkası */
    :where(a,button,select,input,[tabindex]):focus-visible{{
      outline:2px solid var(--md-sys-color-primary);
      outline-offset:2px;
      border-radius:var(--md-sys-shape-corner-xs);
    }}

    /* ══ §9 Layout — top app bar + navigation rail ══════════════════════ */
    .appbar{{
      background:var(--md-sys-color-surface);
      border-bottom:1px solid var(--md-sys-color-outline-variant);
      padding:var(--dash-space-3) var(--dash-space-6);
      display:flex;align-items:center;justify-content:space-between;gap:var(--dash-space-4);
      position:sticky;top:0;z-index:200;
    }}
    .appbar h1{{font:600 22px/28px var(--font-brand);color:var(--md-sys-color-on-surface)}}
    .appbar .right{{display:flex;align-items:center;gap:var(--dash-space-4)}}
    .appbar .upd{{font:400 14px/20px var(--font-plain);color:var(--md-sys-color-on-surface-variant)}}

    /* Tonal buton (§8) */
    .btn-tonal{{
      background:var(--md-sys-color-secondary-container);
      color:var(--md-sys-color-on-secondary-container);
      border:none;border-radius:var(--md-sys-shape-corner-full);
      padding:10px var(--dash-space-4);min-height:40px;
      font:700 14px/20px var(--font-plain);cursor:pointer;white-space:nowrap;
      display:inline-flex;align-items:center;gap:var(--dash-space-2);
      transition:background var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard);
    }}
    .btn-tonal:hover{{background:var(--md-sys-color-surface-container-highest)}}

    .shell{{display:grid;grid-template-columns:88px 1fr;min-height:calc(100vh - 57px)}}

    .rail{{
      background:var(--md-sys-color-surface);
      border-right:1px solid var(--md-sys-color-outline-variant);
      display:flex;flex-direction:column;align-items:center;
      gap:var(--dash-space-1);padding:var(--dash-space-3) var(--dash-space-2);
      position:sticky;top:57px;height:calc(100vh - 57px);
    }}
    .rail-item{{
      width:100%;background:none;border:none;cursor:pointer;
      display:flex;flex-direction:column;align-items:center;gap:var(--dash-space-1);
      padding:var(--dash-space-2) 0;color:var(--md-sys-color-on-surface-variant);
      font:700 11px/16px var(--font-plain);letter-spacing:.2px;text-align:center;
    }}
    .rail-ind{{
      width:56px;height:32px;border-radius:var(--md-sys-shape-corner-full);
      display:flex;align-items:center;justify-content:center;font-size:18px;line-height:1;
      transition:background var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-emphasized);
    }}
    .rail-item:hover .rail-ind{{background:var(--md-sys-color-surface-container)}}
    .rail-item[aria-selected="true"]{{color:var(--md-sys-color-on-surface)}}
    .rail-item[aria-selected="true"] .rail-ind{{
      background:var(--md-sys-color-secondary-container);
      color:var(--md-sys-color-on-secondary-container);
    }}
    .rail-label{{max-width:80px;overflow-wrap:anywhere}}

    .screen{{display:none;padding:var(--dash-space-6);max-width:1700px;margin:0 auto}}
    .screen.active{{display:block}}

    /* ── §8 Metrik (KPI) kartı ── */
    .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
              gap:var(--dash-space-6);margin-bottom:var(--dash-space-8)}}
    .kcard{{
      background:var(--md-sys-color-surface-container-low);
      border:1px solid var(--md-sys-color-outline-variant);
      border-radius:var(--md-sys-shape-corner-lg);padding:var(--dash-space-4);
      box-shadow:var(--dash-shadow-1);
      transition:background var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard);
    }}
    .kcard:hover{{background:var(--md-sys-color-surface-container)}}
    .khat{{font:700 11px/16px var(--font-plain);letter-spacing:.8px;text-transform:uppercase;
          color:var(--md-sys-color-on-surface-variant);display:flex;align-items:center;
          gap:var(--dash-space-2);margin-bottom:var(--dash-space-3)}}
    .kdot{{width:10px;height:10px;border-radius:var(--md-sys-shape-corner-full);flex:none}}
    .klabel{{font:700 11px/16px var(--font-plain);letter-spacing:.4px;
            color:var(--md-sys-color-on-surface-variant);margin-bottom:2px}}
    .kval{{font:700 36px/44px var(--font-brand);color:var(--md-sys-color-on-surface)}}
    .kval-sm{{font:600 22px/28px var(--font-brand);color:var(--md-sys-color-on-surface)}}
    .ksub{{font:400 14px/20px var(--font-plain);color:var(--md-sys-color-on-surface-variant)}}
    .krow{{margin-bottom:var(--dash-space-3)}}
    .trpbar{{height:6px;background:var(--md-sys-color-surface-container-high);
            border-radius:var(--md-sys-shape-corner-full);margin-top:var(--dash-space-2);overflow:hidden}}
    .trpfill{{height:100%;border-radius:var(--md-sys-shape-corner-full);
             transition:width var(--md-sys-motion-duration-medium) var(--md-sys-motion-easing-emphasized)}}
    .kmini{{display:grid;grid-template-columns:1fr 1fr;gap:var(--dash-space-2);margin-top:var(--dash-space-3)}}

    /* §8 rozet — durum renk + etiket birlikte (§11) */
    .chip-stat{{display:inline-flex;align-items:center;gap:var(--dash-space-1);
      padding:2px var(--dash-space-2);border-radius:var(--md-sys-shape-corner-full);
      font:700 11px/16px var(--font-plain)}}
    .st-ok  {{background:var(--dash-color-success-container);color:var(--dash-color-success)}}
    .st-warn{{background:var(--dash-color-warning-container);color:var(--dash-color-warning)}}
    .st-bad {{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}}

    .section-head{{font:600 16px/24px var(--font-brand);color:var(--md-sys-color-on-surface-variant);
                  margin-bottom:var(--dash-space-3)}}
    .smf-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
             gap:var(--dash-space-6);margin-bottom:var(--dash-space-8)}}

    /* ── §8 Grafik kapsayıcısı ── */
    .crow{{display:grid;grid-template-columns:1fr 1fr;gap:var(--dash-space-6);margin-bottom:var(--dash-space-6)}}
    .crow.full{{grid-template-columns:1fr}}
    .ccard{{
      background:var(--md-sys-color-surface-container-low);
      border:1px solid var(--md-sys-color-outline-variant);
      border-radius:var(--md-sys-shape-corner-lg);padding:var(--dash-space-4);
      box-shadow:var(--dash-shadow-1);
    }}
    .ctitle{{font:600 16px/24px var(--font-brand);color:var(--md-sys-color-on-surface);
            margin-bottom:var(--dash-space-3)}}
    .cnote{{font:400 14px/20px var(--font-plain);color:var(--md-sys-color-on-surface-variant);
           margin-top:var(--dash-space-2)}}
    .cwrap{{position:relative;height:270px}}

    /* ── §8 Chip / filtre ── */
    .filt{{display:flex;flex-wrap:wrap;gap:var(--dash-space-2);margin-bottom:var(--dash-space-4);
          align-items:center}}
    .filt > span{{font:700 11px/16px var(--font-plain);letter-spacing:.4px;
                 color:var(--md-sys-color-on-surface-variant);text-transform:uppercase}}
    .chip{{
      display:inline-flex;align-items:center;gap:var(--dash-space-2);
      min-height:40px;padding:var(--dash-space-2) var(--dash-space-4);
      border-radius:var(--md-sys-shape-corner-full);
      border:1px solid var(--md-sys-color-outline-variant);background:transparent;
      color:var(--md-sys-color-on-surface-variant);font:700 14px/20px var(--font-plain);
      cursor:pointer;
      transition:background var(--md-sys-motion-duration-short) var(--md-sys-motion-easing-standard);
    }}
    .chip:hover{{background:var(--md-sys-color-surface-container)}}
    .chip[aria-pressed="true"]{{
      background:var(--md-sys-color-secondary-container);
      color:var(--md-sys-color-on-secondary-container);
      border-color:transparent;
    }}
    /* Seri rengi noktayla taşınır; anlam yalnız renge binmesin diye etiket de var (§11) */
    .chip-dot{{width:10px;height:10px;border-radius:var(--md-sys-shape-corner-full);flex:none}}

    /* ── §8 Formlar & inputlar ── */
    .field{{display:flex;flex-direction:column;gap:var(--dash-space-1)}}
    .field label{{font:700 14px/20px var(--font-plain);color:var(--md-sys-color-on-surface-variant)}}
    select,input[type="text"]{{
      background:var(--md-sys-color-surface-container-lowest);
      color:var(--md-sys-color-on-surface);
      border:1px solid var(--md-sys-color-outline-variant);
      border-radius:var(--md-sys-shape-corner-md);
      padding:10px var(--dash-space-3);min-height:40px;
      font:400 14px/20px var(--font-plain);
    }}
    select:hover,input[type="text"]:hover{{border-color:var(--md-sys-color-outline)}}

    /* ── §8 Tablolar (uygulamanın kalbi) ── */
    .twrap{{
      background:var(--md-sys-color-surface-container-low);
      border:1px solid var(--md-sys-color-outline-variant);
      border-radius:var(--md-sys-shape-corner-lg);overflow:hidden;
      box-shadow:var(--dash-shadow-1);
    }}
    .fbar{{display:flex;gap:var(--dash-space-3);padding:var(--dash-space-4);
          border-bottom:1px solid var(--md-sys-color-outline-variant);
          flex-wrap:wrap;align-items:flex-end}}
    .tscroll{{overflow:auto;max-height:70vh}}
    table{{width:100%;border-collapse:collapse;min-width:820px}}
    thead th{{
      position:sticky;top:0;z-index:1;
      background:var(--md-sys-color-surface-container);
      color:var(--md-sys-color-on-surface-variant);
      font:600 16px/24px var(--font-brand);font-size:13px;
      text-align:left;padding:var(--dash-space-3) 14px;
      border-bottom:1px solid var(--md-sys-color-outline-variant);white-space:nowrap;
    }}
    tbody td{{
      padding:10px 14px;height:44px;
      border-bottom:1px solid var(--md-sys-color-outline-variant);
      font:400 14px/20px var(--font-plain);color:var(--md-sys-color-on-surface);
    }}
    tbody tr:last-child td{{border-bottom:none}}
    /* §8 — zebra değil hover */
    tbody tr:hover td{{background:var(--row-hover)}}
    .num{{text-align:right;font-variant-numeric:tabular-nums}}
    th.num{{text-align:right}}
    .cell-mut{{color:var(--md-sys-color-on-surface-variant)}}
    .cell-ref{{color:var(--md-sys-color-info);font-weight:700}}
    .cell-clip{{max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}

    /* §8 rozetler — hepsi mevcut token'lara eşlendi, palet dışına çıkılmadı (§12) */
    .badge{{display:inline-block;padding:2px var(--dash-space-2);
           border-radius:var(--md-sys-shape-corner-full);
           font:700 11px/16px var(--font-plain);white-space:nowrap;border:1px solid transparent}}
    .ba{{background:var(--md-sys-color-error-container);color:var(--md-sys-color-on-error-container)}}
    .bk{{background:var(--dash-color-warning-container);color:var(--dash-color-warning)}}
    .bp{{background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container)}}
    .bs{{background:var(--dash-color-success-container);color:var(--dash-color-success)}}
    .bm{{background:var(--md-sys-color-tertiary-container);color:var(--md-sys-color-on-tertiary-container)}}
    .bl{{background:var(--md-sys-color-secondary-container);color:var(--md-sys-color-on-secondary-container)}}
    .bd{{background:var(--md-sys-color-surface-container-high);color:var(--md-sys-color-on-surface-variant)}}

    .empty{{text-align:center;color:var(--md-sys-color-on-surface-variant);
           padding:var(--dash-space-8);font:400 16px/24px var(--font-plain)}}

    /* ── §8-9 Dar ekran: rail yerine alt navigation bar ── */
    @media(max-width:900px){{
      .crow{{grid-template-columns:1fr}}
      .shell{{grid-template-columns:1fr}}
      .rail{{
        position:fixed;bottom:0;left:0;right:0;top:auto;height:auto;width:100%;
        flex-direction:row;justify-content:space-around;
        border-right:none;border-top:1px solid var(--md-sys-color-outline-variant);
        background:var(--md-sys-color-surface-container);z-index:300;
        padding:var(--dash-space-2) var(--dash-space-1);
      }}
      .rail-item{{width:auto;flex:1;min-width:0}}
      .rail-ind{{width:44px;height:28px}}
      .rail-label{{max-width:64px;font-size:10px}}
      .screen{{padding:var(--dash-space-4) var(--dash-space-4) 84px}}
      .appbar{{padding:var(--dash-space-3) var(--dash-space-4)}}
      .appbar h1{{font-size:17px;line-height:24px}}
      .appbar .upd{{display:none}}
    }}
  </style>
</head>
<body>

<header class="appbar">
  <h1>DMF Daily — Üretim Takip</h1>
  <div class="right">
    <span class="upd" id="upd-date"></span>
    <button class="btn-tonal" id="th-btn" onclick="toggleTheme()"
            aria-label="Koyu temaya geç" title="Tema değiştir">
      <span id="th-icon" aria-hidden="true">🌙</span><span id="th-text">Koyu</span>
    </button>
  </div>
</header>

<div class="shell">
  <nav class="rail" role="tablist" aria-label="Dashboard bölümleri" id="rail"></nav>

  <main>
    <!-- E1: KPI -->
    <section id="screen-e1" class="screen active" role="tabpanel" aria-labelledby="tab-e1">
      <div class="kpi-grid" id="kpi-grid"></div>
      <h2 class="section-head">SMF-DOOSAN — Aralık 2025 – Şubat 2026</h2>
      <div class="smf-row" id="smf-cards"></div>
      <div class="crow">
        <div class="ccard"><h3 class="ctitle">Aylık Üretim — DMF Hatları</h3><div class="cwrap"><canvas id="ch-m-dmf"></canvas></div></div>
        <div class="ccard"><h3 class="ctitle">Aylık Üretim — PFW &amp; ITL</h3><div class="cwrap"><canvas id="ch-m-pfw"></canvas></div></div>
      </div>
      <div class="crow full">
        <div class="ccard"><h3 class="ctitle">SMF-DOOSAN Günlük Üretim</h3><div class="cwrap" style="height:230px"><canvas id="ch-smf"></canvas></div></div>
      </div>
    </section>

    <!-- E2: Trend -->
    <section id="screen-e2" class="screen" role="tabpanel" aria-labelledby="tab-e2">
      <div class="filt"><span>Hat</span><div class="filt" id="hf-btns" style="margin:0"></div></div>
      <div class="crow full"><div class="ccard"><h3 class="ctitle">Haftalık Üretim Trendi (Adet)</h3><div class="cwrap" style="height:330px"><canvas id="ch-tw-prod"></canvas></div></div></div>
      <div class="crow full"><div class="ccard"><h3 class="ctitle">Haftalık TRP (%) — Vardiya Başına Ortalama</h3><div class="cwrap" style="height:300px"><canvas id="ch-tw-trp"></canvas></div></div></div>
    </section>

    <!-- E3: Vardiya -->
    <section id="screen-e3" class="screen" role="tabpanel" aria-labelledby="tab-e3">
      <div class="filt"><div class="field"><label for="vrd-hat-sel">Hat</label>
        <select id="vrd-hat-sel" onchange="renderVardiya()"></select></div></div>
      <div class="crow">
        <div class="ccard"><h3 class="ctitle">Aylık Ortalama Vardiya Üretimi (Adet/Shift)</h3><div class="cwrap" style="height:310px"><canvas id="ch-vrd-aylik"></canvas></div></div>
        <div class="ccard"><h3 class="ctitle">Vardiya Toplam Dağılımı (Tüm Dönem)</h3><div class="cwrap" style="height:310px"><canvas id="ch-vrd-pie"></canvas></div></div>
      </div>
      <div class="crow full">
        <div class="ccard"><h3 class="ctitle">Aylık Vardiya Karşılaştırması</h3><div class="cwrap" style="height:300px"><canvas id="ch-vrd-trp"></canvas></div></div>
      </div>
    </section>

    <!-- E4: Referans -->
    <section id="screen-e4" class="screen" role="tabpanel" aria-labelledby="tab-e4">
      <div class="filt"><div class="field"><label for="ref-hat-sel">Hat</label>
        <select id="ref-hat-sel" onchange="renderRef()"></select></div></div>
      <div class="crow">
        <div class="ccard"><h3 class="ctitle">Referans Bazında Toplam Üretim (Adet)</h3><div class="cwrap" style="height:330px"><canvas id="ch-ref-bar"></canvas></div></div>
        <div class="ccard"><h3 class="ctitle">Referans Üretim Payı (%)</h3><div class="cwrap" style="height:330px"><canvas id="ch-ref-pie"></canvas></div></div>
      </div>
      <div class="crow full">
        <div class="ccard"><h3 class="ctitle">Referans Bazında Ortalama TRP (%)</h3>
          <div class="cwrap" style="height:360px"><canvas id="ch-ref-trp"></canvas></div>
          <p class="cnote">En az 3 vardiya kaydı olan referanslar. Referans–vardiya eşleşmesi yalnız DMF hatlarında var.</p>
        </div>
      </div>
    </section>

    <!-- E5: Duruş -->
    <section id="screen-e5" class="screen" role="tabpanel" aria-labelledby="tab-e5">
      <div class="crow">
        <div class="ccard"><h3 class="ctitle">Duruş Sebebi Pareto (dk)</h3><div class="cwrap" style="height:400px"><canvas id="ch-pc"></canvas></div></div>
        <div class="ccard"><h3 class="ctitle">Hat Bazında Toplam Duruş (dk)</h3><div class="cwrap" style="height:400px"><canvas id="ch-ph"></canvas></div></div>
      </div>
      <div class="crow full">
        <div class="ccard"><h3 class="ctitle">Aylık Duruş — Sebep Dağılımı (dk)</h3><div class="cwrap" style="height:310px"><canvas id="ch-durus-ay"></canvas></div></div>
      </div>
    </section>

    <!-- E6: Detay -->
    <section id="screen-e6" class="screen" role="tabpanel" aria-labelledby="tab-e6">
      <div class="twrap">
        <div class="fbar">
          <div class="field"><label for="f-hat">Hat</label>
            <select id="f-hat" onchange="flt()"><option value="">Tüm hatlar</option></select></div>
          <div class="field"><label for="f-sebep">Sebep</label>
            <select id="f-sebep" onchange="flt()"><option value="">Tüm sebepler</option></select></div>
          <div class="field"><label for="f-vardiya">Vardiya</label>
            <select id="f-vardiya" onchange="flt()"><option value="">Tümü</option><option>A</option><option>B</option><option>C</option></select></div>
          <div class="field" style="flex:1;min-width:200px"><label for="f-text">Açıklamada ara</label>
            <input id="f-text" type="text" placeholder="örn. robot" oninput="fltDebounced()"></div>
          <span class="chip-stat st-ok" id="fcount" role="status" aria-live="polite"></span>
        </div>
        <div class="tscroll">
          <table>
            <thead><tr>
              <th>Tarih</th><th>Vrd.</th><th>Hat</th><th>Referans</th>
              <th>Sebep</th><th class="num">Süre (dk)</th><th>Açıklama</th><th class="num">OP</th>
            </tr></thead>
            <tbody id="dur-tbody"></tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
</div>
<script>
const D           = {data_js};
const HC_DARK     = {hat_dark_js};
const HC_LIGHT    = {hat_light_js};
const SER_DARK    = {series_dark_js};
const SER_LIGHT   = {series_light_js};
let   HC = HC_LIGHT, SER = SER_LIGHT;

// ── utils ──────────────────────────────────────────────────────────────────
const h2r=(h,a=1)=>{{const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return`rgba(${{r}},${{g}},${{b}},${{a}})`;}};
const fmt=n=>new Intl.NumberFormat('tr-TR').format(Math.round(n));
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
const badgeCls=s=>/Arıza|Robot/.test(s)?'ba':/Kalite/.test(s)?'bk':/Parça|Sipariş|Besleme/.test(s)?'bp':/Set|Kesici/.test(s)?'bs':/Metod|Arge/.test(s)?'bm':/Planlı/.test(s)?'bl':'bd';

// ── tema (design.md §2.4) ──────────────────────────────────────────────────
// Kural §2.4: kodda sabit renk yok — her şey var(--md-sys-color-*) rolünden.
// Chart.js canvas'a çizdiği için token'lar JS'e getComputedStyle ile okunur.
const CSSV=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let TH={{}};
function readTheme(){{
  const dark=document.documentElement.getAttribute('data-theme')==='dark';
  HC  = dark?HC_DARK:HC_LIGHT;
  SER = dark?SER_DARK:SER_LIGHT;
  TH={{
    dark,
    txt:     CSSV('--md-sys-color-on-surface'),
    mut:     CSSV('--md-sys-color-on-surface-variant'),
    grid:    CSSV('--md-sys-color-outline-variant'),
    outline: CSSV('--md-sys-color-outline'),
    tipBg:   CSSV('--md-sys-color-surface-container-lowest'),
    surf:    CSSV('--md-sys-color-surface-container-low'),
    ok:      CSSV('--dash-color-success'),
    warn:    CSSV('--dash-color-warning'),
    bad:     CSSV('--md-sys-color-error'),
    accent:  CSSV('--md-sys-color-tertiary'),
    onAccent:CSSV('--md-sys-color-on-tertiary'),
  }};
  if(window.Chart){{
    Chart.defaults.color=TH.mut;
    Chart.defaults.borderColor=TH.grid;
    Chart.defaults.font.family="'Lato',system-ui,sans-serif";
  }}
}}
function applyTheme(t){{
  document.documentElement.setAttribute('data-theme',t);
  const dark=t==='dark';
  document.getElementById('th-icon').textContent = dark?'☀':'🌙';
  document.getElementById('th-text').textContent = dark?'Açık':'Koyu';
  document.getElementById('th-btn').setAttribute('aria-label', dark?'Açık temaya geç':'Koyu temaya geç');
  readTheme();
}}
function toggleTheme(){{
  const next=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';
  applyTheme(next);
  try{{localStorage.setItem('valeo-theme',next);}}catch(e){{}}
  // Renkler grafik options'ına gömülü; hepsi kirletilir, görünür olan hemen kurulur.
  Object.keys(BUILD).forEach(k=>DIRTY.add(k));
  ensure(ACTIVE);
}}
applyTheme(document.documentElement.getAttribute('data-theme')||'light');

// ── veri etiketleri ────────────────────────────────────────────────────────
// Kalıcı etiket; display:'auto' yalnız üst üste binenleri gizler.
Chart.register(ChartDataLabels);
Chart.defaults.set('plugins.datalabels',{{
  color:()=>TH.mut,
  font:{{size:9,weight:'700',family:"'Lato',system-ui,sans-serif"}},
  formatter:v=>(v===null||v===undefined||v===0)?'':fmt(v),
}});
const DL_V    = {{anchor:'end',align:'end',offset:1,display:'auto',clamp:true}};
const DL_H    = {{anchor:'end',align:'right',offset:3,display:'auto',clamp:true}};
const DL_LINE = {{anchor:'end',align:'top',offset:4,display:'auto',clamp:true}};
// Dolgu içine yazılan etiket her iki temada okunsun diye beyaz + koyu kontur.
const DL_IN   = {{anchor:'center',align:'center',display:'auto',color:'#fff',
                textStrokeColor:'rgba(0,0,0,.6)',textStrokeWidth:3,
                font:{{size:10,weight:'700',family:"'Lato',system-ui,sans-serif"}}}};
const pctFmt=(v,c)=>{{const t=c.dataset.data.reduce((a,b)=>a+(b||0),0);return(!v||!t)?'':(v/t*100).toFixed(1)+'%';}};
const trpFmt=v=>(v===null||v===undefined||v===0)?'':(+v).toFixed(1)+'%';
const trpTone=v=>v>=75?TH.ok:v>=55?TH.warn:TH.bad;

// Seri paleti 9 renk; duruş sebebi 13 tane. Modulo ile sarmalamak aynı rengi
// iki kategoriye verip legend'ı okunamaz hale getiriyordu. Her ek turda ton
// zeminden UZAĞA kaydırılır (koyu temada açılır, açık temada koyulaşır), böylece
// hem ayırt edilir hem §11'in 3:1 grafik kontrastı korunur.
const mix=(hex,t,toward)=>{{
  const n=parseInt(hex.slice(1),16),r=n>>16,g=(n>>8)&255,b=n&255;
  const f=(c)=>Math.round(c+(toward-c)*t);
  return'#'+[f(r),f(g),f(b)].map(v=>v.toString(16).padStart(2,'0')).join('');
}};
function serColor(i){{
  const n=SER.length,cycle=Math.floor(i/n),base=SER[i%n];
  if(cycle===0)return base;
  return mix(base,Math.min(.30+.22*(cycle-1),.72),TH.dark?255:0);
}}
// Duruş sebebi → renk eşlemesi tek yerde kurulur ki Pareto ve aylık dağılım
// grafiklerinde aynı sebep aynı rengi alsın.
let SEBEP_COLOR={{}};
function buildSebepColors(){{
  const order=[...D.pareto_cat_etiket];
  Object.values(D.durus_aylik).forEach(o=>Object.keys(o).forEach(s=>{{if(!order.includes(s))order.push(s);}}));
  SEBEP_COLOR={{}}; order.forEach((s,i)=>SEBEP_COLOR[s]=serColor(i));
}}

// ── ortak grafik ayarları ──────────────────────────────────────────────────
// §8: ızgara outline-variant, eksen etiketleri on-surface-variant.
const baseScales=()=>({{
  x:{{grid:{{color:TH.grid}},ticks:{{color:TH.mut,maxTicksLimit:14,maxRotation:45}}}},
  y:{{grid:{{color:TH.grid}},ticks:{{color:TH.mut}}}}
}});
const catAxis=()=>({{grid:{{color:'transparent'}},ticks:{{color:TH.txt,autoSkip:false,font:{{size:10}}}}}});
const baseLegend=()=>({{labels:{{color:TH.txt,font:{{size:12}},usePointStyle:true,pointStyle:'circle',boxWidth:8}}}});
const baseTip=()=>({{backgroundColor:TH.tipBg,borderColor:TH.outline,borderWidth:1,
                   titleColor:TH.txt,bodyColor:TH.txt,padding:10,cornerRadius:8}});

// ── grafik kaydı & sekme bazlı tembel kurulum ──────────────────────────────
const CHARTS={{}};
function mk(id,cfg){{
  if(CHARTS[id]){{CHARTS[id].destroy();delete CHARTS[id];}}
  CHARTS[id]=new Chart(document.getElementById(id),cfg);
  return CHARTS[id];
}}

// ── §8-9 Navigation rail ───────────────────────────────────────────────────
const TABS=[
  ['e1','📊','KPI Özet'],   ['e2','📈','Üretim Trendi'], ['e3','🔀','Vardiya'],
  ['e4','🏷','Referans'],   ['e5','⏱','Duruş Analizi'],  ['e6','📋','Duruş Detay'],
];
const rail=document.getElementById('rail');
TABS.forEach(([id,icon,label],i)=>{{
  const b=document.createElement('button');
  b.className='rail-item'; b.id='tab-'+id; b.type='button';
  b.setAttribute('role','tab');
  b.setAttribute('aria-selected',i===0?'true':'false');
  b.setAttribute('aria-controls','screen-'+id);
  b.innerHTML=`<span class="rail-ind" aria-hidden="true">${{icon}}</span><span class="rail-label">${{esc(label)}}</span>`;
  b.onclick=()=>T(id);
  rail.appendChild(b);
}});
function T(id){{
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.rail-item').forEach(t=>t.setAttribute('aria-selected','false'));
  document.getElementById('screen-'+id).classList.add('active');
  document.getElementById('tab-'+id).setAttribute('aria-selected','true');
  ACTIVE=id; ensure(id);
}}
function ensure(id){{ if(DIRTY.has(id)){{ BUILD[id](); DIRTY.delete(id); }} }}

// ── E1: KPI ───────────────────────────────────────────────────────────────
document.getElementById('upd-date').textContent='Son güncelleme: '+D.meta.guncelleme;

function buildE1(){{
  const g=document.getElementById('kpi-grid'); g.innerHTML='';
  D.meta.hatlar.forEach(hat=>{{
    const k=D.kpi[hat],c=HC[hat];
    const tp=k.ort_trp?(k.ort_trp*100):null;
    const ts=tp!==null?tp.toFixed(1)+'%':'—';
    const tone=tp===null?TH.mut:trpTone(tp);
    const cls=tp===null?'bd':tp>=75?'st-ok':tp>=55?'st-warn':'st-bad';
    const word=tp===null?'veri yok':tp>=75?'iyi':tp>=55?'orta':'düşük';
    g.innerHTML+=`<article class="kcard">
      <div class="khat"><span class="kdot" style="background:${{c}}"></span>${{esc(hat)}}</div>
      <div class="krow"><div class="klabel">Toplam Üretim</div>
        <div class="kval">${{fmt(k.toplam)}}</div>
        <div class="ksub">Haziran: ${{fmt(k.son_ay)}}</div></div>
      <div class="krow"><div class="klabel">TRP — son 4 hafta</div>
        <div class="kval-sm" style="color:${{tone}}">${{ts}}
          <span class="chip-stat ${{cls}}">${{word}}</span></div>
        <div class="trpbar"><div class="trpfill" style="width:${{Math.min(tp||0,100)}}%;background:${{tone}}"></div></div></div>
      <div class="kmini">
        <div><div class="klabel">Rework</div><div class="kval-sm" style="color:${{TH.warn}}">${{fmt(k.rework)}}</div></div>
        <div><div class="klabel">İskarta</div><div class="kval-sm" style="color:${{TH.bad}}">${{fmt(k.iskarta)}}</div></div>
      </div></article>`;
  }});

  const sk=D.smf_kpi;
  document.getElementById('smf-cards').innerHTML=`
    <article class="kcard"><div class="klabel">JX22 Toplam</div><div class="kval-sm">${{fmt(sk.jx22_toplam)}}</div></article>
    <article class="kcard"><div class="klabel">EB2 Toplam</div><div class="kval-sm">${{fmt(sk.eb2_toplam)}}</div></article>
    <article class="kcard"><div class="klabel">Genel Toplam</div><div class="kval-sm" style="color:${{TH.accent}}">${{fmt(sk.toplam)}}</div></article>
    <article class="kcard"><div class="klabel">NOK Adet</div><div class="kval-sm" style="color:${{TH.bad}}">${{fmt(sk.nok)}}</div></article>
    <article class="kcard"><div class="klabel">Aktif Gün</div><div class="kval-sm">${{sk.aktif_gun}}</div><div class="ksub">Ara.2025–Şub.2026</div></article>`;

  const mBar=(id,hats)=>mk(id,{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:hats.map(h=>({{label:h,data:D.aylik_uretim[h],
      backgroundColor:h2r(HC[h],.85),borderColor:HC[h],borderWidth:1,
      borderRadius:{{topLeft:6,topRight:6}}}}))}},
    options:{{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:18}}}},
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_V,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
  mBar('ch-m-dmf',['DMF1','DMF2','DMF3','DMF4']);
  mBar('ch-m-pfw',['PFW1','PFW2','PFW3','PFW4','ITL']);

  mk('ch-smf',{{type:'bar',
    data:{{labels:D.smf_dates,datasets:[
      {{label:'JX22',data:D.smf_jx22,backgroundColor:h2r(SER[1],.9),stack:'s',borderRadius:3}},
      {{label:'EB2', data:D.smf_eb2, backgroundColor:h2r(SER[3],.9),stack:'s',borderRadius:3}},
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_IN,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:{{...baseScales().x,stacked:true}},y:{{...baseScales().y,stacked:true,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
}}

// ── E2: Trend ──────────────────────────────────────────────────────────────
let actH=new Set(['DMF1','DMF2','DMF3','DMF4']);
const tDS=ser=>[...actH].map(h=>({{label:h,data:ser[h]||[],borderColor:HC[h],
  backgroundColor:h2r(HC[h],.08),borderWidth:2.5,pointRadius:3,
  pointBackgroundColor:HC[h],tension:.3,fill:false}}));
const tOpts=(yFn,dlFmt)=>({{responsive:true,maintainAspectRatio:false,
  interaction:{{mode:'index',intersect:false}},layout:{{padding:{{top:16,right:22,left:8}}}},
  plugins:{{legend:baseLegend(),tooltip:baseTip(),
    datalabels:{{...DL_LINE,font:{{size:8,weight:'700'}},formatter:dlFmt}}}},
  scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:yFn}}}}}}}});

function buildE2(){{
  const hf=document.getElementById('hf-btns'); hf.innerHTML='';
  D.meta.hatlar.forEach(h=>{{
    const b=document.createElement('button');
    b.className='chip'; b.type='button';
    b.setAttribute('aria-pressed',actH.has(h)?'true':'false');
    b.innerHTML=`<span class="chip-dot" style="background:${{HC[h]}}"></span>${{esc(h)}}`;
    b.onclick=()=>{{
      if(actH.has(h)){{actH.delete(h);b.setAttribute('aria-pressed','false');}}
      else{{actH.add(h);b.setAttribute('aria-pressed','true');}}
      updTrend();
    }};
    hf.appendChild(b);
  }});
  mk('ch-tw-prod',{{type:'line',data:{{labels:D.haftalik_etiket,datasets:tDS(D.haftalik_uretim)}},options:tOpts(v=>fmt(v),v=>v?fmt(v):'')}});
  mk('ch-tw-trp', {{type:'line',data:{{labels:D.haftalik_etiket,datasets:tDS(D.haftalik_trp)}}, options:tOpts(v=>v+'%',trpFmt)}});
}}
function updTrend(){{
  const a=CHARTS['ch-tw-prod'],b=CHARTS['ch-tw-trp'];
  if(a){{a.data.datasets=tDS(D.haftalik_uretim);a.update();}}
  if(b){{b.data.datasets=tDS(D.haftalik_trp);b.update();}}
}}

// ── E3: Vardiya ─────────────────────────────────────────────────────────────
const vrdSel=document.getElementById('vrd-hat-sel');
D.meta.hatlar.forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;vrdSel.appendChild(o);}});
function renderVardiya(){{
  const hat=vrdSel.value||D.meta.hatlar[0];
  const vc=D.vardiya_chart[hat];
  // Vardiya A/B/C: seri paletinin ilk üç ayırt edici tonu.
  const vC={{A:SER[0],B:SER[1],C:SER[7]}};
  const vSet=()=>['A','B','C'].map(v=>({{label:'Vardiya '+v,data:vc[v],
    backgroundColor:h2r(vC[v],.85),borderColor:vC[v],borderWidth:1,
    borderRadius:{{topLeft:6,topRight:6}}}}));
  const barOpts=()=>({{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:18}}}},
    plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_V,font:{{size:8,weight:'700'}}}}}},
    scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}});

  mk('ch-vrd-aylik',{{type:'bar',data:{{labels:D.aylik_etiket,datasets:vSet()}},options:barOpts()}});

  const tot={{A:0,B:0,C:0}};
  ['A','B','C'].forEach(v=>(vc[v]||[]).forEach(x=>tot[v]+=x));
  mk('ch-vrd-pie',{{type:'doughnut',
    data:{{labels:['Vardiya A','Vardiya B','Vardiya C'],
      datasets:[{{data:[tot.A,tot.B,tot.C],backgroundColor:[h2r(vC.A,.85),h2r(vC.B,.85),h2r(vC.C,.85)],
        borderColor:TH.surf,borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,cutout:'58%',
      plugins:{{legend:baseLegend(),
        tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)+' adet'}}}},
        datalabels:{{...DL_IN,formatter:pctFmt}}}}}}
  }});

  mk('ch-vrd-trp',{{type:'bar',data:{{labels:D.aylik_etiket,datasets:vSet()}},options:barOpts()}});
}}

// ── E4: Referans ─────────────────────────────────────────────────────────────
const refSel=document.getElementById('ref-hat-sel');
D.meta.hatlar.forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;refSel.appendChild(o);}});
function renderRef(){{
  const hat=refSel.value||D.meta.hatlar[0];
  const r=D.ref_top[hat];
  const cols=r.labels.map((_,i)=>serColor(i));

  mk('ch-ref-bar',{{type:'bar',
    data:{{labels:r.labels,datasets:[{{label:'Üretim (adet)',data:r.data,
      backgroundColor:cols.map(c=>h2r(c,.85)),borderColor:cols,borderWidth:1,
      borderRadius:{{topRight:6,bottomRight:6}}}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:52}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:catAxis()}}}}
  }});

  mk('ch-ref-pie',{{type:'doughnut',
    data:{{labels:r.labels,datasets:[{{data:r.data,backgroundColor:cols.map(c=>h2r(c,.85)),
      borderColor:TH.surf,borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,cutout:'58%',
      plugins:{{legend:baseLegend(),
        tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)}}}},
        datalabels:{{...DL_IN,formatter:pctFmt}}}}}}
  }});

  const rt=D.ref_trp_avg[hat];
  if(rt&&rt.labels.length){{
    mk('ch-ref-trp',{{type:'bar',
      data:{{labels:rt.labels,datasets:[{{label:'Ort. TRP (%)',data:rt.trp,
        backgroundColor:rt.trp.map(v=>h2r(trpTone(v),.85)),
        borderColor:rt.trp.map(v=>trpTone(v)),borderWidth:1,
        borderRadius:{{topRight:6,bottomRight:6}}}}]}},
      options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:48}}}},
        plugins:{{legend:{{display:false}},
          tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.parsed.x.toFixed(1)+'%  ('+rt.shifts[ctx.dataIndex]+' vardiya)'}}}},
          datalabels:{{...DL_H,formatter:trpFmt}}}},
        scales:{{x:{{...baseScales().x,min:0,max:100,ticks:{{color:TH.mut,callback:v=>v+'%'}}}},y:catAxis()}}}}
    }});
  }} else {{
    if(CHARTS['ch-ref-trp']){{CHARTS['ch-ref-trp'].destroy();delete CHARTS['ch-ref-trp'];}}
    const cv=document.getElementById('ch-ref-trp'),ctx=cv.getContext('2d');
    cv.width=cv.clientWidth; cv.height=cv.clientHeight;
    ctx.clearRect(0,0,cv.width,cv.height);
    ctx.fillStyle=TH.mut; ctx.textAlign='center';
    ctx.font="400 16px 'Lato',system-ui,sans-serif";
    ctx.fillText('Bu hat için referans bazlı TRP verisi yok (PFW / ITL)',cv.width/2,cv.height/2);
  }}
}}

// ── E5: Duruş ─────────────────────────────────────────────────────────────
function buildE5(){{
  buildSebepColors();
  const pc=D.pareto_cat_etiket.map(s=>SEBEP_COLOR[s]);
  mk('ch-pc',{{type:'bar',
    data:{{labels:D.pareto_cat_etiket,datasets:[{{label:'Duruş (dk)',data:D.pareto_cat_deger,
      backgroundColor:pc.map(c=>h2r(c,.85)),borderColor:pc,borderWidth:1,
      borderRadius:{{topRight:6,bottomRight:6}}}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:56}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:catAxis()}}}}
  }});

  mk('ch-ph',{{type:'bar',
    data:{{labels:D.pareto_hat_etiket,datasets:[{{label:'Duruş (dk)',data:D.pareto_hat_deger,
      backgroundColor:D.pareto_hat_etiket.map(h=>h2r(HC[h]||TH.mut,.85)),
      borderColor:D.pareto_hat_etiket.map(h=>HC[h]||TH.mut),borderWidth:1,
      borderRadius:{{topRight:6,bottomRight:6}}}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:56}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:catAxis()}}}}
  }});

  const sebepler=[...new Set(Object.values(D.durus_aylik).flatMap(o=>Object.keys(o)))];
  mk('ch-durus-ay',{{type:'bar',
    data:{{labels:D.durus_aylar,datasets:sebepler.map((s,i)=>({{
      label:s,data:D.durus_aylar.map(ay=>(D.durus_aylik[ay]||{{}})[s]||0),
      backgroundColor:h2r(SEBEP_COLOR[s]||SER[i%SER.length],.9),stack:'d',borderRadius:2}}))}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{...baseLegend(),position:'bottom'}},tooltip:baseTip(),
        datalabels:{{...DL_IN,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:{{...baseScales().x,stacked:true}},y:{{...baseScales().y,stacked:true,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
}}

// ── E6: Duruş Detay ───────────────────────────────────────────────────────
const hSel=document.getElementById('f-hat'),sSel=document.getElementById('f-sebep');
[...new Set(D.son_duruslar.map(r=>r.hat))].sort().forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;hSel.appendChild(o);}});
[...new Set(D.son_duruslar.map(r=>r.sebep))].sort().forEach(s=>{{const o=document.createElement('option');o.value=s;o.textContent=s;sSel.appendChild(o);}});
let _fltT;
function fltDebounced(){{clearTimeout(_fltT);_fltT=setTimeout(flt,120);}}
function flt(){{
  const h=hSel.value,s=sSel.value,v=document.getElementById('f-vardiya').value,
        t=document.getElementById('f-text').value.toLowerCase();
  const rows=D.son_duruslar.filter(r=>(!h||r.hat===h)&&(!s||r.sebep===s)&&(!v||r.vardiya===v)&&(!t||r.aciklama.toLowerCase().includes(t)));
  document.getElementById('fcount').textContent=fmt(rows.length)+' kayıt';
  const tb=document.getElementById('dur-tbody');
  if(!rows.length){{tb.innerHTML='<tr><td colspan="8" class="empty">Kayıt bulunamadı</td></tr>';return;}}
  tb.innerHTML=rows.map(r=>{{
    const tone=r.sure>=120?TH.bad:r.sure>=60?TH.warn:TH.txt;
    return`<tr>
      <td class="cell-mut">${{esc(r.tarih)}}</td>
      <td>${{esc(r.vardiya)}}</td>
      <td><span class="chip-dot" style="display:inline-block;margin-right:6px;background:${{HC[r.hat]||TH.mut}}"></span>${{esc(r.hat)}}</td>
      <td class="cell-ref">${{esc(r.ref||'—')}}</td>
      <td><span class="badge ${{badgeCls(r.sebep)}}">${{esc(r.sebep)}}</span></td>
      <td class="num" style="color:${{tone}};font-weight:700">${{esc(r.sure)}}</td>
      <td class="cell-clip" title="${{esc(r.aciklama)}}">${{esc(r.aciklama)}}</td>
      <td class="num cell-mut">${{esc(r.op)}}</td></tr>`;
  }}).join('');
}}

// ── başlat ────────────────────────────────────────────────────────────────
const BUILD={{e1:buildE1,e2:buildE2,e3:renderVardiya,e4:renderRef,e5:buildE5,e6:flt}};
const DIRTY=new Set(Object.keys(BUILD));
let ACTIVE='e1';
ensure('e1');
</script>
</body>
</html>"""

with open(OUTPUT_PATH,'w',encoding='utf-8') as f:
    f.write(html)

print(f"\n✓ {OUTPUT_PATH}")
print(f"  Dosya boyutu: {len(html.encode('utf-8'))//1024} KB")
print(f"  Haftalar: {data_json['haftalik_etiket'][0]} → {data_json['haftalik_etiket'][-1]}")
print(f"  Duruş kaydı: {len(data_json['son_duruslar'])}")
