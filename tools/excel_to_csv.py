#!/usr/bin/env python3
"""Excel → Google Sheet'e aktarılacak normalize CSV'ler.

Excel'de her hat ailesinin kolon düzeni farklı (DMF üretim E, PFW/ITL K…) ve
satırlar saatlik. Buradaki çıktı normalize edilir: bir vardiya = bir satır.
Saatlik kırılım dashboard'da hiçbir yerde gösterilmediği için taşınmaz.

  Uretim : tarih | vardiya | hat | referans | adet | rework | iskarta
  Durus  : tarih | vardiya | hat | sebep | sure_dk | aciklama | op
  Cycle  : hat | referans | cycle_sn
  SMF    : tarih | jx22 | eb2 | doosan | nok

Kullanım:
    DMF_EXCEL=/yol/dosya.xlsx python3 tools/excel_to_csv.py [cikti_dizini]

NOT: Bu araç gerçek Excel dosyasına karşı çalıştırılmadı (dosya elimde yok).
Bu yüzden tutarsızlıkları sessizce geçmez — vardiya toplamı ile saatlik
toplamın uyuşmadığı her vardiyayı ekrana yazar.
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL = os.environ.get('DMF_EXCEL',
                       os.path.join(BASE, 'data', 'DMF_Daily_Followup_New_Version_2026.xlsx'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'sheets-csv')

if not os.path.exists(EXCEL):
    raise SystemExit(f"Excel bulunamadi: {EXCEL}\nDMF_EXCEL ile yol verin.")
try:
    import openpyxl
except ImportError:
    raise SystemExit("openpyxl kurulu degil.  pip install openpyxl")

VARSAYILAN_CT = {'DMF1': 47, 'DMF2': 49, 'DMF3': 46, 'DMF4': 47,
                 'PFW1': 50, 'PFW2': 50, 'PFW3': 50, 'PFW4': 50, 'ITL': 56}

# Hat ailesi başına kolon indeksleri (0 tabanlı) — extract_excel.py ile aynı.
DUZEN = {
    'DMF': dict(bas=3, vardiya=2, ref=3,  adet=4,  vtoplam=5,  rework=18, iskarta=20),
    'PFW': dict(bas=3, vardiya=3, ref=4,  adet=10, vtoplam=11, rework=None, iskarta=None),
    'ITL': dict(bas=4, vardiya=2, ref=3,  adet=10, vtoplam=11, rework=None, iskarta=None),
}
AILE = {h: ('DMF' if h.startswith('DMF') else 'PFW' if h.startswith('PFW') else 'ITL')
        for h in VARSAYILAN_CT}


def sayi(v):
    if v is None or v == '':
        return 0.0
    try:
        return float(str(v).replace(',', '.'))
    except (TypeError, ValueError):
        return 0.0


def hucre(row, i):
    return row[i] if i is not None and len(row) > i else None


print(f"Excel: {EXCEL}")
wb = openpyxl.load_workbook(EXCEL, read_only=True, data_only=True)
os.makedirs(OUT, exist_ok=True)

uretim = defaultdict(lambda: {'referans': '', 'adet': 0.0, 'vtoplam': 0.0,
                              'rework': 0.0, 'iskarta': 0.0})
uyarilar = []

for hat, aile in AILE.items():
    if hat not in wb.sheetnames:
        uyarilar.append(f"{hat}: sekme yok, atlandı")
        continue
    d = DUZEN[aile]
    for row in wb[hat].iter_rows(min_row=d['bas'], values_only=True):
        t = hucre(row, 0)
        if not isinstance(t, datetime):
            continue
        ds = t.strftime('%Y-%m-%d')
        v = str(hucre(row, d['vardiya']) or '').strip().upper()
        if v not in ('A', 'B', 'C'):
            continue
        k = (ds, v, hat)
        rec = uretim[k]

        rec['adet'] += sayi(hucre(row, d['adet']))
        vt = sayi(hucre(row, d['vtoplam']))
        if vt > 0 and rec['vtoplam'] == 0:
            rec['vtoplam'] = vt          # extract_excel.py "ilk non-zero" davranışı
        rec['rework']  += sayi(hucre(row, d['rework']))
        rec['iskarta'] += sayi(hucre(row, d['iskarta']))

        ref = str(hucre(row, d['ref']) or '').strip()
        # "Çalışma Yok" gibi parça numarası olmayan değerler elenir.
        if ref and ref != 'None' and ' ' not in ref:
            rec['referanslar'] = rec.get('referanslar', set())
            rec['referanslar'].add(ref)

satirlar_uretim = []
sapan = 0
for (ds, v, hat), r in sorted(uretim.items()):
    refs = sorted(r.get('referanslar', set()))
    if len(refs) > 1:
        uyarilar.append(f"{ds} {hat} vardiya {v}: birden çok referans {refs} — ilki alındı")
    adet = r['adet']
    # Saatlik toplam ile sayfadaki "vardiya toplam" ayrışıyorsa bildir:
    # kpi.toplam saatlik toplamdan, TRP vardiya toplamından hesaplanıyordu.
    if r['vtoplam'] > 0 and abs(r['vtoplam'] - adet) > max(1, adet * 0.02):
        sapan += 1
        if sapan <= 10:
            uyarilar.append(f"{ds} {hat} {v}: saatlik toplam {adet:.0f} ≠ "
                            f"vardiya toplam {r['vtoplam']:.0f}")
    if adet <= 0 and r['rework'] <= 0 and r['iskarta'] <= 0:
        continue
    satirlar_uretim.append([ds, v, hat, refs[0] if refs else '',
                            round(adet), round(r['rework']), round(r['iskarta'])])

# ── Duruş ────────────────────────────────────────────────────────────────────
satirlar_durus = []
if 'Duruş Süre&Sebep' in wb.sheetnames:
    for row in wb['Duruş Süre&Sebep'].iter_rows(min_row=2, values_only=True):
        t = hucre(row, 0)
        if not isinstance(t, datetime):
            continue
        sure = sayi(hucre(row, 4))
        if sure <= 0:
            continue
        satirlar_durus.append([
            t.strftime('%Y-%m-%d'),
            str(hucre(row, 1) or '').strip().upper(),
            str(hucre(row, 3) or '').strip(),
            str(hucre(row, 2) or 'Bilinmiyor').strip(),
            round(sure, 1),
            str(hucre(row, 5) or '')[:500],
            str(hucre(row, 6) or ''),
        ])
    satirlar_durus.sort(key=lambda r: r[0], reverse=True)
else:
    uyarilar.append("'Duruş Süre&Sebep' sekmesi yok")

# ── SMF ──────────────────────────────────────────────────────────────────────
satirlar_smf = []
if 'SMF-DOOSAN' in wb.sheetnames:
    for row in wb['SMF-DOOSAN'].iter_rows(min_row=3, values_only=True):
        t = hucre(row, 0)
        if not isinstance(t, datetime):
            continue
        jx, eb = sayi(hucre(row, 5)), sayi(hucre(row, 9))
        if jx + eb <= 0:
            continue
        satirlar_smf.append([t.strftime('%Y-%m-%d'), round(jx), round(eb),
                             round(sayi(hucre(row, 14))), round(sayi(hucre(row, 4)))])
else:
    uyarilar.append("'SMF-DOOSAN' sekmesi yok")

# ── Cycle ────────────────────────────────────────────────────────────────────
# CYCLE sekmesi varsa referans bazlı değerler okunur; yoksa hat varsayılanları.
satirlar_cycle = [[h, '', ct] for h, ct in VARSAYILAN_CT.items()]
if 'CYCLE' in wb.sheetnames:
    for row in wb['CYCLE'].iter_rows(min_row=2, values_only=True):
        hat = str(hucre(row, 0) or '').strip()
        ref = str(hucre(row, 1) or '').strip()
        sn = sayi(hucre(row, 2))
        if hat in VARSAYILAN_CT and ref and sn > 0:
            satirlar_cycle.append([hat, ref, sn])


def yaz(ad, basliklar, satirlar):
    with open(os.path.join(OUT, ad + '.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(basliklar)
        w.writerows(satirlar)
    print(f"  {ad + '.csv':14s} {len(satirlar):6d} satır")


print(f"\nÇıktı: {OUT}")
yaz('Uretim', ['tarih', 'vardiya', 'hat', 'referans', 'adet', 'rework', 'iskarta'], satirlar_uretim)
yaz('Durus',  ['tarih', 'vardiya', 'hat', 'sebep', 'sure_dk', 'aciklama', 'op'], satirlar_durus)
yaz('Cycle',  ['hat', 'referans', 'cycle_sn'], satirlar_cycle)
yaz('SMF',    ['tarih', 'jx22', 'eb2', 'doosan', 'nok'], satirlar_smf)

if uyarilar:
    print(f"\n⚠ {len(uyarilar)} uyarı:")
    for u in uyarilar[:25]:
        print("   " + u)
    if len(uyarilar) > 25:
        print(f"   … ve {len(uyarilar) - 25} tane daha")
    if sapan:
        print(f"\n   {sapan} vardiyada saatlik toplam ile vardiya toplamı ayrışıyor.")
        print("   Excel'de kpi.toplam saatlikten, TRP vardiya toplamından hesaplanıyordu;")
        print("   normalize şemada tek 'adet' var ve saatlik toplam esas alındı.")
else:
    print("\n✓ uyarı yok")
