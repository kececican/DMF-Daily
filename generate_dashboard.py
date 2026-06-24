#!/usr/bin/env python3
"""DMF Daily Dashboard Generator — Excel → HTML  (Kapsamlı versiyon)"""

import openpyxl
import json
from datetime import datetime
from collections import defaultdict

EXCEL_PATH = '/root/.claude/uploads/4578e74e-02a1-5b7f-8de5-d3e4492a6ee8/5ec281bc-Copy_of_DMF_Daily_Followup_New_Version_2026.xlsx'
OUTPUT_PATH = '/home/user/DMF-Daily/dashboard/index.html'

print("Excel yükleniyor...")
wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)

# ── Cycle Times (saniye / parça) ─────────────────────────────────────────────
hat_default_ct = {
    'DMF1': 47, 'DMF2': 49, 'DMF3': 46, 'DMF4': 47,
    'PFW1': 50, 'PFW2': 50, 'PFW3': 50, 'PFW4': 50, 'ITL': 56
}
teorik_max_shift = {h: 480*60/ct for h, ct in hat_default_ct.items()}

ALL_HATS = ['DMF1','DMF2','DMF3','DMF4','PFW1','PFW2','PFW3','PFW4','ITL']

def safe_float(v):
    try: return float(v) if v is not None and isinstance(v, (int,float)) else 0.0
    except: return 0.0

def get_week(ds):
    dt = datetime.strptime(ds, '%Y-%m-%d')
    y, w, _ = dt.isocalendar()
    return f'{y}-H{w:02d}'

# ── DMF Extraction ───────────────────────────────────────────────────────────
print("DMF hatları işleniyor...")

daily_prod  = {}   # {hat: {date: {prod, durus, rework, iskarta}}}
trp_shifts  = {}   # {hat: [{date,vardiya,vt,teorik}]}
vardiya_raw = {}   # {hat: {(date,vardiya): toplam_adet}} — ilk non-zero
ref_prod    = {}   # {hat: {ref: toplam_adet}}
ref_lookup  = {}   # {hat: {(date,vardiya): ref}} — duruş için

DMF_DC = [(7,'Çay/Yemek'),(8,'Temizlik'),(9,'Metod/Proje'),
           (10,'Parça Yok'),(11,'SetUp'),(12,'Tuzak Parça'),
           (13,'Kalite Prob.'),(14,'Arıza')]

for hat in ['DMF1','DMF2','DMF3','DMF4']:
    ws = wb[hat]
    daily_prod[hat]  = {}
    trp_shifts[hat]  = []
    vardiya_raw[hat] = {}
    ref_prod[hat]    = {}
    ref_lookup[hat]  = {}

    for row in ws.iter_rows(min_row=3, values_only=True):
        if not (row[0] and isinstance(row[0], datetime)): continue
        ds = row[0].strftime('%Y-%m-%d')
        v  = str(row[2]) if row[2] and str(row[2]) in ('A','B','C') else None
        ref = str(row[3]).strip() if row[3] else None

        if ds not in daily_prod[hat]:
            daily_prod[hat][ds] = {'prod':0,'durus':defaultdict(float),'rework':0,'iskarta':0}
        d = daily_prod[hat][ds]

        prod = safe_float(row[4])
        if prod > 0:
            d['prod'] += prod
            if ref and ref != 'None':
                ref_prod[hat][ref] = ref_prod[hat].get(ref,0) + prod

        for ci,cn in DMF_DC:
            if len(row)>ci: d['durus'][cn] += safe_float(row[ci])
        if len(row)>18: d['rework']  += safe_float(row[18])
        if len(row)>20: d['iskarta'] += safe_float(row[20])

        # Referans: son saat satırında (saat 8/16/24) bulunur
        if ref and ref != 'None' and v:
            ref_lookup[hat][(ds, v)] = ref

        # Vardiya Toplam: ilk non-zero olan satırı al
        vt = safe_float(row[5])
        if v and vt > 0:
            key = (ds, v)
            if key not in vardiya_raw[hat]:
                vardiya_raw[hat][key] = vt
                trp_shifts[hat].append({'date':ds,'vardiya':v,'vt':vt,'teorik':teorik_max_shift[hat]})

# ── PFW Extraction ───────────────────────────────────────────────────────────
print("PFW hatları işleniyor...")

PFW_DC = [(13,'Çay/Yemek'),(14,'Temizlik'),(15,'Kor.Bakım'),(16,'Metod/Proje'),
           (17,'Sipariş Yok'),(18,'Parça Yok'),(19,'SetUp'),(20,'Kesici Değ.'),
           (21,'Kalite Prob.'),(22,'Arıza')]

