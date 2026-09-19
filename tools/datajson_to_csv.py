#!/usr/bin/env python3
"""dashboard/data.json → Google Sheet'e aktarılacak CSV'ler.

data.json TOPLANMIŞ veri tutar. Buradan tam olarak geri kurulabilenler:
  • Duruş kayıtları  — 1074 satırın tamamı, alan alan
  • SMF-DOOSAN       — günlük JX22 / EB2

Geri kurulamayan:
  • Üretim satırları — data.json'da yalnız haftalık/aylık/vardiya-ortalaması
    olarak var; vardiya bazlı ham satırlar yok. Bunlar için Excel şart
    (tools/excel_to_csv.py).
  • SMF günlük NOK   — data.json sadece toplamı tutuyor (smf_kpi.nok).

Kullanım:  python3 tools/datajson_to_csv.py [cikti_dizini]
"""

import csv
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(BASE, 'dashboard', 'data.json')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'sheets-csv')

VARSAYILAN_CT = {'DMF1': 47, 'DMF2': 49, 'DMF3': 46, 'DMF4': 47,
                 'PFW1': 50, 'PFW2': 50, 'PFW3': 50, 'PFW4': 50, 'ITL': 56}

with open(CACHE, encoding='utf-8') as f:
    D = json.load(f)

os.makedirs(OUT, exist_ok=True)


def yaz(ad, basliklar, satirlar):
    p = os.path.join(OUT, ad + '.csv')
    with open(p, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(basliklar)
        w.writerows(satirlar)
    print(f"  {ad + '.csv':16s} {len(satirlar):5d} satır")


print(f"Çıktı: {OUT}")

# ── Durus ────────────────────────────────────────────────────────────────────
# 'ref' sütunu yazılmaz: referans, Uretim sekmesinden (tarih|vardiya|hat) ile
# türetilir — Excel'deki davranışın aynısı, tek kaynak ilkesi korunur.
yaz('Durus',
    ['tarih', 'vardiya', 'hat', 'sebep', 'sure_dk', 'aciklama', 'op'],
    [[r['tarih'], r['vardiya'], r['hat'], r['sebep'], r['sure'],
      r['aciklama'], r['op']] for r in D['son_duruslar']])

# ── SMF ──────────────────────────────────────────────────────────────────────
smf = [[t, j, e, '', ''] for t, j, e in
       zip(D['smf_dates'], D['smf_jx22'], D['smf_eb2'])]
yaz('SMF', ['tarih', 'jx22', 'eb2', 'doosan', 'nok'], smf)

# ── Cycle ────────────────────────────────────────────────────────────────────
# Hat varsayılanları (referans sütunu boş = o hattın varsayılanı).
# Cycle time şimdiye kadar kodda sabit dict'ti; artık düzenlenebilir veri.
yaz('Cycle', ['hat', 'referans', 'cycle_sn'],
    [[h, '', ct] for h, ct in VARSAYILAN_CT.items()])

# ── Uretim ───────────────────────────────────────────────────────────────────
# Yalnız başlık — ham satırlar data.json'da yok.
yaz('Uretim', ['tarih', 'vardiya', 'hat', 'referans', 'adet', 'rework', 'iskarta'], [])

print("""
⚠ Uretim.csv BOŞ — vardiya bazlı ham üretim satırları data.json'da yok.
  Üretim geçmişini taşımak için Excel gerekiyor:
      DMF_EXCEL=/yol/dosya.xlsx python3 tools/excel_to_csv.py
  Uretim boş kalırsa dashboard duruş ve SMF sekmelerini gösterir;
  KPI / trend / vardiya / referans sekmeleri veri girilene kadar boş olur.

⚠ SMF nok sütunu boş — data.json yalnız toplamı tutuyor (smf_kpi.nok).
""")
