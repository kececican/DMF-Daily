#!/usr/bin/env python3
"""DMF Daily Dashboard Generator — Excel → HTML"""

import openpyxl
import json
from datetime import datetime
from collections import defaultdict

EXCEL_PATH = '/root/.claude/uploads/4578e74e-02a1-5b7f-8de5-d3e4492a6ee8/5ec281bc-Copy_of_DMF_Daily_Followup_New_Version_2026.xlsx'
OUTPUT_PATH = '/home/user/DMF-Daily/dashboard/index.html'

print("Excel yükleniyor...")
wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

# ─── Cycle Times (saniye) ────────────────────────────────────────────────────
hat_default_ct = {
    'DMF1': 47, 'DMF2': 49, 'DMF3': 46, 'DMF4': 47,
    'PFW1': 50, 'PFW2': 50, 'PFW3': 50, 'PFW4': 50,
    'ITL': 56
}
# Teorik max per shift = 480 * 60 / CT
teorik_max_shift = {hat: 480 * 60 / ct for hat, ct in hat_default_ct.items()}

# ─── Helpers ─────────────────────────────────────────────────────────────────
def safe_float(v):
    try:
        return float(v) if v is not None and isinstance(v, (int, float)) else 0.0
    except:
        return 0.0

def get_week_label(date_str):
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    y, w, _ = dt.isocalendar()
    return f'{y}-H{w:02d}'

# ─── DMF Production + TRP ────────────────────────────────────────────────────
print("DMF hatları işleniyor...")

daily_prod = {}   # {hat: {date: {prod, durus, rework, iskarta}}}
trp_shifts = {}   # {hat: [(date, vardiya, vardiya_toplam, teorik_max)]}

DMF_DURUS_COLS = [
    (7, 'Çay/Yemek'), (8, 'Temizlik'), (9, 'Metod/Proje'),
    (10, 'Parça Yok'), (11, 'SetUp'), (12, 'Tuzak Parça'),
    (13, 'Kalite Prob.'), (14, 'Arıza')
]

for hat in ['DMF1', 'DMF2', 'DMF3', 'DMF4']:
    ws = wb[hat]
    daily_prod[hat] = {}
    trp_shifts[hat] = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if not (row[0] and isinstance(row[0], datetime)):
            continue
        ds = row[0].strftime('%Y-%m-%d')
        saat = safe_float(row[1])
        vardiya = row[2] or ''

        if ds not in daily_prod[hat]:
            daily_prod[hat][ds] = {'prod': 0, 'durus': defaultdict(float), 'rework': 0, 'iskarta': 0}
        d = daily_prod[hat][ds]

        prod = safe_float(row[4])
        if prod > 0:
            d['prod'] += prod

        for ci, cn in DMF_DURUS_COLS:
            if len(row) > ci:
                d['durus'][cn] += safe_float(row[ci])

        if len(row) > 18: d['rework']  += safe_float(row[18])
        if len(row) > 20: d['iskarta'] += safe_float(row[20])

        # TRP: from Vardiya Toplam (col 5) - only in Saat==1 row
        if saat == 1.0 and len(row) > 5:
            vt = safe_float(row[5])
            if vt > 0:
                trp_shifts[hat].append({
                    'date': ds, 'vardiya': vardiya,
                    'vt': vt, 'teorik': teorik_max_shift[hat]
                })

# ─── PFW Production + TRP ────────────────────────────────────────────────────
print("PFW hatları işleniyor...")

PFW_DURUS_COLS = [
    (13, 'Çay/Yemek'), (14, 'Temizlik'), (15, 'Kor.Bakım'), (16, 'Metod/Proje'),
    (17, 'Sipariş Yok'), (18, 'Parça Yok'), (19, 'SetUp'), (20, 'Kesici Değ.'),
    (21, 'Kalite Prob.'), (22, 'Arıza')
]