for hat in ['PFW1','PFW2','PFW3','PFW4']:
    ws = wb[hat]
    daily_prod[hat]  = {}
    trp_shifts[hat]  = []
    vardiya_raw[hat] = {}
    ref_prod[hat]    = {}

    for row in ws.iter_rows(min_row=3, values_only=True):
        if not (row[0] and isinstance(row[0], datetime)): continue
        ds = row[0].strftime('%Y-%m-%d')
        v  = str(row[3]) if row[3] and str(row[3]) in ('A','B','C') else None
        ref = str(row[4]).strip() if row[4] else None

        if ds not in daily_prod[hat]:
            daily_prod[hat][ds] = {'prod':0,'durus':defaultdict(float),'rework':0,'iskarta':0}
        d = daily_prod[hat][ds]

        if len(row)>10:
            prod = safe_float(row[10])
            if prod > 0:
                d['prod'] += prod
                if ref and ref != 'None':
                    ref_prod[hat][ref] = ref_prod[hat].get(ref,0) + prod

        for ci,cn in PFW_DC:
            if len(row)>ci: d['durus'][cn] += safe_float(row[ci])

        vt = safe_float(row[11]) if len(row)>11 else 0
        if v and vt > 0:
            key = (ds,v)
            if key not in vardiya_raw[hat]:
                vardiya_raw[hat][key] = vt
                trp_shifts[hat].append({'date':ds,'vardiya':v,'vt':vt,'teorik':teorik_max_shift[hat]})

# ── ITL Extraction ───────────────────────────────────────────────────────────
print("ITL hattı işleniyor...")

ITL_DC = [(13,'Çay/Yemek'),(14,'Temizlik'),(15,'Kor.Bakım'),(16,'Metod/Proje'),
           (17,'Sipariş Yok'),(18,'Parça Yok'),(19,'Hat Besleme'),
           (20,'Kalite Prob.'),(21,'Arıza')]

ws = wb['ITL']
daily_prod['ITL']  = {}
trp_shifts['ITL']  = []
vardiya_raw['ITL'] = {}
ref_prod['ITL']    = {}

for row in ws.iter_rows(min_row=4, values_only=True):
    if not (row[0] and isinstance(row[0], datetime)): continue
    ds = row[0].strftime('%Y-%m-%d')
    v  = str(row[2]) if row[2] and str(row[2]) in ('A','B','C') else None
    ref = str(row[3]).strip() if row[3] else None

    if ds not in daily_prod['ITL']:
        daily_prod['ITL'][ds] = {'prod':0,'durus':defaultdict(float),'rework':0,'iskarta':0}
    d = daily_prod['ITL'][ds]

    if len(row)>10:
        prod = safe_float(row[10])
        if prod > 0:
            d['prod'] += prod
            if ref and ref != 'None':
                ref_prod['ITL'][ref] = ref_prod['ITL'].get(ref,0) + prod

    for ci,cn in ITL_DC:
        if len(row)>ci: d['durus'][cn] += safe_float(row[ci])

    vt = safe_float(row[11]) if len(row)>11 else 0
    if v and vt > 0:
        key = (ds,v)
        if key not in vardiya_raw['ITL']:
            vardiya_raw['ITL'][key] = vt
            trp_shifts['ITL'].append({'date':ds,'vardiya':v,'vt':vt,'teorik':teorik_max_shift['ITL']})

# ── SMF-DOOSAN Extraction ────────────────────────────────────────────────────
print("SMF-DOOSAN işleniyor...")

smf_daily = {}  # {date: {jx22, eb2, doosan, total, nok}}
ws = wb['SMF-DOOSAN']
for row in ws.iter_rows(min_row=3, values_only=True):
    if not (row[0] and isinstance(row[0], datetime)): continue
    # Cols: 0=Tarih, 1=JX22-A, 2=JX22-B, 3=JX22-C, 4=NOK, 5=JX22 toplam
    #       6=EB2-A, 7=EB2-B, 8=EB2-C, 9=EB2 toplam, 10=Total
    #       11=Doosan-A, 12=Doosan-B, 13=Doosan-C, 14=Doosan toplam
    jx22 = safe_float(row[5])
    eb2  = safe_float(row[9])
    nok  = safe_float(row[4])
    doos = safe_float(row[14]) if len(row)>14 else 0
    total = jx22 + eb2
    if total > 0:
        ds = row[0].strftime('%Y-%m-%d')
        smf_daily[ds] = {'jx22':jx22, 'eb2':eb2, 'doosan':doos, 'total':total, 'nok':nok}

# ── Duruş Records ────────────────────────────────────────────────────────────
print("Duruş kayıtları işleniyor...")

ws_dur = wb['Duruş Süre&Sebep']
durus_kayitlar = []
for row in ws_dur.iter_rows(min_row=2, values_only=True):
    if not (row[0] and isinstance(row[0], datetime)): continue
    sure = safe_float(row[4])
    if sure <= 0: continue
    hat_d  = str(row[3]) if row[3] else ''
    vrd_d  = str(row[1]) if row[1] else ''
    tar_d  = row[0].strftime('%Y-%m-%d')
    ref_d  = ref_lookup.get(hat_d, {}).get((tar_d, vrd_d), '')
    durus_kayitlar.append({
        'tarih':   tar_d,
        'vardiya': vrd_d,
        'sebep':   str(row[2]) if row[2] else 'Bilinmiyor',
        'hat':     hat_d,
        'ref':     ref_d,
        'sure':    round(sure,1),
        'aciklama':str(row[5])[:90] if row[5] else '',
        'op':      str(row[6]) if row[6] else '',
    })
