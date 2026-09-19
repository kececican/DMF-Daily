/**
 * DMF Daily — Apps Script sunucu katmanı.
 *
 * Sorumluluklar:
 *   • doGet()      — dashboard'ı HtmlService ile servis eder
 *   • verileriGetir() — Sheet'i okuyup Toplama.gs ile JSON'a çevirir (önbellekli)
 *   • *Ekle()      — dashboard formlarından gelen kayıtları Sheet'e yazar
 *   • kurulum()    — sekmeleri ve başlıkları bir kez oluşturur
 *
 * Güvenlik: istemciden gelen hiçbir değere güvenilmez; her yazma
 * sunucu tarafında doğrulanır (dogrula* fonksiyonları).
 */

var SEKMELER = {
  uretim: { ad: 'Uretim', basliklar: ['tarih','vardiya','hat','referans','adet','rework','iskarta','kaydeden','kayit_zamani'] },
  durus:  { ad: 'Durus',  basliklar: ['tarih','vardiya','hat','sebep','sure_dk','aciklama','op','kaydeden','kayit_zamani'] },
  cycle:  { ad: 'Cycle',  basliklar: ['hat','referans','cycle_sn'] },
  smf:    { ad: 'SMF',    basliklar: ['tarih','jx22','eb2','doosan','nok','kaydeden','kayit_zamani'] }
};

var CACHE_ANAHTAR = 'dmf_veri_v1';
var CACHE_SANIYE  = 21600;   // 6 saat; her yazmada geçersiz kılınır
var CACHE_PARCA   = 90000;   // CacheService anahtar başına ~100 KB sınırı

// ── Altyapı ─────────────────────────────────────────────────────────────────

function dosya_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  return id ? SpreadsheetApp.openById(id) : SpreadsheetApp.getActive();
}

function sekme_(anahtar) {
  var tanim = SEKMELER[anahtar];
  var ss = dosya_();
  var sh = ss.getSheetByName(tanim.ad);
  if (!sh) {
    sh = ss.insertSheet(tanim.ad);
    sh.appendRow(tanim.basliklar);
    sh.setFrozenRows(1);
  }
  return sh;
}

/** Sekmeyi başlık adlarına göre nesne dizisine çevirir. */
function satirlar_(anahtar) {
  var sh = sekme_(anahtar);
  var son = sh.getLastRow();
  if (son < 2) return [];
  var basliklar = SEKMELER[anahtar].basliklar;
  var veri = sh.getRange(2, 1, son - 1, basliklar.length).getValues();
  return veri.map(function (r) {
    var o = {};
    basliklar.forEach(function (b, i) { o[b] = r[i]; });
    return o;
  }).filter(function (o) {
    return Object.keys(o).some(function (k) { return o[k] !== '' && o[k] !== null; });
  });
}

/** Sekmeleri ve başlıkları oluşturur. Kurulumda bir kez elle çalıştırılır. */
function kurulum() {
  Object.keys(SEKMELER).forEach(function (k) { sekme_(k); });
  onbellegiTemizle_();
  return 'Sekmeler hazır: ' + Object.keys(SEKMELER).map(function (k) {
    return SEKMELER[k].ad;
  }).join(', ');
}

// ── Önbellek ────────────────────────────────────────────────────────────────

function onbellegiTemizle_() {
  var c = CacheService.getScriptCache();
  var n = Number(c.get(CACHE_ANAHTAR + '_n') || 0);
  var anahtarlar = [CACHE_ANAHTAR + '_n'];
  for (var i = 0; i < n; i++) anahtarlar.push(CACHE_ANAHTAR + '_' + i);
  if (anahtarlar.length) c.removeAll(anahtarlar);
}

function onbellektenOku_() {
  var c = CacheService.getScriptCache();
  var n = Number(c.get(CACHE_ANAHTAR + '_n') || 0);
  if (!n) return null;
  var anahtarlar = [];
  for (var i = 0; i < n; i++) anahtarlar.push(CACHE_ANAHTAR + '_' + i);
  var parcalar = c.getAll(anahtarlar);
  var metin = '';
  for (var j = 0; j < n; j++) {
    var p = parcalar[CACHE_ANAHTAR + '_' + j];
    if (p === null || p === undefined) return null;   // parça düşmüş
    metin += p;
  }
  try { return JSON.parse(metin); } catch (e) { return null; }
}