for hat in ['PFW1', 'PFW2', 'PFW3', 'PFW4']:
    ws = wb[hat]
    daily_prod[hat] = {}
    trp_shifts[hat] = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if not (row[0] and isinstance(row[0], datetime)):
            continue
        ds = row[0].strftime('%Y-%m-%d')
        saat = safe_float(row[1])
        vardiya = row[3] or ''  # PFW: col 3

        if ds not in daily_prod[hat]:
            daily_prod[hat][ds] = {'prod': 0, 'durus': defaultdict(float), 'rework': 0, 'iskarta': 0}
        d = daily_prod[hat][ds]

        if len(row) > 10:
            prod = safe_float(row[10])
            if prod > 0:
                d['prod'] += prod

        for ci, cn in PFW_DURUS_COLS:
            if len(row) > ci:
                d['durus'][cn] += safe_float(row[ci])

        # TRP from Vardiya Toplam (col 11)
        if saat == 1.0 and len(row) > 11:
            vt = safe_float(row[11])
            if vt > 0:
                trp_shifts[hat].append({
                    'date': ds, 'vardiya': vardiya,
                    'vt': vt, 'teorik': teorik_max_shift[hat]
                })

# ─── ITL Production + TRP ────────────────────────────────────────────────────
print("ITL hattı işleniyor...")

ITL_DURUS_COLS = [
    (13, 'Çay/Yemek'), (14, 'Temizlik'), (15, 'Kor.Bakım'), (16, 'Metod/Proje'),
    (17, 'Sipariş Yok'), (18, 'Parça Yok'), (19, 'Hat Besleme'),
    (20, 'Kalite Prob.'), (21, 'Arıza')
]

ws = wb['ITL']
daily_prod['ITL'] = {}
trp_shifts['ITL'] = []
for row in ws.iter_rows(min_row=4, values_only=True):
    if not (row[0] and isinstance(row[0], datetime)):
        continue
    ds = row[0].strftime('%Y-%m-%d')
    vardiya = row[2] or ''

    if ds not in daily_prod['ITL']:
        daily_prod['ITL'][ds] = {'prod': 0, 'durus': defaultdict(float), 'rework': 0, 'iskarta': 0}
    d = daily_prod['ITL'][ds]

    if len(row) > 10:
        prod = safe_float(row[10])
        if prod > 0:
            d['prod'] += prod

    for ci, cn in ITL_DURUS_COLS:
        if len(row) > ci:
            d['durus'][cn] += safe_float(row[ci])

    # ITL Vardiya Toplam (col 11)
    if len(row) > 11:
        vt = safe_float(row[11])
        if vt > 0:
            trp_shifts['ITL'].append({
                'date': ds, 'vardiya': vardiya,
                'vt': vt, 'teorik': teorik_max_shift['ITL']
            })

# ─── Duruş Detailed Records ──────────────────────────────────────────────────
print("Duruş kayıtları işleniyor...")

ws_durus = wb['Duruş Süre&Sebep']
durus_kayitlar = []
for row in ws_durus.iter_rows(min_row=2, values_only=True):
    if not (row[0] and isinstance(row[0], datetime)):
        continue
    sure = safe_float(row[4])
    if sure <= 0:
        continue
    durus_kayitlar.append({
        'tarih': row[0].strftime('%Y-%m-%d'),
        'vardiya': str(row[1]) if row[1] else '',
        'sebep': str(row[2]) if row[2] else 'Bilinmiyor',
        'hat': str(row[3]) if row[3] else '',
        'sure': round(sure, 1),
        'aciklama': str(row[5])[:80] if row[5] else '',
        'op': str(row[6]) if row[6] else '',
    })

durus_kayitlar.sort(key=lambda x: x['tarih'], reverse=True)

# ─── Weekly Aggregates ────────────────────────────────────────────────────────
print("Haftalık özetler hesaplanıyor...")

ALL_HATS = ['DMF1', 'DMF2', 'DMF3', 'DMF4', 'PFW1', 'PFW2', 'PFW3', 'PFW4', 'ITL']

weekly_prod = {hat: {} for hat in ALL_HATS}
weekly_trp  = {hat: {} for hat in ALL_HATS}

for hat in ALL_HATS:
    for ds, d in daily_prod[hat].items():
        if d['prod'] == 0:
            continue  # skip empty days
        wk = get_week_label(ds)
        if wk not in weekly_prod[hat]:
            weekly_prod[hat][wk] = 0
        weekly_prod[hat][wk] += d['prod']

    # TRP: average per week from actual shifts
    for shift in trp_shifts[hat]:
        wk = get_week_label(shift['date'])
        if wk not in weekly_trp[hat]:
            weekly_trp[hat][wk] = []
        weekly_trp[hat][wk].append(shift['vt'] / shift['teorik'])