durus_kayitlar.sort(key=lambda x: x['tarih'], reverse=True)

# ── Weekly & Monthly Aggregates ──────────────────────────────────────────────
print("Özetler hesaplanıyor...")

weekly_prod = {h:{} for h in ALL_HATS}
weekly_trp  = {h:{} for h in ALL_HATS}

for hat in ALL_HATS:
    for ds,d in daily_prod[hat].items():
        if d['prod']==0: continue
        wk = get_week(ds)
        weekly_prod[hat][wk] = weekly_prod[hat].get(wk,0) + d['prod']
    for sh in trp_shifts[hat]:
        wk = get_week(sh['date'])
        if wk not in weekly_trp[hat]: weekly_trp[hat][wk] = []
        weekly_trp[hat][wk].append(sh['vt']/sh['teorik'])

all_weeks = sorted({wk for h in ALL_HATS for wk in weekly_prod[h]})[-20:]

ay_labels = sorted({ds[:7] for h in ALL_HATS for ds,d in daily_prod[h].items() if d['prod']>0})[-8:]

monthly_prod = {}
for hat in ALL_HATS:
    monthly_prod[hat] = [
        int(sum(d['prod'] for ds,d in daily_prod[hat].items() if ds.startswith(ay)))
        for ay in ay_labels
    ]

# ── Vardiya Monthly Averages ─────────────────────────────────────────────────
# Per hat, per month: average shift production for A, B, C
vardiya_monthly = {}   # {hat: {ay: {A:[], B:[], C:[]}}}
for hat in ALL_HATS:
    vardiya_monthly[hat] = {}
    for (ds,v), vt in vardiya_raw[hat].items():
        ay = ds[:7]
        if ay not in vardiya_monthly[hat]:
            vardiya_monthly[hat][ay] = {'A':[],'B':[],'C':[]}
        if v in ('A','B','C'):
            vardiya_monthly[hat][ay][v].append(vt)

vardiya_chart = {}  # {hat: {A:[ort/ay], B:[ort/ay], C:[ort/ay]}}
for hat in ALL_HATS:
    vardiya_chart[hat] = {'A':[],'B':[],'C':[]}
    for ay in ay_labels:
        ayd = vardiya_monthly[hat].get(ay, {'A':[],'B':[],'C':[]})
        for v in ('A','B','C'):
            lst = ayd.get(v,[])
            vardiya_chart[hat][v].append(round(sum(lst)/len(lst),0) if lst else 0)

# ── Reference Distribution ───────────────────────────────────────────────────
# Top 8 refs per hat
ref_top = {}
for hat in ALL_HATS:
    sorted_refs = sorted(ref_prod[hat].items(), key=lambda x: -x[1])[:8]
    ref_top[hat] = {
        'labels': [r[0] for r in sorted_refs],
        'data':   [int(r[1]) for r in sorted_refs],
    }

# ── KPI ──────────────────────────────────────────────────────────────────────
kpi = {}
for hat in ALL_HATS:
    all_prod = sum(d['prod'] for d in daily_prod[hat].values())
    son_ay   = sum(d['prod'] for ds,d in daily_prod[hat].items() if ds>='2026-06-01')
    son4 = [t for wk in all_weeks[-4:] for t in weekly_trp[hat].get(wk,[])]
    avg_trp = round(sum(son4)/len(son4),3) if son4 else None
    kpi[hat] = {
        'toplam': int(all_prod), 'son_ay': int(son_ay),
        'rework': int(sum(d['rework'] for d in daily_prod[hat].values())),
        'iskarta': int(sum(d['iskarta'] for d in daily_prod[hat].values())),
        'ort_trp': avg_trp,
    }

# SMF KPI
smf_kpi = {
    'jx22_toplam': int(sum(v['jx22'] for v in smf_daily.values())),
    'eb2_toplam':  int(sum(v['eb2']  for v in smf_daily.values())),
    'toplam':      int(sum(v['total'] for v in smf_daily.values())),
    'nok':         int(sum(v['nok']  for v in smf_daily.values())),
    'aktif_gun':   len(smf_daily),
}

# ── Duruş Pareto ─────────────────────────────────────────────────────────────
durus_cat  = defaultdict(float)
durus_hat2 = defaultdict(float)
durus_aylik= defaultdict(lambda: defaultdict(float))

for r in durus_kayitlar:
    durus_cat[r['sebep']]    += r['sure']
    durus_hat2[r['hat']]     += r['sure']
    durus_aylik[r['tarih'][:7]][r['sebep']] += r['sure']

pareto_cat = sorted(durus_cat.items(), key=lambda x:-x[1])
pareto_hat = sorted(durus_hat2.items(), key=lambda x:-x[1])
aylar      = sorted(durus_aylik.keys())

# ── Weekly series ─────────────────────────────────────────────────────────────
def wk_avg(trp_dict, wk):
    lst = trp_dict.get(wk,[])
    return round(sum(lst)/len(lst)*100,1) if lst else 0

