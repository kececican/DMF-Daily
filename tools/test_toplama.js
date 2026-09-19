/**
 * apps-script/Toplama.gs'i mevcut data.json'a karşı doğrular.
 *
 * Üretim satırları göç edilemediği için (bkz. datajson_to_csv.py) duruş ve SMF
 * çıktıları birebir karşılaştırılır; üretim tarafı sentetik veriyle,
 * elle hesaplanmış beklenen değerlere karşı test edilir.
 */
const fs = require('fs');
const path = require('path');
const { topla } = require('../apps-script/Toplama.gs');

const BASE = path.join(__dirname, '..');
const D = JSON.parse(fs.readFileSync(path.join(BASE, 'dashboard/data.json'), 'utf8'));

/** RFC4180 CSV: tırnak içindeki virgül VE satır sonlarını doğru çözer.
 *  (Duruş açıklamalarının 6'sında gömülü \n var — naif split('\n') bunları böler.) */
function csv(ad) {
  const metin = fs.readFileSync(path.join(BASE, 'sheets-csv', ad + '.csv'), 'utf8')
    .replace(/^\uFEFF/, '');
  const satirlar = [];
  let hucre = '', satir = [], q = false;
  for (let i = 0; i < metin.length; i++) {
    const ch = metin[i];
    if (q) {
      if (ch === '"') { if (metin[i + 1] === '"') { hucre += '"'; i++; } else q = false; }
      else hucre += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { satir.push(hucre); hucre = ''; }
    else if (ch === '\n') { satir.push(hucre); satirlar.push(satir); satir = []; hucre = ''; }
    else if (ch !== '\r') hucre += ch;
  }
  if (hucre !== '' || satir.length) { satir.push(hucre); satirlar.push(satir); }
  if (!satirlar.length) return [];
  const head = satirlar.shift();
  return satirlar
    .filter(r => r.some(c => c !== ''))
    .map(r => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}

let gecti = 0, kaldi = 0;

// JSON nesnelerinde anahtar SIRASI anlamsız (dashboard hepsine anahtarla
// erişir), dizilerde anlamlı. Karşılaştırmadan önce nesne anahtarları
// sıralanır; dizi sırası korunur.
const kanonik = v => {
  if (Array.isArray(v)) return v.map(kanonik);
  if (v && typeof v === 'object') {
    return Object.keys(v).sort().reduce((o, k) => {
      if (v[k] !== undefined) o[k] = kanonik(v[k]);
      return o;
    }, {});
  }
  return v;
};
const esit = (ad, a, b) => {
  const ok = JSON.stringify(kanonik(a)) === JSON.stringify(kanonik(b));
  console.log(`  ${ok ? '✅' : '❌'} ${ad}`);
  if (!ok) {
    console.log('     beklenen:', JSON.stringify(kanonik(b)).slice(0, 260));
    console.log('     çıkan   :', JSON.stringify(kanonik(a)).slice(0, 260));
    kaldi++;
  } else gecti++;
};

console.log('\n═══ 1. GERÇEK VERİ — duruş & SMF (1074 + 24 satır) ═══');
const out = topla(csv('Uretim'), csv('Durus'), csv('Cycle'), csv('SMF'), D.meta.guncelleme);

esit('pareto_cat_etiket', out.pareto_cat_etiket, D.pareto_cat_etiket);
esit('pareto_cat_deger',  out.pareto_cat_deger,  D.pareto_cat_deger);
esit('pareto_hat_etiket', out.pareto_hat_etiket, D.pareto_hat_etiket);
esit('pareto_hat_deger',  out.pareto_hat_deger,  D.pareto_hat_deger);
esit('durus_aylar',       out.durus_aylar,       D.durus_aylar);
esit('durus_aylik',       out.durus_aylik,       D.durus_aylik);
esit('duruş kayıt sayısı', out.son_duruslar.length, D.son_duruslar.length);

// ref alanı Uretim'den türetilir; Uretim boş olduğu için hariç tutulur
const siy = r => ({ ...r, ref: undefined });
esit('duruş kayıtları (ref hariç)',
     out.son_duruslar.map(siy), D.son_duruslar.map(siy));

esit('smf_dates', out.smf_dates, D.smf_dates);
esit('smf_jx22',  out.smf_jx22,  D.smf_jx22);
esit('smf_eb2',   out.smf_eb2,   D.smf_eb2);
esit('smf_total', out.smf_total, D.smf_total);
esit('smf aktif gün', out.smf_kpi.aktif_gun, D.smf_kpi.aktif_gun);
esit('smf jx22 toplam', out.smf_kpi.jx22_toplam, D.smf_kpi.jx22_toplam);
esit('smf eb2 toplam',  out.smf_kpi.eb2_toplam,  D.smf_kpi.eb2_toplam);

console.log('\n═══ 2. SENTETİK ÜRETİM — elle hesaplanmış beklenenler ═══');
// DMF1 cycle 47 sn → teorik vardiya = 480*60/47 = 612.766
// 2026-06-01 (Pazartesi, 2026-H23): A=600, B=500 | 2026-06-02: A=400
const u = [
  { tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', referans: 'R1', adet: 600, rework: 10, iskarta: 2 },
  { tarih: '2026-06-01', vardiya: 'B', hat: 'DMF1', referans: 'R1', adet: 500, rework: 5,  iskarta: 1 },
  { tarih: '2026-06-02', vardiya: 'A', hat: 'DMF1', referans: 'R2', adet: 400, rework: 0,  iskarta: 0 },
];
const dd = [{ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', sebep: 'Arıza', sure_dk: 30, aciklama: 'test', op: '10' }];
const o2 = topla(u, dd, csv('Cycle'), [], '');

const teorik = 480 * 60 / 47;
esit('DMF1 toplam üretim', o2.kpi.DMF1.toplam, 1500);
esit('DMF1 rework', o2.kpi.DMF1.rework, 15);
esit('DMF1 iskarta', o2.kpi.DMF1.iskarta, 3);
esit('DMF1 TRP (ağırlıklı: 1500/(3×teorik))',
     o2.kpi.DMF1.ort_trp, Math.round(1500 / (3 * teorik) * 1000) / 1000);
esit('aylık etiket', o2.aylik_etiket, ['2026-06']);
esit('DMF1 aylık üretim', o2.aylik_uretim.DMF1, [1500]);
esit('DMF1 vardiya A ortalaması ((600+400)/2)', o2.vardiya_chart.DMF1.A, [500]);
esit('DMF1 vardiya B ortalaması', o2.vardiya_chart.DMF1.B, [500]);
esit('DMF1 vardiya C (veri yok)', o2.vardiya_chart.DMF1.C, [0]);
esit('DMF1 ref_top', o2.ref_top.DMF1, { labels: ['R1', 'R2'], data: [1100, 400] });
esit('ref_trp_avg (3 vardiyadan az → boş)', o2.ref_trp_avg.DMF1.labels, []);
esit('duruşa referans iliştirildi', o2.son_duruslar[0].ref, 'R1');
esit('PFW1 boş KPI', o2.kpi.PFW1, { toplam: 0, son_ay: 0, rework: 0, iskarta: 0, ort_trp: null });

console.log('\n═══ 3. TRP FORMÜLÜ — Python ile denklik ═══');
// Python (extract_excel.py) ort_trp'yi vardiya oranlarının DÜZ ortalaması
// olarak hesaplar; burada AĞIRLIKLI (Σüretim/Σteorik) hesaplanıyor. Cycle time
// hat başına sabitken ikisi özdeştir — göçte sayılar değişmemeli. Referans
// bazlı cycle time girilirse ağırlıklı olan doğru sonucu verir.
const duzOrtalama = (satirlar, ct) => {
  const teorik = 480 * 60 / ct;
  const oranlar = satirlar.map(r => r.adet / teorik);
  return Math.round(oranlar.reduce((a, b) => a + b, 0) / oranlar.length * 1000) / 1000;
};
const sabitCt = [{ hat: 'DMF1', referans: '', cycle_sn: 47 }];
const karisik = [
  { tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', referans: 'R1', adet: 600 },
  { tarih: '2026-06-01', vardiya: 'B', hat: 'DMF1', referans: 'R1', adet: 350 },
  { tarih: '2026-06-02', vardiya: 'A', hat: 'DMF1', referans: 'R1', adet: 512 },
  { tarih: '2026-06-02', vardiya: 'B', hat: 'DMF1', referans: 'R1', adet: 480 },
];
const o3 = topla(karisik, [], sabitCt, [], '');
esit('sabit cycle time → ağırlıklı = düz ortalama (Python ile aynı)',
     o3.kpi.DMF1.ort_trp, duzOrtalama(karisik, 47));

// Referans bazlı cycle time girilince ayrışırlar; ağırlıklı olan doğrudur.
const refCt = [{ hat: 'DMF1', referans: '', cycle_sn: 47 },
               { hat: 'DMF1', referans: 'YAVAS', cycle_sn: 94 }];
const ikiRef = [
  { tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', referans: 'R1',    adet: 600 },
  { tarih: '2026-06-01', vardiya: 'B', hat: 'DMF1', referans: 'YAVAS', adet: 300 },
];
const o4 = topla(ikiRef, [], refCt, [], '');
const beklenen = Math.round(900 / (480 * 60 / 47 + 480 * 60 / 94) * 1000) / 1000;
esit('referans bazlı cycle time → ağırlıklı TRP doğru', o4.kpi.DMF1.ort_trp, beklenen);

console.log('\n═══ 4. son_ay — sabit tarih yerine veriden ═══');
// Python'da son_ay eşiği koda gömülü: ds >= '2026-06-01'. Temmuz verisi
// girildiğinde sessizce yanlışlanırdı. Burada veri içindeki son ay kullanılır.
const ikiAy = [
  { tarih: '2026-06-20', vardiya: 'A', hat: 'DMF1', referans: 'R', adet: 100 },
  { tarih: '2026-07-05', vardiya: 'A', hat: 'DMF1', referans: 'R', adet: 250 },
];
esit('son_ay = veri içindeki son ay (Temmuz)', topla(ikiAy, [], sabitCt, [], '').kpi.DMF1.son_ay, 250);

console.log(`\n═══ SONUÇ: ${gecti} geçti, ${kaldi} kaldı ═══`);
process.exit(kaldi ? 1 : 0);