function onbellegeYaz_(nesne) {
  try {
    var metin = JSON.stringify(nesne);
    var c = CacheService.getScriptCache();
    var yaz = {}, n = 0;
    for (var i = 0; i < metin.length; i += CACHE_PARCA) {
      yaz[CACHE_ANAHTAR + '_' + n] = metin.substr(i, CACHE_PARCA);
      n++;
    }
    yaz[CACHE_ANAHTAR + '_n'] = String(n);
    c.putAll(yaz, CACHE_SANIYE);
  } catch (e) {
    // Önbellek en iyi çaba; başarısızlık veriyi etkilemez.
  }
}

// ── Okuma ───────────────────────────────────────────────────────────────────

/** Dashboard'ın çağırdığı ana fonksiyon. */
function verileriGetir(onbellegiAtla) {
  if (!onbellegiAtla) {
    var hazir = onbellektenOku_();
    if (hazir) return hazir;
  }
  var tz = Session.getScriptTimeZone() || 'Europe/Istanbul';
  var damga = Utilities.formatDate(new Date(), tz, 'dd.MM.yyyy HH:mm');
  var veri = topla(satirlar_('uretim'), satirlar_('durus'),
                   satirlar_('cycle'), satirlar_('smf'), damga);
  onbellegeYaz_(veri);
  return veri;
}

/** Formların açılır listeleri için mevcut değerler. */
function secenekleriGetir() {
  var refler = {}, sebepler = {};
  satirlar_('uretim').forEach(function (u) {
    var h = String(u.hat || '').trim(), r = String(u.referans || '').trim();
    if (!h || !r) return;
    if (!refler[h]) refler[h] = {};
    refler[h][r] = 1;
  });
  satirlar_('durus').forEach(function (d) {
    var s = String(d.sebep || '').trim();
    if (s) sebepler[s] = 1;
  });
  var refListe = {};
  Object.keys(refler).forEach(function (h) { refListe[h] = Object.keys(refler[h]).sort(); });
  return {
    hatlar: HATLAR,
    vardiyalar: VARDIYALAR,
    referanslar: refListe,
    sebepler: Object.keys(sebepler).sort()
  };
}

// ── Doğrulama ───────────────────────────────────────────────────────────────

function hata_(mesaj) { throw new Error(mesaj); }

function dogrulaTarih_(v) {
  var s = String(v || '').trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) hata_('Tarih GG formatında değil (YYYY-AA-GG): ' + s);
  var p = s.split('-'), d = new Date(+p[0], +p[1] - 1, +p[2]);
  if (d.getFullYear() !== +p[0] || d.getMonth() !== +p[1] - 1 || d.getDate() !== +p[2]) {
    hata_('Geçersiz tarih: ' + s);
  }
  var yarin = new Date(); yarin.setDate(yarin.getDate() + 1);
  if (d > yarin) hata_('Tarih gelecekte olamaz: ' + s);
  return s;
}

function dogrulaHat_(v) {
  var s = String(v || '').trim();
  if (HATLAR.indexOf(s) < 0) hata_('Bilinmeyen hat: ' + s);
  return s;
}

function dogrulaVardiya_(v) {
  var s = String(v || '').trim().toUpperCase();
  if (VARDIYALAR.indexOf(s) < 0) hata_('Vardiya A, B veya C olmalı: ' + s);
  return s;
}

function dogrulaSayi_(v, ad, enAz, enCok) {
  var n = typeof v === 'number' ? v : parseFloat(String(v == null ? '' : v).replace(',', '.'));
  if (isNaN(n)) hata_(ad + ' sayı olmalı');
  if (n < enAz) hata_(ad + ' en az ' + enAz + ' olmalı');
  if (enCok !== undefined && n > enCok) hata_(ad + ' en çok ' + enCok + ' olabilir');
  return n;
}

function kullanici_() {
  try { return Session.getActiveUser().getEmail() || 'bilinmiyor'; }
  catch (e) { return 'bilinmiyor'; }
}

/** Yazma işlemlerini seri hale getirir — eşzamanlı ekleme satır ezmesin. */
function kilitli_(fn) {
  var kilit = LockService.getScriptLock();
  if (!kilit.tryLock(20000)) hata_('Sistem meşgul, birkaç saniye sonra tekrar deneyin.');
  try { return fn(); } finally { kilit.releaseLock(); }
}

// ── Yazma ───────────────────────────────────────────────────────────────────