w_prod = {h:[int(weekly_prod[h].get(wk,0)) for wk in all_weeks] for h in ALL_HATS}
w_trp  = {h:[wk_avg(weekly_trp[h],wk) for wk in all_weeks]      for h in ALL_HATS}

# ── SMF daily series ──────────────────────────────────────────────────────────
smf_dates  = sorted(smf_daily.keys())
smf_jx22   = [smf_daily[d]['jx22']  for d in smf_dates]
smf_eb2    = [smf_daily[d]['eb2']   for d in smf_dates]
smf_total  = [smf_daily[d]['total'] for d in smf_dates]

# ── Build JSON ────────────────────────────────────────────────────────────────
print("JSON hazırlanıyor...")

data_json = {
    'meta':   {'guncelleme': datetime.now().strftime('%d.%m.%Y %H:%M'), 'hatlar': ALL_HATS},
    'kpi':    kpi,
    'smf_kpi': smf_kpi,
    'smf_dates': smf_dates,
    'smf_jx22':  smf_jx22,
    'smf_eb2':   smf_eb2,
    'smf_total': smf_total,
    'haftalik_etiket': all_weeks,
    'haftalik_uretim': w_prod,
    'haftalik_trp':    w_trp,
    'aylik_etiket':    ay_labels,
    'aylik_uretim':    monthly_prod,
    'vardiya_chart':   vardiya_chart,
    'ref_top':         ref_top,
    'pareto_cat_etiket': [x[0] for x in pareto_cat],
    'pareto_cat_deger':  [round(x[1],0) for x in pareto_cat],
    'pareto_hat_etiket': [x[0] for x in pareto_hat],
    'pareto_hat_deger':  [round(x[1],0) for x in pareto_hat],
    'durus_aylar':  aylar,
    'durus_aylik':  {ay:{s:round(v,0) for s,v in sd.items()} for ay,sd in durus_aylik.items()},
    'son_duruslar': durus_kayitlar,
}

# ── HTML ──────────────────────────────────────────────────────────────────────
print("HTML oluşturuluyor...")

