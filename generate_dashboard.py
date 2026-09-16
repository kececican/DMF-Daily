#!/usr/bin/env python3
"""DMF Daily — dashboard/data.json → dashboard/index.html renderer.

Veri ayıklama extract_excel.py içinde; bu dosya yalnız sunum katmanıdır.
Excel olmadan da çalışır — data.json cache'i yeterlidir.
"""

import os
import json

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

# ── HTML ──────────────────────────────────────────────────────────────────────
print("HTML oluşturuluyor...")

# Koyu zemin için seçilmiş özgün hat paleti.
HAT_COLORS = {
    'DMF1':'#2196F3','DMF2':'#4CAF50','DMF3':'#FF9800','DMF4':'#9C27B0',
    'PFW1':'#F44336','PFW2':'#00BCD4','PFW3':'#8BC34A','PFW4':'#FF5722','ITL':'#607D8B'
}
# Light tema için aynı tonların koyulaştırılmış karşılıkları (Material 700/800).
# Turuncu / açık yeşil / camgöbeği beyaz zeminde kontrast sınırında kaldığı için şart.
HAT_COLORS_LIGHT = {
    'DMF1':'#1565C0','DMF2':'#2E7D32','DMF3':'#E65100','DMF4':'#6A1B9A',
    'PFW1':'#C62828','PFW2':'#00838F','PFW3':'#558B2F','PFW4':'#D84315','ITL':'#37474F'
}

data_js        = json.dumps(data_json, ensure_ascii=False, indent=2)
hat_colors_js  = json.dumps(HAT_COLORS)
hat_light_js   = json.dumps(HAT_COLORS_LIGHT)


def _inline(fname, cdn_fallback):
    """vendor/ altındaki kütüphaneyi HTML'e göm; yoksa CDN etiketine düş."""
    path = os.path.join(BASE_DIR, 'vendor', fname)
    try:
        with open(path, encoding='utf-8') as fh:
            body = fh.read().replace('</script>', '<\\/script>')
        return '<script>\n' + body + '\n  </script>'
    except FileNotFoundError:
        return f'<script src="{cdn_fallback}"></script>'


# Chart.js ve datalabels eklentisi HTML'e gömülür — dashboard CDN/internet
# olmadan da (file://, offline, kapalı fabrika ağı) eksiksiz çalışır.
chart_tag = '\n  '.join([
    _inline('chart.umd.min.js',
            'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'),
    _inline('chartjs-plugin-datalabels.min.js',
            'https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js'),
])

