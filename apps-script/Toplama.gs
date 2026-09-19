/**
 * DMF Daily — toplama (aggregation) çekirdeği.
 *
 * Saf fonksiyonlar: girdi satır dizileri, çıktı dashboard'ın beklediği JSON.
 * Hiçbir Google API'si çağırmaz — bu sayede Node altında da çalışır ve
 * tools/test_toplama.js ile mevcut data.json'a karşı doğrulanabilir.
 *
 * Şema (Google Sheet sekmeleri):
 *   Uretim : tarih | vardiya | hat | referans | adet | rework | iskarta
 *   Durus  : tarih | vardiya | hat | sebep | sure_dk | aciklama | op
 *   Cycle  : hat | referans | cycle_sn
 *   SMF    : tarih | jx22 | eb2 | doosan | nok
 *
 * Excel'in hat ailesine göre değişen kolon düzeni (DMF/PFW/ITL ayrı) burada
 * normalize edilmiştir: bir vardiya = bir satır. Saatlik kırılım dashboard'da
 * hiçbir yerde gösterilmediği için taşınmadı.
 */

var HATLAR = ['DMF1','DMF2','DMF3','DMF4','PFW1','PFW2','PFW3','PFW4','ITL'];
var VARDIYALAR = ['A','B','C'];
var VARSAYILAN_CT = {
  DMF1:47, DMF2:49, DMF3:46, DMF4:47,
  PFW1:50, PFW2:50, PFW3:50, PFW4:50, ITL:56
};
var VARDIYA_DK = 480;

function sayi_(v) {
  if (v === null || v === undefined || v === '') return 0;
  var n = typeof v === 'number' ? v : parseFloat(String(v).replace(',', '.'));
  return isNaN(n) ? 0 : n;
}

function tarihStr_(v) {
  if (!v) return '';
  if (Object.prototype.toString.call(v) === '[object Date]') {
    var y = v.getFullYear(),
        m = ('0' + (v.getMonth() + 1)).slice(-2),
        d = ('0' + v.getDate()).slice(-2);
    return y + '-' + m + '-' + d;
  }
  return String(v).slice(0, 10);
}

/** ISO hafta etiketi: 2026-H07 */
function haftaEtiketi_(ds) {
  var p = ds.split('-');
  var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  var gun = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - gun);
  var yilBasi = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  var hafta = Math.ceil(((d - yilBasi) / 86400000 + 1) / 7);
  return d.getUTCFullYear() + '-H' + ('0' + hafta).slice(-2);
}

/** Hat + referans için cycle time; referansa özel kayıt yoksa hat varsayılanı. */
function cycleTime_(cycleRows, hat, ref) {
  for (var i = 0; i < cycleRows.length; i++) {
    var c = cycleRows[i];
    if (c.hat === hat && c.referans && ref && String(c.referans) === String(ref)) {
      var s = sayi_(c.cycle_sn);
      if (s > 0) return s;
    }
  }
  for (var j = 0; j < cycleRows.length; j++) {
    if (cycleRows[j].hat === hat && !cycleRows[j].referans) {
      var s2 = sayi_(cycleRows[j].cycle_sn);
      if (s2 > 0) return s2;
    }
  }
  return VARSAYILAN_CT[hat] || 50;
}

function bosKpi_() {
  return { toplam: 0, son_ay: 0, rework: 0, iskarta: 0, ort_trp: null };
}

/**
 * Tüm satırları dashboard'ın tükettiği JSON'a çevirir.
 * Çıktı şekli generate_dashboard.py'nin ürettiği data.json ile birebir aynıdır.
 */