HAT_COLORS = {
    'DMF1':'#2196F3','DMF2':'#4CAF50','DMF3':'#FF9800','DMF4':'#9C27B0',
    'PFW1':'#F44336','PFW2':'#00BCD4','PFW3':'#8BC34A','PFW4':'#FF5722','ITL':'#607D8B'
}
data_js      = json.dumps(data_json, ensure_ascii=False, indent=2)
hat_colors_js= json.dumps(HAT_COLORS)

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DMF Daily – Üretim Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    :root{{--bg:#0f1117;--sur:#1a1d27;--sur2:#242736;--brd:#2e3348;--txt:#e2e8f0;--mut:#8892a4;--acc:#3b82f6}}
    body{{background:var(--bg);color:var(--txt);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px}}

    .hdr{{background:var(--sur);border-bottom:1px solid var(--brd);padding:13px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:200}}
    .hdr h1{{font-size:17px;font-weight:600;color:#fff}}
    .hdr .upd{{font-size:12px;color:var(--mut)}}

    .tabs{{display:flex;background:var(--sur);border-bottom:1px solid var(--brd);padding:0 20px;overflow-x:auto}}
    .tab{{padding:11px 18px;cursor:pointer;border-bottom:2px solid transparent;color:var(--mut);font-weight:500;white-space:nowrap;user-select:none;transition:color .15s}}
    .tab:hover{{color:var(--txt)}}
    .tab.active{{color:var(--acc);border-bottom-color:var(--acc)}}

    .screen{{display:none;padding:22px;max-width:1700px;margin:0 auto}}
    .screen.active{{display:block}}

    /* KPI */
    .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:13px;margin-bottom:22px}}
    .kcard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:15px}}
    .khat{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:11px}}
    .krow{{margin-bottom:7px}}
    .klabel{{font-size:11px;color:var(--mut);margin-bottom:1px}}
    .kval{{font-size:20px;font-weight:700;color:#fff;line-height:1.1}}
    .ksub{{font-size:11px;color:var(--mut)}}
    .trpbar{{height:5px;background:var(--brd);border-radius:3px;margin-top:5px;overflow:hidden}}
    .trpfill{{height:100%;border-radius:3px}}
    .kmini{{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:9px}}
    .kmini .kval{{font-size:15px}}

    /* SMF card */
    .smf-row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:13px;margin-bottom:22px}}
    .smfcard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:15px;border-top:3px solid #FF9800}}

    /* Charts */
    .crow{{display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px}}
    .crow.full{{grid-template-columns:1fr}}
    .crow.three{{grid-template-columns:1fr 1fr 1fr}}
    .ccard{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;padding:18px}}
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
    .twrap{{background:var(--sur);border:1px solid var(--brd);border-radius:10px;overflow:auto}}
    .fbar{{display:flex;gap:9px;padding:13px 15px;border-bottom:1px solid var(--brd);flex-wrap:wrap;align-items:center}}
    .fbar select,.fbar input{{background:var(--sur2);border:1px solid var(--brd);color:var(--txt);padding:6px 10px;border-radius:6px;font-size:13px}}
    table{{width:100%;border-collapse:collapse;min-width:680px}}
    th{{background:var(--sur2);padding:9px 13px;text-align:left;font-size:11px;font-weight:600;color:var(--mut);text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--brd);white-space:nowrap}}
    td{{padding:8px 13px;border-bottom:1px solid var(--brd);font-size:13px}}
    tr:last-child td{{border-bottom:none}}
    tr:hover td{{background:var(--sur2)}}
    .badge{{display:inline-block;padding:2px 8px;border-radius:11px;font-size:11px;font-weight:600;white-space:nowrap}}
    .ba{{background:#7f1d1d33;color:#fca5a5;border:1px solid #7f1d1d}}
    .bk{{background:#78350f33;color:#fcd34d;border:1px solid #78350f}}
    .bp{{background:#1e3a5f33;color:#93c5fd;border:1px solid #1e3a5f}}
    .bs{{background:#1a3a1a33;color:#86efac;border:1px solid #1a3a1a}}
    .bm{{background:#2e1a4a33;color:#c4b5fd;border:1px solid #2e1a4a}}
    .bl{{background:#1a2e2e33;color:#6ee7b7;border:1px solid #1a2e2e}}
    .bd{{background:#2a2a2a33;color:#d1d5db;border:1px solid #2a2a2a}}

    @media(max-width:900px){{.crow,.crow.three{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>

<div class="hdr">
  <h1>⚙ DMF Daily — Üretim Takip Dashboard</h1>
  <span class="upd" id="upd-date"></span>
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
    <div class="ccard"><div class="ctitle">Aylık Üretim — PFW & ITL</div><div class="cwrap"><canvas id="ch-m-pfw"></canvas></div></div>
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
    <div class="ccard"><div class="ctitle">Referans Bazında Toplam Üretim (Adet)</div><div class="cwrap" style="height:340px"><canvas id="ch-ref-bar"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Referans Üretim Payı (%)</div><div class="cwrap" style="height:340px"><canvas id="ch-ref-pie"></canvas></div></div>
  </div>
</div>

<!-- E5: Duruş -->
<div id="screen-e5" class="screen">
  <div class="crow">
    <div class="ccard"><div class="ctitle">Duruş Sebebi Pareto (dk)</div><div class="cwrap" style="height:350px"><canvas id="ch-pc"></canvas></div></div>
    <div class="ccard"><div class="ctitle">Hat Bazında Toplam Duruş (dk)</div><div class="cwrap" style="height:350px"><canvas id="ch-ph"></canvas></div></div>
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
      <input  id="f-text" type="text" placeholder="Açıklama ara…" oninput="flt()" style="flex:1;min-width:160px">
      <span id="fcount" style="font-size:12px;color:var(--mut);white-space:nowrap"></span>
    </div>
    <table>
      <thead><tr><th>Tarih</th><th>Vrd.</th><th>Hat</th><th>Referans</th><th>Sebep</th><th>Süre(dk)</th><th>Açıklama</th><th>OP</th></tr></thead>
      <tbody id="dur-tbody"></tbody>
    </table>
  </div>
</div>

<script>
const D  = {data_js};
const HC = {hat_colors_js};

// ── utils ──────────────────────────────────────────────────────────────────
const h2r=(h,a=1)=>{{const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16);return`rgba(${{r}},${{g}},${{b}},${{a}})`;}};
const fmt=n=>new Intl.NumberFormat('tr-TR').format(Math.round(n));
const baseScales=()=>({{
  x:{{grid:{{color:'#2e3348'}},ticks:{{color:'#8892a4',maxTicksLimit:14,maxRotation:45}}}},
  y:{{grid:{{color:'#2e3348'}},ticks:{{color:'#8892a4'}}}}
}});
const baseLegend=()=>({{labels:{{color:'#e2e8f0',font:{{size:11}}}}}});
const badgeCls=s=>/Arıza|Robot/.test(s)?'ba':/Kalite/.test(s)?'bk':/Parça|Sipariş|Besleme/.test(s)?'bp':/Set|Kesici/.test(s)?'bs':/Metod|Arge/.test(s)?'bm':/Planlı/.test(s)?'bl':'bd';

// ── tabs ──────────────────────────────────────────────────────────────────
function T(id,el){{
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('screen-'+id).classList.add('active');
  el.classList.add('active');
}}

// ── E1: KPI ───────────────────────────────────────────────────────────────
document.getElementById('upd-date').textContent='Son güncelleme: '+D.meta.guncelleme;

const g=document.getElementById('kpi-grid');
D.meta.hatlar.forEach(hat=>{{
  const k=D.kpi[hat],c=HC[hat];
  const tp=k.ort_trp?(k.ort_trp*100):null;
  const ts=tp!==null?tp.toFixed(1)+'%':'—';
  const tc=tp===null?'#888':tp>=75?'#4ade80':tp>=55?'#facc15':'#f87171';
  g.innerHTML+=`<div class="kcard" style="border-top:3px solid ${{c}}">
    <div class="khat" style="color:${{c}}">${{hat}}</div>
    <div class="krow"><div class="klabel">Toplam Üretim</div><div class="kval">${{fmt(k.toplam)}}</div><div class="ksub">Haziran: ${{fmt(k.son_ay)}}</div></div>
    <div class="krow" style="margin-top:9px"><div class="klabel">TRP (son 4 hafta)</div><div class="kval" style="color:${{tc}};font-size:23px">${{ts}}</div>
      <div class="trpbar"><div class="trpfill" style="width:${{Math.min(tp||0,100)}}%;background:${{tc}}"></div></div></div>
    <div class="kmini">
      <div><div class="klabel">Rework</div><div class="kval" style="color:#fde047">${{fmt(k.rework)}}</div></div>
      <div><div class="klabel">İskarta</div><div class="kval" style="color:#f87171">${{fmt(k.iskarta)}}</div></div>
    </div></div>`;
}});

// SMF cards
const sm=document.getElementById('smf-cards');
const sk=D.smf_kpi;
sm.innerHTML=`
  <div class="smfcard"><div class="klabel">JX22 Toplam</div><div class="kval" style="font-size:22px">${{fmt(sk.jx22_toplam)}}</div></div>
  <div class="smfcard"><div class="klabel">EB2 Toplam</div><div class="kval" style="font-size:22px">${{fmt(sk.eb2_toplam)}}</div></div>
  <div class="smfcard"><div class="klabel">Genel Toplam</div><div class="kval" style="font-size:22px;color:#4ade80">${{fmt(sk.toplam)}}</div></div>
  <div class="smfcard"><div class="klabel">NOK Adet</div><div class="kval" style="font-size:22px;color:#f87171">${{fmt(sk.nok)}}</div></div>
  <div class="smfcard"><div class="klabel">Aktif Gün</div><div class="kval" style="font-size:22px">${{sk.aktif_gun}}</div><div class="ksub">Ara.2025–Şub.2026</div></div>`;

// Monthly bars
function mBar(id,hats){{
  new Chart(document.getElementById(id),{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:hats.map(h=>({{label:h,data:D.aylik_uretim[h],backgroundColor:h2r(HC[h],.75),borderColor:HC[h],borderWidth:1,borderRadius:4}}))}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend()}},scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
  }});
}}
mBar('ch-m-dmf',['DMF1','DMF2','DMF3','DMF4']);
mBar('ch-m-pfw',['PFW1','PFW2','PFW3','PFW4','ITL']);

// SMF chart
new Chart(document.getElementById('ch-smf'),{{type:'bar',
  data:{{labels:D.smf_dates,datasets:[
    {{label:'JX22',data:D.smf_jx22,backgroundColor:h2r('#FF9800',.8),borderRadius:3,stack:'s'}},
    {{label:'EB2', data:D.smf_eb2, backgroundColor:h2r('#2196F3',.8),borderRadius:3,stack:'s'}},
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend()}},
    scales:{{x:{{...baseScales().x,stacked:true}},y:{{...baseScales().y,stacked:true,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
}});

// ── E2: Trend ──────────────────────────────────────────────────────────────
let actH=new Set(['DMF1','DMF2','DMF3','DMF4']);
let chTP,chTT;
const hfDiv=document.getElementById('hf-btns');
D.meta.hatlar.forEach(h=>{{
  const b=document.createElement('button');
  b.className='hbtn'+(actH.has(h)?' on':'');
  if(actH.has(h))b.style.backgroundColor=HC[h];
  b.textContent=h;
  b.onclick=()=>{{actH.has(h)?(actH.delete(h),b.classList.remove('on'),b.style.backgroundColor=''):(actH.add(h),b.classList.add('on'),b.style.backgroundColor=HC[h]);updTrend();}};
  hfDiv.appendChild(b);
}});
const tDS=ser=>[...actH].map(h=>({{label:h,data:ser[h]||[],borderColor:HC[h],backgroundColor:h2r(HC[h],.08),borderWidth:2.5,pointRadius:3,tension:.3,fill:false}}));
const tOpts=(yFn)=>({{responsive:true,maintainAspectRatio:false,interaction:{{mode:'index',intersect:false}},
  plugins:{{legend:baseLegend(),tooltip:{{backgroundColor:'#1a1d27',borderColor:'#2e3348',borderWidth:1}}}},
  scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:yFn}}}}}}}});
chTP=new Chart(document.getElementById('ch-tw-prod'),{{type:'line',data:{{labels:D.haftalik_etiket,datasets:tDS(D.haftalik_uretim)}},options:tOpts(v=>fmt(v))}});
chTT=new Chart(document.getElementById('ch-tw-trp'), {{type:'line',data:{{labels:D.haftalik_etiket,datasets:tDS(D.haftalik_trp)}}, options:tOpts(v=>v+'%')}});
function updTrend(){{chTP.data.datasets=tDS(D.haftalik_uretim);chTP.update();chTT.data.datasets=tDS(D.haftalik_trp);chTT.update();}}

// ── E3: Vardiya ─────────────────────────────────────────────────────────────
const vrdSel=document.getElementById('vrd-hat-sel');
D.meta.hatlar.forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;vrdSel.appendChild(o);}});
let chVA,chVP,chVT;
function renderVardiya(){{
  const hat=vrdSel.value;
  const vc=D.vardiya_chart[hat];
  const vColors={{A:'#4ade80',B:'#60a5fa',C:'#f472b6'}};

  if(chVA)chVA.destroy();
  if(chVP)chVP.destroy();
  if(chVT)chVT.destroy();

  chVA=new Chart(document.getElementById('ch-vrd-aylik'),{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:['A','B','C'].map(v=>({{label:'Vardiya '+v,data:vc[v],backgroundColor:h2r(vColors[v],.75),borderColor:vColors[v],borderWidth:1,borderRadius:4}}))}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend()}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
  }});

  // Pie — total per vardiya across all data
  const allTots={{A:0,B:0,C:0}};
  Object.values(D.vardiya_chart[hat]).forEach((arr,i)=>arr.forEach(v=>allTots[['A','B','C'][i]]+=v));
  chVP=new Chart(document.getElementById('ch-vrd-pie'),{{type:'doughnut',
    data:{{labels:['Vardiya A','Vardiya B','Vardiya C'],
      datasets:[{{data:[allTots.A,allTots.B,allTots.C],backgroundColor:[h2r('#4ade80',.8),h2r('#60a5fa',.8),h2r('#f472b6',.8)],borderColor:['#4ade80','#60a5fa','#f472b6'],borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend(),tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)+' adet'}}}}}}}}
  }});

  // TRP per vardiya per week
  // Compute per-vardiya TRP from trp_shifts for selected hat — approximated via production
  // Show A/B/C average production ratio as TRP proxy (actual trp by vardiya not in data_json)
  // Instead, show weekly A vs B vs C average (vc normalized to max)
  const wkVA=[],wkVB=[],wkVC=[];
  D.haftalik_etiket.forEach(wk=>{{
    // proxy: monthly idx
    const idx=D.aylik_etiket.indexOf(wk.slice(0,7));
    wkVA.push(idx>=0?vc.A[idx]:0);
    wkVB.push(idx>=0?vc.B[idx]:0);
    wkVC.push(idx>=0?vc.C[idx]:0);
  }});
  chVT=new Chart(document.getElementById('ch-vrd-trp'),{{type:'line',
    data:{{labels:D.haftalik_etiket,datasets:[
      {{label:'Vardiya A',data:D.haftalik_etiket.map((_,i)=>0),hidden:true}},
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}},
      title:{{display:true,text:'Aylık ortalama üretim (adet/vardiya) — hat: '+hat,color:'#8892a4',font:{{size:12}}}}}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
  }});
  // Replace with grouped monthly bar showing A/B/C per month (more meaningful)
  chVT.destroy();
  chVT=new Chart(document.getElementById('ch-vrd-trp'),{{type:'bar',
    data:{{labels:D.aylik_etiket,datasets:[
      {{label:'Vardiya A',data:vc.A,backgroundColor:h2r('#4ade80',.75),borderColor:'#4ade80',borderWidth:1,borderRadius:4}},
      {{label:'Vardiya B',data:vc.B,backgroundColor:h2r('#60a5fa',.75),borderColor:'#60a5fa',borderWidth:1,borderRadius:4}},
      {{label:'Vardiya C',data:vc.C,backgroundColor:h2r('#f472b6',.75),borderColor:'#f472b6',borderWidth:1,borderRadius:4}},
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend()}},
      scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
  }});
}}
renderVardiya();

// ── E4: Referans ─────────────────────────────────────────────────────────────
const refSel=document.getElementById('ref-hat-sel');
D.meta.hatlar.forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;refSel.appendChild(o);}});
let chRB,chRP;
const refColors=['#2196F3','#4CAF50','#FF9800','#9C27B0','#F44336','#00BCD4','#8BC34A','#FF5722'];
function renderRef(){{
  const hat=refSel.value;
  const r=D.ref_top[hat];
  if(chRB)chRB.destroy();
  if(chRP)chRP.destroy();
  chRB=new Chart(document.getElementById('ch-ref-bar'),{{type:'bar',
    data:{{labels:r.labels,datasets:[{{label:'Üretim (adet)',data:r.data,backgroundColor:refColors.map(c=>h2r(c,.8)),borderColor:refColors,borderWidth:1,borderRadius:4}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
      scales:{{x:{{...baseScales().x,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}},y:{{grid:{{color:'transparent'}},ticks:{{color:'#e2e8f0'}}}}}}}}
  }});
  chRP=new Chart(document.getElementById('ch-ref-pie'),{{type:'doughnut',
    data:{{labels:r.labels,datasets:[{{data:r.data,backgroundColor:refColors.map(c=>h2r(c,.8)),borderColor:refColors,borderWidth:2}}]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend(),tooltip:{{callbacks:{{label:ctx=>ctx.label+': '+fmt(ctx.raw)}}}}}}}}
  }});
}}
renderRef();