html = f"""<!DOCTYPE html>
<html lang="tr" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DMF Daily – Üretim Dashboard</title>
  {chart_tag}
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}

    /* ── Light (varsayılan) ── */
    :root{{
      --bg:#f4f6fa; --sur:#ffffff; --sur2:#eef1f6; --brd:#d8dee9;
      --txt:#1b2333; --mut:#5c6879; --acc:#2563eb; --strong:#0f1623;
      --grid:#e4e9f2; --tip-bg:#ffffff; --lbl:#2b3648; --tbl:#3d4757;
      --ref:#9a6b00; --shadow:0 1px 3px rgba(16,24,40,.07);
    }}
    /* ── Dark ── */
    :root[data-theme="dark"]{{
      --bg:#0f1117; --sur:#1a1d27; --sur2:#242736; --brd:#2e3348;
      --txt:#e2e8f0; --mut:#8892a4; --acc:#3b82f6; --strong:#ffffff;
      --grid:#2e3348; --tip-bg:#1a1d27; --lbl:#cbd5e1; --tbl:#cbd5e1;
      --ref:#f0c040; --shadow:none;
    }}

    body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}

    .hdr{{background:var(--sur);border-bottom:1px solid var(--brd);padding:13px 24px;display:flex;align-items:center;justify-content:space-between;gap:14px;position:sticky;top:0;z-index:200}}
    .hdr h1{{font-size:17px;font-weight:600;color:var(--strong)}}
    .hdr .right{{display:flex;align-items:center;gap:14px}}
    .hdr .upd{{font-size:12px;color:var(--mut)}}
    .thbtn{{background:var(--sur2);border:1px solid var(--brd);color:var(--txt);padding:6px 12px;border-radius:16px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap;transition:border-color .15s}}
    .thbtn:hover{{border-color:var(--acc)}}

    .tabs{{display:flex;background:var(--sur);border-bottom:1px solid var(--brd);padding:0 20px;overflow-x:auto}}
    .tab{{padding:11px 18px;cursor:pointer;border-bottom:2px solid transparent;color:var(--mut);font-weight:500;white-space:nowrap;user-select:none;transition:color .15s}}
    .tab:hover{{color:var(--txt)}}
    .tab.active{{color:var(--acc);border-bottom-color:var(--acc)}}

    .screen{{display:none;padding:22px;max-width:1700px;margin:0 auto}}
    .screen.active{{display:block}}

    /* KPI */
    .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:13px;margin-bottom:22px}}
    .kcard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:15px;box-shadow:var(--shadow)}}
    .khat{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:11px}}
    .krow{{margin-bottom:7px}}
    .klabel{{font-size:11px;color:var(--mut);margin-bottom:1px}}
    .kval{{font-size:20px;font-weight:700;color:var(--strong);line-height:1.1}}
    .ksub{{font-size:11px;color:var(--mut)}}
    .trpbar{{height:5px;background:var(--brd);border-radius:3px;margin-top:5px;overflow:hidden}}
    .trpfill{{height:100%;border-radius:3px}}
    .kmini{{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:9px}}
    .kmini .kval{{font-size:15px}}

    /* SMF card */
    .smf-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:13px;margin-bottom:22px}}
    .smfcard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:15px;border-top:3px solid #FF9800;box-shadow:var(--shadow)}}

    /* Charts */
    .crow{{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}}
    .crow.full{{grid-template-columns:1fr}}
    .crow.three{{grid-template-columns:1fr 1fr 1fr}}
    .ccard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:18px;box-shadow:var(--shadow)}}
    .ctitle{{font-size:11px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;margin-bottom:14px}}
    .cwrap{{position:relative;height:270px}}

    /* Hat filter */
    .hfilt{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px;align-items:center}}
    .hfilt span{{font-size:12px;color:var(--mut)}}
    .hbtn{{padding:4px 12px;border-radius:16px;border:1px solid var(--brd);background:transparent;color:var(--mut);cursor:pointer;font-size:12px;font-weight:600;transition:all .15s}}
    .hbtn.on{{color:#fff;border-color:transparent}}

    /* Hat select for ref/vardiya */
    .hat-sel{{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center}}
    .hat-sel span{{font-size:12px;color:var(--mut)}}
    .hat-sel select{{background:var(--sur2);border:1px solid var(--brd);color:var(--txt);padding:6px 10px;border-radius:6px;font-size:13px}}

    /* Table */
    .twrap{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;overflow:auto;box-shadow:var(--shadow)}}
    .fbar{{display:flex;gap:9px;padding:13px 15px;border-bottom:1px solid var(--brd);flex-wrap:wrap;align-items:center}}
    .fbar select,.fbar input{{background:var(--sur2);border:1px solid var(--brd);color:var(--txt);padding:6px 10px;border-radius:6px;font-size:13px}}
    table{{width:100%;border-collapse:collapse;min-width:680px}}
    th{{background:var(--sur2);padding:9px 13px;text-align:left;font-size:11px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--brd);white-space:nowrap}}
    td{{padding:8px 13px;border-bottom:1px solid var(--brd);font-size:13px}}
    tr:last-child td{{border-bottom:none}}
    tr:hover td{{background:var(--sur2)}}
    .badge{{display:inline-block;padding:2px 8px;border-radius:11px;font-size:11px;font-weight:600;white-space:nowrap}}
    /* Light rozetler */
    .ba{{background:#fee2e2;color:#991b1b;border:1px solid #fecaca}}
    .bk{{background:#fef3c7;color:#92400e;border:1px solid #fde68a}}
    .bp{{background:#dbeafe;color:#1e40af;border:1px solid #bfdbfe}}
    .bs{{background:#dcfce7;color:#166534;border:1px solid #bbf7d0}}
    .bm{{background:#ede9fe;color:#5b21b6;border:1px solid #ddd6fe}}
    .bl{{background:#ccfbf1;color:#115e59;border:1px solid #99f6e4}}
    .bd{{background:#e5e7eb;color:#374151;border:1px solid #d1d5db}}
    /* Dark rozetler */
    :root[data-theme="dark"] .ba{{background:#7f1d1d33;color:#fca5a5;border-color:#7f1d1d}}
    :root[data-theme="dark"] .bk{{background:#78350f33;color:#fcd34d;border-color:#78350f}}
    :root[data-theme="dark"] .bp{{background:#1e3a5f33;color:#93c5fd;border-color:#1e3a5f}}
    :root[data-theme="dark"] .bs{{background:#1a3a1a33;color:#86efac;border-color:#1a3a1a}}
    :root[data-theme="dark"] .bm{{background:#2e1a4a33;color:#c4b5fd;border-color:#2e1a4a}}
    :root[data-theme="dark"] .bl{{background:#1a2e2e33;color:#6ee7b7;border-color:#1a2e2e}}
    :root[data-theme="dark"] .bd{{background:#2a2a2a33;color:#d1d5db;border-color:#2a2a2a}}

    @media(max-width:900px){{.crow,.crow.three{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>

<div class="hdr">
  <h1>⚙ DMF Daily — Üretim Takip Dashboard</h1>
  <div class="right">
    <span class="upd" id="upd-date"></span>
    <button class="thbtn" id="th-btn" onclick="toggleTheme()">🌙 Dark</button>
  </div>
</div>

<div class="tabs">
  <div class="tab active"  onclick="T('e1',this)">📊 KPI Özet</div>
  <div class="tab"         onclick="T('e2',this)">📈 Üretim Trendi</div>
  <div class="tab"         onclick="T('e3',this)">🔀 Vardiya Analizi</div>
  <div class="tab"         onclick="T('e4',this)">🏷 Referans Dağılımı</div>
  <div class="tab"         onclick="T('e5',this)">⏱ Duruş Analizi</div>
  <div class="tab"         onclick="T('e6',this)">📋 Duruş Detay</div>
</div>

<!-- E1: KPI -->
<div id="screen-e1" class="screen active">
  <div class="kpi-grid" id="kpi-grid"></div>

  <div style="font-size:12px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px">SMF-DOOSAN (Aralık 2025 – Şubat 2026)</div>
  <div class="smf-row" id="smf-cards"></div>

  <div class="crow">
    <div class="ccard"><div class="ctitle">Aylık Üretim — DMF Hatları</div><div class="cwrap"><canvas id="ch-m-dmf"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Aylık Üretim — PFW &amp; ITL</div><div class="cwrap"><canvas id="ch-m-pfw"></canvas></div></div>
  </div>
  <div class="crow full">
    <div class="ccard"><div class="ctitle">SMF-DOOSAN Günlük Üretim</div><div class="cwrap" style="height:220px"><canvas id="ch-smf"></canvas></div></div>
  </div>
</div>

<!-- E2: Trend -->
<div id="screen-e2" class="screen">
  <div class="hfilt"><span>Hat:</span><div id="hf-btns"></div></div>
  <div class="crow full"><div class="ccard"><div class="ctitle">Haftalık Üretim Trendi (Adet)</div><div class="cwrap" style="height:310px"><canvas id="ch-tw-prod"></canvas></div></div></div>
  <div class="crow full"><div class="ccard"><div class="ctitle">Haftalık TRP (%) — Vardiya Başına Ortalama</div><div class="cwrap" style="height:280px"><canvas id="ch-tw-trp"></canvas></div></div></div>
</div>

<!-- E3: Vardiya -->
<div id="screen-e3" class="screen">
  <div class="hat-sel"><span>Hat:</span><select id="vrd-hat-sel" onchange="renderVardiya()"></select></div>
  <div class="crow">
    <div class="ccard"><div class="ctitle">Aylık Ortalama Vardiya Üretimi (Adet/Shift)</div><div class="cwrap" style="height:300px"><canvas id="ch-vrd-aylik"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Vardiya Toplam Dağılımı (Tüm Dönem)</div><div class="cwrap" style="height:300px"><canvas id="ch-vrd-pie"></canvas></div></div>
  </div>
  <div class="crow full">
    <div class="ccard"><div class="ctitle">Haftalık TRP — Vardiya Bazında Karşılaştırma</div><div class="cwrap" style="height:280px"><canvas id="ch-vrd-trp"></canvas></div></div>
  </div>
</div>

<!-- E4: Referans -->
<div id="screen-e4" class="screen">
  <div class="hat-sel"><span>Hat:</span><select id="ref-hat-sel" onchange="renderRef()"></select></div>
  <div class="crow">
    <div class="ccard"><div class="ctitle">Referans Bazında Toplam Üretim (Adet)</div><div class="cwrap" style="height:310px"><canvas id="ch-ref-bar"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Referans Üretim Payı (%)</div><div class="cwrap" style="height:310px"><canvas id="ch-ref-pie"></canvas></div></div>
  </div>
  <div class="crow full">
    <div class="ccard"><div class="ctitle">Referans Bazında Ortalama TRP (%) — en az 3 vardiya</div><div class="cwrap" style="height:360px"><canvas id="ch-ref-trp"></canvas></div></div>
  </div>
</div>

<!-- E5: Duruş -->
<div id="screen-e5" class="screen">
  <div class="crow">
    <div class="ccard"><div class="ctitle">Duruş Sebebi Pareto (dk)</div><div class="cwrap" style="height:390px"><canvas id="ch-pc"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Hat Bazında Toplam Duruş (dk)</div><div class="cwrap" style="height:390px"><canvas id="ch-ph"></canvas></div></div>
  </div>
  <div class="crow full">
    <div class="ccard"><div class="ctitle">Aylık Duruş — Sebep Dağılımı (dk)</div><div class="cwrap" style="height:290px"><canvas id="ch-durus-ay"></canvas></div></div>
  </div>
</div>

<!-- E6: Detay -->
<div id="screen-e6" class="screen">
  <div class="twrap">
    <div class="fbar">
      <select id="f-hat"     onchange="flt()"><option value="">Tüm Hatlar</option></select>
      <select id="f-sebep"   onchange="flt()"><option value="">Tüm Sebepler</option></select>
      <select id="f-vardiya" onchange="flt()"><option value="">Vardiya</option><option>A</option><option>B</option><option>C</option></select>
      <input  id="f-text" type="text" placeholder="Açıklama ara…" oninput="fltDebounced()" style="flex:1;min-width:160px">
      <span id="fcount" style="font-size:12px;color:var(--mut);white-space:nowrap"></span>
    </div>
    <table>
      <thead><tr><th>Tarih</th><th>Vrd.</th><th>Hat</th><th>Referans</th><th>Sebep</th><th>Süre(dk)</th><th>Açıklama</th><th>OP</th></tr></thead>
      <tbody id="dur-tbody"></tbody>
    </table>
  </div>
</div>

<script>
const D        = {data_js};
const HC_DARK  = {hat_colors_js};
const HC_LIGHT = {hat_light_js};
let   HC       = HC_LIGHT;

// ── utils ──────────────────────────────────────────────────────────────────
const h2r=(h,a=1)=>{{const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return`rgba(${{r}},${{g}},${{b}},${{a}})`;}};
const fmt=n=>new Intl.NumberFormat('tr-TR').format(Math.round(n));
const badgeCls=s=>/Arıza|Robot/.test(s)?'ba':/Kalite/.test(s)?'bk':/Parça|Sipariş|Besleme/.test(s)?'bp':/Set|Kesici/.test(s)?'bs':/Metod|Arge/.test(s)?'bm':/Planlı/.test(s)?'bl':'bd';

// ── tema ───────────────────────────────────────────────────────────────────
// Grafik renkleri CSS değişkenlerinden okunur; tek renk kaynağı :root bloğudur.
const CSSV=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let TH={{}};
function readTheme(){{
  const dark=document.documentElement.dataset.theme==='dark';
  HC = dark?HC_DARK:HC_LIGHT;
  TH = {{
    dark, txt:CSSV('--txt'), mut:CSSV('--mut'), grid:CSSV('--grid'),
    sur:CSSV('--sur'), brd:CSSV('--brd'), tip:CSSV('--tip-bg'),
    lbl:CSSV('--lbl'), strong:CSSV('--strong'), ref:CSSV('--ref'), tbl:CSSV('--tbl'),
  }};
  if(window.Chart){{Chart.defaults.color=TH.mut;Chart.defaults.borderColor=TH.grid;}}
}}
function applyTheme(t){{
  document.documentElement.dataset.theme=t;
  document.getElementById('th-btn').textContent = t==='dark' ? '☀ Light' : '🌙 Dark';
  readTheme();
}}
function toggleTheme(){{
  const next=document.documentElement.dataset.theme==='dark'?'light':'dark';
  applyTheme(next);
  try{{localStorage.setItem('dmf-theme',next);}}catch(e){{}}
  // Renkler options'a gömülü olduğu için tüm ekranlar kirletilir; yalnız
  // görünür olan hemen kurulur, gizli olanlar sekmesi açılınca kurulur.
  Object.keys(BUILD).forEach(k=>DIRTY.add(k));
  ensure(ACTIVE);
}}
// Varsayılan light; kullanıcı bir kez seçerse tercihi hatırlanır.
let _saved=null; try{{_saved=localStorage.getItem('dmf-theme');}}catch(e){{}}
applyTheme(_saved==='dark'?'dark':'light');

// ── veri etiketleri ────────────────────────────────────────────────────────
// Etiketler kalıcı (hover gerekmez). display:'auto' yalnız üst üste binenleri
// gizler — 9 hat x 20 hafta gibi yoğun grafiklerde okunabilirliği korur.
Chart.register(ChartDataLabels);
Chart.defaults.set('plugins.datalabels',{{
  color:()=>TH.lbl,
  font:{{size:9,weight:'700'}},
  formatter:v=>(v===null||v===undefined||v===0)?'':fmt(v),
}});
const DL_V     = {{anchor:'end',align:'end',offset:1,display:'auto',clamp:true}};
const DL_H     = {{anchor:'end',align:'right',offset:3,display:'auto',clamp:true}};
const DL_LINE  = {{anchor:'end',align:'top',offset:4,display:'auto',clamp:true}};
// Dolgu içine yazılanlar her iki temada da okunsun diye beyaz + koyu kontur.
const DL_IN    = {{anchor:'center',align:'center',display:'auto',color:'#fff',
                 textStrokeColor:'rgba(0,0,0,.55)',textStrokeWidth:3,font:{{size:10,weight:'700'}}}};
const pctFmt=(v,c)=>{{const t=c.dataset.data.reduce((a,b)=>a+(b||0),0);return(!v||!t)?'':(v/t*100).toFixed(1)+'%';}};
const trpFmt=v=>(v===null||v===undefined||v===0)?'':(+v).toFixed(1)+'%';

// ── ortak grafik ayarları ──────────────────────────────────────────────────
const baseScales=()=>({{
  x:{{grid:{{color:TH.grid}},ticks:{{color:TH.mut,maxTicksLimit:14,maxRotation:45}}}},
  y:{{grid:{{color:TH.grid}},ticks:{{color:TH.mut}}}}
}});
const baseLegend=()=>({{labels:{{color:TH.txt,font:{{size:11}}}}}});
const baseTip=()=>({{backgroundColor:TH.tip,borderColor:TH.brd,borderWidth:1,titleColor:TH.strong,bodyColor:TH.txt}});

// ── grafik kaydı & sekme bazlı tembel kurulum ──────────────────────────────
// Chart.js gizli (display:none) canvas'ta 0 boyut hesapladığı için grafikler
// sekmesi ilk kez görünür olduğunda kurulur. Tema değişimi hepsini kirletir.
const CHARTS={{}};
function mk(id,cfg){{
  if(CHARTS[id]){{CHARTS[id].destroy();delete CHARTS[id];}}
  CHARTS[id]=new Chart(document.getElementById(id),cfg);
  return CHARTS[id];
}}

function T(id,el){{
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('screen-'+id).classList.add('active');
  el.classList.add('active');
  ACTIVE=id;
  ensure(id);
}}
function ensure(id){{ if(DIRTY.has(id)){{ BUILD[id](); DIRTY.delete(id); }} }}

// ── E1: KPI ───────────────────────────────────────────────────────────────
document.getElementById('upd-date').textContent='Son güncelleme: '+D.meta.guncelleme;

function buildE1(){{
  const g=document.getElementById('kpi-grid');
  g.innerHTML='';
  D.meta.hatlar.forEach(hat=>{{
    const k=D.kpi[hat],c=HC[hat];
    const tp=k.ort_trp?(k.ort_trp*100):null;
    const ts=tp!==null?tp.toFixed(1)+'%':'—';
    const tc=tp===null?TH.mut:tp>=75?(TH.dark?'#4ade80':'#15803d'):tp>=55?(TH.dark?'#facc15':'#a16207'):(TH.dark?'#f87171':'#b91c1c');
    g.innerHTML+=`<div class="kcard" style="border-top:3px solid ${{c}}">
      <div class="khat" style="color:${{c}}">${{hat}}</div>
      <div class="krow"><div class="klabel">Toplam Üretim</div><div class="kval">${{fmt(k.toplam)}}</div><div class="ksub">Haziran: ${{fmt(k.son_ay)}}</div></div>
      <div class="krow" style="margin-top:9px"><div class="klabel">TRP (son 4 hafta)</div><div class="kval" style="color:${{tc}};font-size:23px">${{ts}}</div>
        <div class="trpbar"><div class="trpfill" style="width:${{Math.min(tp||0,100)}}%;background:${{tc}}"></div></div></div>
      <div class="kmini">
        <div><div class="klabel">Rework</div><div class="kval" style="color:${{TH.dark?'#fde047':'#a16207'}}">${{fmt(k.rework)}}</div></div>
        <div><div class="klabel">İskarta</div><div class="kval" style="color:${{TH.dark?'#f87171':'#b91c1c'}}">${{fmt(k.iskarta)}}</div></div>
      </div></div>`;
  }});

  const sk=D.smf_kpi;
  document.getElementById('smf-cards').innerHTML=`
    <div class="smfcard"><div class="klabel">JX22 Toplam</div><div class="kval" style="font-size:22px">${{fmt(sk.jx22_toplam)}}</div></div>
    <div class="smfcard"><div class="klabel">EB2 Toplam</div><div class="kval" style="font-size:22px">${{fmt(sk.eb2_toplam)}}</div></div>
    <div class="smfcard"><div class="klabel">Genel Toplam</div><div class="kval" style="font-size:22px;color:${{TH.dark?'#4ade80':'#15803d'}}">${{fmt(sk.toplam)}}</div></div>
    <div class="smfcard"><div class="klabel">NOK Adet</div><div class="kval" style="font-size:22px;color:${{TH.dark?'#f87171':'#b91c1c'}}">${{fmt(sk.nok)}}</div></div>
    <div class="smfcard"><div class="klabel">Aktif Gün</div><div class="kval" style="font-size:22px">${{sk.aktif_gun}}</div><div class="ksub">Ara.2025–Şub.2026</div></div>`;

  const mBar=(id,hats)=>mk(id,{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:hats.map(h=>({{label:h,data:D.aylik_uretim[h],backgroundColor:h2r(HC[h],.75),borderColor:HC[h],borderWidth:1,borderRadius:4}}))}},
    options:{{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:18}}}},
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_V,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
  mBar('ch-m-dmf',['DMF1','DMF2','DMF3','DMF4']);
  mBar('ch-m-pfw',['PFW1','PFW2','PFW3','PFW4','ITL']);

  mk('ch-smf',{{type:'bar',
    data:{{labels:D.smf_dates,datasets:[
      {{label:'JX22',data:D.smf_jx22,backgroundColor:h2r('#FF9800',.8),borderRadius:3,stack:'s'}},
      {{label:'EB2', data:D.smf_eb2, backgroundColor:h2r('#2196F3',.8),borderRadius:3,stack:'s'}},
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_IN,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:{{...baseScales().x,stacked:true}},y:{{...baseScales().y,stacked:true,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
}}

// ── E2: Trend ──────────────────────────────────────────────────────────────
let actH=new Set(['DMF1','DMF2','DMF3','DMF4']);
const tDS=ser=>[...actH].map(h=>({{label:h,data:ser[h]||[],borderColor:HC[h],backgroundColor:h2r(HC[h],.08),borderWidth:2.5,pointRadius:3,tension:.3,fill:false}}));
const tOpts=(yFn,dlFmt)=>({{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
  layout:{{padding:{{top:16,right:22,left:8}}}},
  plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_LINE,font:{{size:8,weight:'700'}},formatter:dlFmt}}}},
  scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:yFn}}}}}}}});

function buildE2(){{
  const hfDiv=document.getElementById('hf-btns');
  hfDiv.innerHTML='';
  D.meta.hatlar.forEach(h=>{{
    const b=document.createElement('button');
    b.className='hbtn'+(actH.has(h)?' on':'');
    if(actH.has(h))b.style.backgroundColor=HC[h];
    b.textContent=h;
    b.onclick=()=>{{actH.has(h)?(actH.delete(h),b.classList.remove('on'),b.style.backgroundColor=''):(actH.add(h),b.classList.add('on'),b.style.backgroundColor=HC[h]);updTrend();}};
    hfDiv.appendChild(b);
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
  const vColors=TH.dark?{{A:'#4ade80',B:'#60a5fa',C:'#f472b6'}}:{{A:'#15803d',B:'#1d4ed8',C:'#be185d'}};
  const vSet=k=>['A','B','C'].map(v=>({{label:'Vardiya '+v,data:vc[v],backgroundColor:h2r(vColors[v],.75),borderColor:vColors[v],borderWidth:1,borderRadius:4}}));

  mk('ch-vrd-aylik',{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:vSet()}},
    options:{{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:18}}}},
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_V,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});

  const allTots={{A:0,B:0,C:0}};
  ['A','B','C'].forEach(v=>(vc[v]||[]).forEach(x=>allTots[v]+=x));
  mk('ch-vrd-pie',{{type:'doughnut',
    data:{{labels:['Vardiya A','Vardiya B','Vardiya C'],
      datasets:[{{data:[allTots.A,allTots.B,allTots.C],backgroundColor:[h2r(vColors.A,.8),h2r(vColors.B,.8),h2r(vColors.C,.8)],borderColor:[vColors.A,vColors.B,vColors.C],borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:baseLegend(),tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)+' adet'}}}},
        datalabels:{{...DL_IN,formatter:pctFmt}}}}}}
  }});

  mk('ch-vrd-trp',{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:vSet()}},
    options:{{responsive:true,maintainAspectRatio:false,layout:{{padding:{{top:18}}}},
      plugins:{{legend:baseLegend(),tooltip:baseTip(),datalabels:{{...DL_V,font:{{size:8,weight:'700'}}}}}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}}}}}}
  }});
}}

// ── E4: Referans ─────────────────────────────────────────────────────────────
const refSel=document.getElementById('ref-hat-sel');
D.meta.hatlar.forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;refSel.appendChild(o);}});
const refColorsD=['#2196F3','#4CAF50','#FF9800','#9C27B0','#F44336','#00BCD4','#8BC34A','#FF5722'];
const refColorsL=['#1565C0','#2E7D32','#E65100','#6A1B9A','#C62828','#00838F','#558B2F','#D84315'];
function renderRef(){{
  const hat=refSel.value||D.meta.hatlar[0];
  const r=D.ref_top[hat];
  const rc=TH.dark?refColorsD:refColorsL;

  mk('ch-ref-bar',{{type:'bar',
    data:{{labels:r.labels,datasets:[{{label:'Üretim (adet)',data:r.data,backgroundColor:rc.map(c=>h2r(c,.8)),borderColor:rc,borderWidth:1,borderRadius:4}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:48}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:{{grid:{{color:'transparent'}},ticks:{{color:TH.txt,autoSkip:false,font:{{size:10}}}}}}}}}}
  }});

  mk('ch-ref-pie',{{type:'doughnut',
    data:{{labels:r.labels,datasets:[{{data:r.data,backgroundColor:rc.map(c=>h2r(c,.8)),borderColor:rc,borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:baseLegend(),tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)}}}},
        datalabels:{{...DL_IN,formatter:pctFmt}}}}}}
  }});

  const rt=D.ref_trp_avg[hat];
  if(rt&&rt.labels.length){{
    const barColors=rt.trp.map(v=>v>=70?(TH.dark?'#4ade80':'#15803d'):v>=55?(TH.dark?'#60a5fa':'#1d4ed8'):(TH.dark?'#f87171':'#b91c1c'));
    mk('ch-ref-trp',{{type:'bar',
      data:{{labels:rt.labels,datasets:[{{label:'Ort. TRP (%)',data:rt.trp,backgroundColor:barColors,borderRadius:4}}]}},
      options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:44}}}},
        plugins:{{legend:{{display:false}},
          tooltip:{{...baseTip(),callbacks:{{label:ctx=>ctx.parsed.x.toFixed(1)+'%  ('+rt.shifts[ctx.dataIndex]+' vardiya)'}}}},
          datalabels:{{...DL_H,formatter:trpFmt}}}},
        scales:{{
          x:{{...baseScales().x,min:0,max:100,ticks:{{color:TH.mut,callback:v=>v+'%'}}}},
          y:{{grid:{{color:'transparent'}},ticks:{{color:TH.txt,autoSkip:false,font:{{size:10}}}}}}
        }}
      }}
    }});
  }} else {{
    if(CHARTS['ch-ref-trp']){{CHARTS['ch-ref-trp'].destroy();delete CHARTS['ch-ref-trp'];}}
    const cv=document.getElementById('ch-ref-trp'),ctx=cv.getContext('2d');
    cv.width=cv.clientWidth;cv.height=cv.clientHeight;
    ctx.clearRect(0,0,cv.width,cv.height);
    ctx.fillStyle=TH.mut;ctx.font='14px sans-serif';ctx.textAlign='center';
    ctx.fillText('Bu hat için referans bazlı TRP verisi yok (PFW/ITL)',cv.width/2,cv.height/2);
  }}
}}

// ── E5: Duruş ─────────────────────────────────────────────────────────────
function buildE5(){{
  const L=TH.dark?55:38;   // light temada dolgular biraz koyu olmalı
  const pColors=D.pareto_cat_etiket.map((_,i)=>`hsl(${{i*32%360}},60%,${{L}}%)`);
  mk('ch-pc',{{type:'bar',
    data:{{labels:D.pareto_cat_etiket,datasets:[{{label:'Duruş (dk)',data:D.pareto_cat_deger,backgroundColor:pColors,borderRadius:4}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:52}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:{{grid:{{color:'transparent'}},ticks:{{color:TH.txt,autoSkip:false,font:{{size:10}}}}}}}}}}
  }});

  mk('ch-ph',{{type:'bar',
    data:{{labels:D.pareto_hat_etiket,datasets:[{{label:'Duruş (dk)',data:D.pareto_hat_deger,backgroundColor:D.pareto_hat_etiket.map(h=>h2r(HC[h]||'#888',.8)),borderColor:D.pareto_hat_etiket.map(h=>HC[h]||'#888'),borderWidth:1,borderRadius:4}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,layout:{{padding:{{right:52}}}},
      plugins:{{legend:{{display:false}},tooltip:baseTip(),datalabels:DL_H}},
      scales:{{x:{{...baseScales().x,ticks:{{color:TH.mut,callback:v=>fmt(v)}}}},y:{{grid:{{color:'transparent'}},ticks:{{color:TH.txt,autoSkip:false,font:{{size:10}}}}}}}}}}
  }});

  const sebepler=[...new Set(Object.values(D.durus_aylik).flatMap(o=>Object.keys(o)))];
  mk('ch-durus-ay',{{type:'bar',
    data:{{labels:D.durus_aylar,datasets:sebepler.map((s,i)=>({{
      label:s,data:D.durus_aylar.map(ay=>(D.durus_aylik[ay]||{{}})[s]||0),
      backgroundColor:`hsl(${{i*32%360}},60%,${{L}}%)`,stack:'d',borderRadius:2}}))}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{...baseLegend(),position:'bottom'}},tooltip:baseTip(),datalabels:{{...DL_IN,font:{{size:8,weight:'700'}}}}}},
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
  const h=hSel.value,s=sSel.value,v=document.getElementById('f-vardiya').value,t=document.getElementById('f-text').value.toLowerCase();
  const rows=D.son_duruslar.filter(r=>(!h||r.hat===h)&&(!s||r.sebep===s)&&(!v||r.vardiya===v)&&(!t||r.aciklama.toLowerCase().includes(t)));
  document.getElementById('fcount').textContent=rows.length+' kayıt';
  const tb=document.getElementById('dur-tbody');
  if(!rows.length){{tb.innerHTML='<tr><td colspan="8" style="text-align:center;color:var(--mut);padding:28px">Kayıt bulunamadı</td></tr>';return;}}
  tb.innerHTML=rows.map(r=>{{
    const hc=HC[r.hat]||TH.mut,sc=r.sure>=120?(TH.dark?'#f87171':'#b91c1c'):r.sure>=60?(TH.dark?'#facc15':'#a16207'):TH.txt;
    return`<tr><td>${{r.tarih}}</td><td style="font-weight:600">${{r.vardiya}}</td><td style="color:${{hc}};font-weight:600">${{r.hat}}</td><td style="color:var(--ref);font-weight:600;font-size:12px">${{r.ref||'—'}}</td><td><span class="badge ${{badgeCls(r.sebep)}}">${{r.sebep}}</span></td><td style="color:${{sc}};font-weight:700">${{r.sure}}</td><td style="color:var(--tbl);max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{r.aciklama}}</td><td style="color:var(--mut)">${{r.op}}</td></tr>`;
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
