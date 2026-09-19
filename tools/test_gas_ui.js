/**
 * GAS arayüzünü uçtan uca test eder.
 *
 * google.script.run çağrıları Playwright üzerinden Node'daki GERÇEK Kod.gs'e
 * yönlendirilir (Google API'leri taklit edilmiş, Sheet bellekte). Yani
 * tarayıcıdaki form → sunucu doğrulaması → Toplama.gs → grafikler yolunun
 * tamamı çalışır; yalnız Google'ın kendi altyapısı taklittir.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const BASE = path.join(__dirname, '..');
const SP = process.env.SP || '/tmp';

// ── Node tarafı: gerçek Kod.gs + sahte Google API'leri ──────────────────────
function sahteSheet(ad) {
  const s = [];
  return { ad, satirlar: s, getLastRow: () => s.length, setFrozenRows() {},
    appendRow: r => s.push(r.slice()),
    getRange(r, c, nr, nc) {
      return { getValues: () => s.slice(r - 1, r - 1 + nr).map(x => {
                 const o = x.slice(c - 1, c - 1 + nc);
                 while (o.length < nc) o.push(''); return o; }),
               setValue: v => { s[r - 1][c - 1] = v; } };
    } };
}
function sunucu() {
  const sheetler = {}, cache = {};
  const ctx = { console, Date, Math, JSON, String, Number, Object, Array, isNaN, parseFloat, Error, RegExp,
    SpreadsheetApp: { getActive: () => ({ getSheetByName: n => sheetler[n] || null,
                                          insertSheet: n => (sheetler[n] = sahteSheet(n)) }),
                      openById: () => ctx.SpreadsheetApp.getActive() },
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => null }) },
    CacheService: { getScriptCache: () => ({ get: k => (k in cache ? cache[k] : null),
      getAll: ks => Object.fromEntries(ks.map(k => [k, k in cache ? cache[k] : null])),
      putAll: o => Object.assign(cache, o), removeAll: ks => ks.forEach(k => delete cache[k]) }) },
    LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock() {} }) },
    Session: { getActiveUser: () => ({ getEmail: () => 'test@valeo.com' }), getScriptTimeZone: () => 'Europe/Istanbul' },
    Utilities: { formatDate: () => '19.09.2026 10:00' },
    HtmlService: { createHtmlOutputFromFile: () => ({ getContent: () => '' }) },
    _sheetler: sheetler };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(BASE, 'apps-script/Toplama.gs'), 'utf8')
    .replace(/if \(typeof module[\s\S]*$/, ''), ctx);
  vm.runInContext(fs.readFileSync(path.join(BASE, 'apps-script/Kod.gs'), 'utf8'), ctx);
  ctx.kurulum();
  return ctx;
}

// ── Sayfa: include() çözülür, google.script.run köprülenir ──────────────────
function sayfaHtml() {
  const idx = fs.readFileSync(path.join(BASE, 'apps-script/index.html'), 'utf8');
  const st = fs.readFileSync(path.join(BASE, 'apps-script/styles.html'), 'utf8');
  const kopru = `<script>
    window.google = { script: { run: new Proxy({}, {
      get(_, fn) {
        if (fn === 'withSuccessHandler') return h => (window.__ok = h, google.script.run);
        if (fn === 'withFailureHandler') return h => (window.__err = h, google.script.run);
        return function (...a) {
          const ok = window.__ok, err = window.__err;
          window.__ok = window.__err = null;
          __cagir(String(fn), JSON.stringify(a)).then(r => {
            const o = JSON.parse(r);
            if (o.hata) { if (err) err(new Error(o.hata)); }
            else if (ok) ok(o.sonuc);
          });
        };
      } }) } };
  </script>`;
  return idx.replace("<?!= include('styles'); ?>", st).replace('</head>', kopru + '\n</head>');
}

(async () => {
  const S = sunucu();
  let gecti = 0, kaldi = 0;
  const ok = (ad, k, d) => { if (k) { console.log('  ✅ ' + ad); gecti++; }
                             else { console.log('  ❌ ' + ad + (d ? '  → ' + d : '')); kaldi++; } };

  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 }, colorScheme: 'light' });
  const errs = [];
  page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE: ' + m.text()); });

  await page.exposeFunction('__cagir', (fn, argsJson) => {
    try { return JSON.stringify({ sonuc: S[fn].apply(null, JSON.parse(argsJson)) }); }
    catch (e) { return JSON.stringify({ hata: e.message }); }
  });

  const tmp = path.join(SP, 'gas-test.html');
  fs.writeFileSync(tmp, sayfaHtml());
  await page.goto('file://' + tmp);
  await page.waitForTimeout(1500);

  console.log('\n═══ 1. Açılış — veri sunucudan ═══');
  ok('veri yüklendi (yükleniyor mesajı gitti)', !(await page.textContent('#screen-e1')).includes('yükleniyor'));
  ok('güncelleme damgası geldi', (await page.textContent('#upd-date')).includes('19.09.2026'));
  ok('Veri Girişi sekmesi var', await page.locator('#tab-e7').count() === 1);
  ok('boş Sheet → KPI kartları basıldı', await page.locator('.kcard').count() >= 9,
     'kart=' + await page.locator('.kcard').count());

  console.log('\n═══ 2. Üretim formu — geçerli kayıt ═══');
  await page.click('#tab-e7'); await page.waitForTimeout(500);
  ok('bugünün tarihi otomatik doldu', (await page.inputValue('#u-tarih')).length === 10);
  ok('hat listesi sunucudan geldi', await page.locator('#u-hat option').count() === 9);
  await page.fill('#u-tarih', '2026-06-01');
  await page.selectOption('#u-vardiya', 'A');
  await page.selectOption('#u-hat', 'DMF1');
  await page.fill('#u-referans', 'R1');
  await page.fill('#u-adet', '600');
  await page.fill('#u-rework', '5');
  await page.click('form:has(#u-adet) button[type=submit]');
  await page.waitForTimeout(900);
  const m1 = await page.textContent('#msg-uretim');
  ok('başarı mesajı gösterildi', m1.startsWith('✓'), m1);
  ok('Sheet\'e satır yazıldı', S._sheetler.Uretim.satirlar.length === 2,
     'satır=' + S._sheetler.Uretim.satirlar.length);
  ok('adet alanı temizlendi', (await page.inputValue('#u-adet')) === '');

  console.log('\n═══ 3. Grafikler kendiliğinden güncellendi mi ═══');
  await page.click('#tab-e1'); await page.waitForTimeout(900);
  const kpiMetin = await page.textContent('#kpi-grid');
  ok('KPI kartında yeni üretim görünüyor (600)', kpiMetin.includes('600'), kpiMetin.slice(0, 120));

  console.log('\n═══ 4. Sunucu doğrulaması arayüze yansıyor ═══');
  await page.click('#tab-e7'); await page.waitForTimeout(400);
  await page.fill('#u-tarih', '2026-06-01');
  await page.selectOption('#u-vardiya', 'A');
  await page.selectOption('#u-hat', 'DMF1');
  await page.fill('#u-adet', '999');
  await page.click('form:has(#u-adet) button[type=submit]');
  await page.waitForTimeout(800);
  const m2 = await page.textContent('#msg-uretim');
  ok('çift vardiya reddedildi ve gösterildi', m2.startsWith('✗') && m2.includes('zaten kayıt var'), m2);
  ok('reddedilen kayıt Sheet\'e yazılmadı', S._sheetler.Uretim.satirlar.length === 2);

  console.log('\n═══ 5. Duruş + Cycle formları ═══');
  await page.fill('#d-tarih', '2026-06-01');
  await page.selectOption('#d-vardiya', 'A');
  await page.selectOption('#d-hat', 'DMF1');
  await page.fill('#d-sebep', 'Makine Arıza');
  await page.fill('#d-sure', '45');
  await page.fill('#d-aciklama', 'test duruşu');
  await page.click('form:has(#d-sure) button[type=submit]');
  await page.waitForTimeout(900);
  ok('duruş eklendi', (await page.textContent('#msg-durus')).startsWith('✓'), await page.textContent('#msg-durus'));
  await page.selectOption('#c-hat', 'DMF1');
  await page.fill('#c-sn', '45');
  await page.click('form:has(#c-sn) button[type=submit]');
  await page.waitForTimeout(900);
  ok('cycle time kaydedildi', (await page.textContent('#msg-cycle')).startsWith('✓'), await page.textContent('#msg-cycle'));

  await page.click('#tab-e6'); await page.waitForTimeout(700);
  ok('duruş detay tablosunda yeni kayıt', (await page.textContent('#dur-tbody')).includes('test duruşu'));

  await page.screenshot({ path: path.join(SP, 'gas-e7.png'), fullPage: false });
  await page.click('#tab-e7'); await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SP, 'gas-form.png') });

  console.log('\n═══ JS hataları ═══');
  console.log(errs.length ? '  ❌ ' + errs.join('\n  ') : '  ✅ yok');
  if (errs.length) kaldi++;

  console.log(`\n═══ SONUÇ: ${gecti} geçti, ${kaldi} kaldı ═══`);
  await browser.close();
  process.exit(kaldi ? 1 : 0);
})();