// ── E5: Duruş ─────────────────────────────────────────────────────────────
const pColors=D.pareto_cat_etiket.map((_,i)=>`hsl(${{i*32%360}},60%,55%)`);
new Chart(document.getElementById('ch-pc'),{{type:'bar',
  data:{{labels:D.pareto_cat_etiket,datasets:[{{label:'dk',data:D.pareto_cat_deger,backgroundColor:pColors,borderRadius:4}}]}},
  options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:{{...baseScales().x,ticks:{{color:'#8892a4',callback:v=>fmt(v)+' dk'}}}},y:{{grid:{{color:'transparent'}},ticks:{{color:'#e2e8f0'}}}}}}}}
}});
new Chart(document.getElementById('ch-ph'),{{type:'bar',
  data:{{labels:D.pareto_hat_etiket,datasets:[{{label:'dk',data:D.pareto_hat_deger,backgroundColor:D.pareto_hat_etiket.map(h=>h2r(HC[h]||'#888',.8)),borderColor:D.pareto_hat_etiket.map(h=>HC[h]||'#888'),borderWidth:1,borderRadius:4}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}},
    scales:{{x:baseScales().x,y:{{...baseScales().y,ticks:{{color:'#8892a4',callback:v=>fmt(v)+' dk'}}}}}}}}
}});
new Chart(document.getElementById('ch-durus-ay'),{{type:'bar',
  data:{{labels:D.durus_aylar,datasets:D.pareto_cat_etiket.map((s,i)=>({{label:s,stack:'s',data:D.durus_aylar.map(ay=>D.durus_aylik[ay]?.[s]||0),backgroundColor:`hsl(${{i*32%360}},60%,50%)`}}))}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:baseLegend()}},
    scales:{{x:{{...baseScales().x,stacked:true}},y:{{...baseScales().y,stacked:true,ticks:{{color:'#8892a4',callback:v=>fmt(v)}}}}}}}}
}});

