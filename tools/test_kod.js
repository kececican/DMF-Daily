/**
 * apps-script/Kod.gs doğrulama ve yazma mantığını, Google API'lerini taklit
 * ederek test eder. GAS çalıştırmaz — amaç sunucu tarafı kurallarının
 * (tarih/hat/vardiya doğrulaması, çift kayıt engeli, önbellek geçersizleştirme,
 * kilit) doğru davrandığını kanıtlamak.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const BASE = path.join(__dirname, '..');

// ── Google API taklidi ──────────────────────────────────────────────────────
function sahteSheet(ad) {
  const satirlar = [];
  return {
    ad, satirlar,
    getLastRow: () => satirlar.length,
    setFrozenRows: () => {},
    appendRow: r => satirlar.push(r.slice()),
    getRange(r, c, nr, nc) {
      return {
        getValues: () => satirlar.slice(r - 1, r - 1 + nr).map(x => {
          const s = x.slice(c - 1, c - 1 + nc);
          while (s.length < nc) s.push('');
          return s;
        }),
        setValue: v => { satirlar[r - 1][c - 1] = v; },
      };
    },
  };
}

function kurCtx() {
  const sheetler = {};
  const cache = {};
  let kilitAlindi = 0;
  const ctx = {
    console,
    Date, Math, JSON, String, Number, Object, Array, isNaN, parseFloat,
    Error, RegExp,
    SpreadsheetApp: {
      getActive: () => ({
        getSheetByName: n => sheetler[n] || null,
        insertSheet: n => (sheetler[n] = sahteSheet(n)),
      }),
      openById: () => ctx.SpreadsheetApp.getActive(),
    },
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => null }) },
    CacheService: {
      getScriptCache: () => ({
        get: k => (k in cache ? cache[k] : null),
        getAll: ks => Object.fromEntries(ks.map(k => [k, k in cache ? cache[k] : null])),
        putAll: (o) => Object.assign(cache, o),
        removeAll: ks => ks.forEach(k => delete cache[k]),
      }),
    },
    LockService: {
      getScriptLock: () => ({ tryLock: () => { kilitAlindi++; return true; }, releaseLock: () => {} }),
    },
    Session: {
      getActiveUser: () => ({ getEmail: () => 'test@valeo.com' }),
      getScriptTimeZone: () => 'Europe/Istanbul',
    },
    Utilities: { formatDate: () => '19.09.2026 10:00' },
    HtmlService: { createHtmlOutputFromFile: () => ({ getContent: () => '' }) },
    _sheetler: sheetler, _cache: cache, _kilit: () => kilitAlindi,
  };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(BASE, 'apps-script/Toplama.gs'), 'utf8')
    .replace(/if \(typeof module[\s\S]*$/, ''), ctx);
  vm.runInContext(fs.readFileSync(path.join(BASE, 'apps-script/Kod.gs'), 'utf8'), ctx);
  return ctx;
}

// ── Test yardımcıları ───────────────────────────────────────────────────────
let gecti = 0, kaldi = 0;
const ok = (ad, kosul, detay) => {
  if (kosul) { console.log('  ✅ ' + ad); gecti++; }
  else { console.log('  ❌ ' + ad + (detay ? '  → ' + detay : '')); kaldi++; }
};
const reddetmeli = (ad, fn, parca) => {
  try { fn(); ok(ad, false, 'hata fırlatmadı'); }
  catch (e) {
    ok(ad + '  («' + e.message.slice(0, 48) + '»)',
       !parca || e.message.indexOf(parca) >= 0, e.message);
  }
};

const C = kurCtx();

console.log('\n═══ 1. Kurulum ═══');
const kurulumSonuc = C.kurulum();
ok('4 sekme oluştu', Object.keys(C._sheetler).length === 4, Object.keys(C._sheetler).join(','));
ok('başlıklar yazıldı', C._sheetler.Uretim.satirlar[0][0] === 'tarih');
ok('kurulum mesajı', /Uretim/.test(kurulumSonuc));

console.log('\n═══ 2. Üretim ekleme — geçerli ═══');
const s1 = C.uretimEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', referans: 'R1', adet: 600, rework: 5, iskarta: 1 });
ok('ok:true döndü', s1.ok === true);
ok('satır yazıldı', C._sheetler.Uretim.satirlar.length === 2);
ok('kaydeden dolduruldu', C._sheetler.Uretim.satirlar[1][7] === 'test@valeo.com');
ok('kilit alındı', C._kilit() > 0);

console.log('\n═══ 3. Üretim ekleme — doğrulama reddetmeli ═══');
reddetmeli('bilinmeyen hat', () => C.uretimEkle({ tarih: '2026-06-02', vardiya: 'A', hat: 'DMF9', adet: 1 }), 'Bilinmeyen hat');
reddetmeli('geçersiz vardiya', () => C.uretimEkle({ tarih: '2026-06-02', vardiya: 'D', hat: 'DMF1', adet: 1 }), 'Vardiya');
reddetmeli('bozuk tarih formatı', () => C.uretimEkle({ tarih: '01.06.2026', vardiya: 'A', hat: 'DMF1', adet: 1 }), 'formatında');
reddetmeli('olmayan tarih (31 Şubat)', () => C.uretimEkle({ tarih: '2026-02-31', vardiya: 'A', hat: 'DMF1', adet: 1 }), 'Geçersiz tarih');
reddetmeli('gelecek tarih', () => C.uretimEkle({ tarih: '2099-01-01', vardiya: 'A', hat: 'DMF1', adet: 1 }), 'gelecekte');
reddetmeli('negatif adet', () => C.uretimEkle({ tarih: '2026-06-02', vardiya: 'A', hat: 'DMF1', adet: -5 }), 'en az');
reddetmeli('sayı olmayan adet', () => C.uretimEkle({ tarih: '2026-06-02', vardiya: 'A', hat: 'DMF1', adet: 'çok' }), 'sayı olmalı');
reddetmeli('boşluklu referans', () => C.uretimEkle({ tarih: '2026-06-02', vardiya: 'A', hat: 'DMF1', referans: 'Çalışma Yok', adet: 1 }), 'boşluk');
reddetmeli('AYNI vardiya iki kez', () => C.uretimEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', adet: 500 }), 'zaten kayıt var');
ok('reddedilenler satır yazmadı', C._sheetler.Uretim.satirlar.length === 2, 'satır=' + C._sheetler.Uretim.satirlar.length);

console.log('\n═══ 4. Duruş / SMF / Cycle ═══');
ok('duruş eklendi', C.durusEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', sebep: 'Arıza', sure_dk: 30, aciklama: 'test', op: '10' }).ok);
reddetmeli('boş sebep', () => C.durusEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', sebep: '', sure_dk: 5 }), 'sebebi boş');
reddetmeli('sıfır süre', () => C.durusEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', sebep: 'Arıza', sure_dk: 0 }), 'en az');
reddetmeli('1 günden uzun duruş', () => C.durusEkle({ tarih: '2026-06-01', vardiya: 'A', hat: 'DMF1', sebep: 'Arıza', sure_dk: 2000 }), 'en çok');
ok('SMF eklendi', C.smfEkle({ tarih: '2026-06-01', jx22: 300, eb2: 400, nok: 5 }).ok);
reddetmeli('aynı güne ikinci SMF', () => C.smfEkle({ tarih: '2026-06-01', jx22: 1 }), 'zaten SMF kaydı');
reddetmeli('SMF hepsi sıfır', () => C.smfEkle({ tarih: '2026-06-02', jx22: 0, eb2: 0 }), 'sıfır olamaz');
ok('cycle eklendi', C.cycleKaydet({ hat: 'DMF1', referans: '', cycle_sn: 47 }).ok);
const cy = C.cycleKaydet({ hat: 'DMF1', referans: '', cycle_sn: 45 });
ok('cycle GÜNCELLEDİ (yeni satır değil)', /güncellendi/.test(cy.mesaj) && C._sheetler.Cycle.satirlar.length === 2,
   'satır=' + C._sheetler.Cycle.satirlar.length);

console.log('\n═══ 5. Okuma & önbellek ═══');
const v1 = C.verileriGetir();
ok('JSON şekli doğru', Array.isArray(v1.meta.hatlar) && v1.meta.hatlar.length === 9);
ok('üretim yansıdı (600)', v1.kpi.DMF1.toplam === 600, 'toplam=' + v1.kpi.DMF1.toplam);
ok('duruş yansıdı', v1.son_duruslar.length === 1);
ok('duruşa referans iliştirildi', v1.son_duruslar[0].ref === 'R1', 'ref=' + v1.son_duruslar[0].ref);
ok('cycle güncellemesi TRP\'ye yansıdı (45 sn)',
   v1.kpi.DMF1.ort_trp === Math.round(600 / (480 * 60 / 45) * 1000) / 1000, 'trp=' + v1.kpi.DMF1.ort_trp);
ok('önbelleğe yazıldı', Object.keys(C._cache).some(k => k.startsWith('dmf_veri_v1')));
const v2 = C.verileriGetir();
ok('ikinci çağrı önbellekten', JSON.stringify(v1) === JSON.stringify(v2));
C.uretimEkle({ tarih: '2026-06-01', vardiya: 'B', hat: 'DMF1', referans: 'R1', adet: 400 });
ok('yazma önbelleği temizledi', Object.keys(C._cache).length === 0, 'anahtar=' + Object.keys(C._cache).length);
ok('yeni veri görünür (1000)', C.verileriGetir().kpi.DMF1.toplam === 1000);

console.log('\n═══ 6. Form seçenekleri ═══');
const sec = C.secenekleriGetir();
ok('hat listesi', sec.hatlar.length === 9);
ok('referanslar hat bazında', JSON.stringify(sec.referanslar.DMF1) === '["R1"]', JSON.stringify(sec.referanslar));
ok('sebepler mevcut kayıtlardan', sec.sebepler.indexOf('Arıza') >= 0);

console.log(`\n═══ SONUÇ: ${gecti} geçti, ${kaldi} kaldı ═══`);
process.exit(kaldi ? 1 : 0);