# Get all weeks sorted, last 20 where any hat has production
all_weeks = sorted(set(
    wk for hat in ALL_HATS for wk in weekly_prod[hat]
))[-20:]

# ─── Monthly Aggregates ───────────────────────────────────────────────────────
ay_labels = sorted(set(
    ds[:7] for hat in ALL_HATS for ds, d in daily_prod[hat].items() if d['prod'] > 0
))[-8:]

monthly_prod = {}
for hat in ALL_HATS:
    monthly_prod[hat] = []
    for ay in ay_labels:
        toplam = sum(
            d['prod'] for ds, d in daily_prod[hat].items()
            if ds.startswith(ay)
        )
        monthly_prod[hat].append(int(toplam))

# ─── KPI Summary ─────────────────────────────────────────────────────────────
kpi = {}
for hat in ALL_HATS:
    all_prod = sum(d['prod'] for d in daily_prod[hat].values())
    all_durus = sum(sum(d['durus'].values()) for d in daily_prod[hat].values())
    all_rework = sum(d['rework'] for d in daily_prod[hat].values())
    all_iskarta = sum(d['iskarta'] for d in daily_prod[hat].values())

    son_ay_prod = sum(
        d['prod'] for ds, d in daily_prod[hat].items()
        if ds >= '2026-06-01'
    )

    # TRP son 4 hafta ortalaması
    son4_vals = []
    for wk in all_weeks[-4:]:
        wk_trp_list = weekly_trp[hat].get(wk, [])
        if wk_trp_list:
            son4_vals.extend(wk_trp_list)
    avg_trp = round(sum(son4_vals) / len(son4_vals), 3) if son4_vals else None

    kpi[hat] = {
        'toplam_uretim': int(all_prod),
        'son_ay_uretim': int(son_ay_prod),
        'toplam_durus_dk': round(all_durus, 0),
        'toplam_rework': int(all_rework),
        'toplam_iskarta': int(all_iskarta),
        'ort_trp': avg_trp,
    }

# ─── Duruş Pareto ─────────────────────────────────────────────────────────────
durus_by_cat = defaultdict(float)
durus_by_hat = defaultdict(float)
durus_aylik  = defaultdict(lambda: defaultdict(float))

for r in durus_kayitlar:
    durus_by_cat[r['sebep']] += r['sure']
    durus_by_hat[r['hat']]   += r['sure']
    durus_aylik[r['tarih'][:7]][r['sebep']] += r['sure']

durus_pareto     = sorted(durus_by_cat.items(), key=lambda x: -x[1])
durus_hat_pareto = sorted(durus_by_hat.items(), key=lambda x: -x[1])
aylar            = sorted(durus_aylik.keys())

# ─── Build JSON ───────────────────────────────────────────────────────────────
print("JSON verisi hazırlanıyor...")

weekly_prod_series = {}
weekly_trp_series  = {}
for hat in ALL_HATS:
    weekly_prod_series[hat] = [
        int(weekly_prod.get(hat, {}).get(wk, 0)) for wk in all_weeks
    ]
    weekly_trp_series[hat] = [
        round(
            sum(weekly_trp.get(hat, {}).get(wk, [])) /
            max(len(weekly_trp.get(hat, {}).get(wk, [1])), 1) * 100,
            1
        ) if weekly_trp.get(hat, {}).get(wk) else 0
        for wk in all_weeks
    ]

data_json = {
    'meta': {
        'guncelleme': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'hatlar': ALL_HATS,
    },
    'kpi': kpi,
    'haftalik_etiketler': all_weeks,
    'haftalik_uretim': weekly_prod_series,
    'haftalik_trp': weekly_trp_series,
    'aylik_etiketler': ay_labels,
    'aylik_uretim': monthly_prod,
    'durus_pareto_etiket': [x[0] for x in durus_pareto],
    'durus_pareto_deger': [round(x[1], 0) for x in durus_pareto],
    'durus_hat_etiket': [x[0] for x in durus_hat_pareto],
    'durus_hat_deger': [round(x[1], 0) for x in durus_hat_pareto],
    'durus_aylar': aylar,
    'durus_aylik': {
        ay: {s: round(v, 0) for s, v in sebebler.items()}
        for ay, sebebler in durus_aylik.items()
    },
    'son_duruslar': durus_kayitlar[:150],
}