function topla(uretimRows, durusRows, cycleRows, smfRows, guncellemeStr) {
  cycleRows = cycleRows || [];

  // ── Normalize ─────────────────────────────────────────────────────────────
  var uretim = [];
  for (var i = 0; i < uretimRows.length; i++) {
    var r = uretimRows[i];
    var ds = tarihStr_(r.tarih);
    var hat = String(r.hat || '').trim();
    if (!ds || HATLAR.indexOf(hat) < 0) continue;
    var v = String(r.vardiya || '').trim().toUpperCase();
    if (VARDIYALAR.indexOf(v) < 0) v = '';
    var ref = r.referans ? String(r.referans).trim() : '';
    // Excel'deki "Çalışma Yok" gibi parça numarası olmayan değerler elenir.
    if (ref.indexOf(' ') >= 0) ref = '';
    uretim.push({
      tarih: ds, vardiya: v, hat: hat, referans: ref,
      adet: sayi_(r.adet), rework: sayi_(r.rework), iskarta: sayi_(r.iskarta)
    });
  }

  var durus = [];
  for (var j = 0; j < durusRows.length; j++) {
    var d = durusRows[j];
    var dds = tarihStr_(d.tarih);
    var sure = sayi_(d.sure_dk);
    if (!dds || sure <= 0) continue;
    durus.push({
      tarih: dds,
      vardiya: String(d.vardiya || '').trim().toUpperCase(),
      hat: String(d.hat || '').trim(),
      sebep: String(d.sebep || 'Bilinmiyor').trim(),
      sure: Math.round(sure * 10) / 10,
      aciklama: String(d.aciklama || '').slice(0, 90),
      op: d.op === null || d.op === undefined ? '' : String(d.op)
    });
  }

  // ── Referans arama tablosu: duruş kaydına referans iliştirmek için ────────
  var refLookup = {};
  uretim.forEach(function (u) {
    if (u.referans && u.vardiya) refLookup[u.hat + '|' + u.tarih + '|' + u.vardiya] = u.referans;
  });
  durus.forEach(function (d) {
    d.ref = refLookup[d.hat + '|' + d.tarih + '|' + d.vardiya] || '';
  });
  durus.sort(function (a, b) { return a.tarih < b.tarih ? 1 : a.tarih > b.tarih ? -1 : 0; });

  // ── Hat bazında biriktirme ───────────────────────────────────────────────
  var kpi = {}, refProd = {}, trpShifts = {}, vardiyaAylik = {}, aylikProd = {}, haftalikProd = {};
  var aylarSet = {}, haftalarSet = {};

  HATLAR.forEach(function (h) {
    kpi[h] = bosKpi_(); refProd[h] = {}; trpShifts[h] = [];
    vardiyaAylik[h] = {}; aylikProd[h] = {}; haftalikProd[h] = {};
  });

  uretim.forEach(function (u) {
    var h = u.hat, ay = u.tarih.slice(0, 7), hf = haftaEtiketi_(u.tarih);
    aylarSet[ay] = 1; haftalarSet[hf] = 1;

    kpi[h].toplam  += u.adet;
    kpi[h].rework  += u.rework;
    kpi[h].iskarta += u.iskarta;

    aylikProd[h][ay]    = (aylikProd[h][ay] || 0) + u.adet;
    haftalikProd[h][hf] = (haftalikProd[h][hf] || 0) + u.adet;

    if (u.referans && u.adet > 0) refProd[h][u.referans] = (refProd[h][u.referans] || 0) + u.adet;

    if (u.vardiya && u.adet > 0) {
      var teorik = (VARDIYA_DK * 60) / cycleTime_(cycleRows, h, u.referans);
      trpShifts[h].push({ tarih: u.tarih, hafta: hf, ay: ay, vardiya: u.vardiya,
                          vt: u.adet, teorik: teorik, ref: u.referans });
      if (!vardiyaAylik[h][ay]) vardiyaAylik[h][ay] = { A: [], B: [], C: [] };
      vardiyaAylik[h][ay][u.vardiya].push(u.adet);
    }
  });

  var aylar   = Object.keys(aylarSet).sort();
  var haftalar = Object.keys(haftalarSet).sort();
  var sonAy   = aylar.length ? aylar[aylar.length - 1] : null;

  // ── TRP: üretim/teorik oranının ağırlıklı ortalaması (son 4 hafta) ────────
  var son4 = haftalar.slice(-4);
  HATLAR.forEach(function (h) {
    if (sonAy) kpi[h].son_ay = Math.round(aylikProd[h][sonAy] || 0);
    kpi[h].toplam = Math.round(kpi[h].toplam);
    kpi[h].rework = Math.round(kpi[h].rework);
    kpi[h].iskarta = Math.round(kpi[h].iskarta);
    var vt = 0, teorik = 0;
    trpShifts[h].forEach(function (s) {
      if (son4.indexOf(s.hafta) >= 0) { vt += s.vt; teorik += s.teorik; }
    });
    kpi[h].ort_trp = teorik > 0 ? Math.round(vt / teorik * 1000) / 1000 : null;
  });

  // ── Haftalık seriler ─────────────────────────────────────────────────────
  var haftalikUretim = {}, haftalikTrp = {};
  HATLAR.forEach(function (h) {
    haftalikUretim[h] = []; haftalikTrp[h] = [];
    haftalar.forEach(function (hf) {
      haftalikUretim[h].push(Math.round(haftalikProd[h][hf] || 0));
      var vt = 0, te = 0;
      trpShifts[h].forEach(function (s) { if (s.hafta === hf) { vt += s.vt; te += s.teorik; } });
      haftalikTrp[h].push(te > 0 ? Math.round(vt / te * 1000) / 10 : 0);
    });
  });

  // ── Aylık üretim & vardiya ortalamaları ──────────────────────────────────
  var aylikUretim = {}, vardiyaChart = {};
  HATLAR.forEach(function (h) {
    aylikUretim[h] = aylar.map(function (a) { return Math.round(aylikProd[h][a] || 0); });
    vardiyaChart[h] = { A: [], B: [], C: [] };
    aylar.forEach(function (a) {
      VARDIYALAR.forEach(function (v) {
        var lst = (vardiyaAylik[h][a] && vardiyaAylik[h][a][v]) || [];
        var s = 0; lst.forEach(function (x) { s += x; });
        vardiyaChart[h][v].push(lst.length ? Math.round(s / lst.length) : 0);
      });
    });
  });

  // ── Referans dağılımı ────────────────────────────────────────────────────
  var refTop = {}, refTrpAvg = {};
  HATLAR.forEach(function (h) {
    var girdiler = Object.keys(refProd[h]).map(function (r) { return [r, refProd[h][r]]; });
    girdiler.sort(function (a, b) { return b[1] - a[1]; });
    girdiler = girdiler.slice(0, 8);
    refTop[h] = {
      labels: girdiler.map(function (e) { return e[0]; }),
      data:   girdiler.map(function (e) { return Math.round(e[1]); })
    };

    var perRef = {};
    trpShifts[h].forEach(function (s) {
      if (!s.ref) return;
      if (!perRef[s.ref]) perRef[s.ref] = [];
      perRef[s.ref].push(s.vt / s.teorik);
    });
    var rows = [];
    Object.keys(perRef).forEach(function (r) {
      var lst = perRef[r];
      if (lst.length < 3) return;          // en az 3 vardiya
      var s = 0; lst.forEach(function (x) { s += x; });
      rows.push([r, Math.round(s / lst.length * 1000) / 10, lst.length]);
    });
    rows.sort(function (a, b) { return b[1] - a[1]; });
    refTrpAvg[h] = {
      labels: rows.map(function (e) { return e[0]; }),
      trp:    rows.map(function (e) { return e[1]; }),
      shifts: rows.map(function (e) { return e[2]; })
    };
  });

  // ── Duruş toplamları ─────────────────────────────────────────────────────
  var catTot = {}, hatTot = {}, aylikDurus = {}, durusAylarSet = {};
  durus.forEach(function (d) {
    catTot[d.sebep] = (catTot[d.sebep] || 0) + d.sure;
    if (d.hat) hatTot[d.hat] = (hatTot[d.hat] || 0) + d.sure;
    var ay = d.tarih.slice(0, 7);
    durusAylarSet[ay] = 1;
    if (!aylikDurus[ay]) aylikDurus[ay] = {};
    aylikDurus[ay][d.sebep] = (aylikDurus[ay][d.sebep] || 0) + d.sure;
  });
  var sirala_ = function (o) {
    return Object.keys(o).map(function (k) { return [k, o[k]]; })
                  .sort(function (a, b) { return b[1] - a[1]; });
  };
  var paretoCat = sirala_(catTot), paretoHat = sirala_(hatTot);
  var durusAylar = Object.keys(durusAylarSet).sort();
  var aylikDurusYuvarlak = {};
  durusAylar.forEach(function (a) {
    aylikDurusYuvarlak[a] = {};
    Object.keys(aylikDurus[a]).forEach(function (s) {
      aylikDurusYuvarlak[a][s] = Math.round(aylikDurus[a][s]);
    });
  });

  // ── SMF-DOOSAN ───────────────────────────────────────────────────────────
  var smf = [];
  (smfRows || []).forEach(function (r) {
    var ds = tarihStr_(r.tarih);
    var jx = sayi_(r.jx22), eb = sayi_(r.eb2);
    if (ds && (jx + eb) > 0) smf.push({ tarih: ds, jx22: jx, eb2: eb, nok: sayi_(r.nok) });
  });
  smf.sort(function (a, b) { return a.tarih < b.tarih ? -1 : 1; });
  var smfKpi = { jx22_toplam: 0, eb2_toplam: 0, toplam: 0, nok: 0, aktif_gun: smf.length };
  smf.forEach(function (s) {
    smfKpi.jx22_toplam += s.jx22; smfKpi.eb2_toplam += s.eb2; smfKpi.nok += s.nok;
  });
  smfKpi.toplam = smfKpi.jx22_toplam + smfKpi.eb2_toplam;

  return {
    meta: { guncelleme: guncellemeStr || '', hatlar: HATLAR },
    kpi: kpi,
    smf_kpi: smfKpi,
    smf_dates: smf.map(function (s) { return s.tarih; }),
    smf_jx22:  smf.map(function (s) { return s.jx22; }),
    smf_eb2:   smf.map(function (s) { return s.eb2; }),
    smf_total: smf.map(function (s) { return s.jx22 + s.eb2; }),
    haftalik_etiket: haftalar,
    haftalik_uretim: haftalikUretim,
    haftalik_trp: haftalikTrp,
    aylik_etiket: aylar,
    aylik_uretim: aylikUretim,
    vardiya_chart: vardiyaChart,
    ref_top: refTop,
    ref_trp_avg: refTrpAvg,
    pareto_cat_etiket: paretoCat.map(function (e) { return e[0]; }),
    pareto_cat_deger:  paretoCat.map(function (e) { return Math.round(e[1]); }),
    pareto_hat_etiket: paretoHat.map(function (e) { return e[0]; }),
    pareto_hat_deger:  paretoHat.map(function (e) { return Math.round(e[1]); }),
    durus_aylar: durusAylar,
    durus_aylik: aylikDurusYuvarlak,
    son_duruslar: durus
  };
}

// Node altında test edilebilsin diye (Apps Script bu satırı yok sayar).
if (typeof module !== 'undefined') module.exports = { topla: topla, haftaEtiketi_: haftaEtiketi_ };