function uretimEkle(k) {
  return kilitli_(function () {
    var tarih   = dogrulaTarih_(k.tarih);
    var vardiya = dogrulaVardiya_(k.vardiya);
    var hat     = dogrulaHat_(k.hat);
    var adet    = dogrulaSayi_(k.adet, 'Üretim adedi', 0, 100000);
    var rework  = dogrulaSayi_(k.rework  || 0, 'Rework', 0, 100000);
    var iskarta = dogrulaSayi_(k.iskarta || 0, 'İskarta', 0, 100000);
    var ref     = String(k.referans || '').trim();
    if (ref.indexOf(' ') >= 0) hata_('Referans boşluk içeremez: ' + ref);

    // Aynı vardiya iki kez girilmesin — TRP'yi bozar.
    var mevcut = satirlar_('uretim').filter(function (u) {
      return tarihStr_(u.tarih) === tarih &&
             String(u.vardiya).trim().toUpperCase() === vardiya &&
             String(u.hat).trim() === hat;
    });
    if (mevcut.length) {
      hata_(tarih + ' ' + hat + ' vardiya ' + vardiya + ' için zaten kayıt var. ' +
            'Düzeltmek için Sheet üzerinden güncelleyin.');
    }

    sekme_('uretim').appendRow([tarih, vardiya, hat, ref, adet, rework, iskarta,
                                kullanici_(), new Date()]);
    onbellegiTemizle_();
    return { ok: true, mesaj: tarih + ' · ' + hat + ' · vardiya ' + vardiya + ' eklendi' };
  });
}

function durusEkle(k) {
  return kilitli_(function () {
    var tarih   = dogrulaTarih_(k.tarih);
    var vardiya = dogrulaVardiya_(k.vardiya);
    var hat     = dogrulaHat_(k.hat);
    var sure    = dogrulaSayi_(k.sure_dk, 'Duruş süresi', 0.1, 1440);
    var sebep   = String(k.sebep || '').trim();
    if (!sebep) hata_('Duruş sebebi boş olamaz');
    sekme_('durus').appendRow([tarih, vardiya, hat, sebep, Math.round(sure * 10) / 10,
                               String(k.aciklama || '').slice(0, 500),
                               String(k.op || ''), kullanici_(), new Date()]);
    onbellegiTemizle_();
    return { ok: true, mesaj: sure + ' dk · ' + sebep + ' · ' + hat + ' eklendi' };
  });
}

function smfEkle(k) {
  return kilitli_(function () {
    var tarih = dogrulaTarih_(k.tarih);
    var jx22  = dogrulaSayi_(k.jx22 || 0, 'JX22', 0, 100000);
    var eb2   = dogrulaSayi_(k.eb2  || 0, 'EB2',  0, 100000);
    var doos  = dogrulaSayi_(k.doosan || 0, 'Doosan', 0, 100000);
    var nok   = dogrulaSayi_(k.nok  || 0, 'NOK',  0, 100000);
    if (jx22 + eb2 <= 0) hata_('JX22 ve EB2 birlikte sıfır olamaz');

    var mevcut = satirlar_('smf').filter(function (s) { return tarihStr_(s.tarih) === tarih; });
    if (mevcut.length) hata_(tarih + ' için zaten SMF kaydı var.');

    sekme_('smf').appendRow([tarih, jx22, eb2, doos, nok, kullanici_(), new Date()]);
    onbellegiTemizle_();
    return { ok: true, mesaj: tarih + ' SMF kaydı eklendi' };
  });
}

/** Cycle time ekler ya da mevcut (hat, referans) satırını günceller. */
function cycleKaydet(k) {
  return kilitli_(function () {
    var hat = dogrulaHat_(k.hat);
    var ref = String(k.referans || '').trim();
    var sn  = dogrulaSayi_(k.cycle_sn, 'Cycle time', 1, 3600);

    var sh = sekme_('cycle');
    var son = sh.getLastRow();
    if (son >= 2) {
      var veri = sh.getRange(2, 1, son - 1, 3).getValues();
      for (var i = 0; i < veri.length; i++) {
        if (String(veri[i][0]).trim() === hat && String(veri[i][1]).trim() === ref) {
          sh.getRange(i + 2, 3).setValue(sn);
          onbellegiTemizle_();
          return { ok: true, mesaj: hat + (ref ? ' · ' + ref : ' varsayılanı') + ' güncellendi: ' + sn + ' sn' };
        }
      }
    }
    sh.appendRow([hat, ref, sn]);
    onbellegiTemizle_();
    return { ok: true, mesaj: hat + (ref ? ' · ' + ref : ' varsayılanı') + ' eklendi: ' + sn + ' sn' };
  });
}

// ── Servis ──────────────────────────────────────────────────────────────────

function include(dosyaAdi) {
  return HtmlService.createHtmlOutputFromFile(dosyaAdi).getContent();
}

function doGet() {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('DMF Daily — Üretim Takip')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}