# ─── HTML ─────────────────────────────────────────────────────────────────────
print("HTML dashboard oluşturuluyor...")

HAT_COLORS = {
    'DMF1': '#2196F3', 'DMF2': '#4CAF50', 'DMF3': '#FF9800', 'DMF4': '#9C27B0',
    'PFW1': '#F44336', 'PFW2': '#00BCD4', 'PFW3': '#8BC34A', 'PFW4': '#FF5722',
    'ITL':  '#607D8B'
}

hat_colors_js = json.dumps(HAT_COLORS)
data_js = json.dumps(data_json, ensure_ascii=False, indent=2)

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DMF Daily – Üretim Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #0f1117; --surface: #1a1d27; --surface2: #242736;
      --border: #2e3348; --text: #e2e8f0; --muted: #8892a4; --accent: #3b82f6;
    }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 14px; }}

    .header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; }}
    .header h1 {{ font-size: 18px; font-weight: 600; color: #fff; }}
    .header .meta {{ font-size: 12px; color: var(--muted); }}

    .tabs {{ display: flex; gap: 2px; background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; }}
    .tab {{ padding: 12px 20px; cursor: pointer; border-bottom: 2px solid transparent; color: var(--muted); font-weight: 500; transition: all .15s; white-space: nowrap; user-select: none; }}
    .tab:hover {{ color: var(--text); }}
    .tab.active {{ color: var(--accent); border-bottom-color: var(--accent); }}

    .screen {{ display: none; padding: 24px; max-width: 1600px; margin: 0 auto; }}
    .screen.active {{ display: block; }}

    /* E1 KPI */
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; margin-bottom: 24px; }}
    .kpi-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
    .kpi-hat {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .8px; margin-bottom: 12px; }}
    .kpi-row {{ margin-bottom: 8px; }}
    .kpi-label {{ font-size: 11px; color: var(--muted); margin-bottom: 2px; }}
    .kpi-val {{ font-size: 21px; font-weight: 700; color: #fff; line-height: 1.1; }}
    .kpi-sub {{ font-size: 11px; color: var(--muted); }}
    .trp-bar {{ height: 6px; background: var(--border); border-radius: 3px; margin-top: 6px; overflow: hidden; }}
    .trp-fill {{ height: 100%; border-radius: 3px; }}
    .kpi-mini {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 10px; }}
    .kpi-mini-item .kpi-label {{ font-size: 10px; }}
    .kpi-mini-item .kpi-val {{ font-size: 15px; }}

    /* Charts */
    .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
    .chart-row.full {{ grid-template-columns: 1fr; }}
    .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }}
    .chart-title {{ font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 16px; }}
    .chart-wrap {{ position: relative; height: 280px; }}

    /* Hat filter buttons */
    .hat-filter {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; align-items: center; }}
    .hat-filter label {{ font-size: 12px; color: var(--muted); }}
    .hat-btn {{ padding: 5px 13px; border-radius: 20px; border: 1px solid var(--border); background: transparent; color: var(--muted); cursor: pointer; font-size: 12px; font-weight: 600; transition: all .15s; }}
    .hat-btn.on {{ color: #fff; border-color: transparent; }}

    /* E3 */
    .pareto-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}

    /* E4 Table */
    .table-wrap {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: auto; }}
    .filter-bar {{ display: flex; gap: 10px; padding: 14px 16px; border-bottom: 1px solid var(--border); flex-wrap: wrap; align-items: center; }}
    .filter-bar select, .filter-bar input {{
      background: var(--surface2); border: 1px solid var(--border); color: var(--text);
      padding: 6px 10px; border-radius: 6px; font-size: 13px;
    }}
    table {{ width: 100%; border-collapse: collapse; min-width: 700px; }}
    th {{ background: var(--surface2); padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
    td {{ padding: 9px 14px; border-bottom: 1px solid var(--border); font-size: 13px; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: var(--surface2); }}
    .badge {{ display: inline-block; padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; white-space: nowrap; }}
    .b-ariza   {{ background: #7f1d1d33; color: #fca5a5; border: 1px solid #7f1d1d; }}
    .b-kalite  {{ background: #78350f33; color: #fcd34d; border: 1px solid #78350f; }}
    .b-parca   {{ background: #1e3a5f33; color: #93c5fd; border: 1px solid #1e3a5f; }}
    .b-setup   {{ background: #1a3a1a33; color: #86efac; border: 1px solid #1a3a1a; }}
    .b-metod   {{ background: #2e1a4a33; color: #c4b5fd; border: 1px solid #2e1a4a; }}
    .b-plan    {{ background: #1a2e2e33; color: #6ee7b7; border: 1px solid #1a2e2e; }}
    .b-diger   {{ background: #2a2a2a33; color: #d1d5db; border: 1px solid #2a2a2a; }}

    @media (max-width: 900px) {{
      .chart-row, .pareto-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<div class="header">
  <h1>⚙ DMF Daily — Üretim Takip Dashboard</h1>
  <span class="meta" id="meta-date"></span>
</div>

<div class="tabs">
  <div class="tab active"  onclick="showTab('e1',this)">📊 KPI Özet</div>
  <div class="tab"         onclick="showTab('e2',this)">📈 Üretim Trendi</div>
  <div class="tab"         onclick="showTab('e3',this)">⏱ Duruş Analizi</div>
  <div class="tab"         onclick="showTab('e4',this)">📋 Duruş Detay</div>
</div>

<!-- E1 -->
<div id="screen-e1" class="screen active">
  <div class="kpi-grid" id="kpi-grid"></div>
  <div class="chart-row">
    <div class="chart-card">
      <div class="chart-title">Aylık Üretim — DMF Hatları</div>
      <div class="chart-wrap"><canvas id="ch-monthly-dmf"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Aylık Üretim — PFW & ITL Hatları</div>
      <div class="chart-wrap"><canvas id="ch-monthly-pfw"></canvas></div>
    </div>
  </div>
</div>

<!-- E2 -->
<div id="screen-e2" class="screen">
  <div class="hat-filter">
    <span style="font-size:12px;color:var(--muted)">Hat seç:</span>
    <div id="hat-filter-btns"></div>
  </div>
  <div class="chart-row full">
    <div class="chart-card">
      <div class="chart-title">Haftalık Üretim Trendi (Adet)</div>
      <div class="chart-wrap" style="height:320px"><canvas id="ch-trend-prod"></canvas></div>
    </div>
  </div>
  <div class="chart-row full">
    <div class="chart-card">
      <div class="chart-title">Haftalık TRP (%) — Vardiya Başına Ortalama</div>
      <div class="chart-wrap" style="height:300px"><canvas id="ch-trend-trp"></canvas></div>
    </div>
  </div>
</div>

<!-- E3 -->
<div id="screen-e3" class="screen">
  <div class="pareto-grid">
    <div class="chart-card">
      <div class="chart-title">Duruş Sebebi Pareto (dk)</div>
      <div class="chart-wrap" style="height:360px"><canvas id="ch-pareto-cat"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-title">Hat Bazında Toplam Duruş (dk)</div>
      <div class="chart-wrap" style="height:360px"><canvas id="ch-pareto-hat"></canvas></div>
    </div>
  </div>
  <div class="chart-row full">
    <div class="chart-card">
      <div class="chart-title">Aylık Duruş Dağılımı — Sebep Bazında (dk)</div>
      <div class="chart-wrap" style="height:300px"><canvas id="ch-durus-aylik"></canvas></div>
    </div>
  </div>
</div>

<!-- E4 -->
<div id="screen-e4" class="screen">
  <div class="table-wrap">
    <div class="filter-bar">
      <select id="f-hat"     onchange="filterTable()"><option value="">Tüm Hatlar</option></select>
      <select id="f-sebep"   onchange="filterTable()"><option value="">Tüm Sebepler</option></select>
      <select id="f-vardiya" onchange="filterTable()">
        <option value="">Tüm Vardiyalar</option>
        <option>A</option><option>B</option><option>C</option>
      </select>
      <input type="text" id="f-text" placeholder="Açıklama ara…" oninput="filterTable()" style="flex:1;min-width:180px">
      <span id="row-count" style="font-size:12px;color:var(--muted);white-space:nowrap"></span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Tarih</th><th>Vrd.</th><th>Hat</th>
          <th>Duruş Sebebi</th><th>Süre (dk)</th><th>Açıklama</th><th>OP</th>
        </tr>
      </thead>
      <tbody id="durus-tbody"></tbody>
    </table>
  </div>
</div>

<script>
const DATA = {data_js};
const COLORS = {hat_colors_js};

// ── utils ──────────────────────────────────────────────────────────────────
function hex2rgba(h, a=1) {{
  const r=parseInt(h.slice(1,3),16), g=parseInt(h.slice(3,5),16), b=parseInt(h.slice(5,7),16);
  return `rgba(${{r}},${{g}},${{b}},${{a}})`;
}}
function fmt(n) {{ return new Intl.NumberFormat('tr-TR').format(Math.round(n)); }}

function badgeCls(s) {{
  if (/Arıza|Robot/.test(s))  return 'b-ariza';
  if (/Kalite/.test(s))       return 'b-kalite';
  if (/Parça|Sipariş|Besleme/.test(s)) return 'b-parca';
  if (/Set|Kesici/.test(s))   return 'b-setup';
  if (/Metod|Arge/.test(s))   return 'b-metod';
  if (/Planlı/.test(s))       return 'b-plan';
  return 'b-diger';
}}

// ── tabs ──────────────────────────────────────────────────────────────────
function showTab(id, el) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('screen-' + id).classList.add('active');
  el.classList.add('active');
}}

// ── E1: KPI ───────────────────────────────────────────────────────────────
document.getElementById('meta-date').textContent = 'Son güncelleme: ' + DATA.meta.guncelleme;

const grid = document.getElementById('kpi-grid');
DATA.meta.hatlar.forEach(hat => {{
  const k = DATA.kpi[hat];
  const c = COLORS[hat];
  const trpPct = k.ort_trp ? (k.ort_trp * 100) : null;
  const trpStr = trpPct !== null ? trpPct.toFixed(1) + '%' : '—';
  const trpColor = trpPct === null ? '#888' : trpPct >= 75 ? '#4ade80' : trpPct >= 55 ? '#facc15' : '#f87171';
  grid.innerHTML += `
    <div class="kpi-card" style="border-top:3px solid ${{c}}">
      <div class="kpi-hat" style="color:${{c}}">${{hat}}</div>
      <div class="kpi-row">
        <div class="kpi-label">Toplam Üretim</div>
        <div class="kpi-val">${{fmt(k.toplam_uretim)}}</div>
        <div class="kpi-sub">Haziran: ${{fmt(k.son_ay_uretim)}} adet</div>
      </div>
      <div class="kpi-row" style="margin-top:10px">
        <div class="kpi-label">TRP (son 4 hafta ort.)</div>
        <div class="kpi-val" style="color:${{trpColor}};font-size:24px">${{trpStr}}</div>
        <div class="trp-bar"><div class="trp-fill" style="width:${{Math.min(trpPct||0,100)}}%;background:${{trpColor}}"></div></div>
      </div>
      <div class="kpi-mini">
        <div class="kpi-mini-item">
          <div class="kpi-label">Rework</div>
          <div class="kpi-val" style="color:#fde047">${{fmt(k.toplam_rework)}}</div>
        </div>
        <div class="kpi-mini-item">
          <div class="kpi-label">İskarta</div>
          <div class="kpi-val" style="color:#f87171">${{fmt(k.toplam_iskarta)}}</div>
        </div>
      </div>
    </div>`;
}});

// ── Monthly bar charts ─────────────────────────────────────────────────────
function monthlyChart(canvasId, hats) {{
  new Chart(document.getElementById(canvasId), {{
    type: 'bar',
    data: {{
      labels: DATA.aylik_etiketler,
      datasets: hats.map(h => ({{
        label: h, data: DATA.aylik_uretim[h],
        backgroundColor: hex2rgba(COLORS[h], .75),
        borderColor: COLORS[h], borderWidth: 1, borderRadius: 4,
      }}))
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }} }},
      scales: {{
        x: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4' }} }},
        y: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', callback: v => fmt(v) }} }}
      }}
    }}
  }});
}}
monthlyChart('ch-monthly-dmf', ['DMF1','DMF2','DMF3','DMF4']);
monthlyChart('ch-monthly-pfw', ['PFW1','PFW2','PFW3','PFW4','ITL']);

// ── E2: Trend ──────────────────────────────────────────────────────────────
let activeHats = new Set(['DMF1','DMF2','DMF3','DMF4']);
let chProd, chTrp;

const btnDiv = document.getElementById('hat-filter-btns');
DATA.meta.hatlar.forEach(h => {{
  const b = document.createElement('button');
  b.className = 'hat-btn' + (activeHats.has(h) ? ' on' : '');
  b.style.backgroundColor = activeHats.has(h) ? COLORS[h] : '';
  b.textContent = h;
  b.onclick = () => {{
    if (activeHats.has(h)) {{ activeHats.delete(h); b.classList.remove('on'); b.style.backgroundColor=''; }}
    else {{ activeHats.add(h); b.classList.add('on'); b.style.backgroundColor=COLORS[h]; }}
    updateTrend();
  }};
  btnDiv.appendChild(b);
}});

function trendDS(series) {{
  return [...activeHats].map(h => ({{
    label: h, data: series[h] || [],
    borderColor: COLORS[h], backgroundColor: hex2rgba(COLORS[h], .08),
    borderWidth: 2.5, pointRadius: 3, tension: 0.3, fill: false,
  }}));
}}

const trendOpts = (yFmt) => ({{
  responsive: true, maintainAspectRatio: false,
  interaction: {{ mode: 'index', intersect: false }},
  plugins: {{
    legend: {{ labels: {{ color: '#e2e8f0', font: {{ size: 11 }} }} }},
    tooltip: {{ backgroundColor: '#1a1d27', borderColor: '#2e3348', borderWidth: 1, titleColor: '#e2e8f0', bodyColor: '#e2e8f0' }}
  }},
  scales: {{
    x: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', maxTicksLimit: 12, maxRotation: 45 }} }},
    y: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', callback: yFmt }} }}
  }}
}});

chProd = new Chart(document.getElementById('ch-trend-prod'), {{
  type: 'line',
  data: {{ labels: DATA.haftalik_etiketler, datasets: trendDS(DATA.haftalik_uretim) }},
  options: trendOpts(v => fmt(v))
}});
chTrp = new Chart(document.getElementById('ch-trend-trp'), {{
  type: 'line',
  data: {{ labels: DATA.haftalik_etiketler, datasets: trendDS(DATA.haftalik_trp) }},
  options: {{ ...trendOpts(v => v + '%'), scales: {{ x: trendOpts().scales.x, y: {{ ...trendOpts().scales.y, min: 0, max: 100, ticks: {{ color: '#8892a4', callback: v => v+'%' }} }} }} }}
}});

function updateTrend() {{
  chProd.data.datasets = trendDS(DATA.haftalik_uretim); chProd.update();
  chTrp.data.datasets  = trendDS(DATA.haftalik_trp);   chTrp.update();
}}

// ── E3: Pareto ─────────────────────────────────────────────────────────────
const paretoColors = DATA.durus_pareto_etiket.map((_,i) => `hsl(${{i*32%360}},60%,55%)`);

new Chart(document.getElementById('ch-pareto-cat'), {{
  type: 'bar',
  data: {{
    labels: DATA.durus_pareto_etiket,
    datasets: [{{ label: 'Duruş (dk)', data: DATA.durus_pareto_deger, backgroundColor: paretoColors, borderRadius: 4 }}]
  }},
  options: {{
    indexAxis: 'y', responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', callback: v => fmt(v)+' dk' }} }},
      y: {{ grid: {{ color: 'transparent' }}, ticks: {{ color: '#e2e8f0' }} }}
    }}
  }}
}});

new Chart(document.getElementById('ch-pareto-hat'), {{
  type: 'bar',
  data: {{
    labels: DATA.durus_hat_etiket,
    datasets: [{{
      label: 'Toplam Duruş (dk)', data: DATA.durus_hat_deger, borderRadius: 4,
      backgroundColor: DATA.durus_hat_etiket.map(h => hex2rgba(COLORS[h]||'#888', .8)),
      borderColor: DATA.durus_hat_etiket.map(h => COLORS[h]||'#888'), borderWidth: 1,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4' }} }},
      y: {{ grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', callback: v => fmt(v)+' dk' }} }}
    }}
  }}
}});

// Monthly stacked
const allSebepler = DATA.durus_pareto_etiket;
new Chart(document.getElementById('ch-durus-aylik'), {{
  type: 'bar',
  data: {{
    labels: DATA.durus_aylar,
    datasets: allSebepler.map((s, i) => ({{
      label: s, stack: 'stk',
      data: DATA.durus_aylar.map(ay => DATA.durus_aylik[ay]?.[s] || 0),
      backgroundColor: `hsl(${{i*32%360}},60%,50%)`,
    }}))
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ labels: {{ color: '#e2e8f0', font: {{ size: 10 }}, boxWidth: 12 }} }} }},
    scales: {{
      x: {{ stacked: true, grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4' }} }},
      y: {{ stacked: true, grid: {{ color: '#2e3348' }}, ticks: {{ color: '#8892a4', callback: v => fmt(v) }} }}
    }}
  }}
}});

// ── E4: Table ──────────────────────────────────────────────────────────────
const hatSel  = document.getElementById('f-hat');
const sebepSel= document.getElementById('f-sebep');
[...new Set(DATA.son_duruslar.map(r => r.hat))].sort()
  .forEach(h => {{ const o=document.createElement('option'); o.value=h; o.textContent=h; hatSel.appendChild(o); }});
[...new Set(DATA.son_duruslar.map(r => r.sebep))].sort()
  .forEach(s => {{ const o=document.createElement('option'); o.value=s; o.textContent=s; sebepSel.appendChild(o); }});

function filterTable() {{
  const hat  = document.getElementById('f-hat').value;
  const sebep= document.getElementById('f-sebep').value;
  const vrd  = document.getElementById('f-vardiya').value;
  const txt  = document.getElementById('f-text').value.toLowerCase();
  const rows = DATA.son_duruslar.filter(r =>
    (!hat   || r.hat === hat) &&
    (!sebep || r.sebep === sebep) &&
    (!vrd   || r.vardiya === vrd) &&
    (!txt   || r.aciklama.toLowerCase().includes(txt))
  );
  document.getElementById('row-count').textContent = rows.length + ' kayıt';
  const tbody = document.getElementById('durus-tbody');
  if (!rows.length) {{
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:32px">Kayıt bulunamadı</td></tr>';
    return;
  }}
  tbody.innerHTML = rows.slice(0,200).map(r => {{
    const hc = COLORS[r.hat] || '#888';
    const sc = r.sure >= 120 ? '#f87171' : r.sure >= 60 ? '#facc15' : '#e2e8f0';
    return `<tr>
      <td>${{r.tarih}}</td>
      <td style="font-weight:600">${{r.vardiya}}</td>
      <td style="color:${{hc}};font-weight:600">${{r.hat}}</td>
      <td><span class="badge ${{badgeCls(r.sebep)}}">${{r.sebep}}</span></td>
      <td style="color:${{sc}};font-weight:700">${{r.sure}}</td>
      <td style="color:#cbd5e1;max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{r.aciklama}}</td>
      <td style="color:#8892a4">${{r.op}}</td>
    </tr>`;
  }}).join('');
}}
filterTable();
</script>
</body>
</html>"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✓ Dashboard: {OUTPUT_PATH}")
print(f"  Toplam duruş: {len(durus_kayitlar)} kayıt")
print(f"  Haftalar: {all_weeks[0]} → {all_weeks[-1]}")
print("\n=== KPI ===")
for hat, k in kpi.items():
    trp = f"{k['ort_trp']*100:.1f}%" if k['ort_trp'] else 'N/A'
    print(f"  {hat}: {k['toplam_uretim']:,} adet | TRP={trp} | Rework={k['toplam_rework']} | İskarta={k['toplam_iskarta']}")