// ── E6: Detay ─────────────────────────────────────────────────────────────
const hSel=document.getElementById('f-hat'),sSel=document.getElementById('f-sebep');
[...new Set(D.son_duruslar.map(r=>r.hat))].sort().forEach(h=>{{const o=document.createElement('option');o.value=h;o.textContent=h;hSel.appendChild(o);}});
[...new Set(D.son_duruslar.map(r=>r.sebep))].sort().forEach(s=>{{const o=document.createElement('option');o.value=s;o.textContent=s;sSel.appendChild(o);}});
function flt(){{
  const h=hSel.value,s=sSel.value,v=document.getElementById('f-vardiya').value,t=document.getElementById('f-text').value.toLowerCase();
  const rows=D.son_duruslar.filter(r=>(!h||r.hat===h)&&(!s||r.sebep===s)&&(!v||r.vardiya===v)&&(!t||r.aciklama.toLowerCase().includes(t)));
  document.getElementById('fcount').textContent=rows.length+' kayıt';
  const tb=document.getElementById('dur-tbody');
  if(!rows.length){{tb.innerHTML='<tr><td colspan="7" style="text-align:center;color:var(--mut);padding:28px">Kayıt bulunamadı</td></tr>';return;}}
  tb.innerHTML=rows.slice(0,200).map(r=>{{
    const hc=HC[r.hat]||'#888',sc=r.sure>=120?'#f87171':r.sure>=60?'#facc15':'#e2e8f0';
    return`<tr><td>${{r.tarih}}</td><td style="font-weight:600">${{r.vardiya}}</td><td style="color:${{hc}};font-weight:600">${{r.hat}}</td><td style="color:#f0c040;font-weight:600;font-size:12px">${{r.ref||'—'}}</td><td><span class="badge ${{badgeCls(r.sebep)}}">${{r.sebep}}</span></td><td style="color:${{sc}};font-weight:700">${{r.sure}}</td><td style="color:#cbd5e1;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{r.aciklama}}</td><td style="color:#8892a4">${{r.op}}</td></tr>`;
  }}).join('');
}}
flt();
</script>
</body>
</html>"""

with open(OUTPUT_PATH,'w',encoding='utf-8') as f:
    f.write(html)

print(f"\n✓ {OUTPUT_PATH}")
print(f"  Dosya boyutu: {len(html)//1024} KB")
print(f"  Haftalar: {all_weeks[0]} → {all_weeks[-1]}")
print(f"  SMF aktif gün: {len(smf_daily)}")
print("\n=== KPI ===")
for hat,k in kpi.items():
    t=f"{k['ort_trp']*100:.1f}%" if k['ort_trp'] else 'N/A'
    print(f"  {hat}: {k['toplam']:,} adet | TRP={t}")
print("\n=== Vardiya (DMF3 örnek) ===")
for ay in ay_labels[-3:]:
    ayd=vardiya_monthly['DMF3'].get(ay,{})
    for v in ('A','B','C'):
        lst=ayd.get(v,[])
        if lst: print(f"  DMF3 {ay} {v}: ort={sum(lst)/len(lst):.0f} ({len(lst)} shift)")
