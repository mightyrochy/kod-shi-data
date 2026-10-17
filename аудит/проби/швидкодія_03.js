/* КРОК 0.3 · дослід швидкодії «Зібрати образи» → картки на стенді (заглушка моделей, 390×844).
   Продукт і стенд не правляться: цей файл — і драйвер, і попереднє завантаження (`node -r`) для `рв6_стенд.js`.

   Драйвер:  node аудит/проби/швидкодія_03.js <зібрана_тека> <тека_pyodide> <тека_виходу> [холодних=3] [теплих=3] [сід=3]
   Прогін:   node -r ./швидкодія_03.js рв6_стенд.js … з env VYMIR_OUT=<json> VYMIR_MODE=cold|warm VYMIR_PROFILE=<тека профілю>
   Вимір у самій сторінці (init-скрипт): мітка t0 — дотик `#зб-зібрати`; перша / четверта картка `#картки .картка`
   (MutationObserver); long tasks і Event Timing; «пульс» 50 мс (найдовший розрив); пам'ять JS-купи й купи WASM.
   Затримка дотику — з Node через CDP: кожні ~700 мс миша тисне в точку (1,1); у сторінці `pointerdown` пише
   `performance.now() − event.timeStamp`; сама команда CDP вертається, лише коли головний потік її прийняв.
   Холодний прогін — свіжий профіль Chromium; теплий — профіль після одного прогріваючого (відкинутого) прогону.
   Прогін зупиняється через 2 с після четвертої картки (решту сцен стенда не міряємо). */
'use strict';
const path = require('path'), fs = require('fs'), cp = require('child_process');

if (require.main === module) {            // ───── драйвер ─────
  const [корінь, пиодід, вихід, х = '3', т = '3', сід = '3'] = process.argv.slice(2);
  if (!корінь || !пиодід || !вихід) { console.error('використання: див. шапку'); process.exit(2); }
  fs.mkdirSync(вихід, { recursive: true });
  const стенд = path.join(__dirname, 'рв6_стенд.js');
  const результати = [];
  const прогін = (мітка, режим, профіль) => {
    const json = path.join(вихід, мітка + '.json'), лог = path.join(вихід, мітка + '.log');
    const t = Date.now();
    const r = cp.spawnSync(process.execPath, ['-r', __filename, стенд, 'http://127.0.0.1:8765', корінь, пиодід, сід],
      { env: { ...process.env, VYMIR_OUT: json, VYMIR_MODE: режим, VYMIR_PROFILE: профіль, PYTHONUTF8: '1' },
        encoding: 'utf8', maxBuffer: 1 << 28, timeout: 1500000 });
    fs.writeFileSync(лог, (r.stdout || '') + (r.stderr ? '\n--- stderr ---\n' + r.stderr : ''));
    const ok = fs.existsSync(json);
    console.log(мітка, режим, 'rc', r.status, ok ? 'ok' : 'БЕЗ ВИМІРУ', ((Date.now() - t) / 1000).toFixed(0) + ' с');
    if (ok) результати.push(JSON.parse(fs.readFileSync(json, 'utf8')));
  };
  const теплий = path.join(вихід, 'профіль_теплий');
  fs.rmSync(теплий, { recursive: true, force: true, maxRetries: 20, retryDelay: 500 });
  for (let i = 1; i <= Number(х); i++) {
    const п = path.join(вихід, 'профіль_холодний_' + i);
    fs.rmSync(п, { recursive: true, force: true, maxRetries: 20, retryDelay: 500 });
    прогін('холодний_' + i, 'cold', п);
    try { fs.rmSync(п, { recursive: true, force: true, maxRetries: 20, retryDelay: 500 }); } catch (e) {}
  }
  прогін('прогрів_відкинутий', 'warm', теплий);
  for (let i = 1; i <= Number(т); i++) прогін('теплий_' + i, 'warm', теплий);
  try { fs.rmSync(теплий, { recursive: true, force: true, maxRetries: 20, retryDelay: 500 }); } catch (e) { /* Chromium ще тримає теку */ }
  fs.writeFileSync(path.join(вихід, 'усе.json'), JSON.stringify(результати, null, 1));
  return;
}

// ───── попереднє завантаження всередині процесу стенда ─────
const { chromium } = require('playwright');
const MODE = process.env.VYMIR_MODE || 'cold', ПРОФІЛЬ = process.env.VYMIR_PROFILE, ВИХІД = process.env.VYMIR_OUT;
const ПОЧАТОК = Date.now();

const ІНІТ = () => {
  const V = window.__vymir = { t0: null, tFirst: null, tAll: null, long: [], ev: [], gap: 0, mem: [], probes: [], nav: performance.timeOrigin };
  const now = () => performance.now();
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) V.long.push([+e.startTime.toFixed(1), +e.duration.toFixed(1)]); })
    .observe({ type: 'longtask', buffered: true }); } catch (e) { V.noLong = String(e); }
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) V.ev.push([e.name, +e.startTime.toFixed(1), +(e.processingStart - e.startTime).toFixed(1), e.duration]); })
    .observe({ type: 'event', durationThreshold: 16, buffered: true }); } catch (e) { V.noEv = String(e); }
  let last = now();
  setInterval(() => { const t = now(); V.gap = Math.max(V.gap, t - last - 50); last = t; }, 50);
  const mem = () => {
    let wasm = null;
    try { wasm = (typeof pyodide_показу !== 'undefined' && pyodide_показу && pyodide_показу._module.HEAPU8.length) || null; } catch (e) {}
    V.mem.push([+now().toFixed(0), performance.memory ? performance.memory.usedJSHeapSize : null, wasm]);
  };
  setInterval(mem, 250);
  const карток = () => document.querySelectorAll('#картки .картка').length;
  const перевір = () => {
    const n = карток();
    if (V.t0 !== null && n >= 1 && V.tFirst === null) V.tFirst = now();
    if (V.t0 !== null && n >= 4 && V.tAll === null) { V.tAll = now(); mem(); }
  };
  document.addEventListener('DOMContentLoaded', () => new MutationObserver(перевір).observe(document.documentElement, { childList: true, subtree: true }));
  window.addEventListener('click', e => { if (V.t0 === null && e.target && e.target.closest && e.target.closest('#зб-зібрати')) V.t0 = now(); }, true);
  window.addEventListener('pointerdown', e => {
    const t = now();
    V.probes.push({ at: +t.toFixed(0), delay: +(t - e.timeStamp).toFixed(1), фаза: V.t0 === null ? 'до' : (V.tAll === null ? 'збір' : 'після') });
  }, true);
};

function пам_процесів(профіль) {
  try {
    const ps = `$ids = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*${профіль.replace(/'/g, "''")}*' } | ForEach-Object { $_.ProcessId }; Get-Process -Id $ids | ForEach-Object { "$($_.WorkingSet64),$($_.PeakWorkingSet64)" }`;
    const out = cp.execFileSync('powershell', ['-NoProfile', '-Command', ps], { encoding: 'utf8' }).trim().split(/\r?\n/).filter(Boolean);
    const рядки = out.map(s => s.split(',').map(Number));
    return { процесів: рядки.length, сума_ws_МБ: +(рядки.reduce((a, r) => a + r[0], 0) / 1048576).toFixed(0),
      макс_пік_ws_МБ: +(Math.max(0, ...рядки.map(r => r[1])) / 1048576).toFixed(0), };
  } catch (e) { return { помилка: String(e).slice(0, 120) }; }
}

const orig = chromium.launch.bind(chromium);
chromium.launch = async (opts = {}) => {
  const ctx = await chromium.launchPersistentContext(ПРОФІЛЬ, { headless: true, executablePath: opts.executablePath, proxy: opts.proxy,
    viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: true, acceptDownloads: true });
  /* Теплий профіль зберігає кеш Chromium, але не стан застосунку: localStorage/IndexedDB із минулого прогону
     пропустили б знайомство, і стенд не знайшов би його кнопок. Тож сховища сайту чистимо в обох режимах. */
  { const тимч = await ctx.newPage(), s0 = await ctx.newCDPSession(тимч);
    await s0.send('Storage.clearDataForOrigin', { origin: 'http://127.0.0.1:8765', storageTypes: 'local_storage,session_storage,indexeddb,cookies,websql' });
    await тимч.close(); }
  await ctx.addInitScript(ІНІТ);
  let сторінка = null, зупинено = false;
  ctx.on('page', p => { сторінка = p; });
  const мікроби = [];
  const цикл = async () => {
    await new Promise(r => setTimeout(r, 1500));
    while (!зупинено) {
      try {
        if (!сторінка || сторінка.isClosed()) { await new Promise(r => setTimeout(r, 300)); continue; }
        const s = цикл.cdp || (цикл.cdp = await ctx.newCDPSession(сторінка));
        const t = Date.now();
        await s.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: 1, y: 1, button: 'left', clickCount: 1 });
        await s.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: 1, y: 1, button: 'left', clickCount: 1 });
        мікроби.push(Date.now() - t);
      } catch (e) { /* сторінка ще вантажиться */ }
      await new Promise(r => setTimeout(r, 700));
    }
  };
  цикл();
  const завершити = async () => {
    for (;;) {                                           // чекаємо 4 картки й 2 с після них
      await new Promise(r => setTimeout(r, 250));
      try {
        if (!сторінка || сторінка.isClosed()) continue;
        const tAll = await сторінка.evaluate(() => window.__vymir && window.__vymir.tAll).catch(() => null);
        if (tAll !== null && tAll !== undefined) break;
      } catch (e) {}
      if (Date.now() - ПОЧАТОК > 1400000) break;
    }
    await new Promise(r => setTimeout(r, 2000));
    зупинено = true;
    let V = null, метрики = null;
    try { V = await сторінка.evaluate(() => window.__vymir); } catch (e) { V = { помилка: String(e) }; }
    const памʼять = пам_процесів(ПРОФІЛЬ);
    if (V && V.t0 !== null && V.tAll !== null) {
      const вікно = [V.t0, V.tAll];
      const довгі = V.long.filter(([s0]) => s0 >= вікно[0] && s0 <= вікно[1]);
      const збір = V.probes.filter(p => p.фаза === 'збір'), до = V.probes.filter(p => p.фаза === 'до');
      const mem = V.mem.filter(m => m[0] >= V.t0 - 1);
      var підсумок = {
        режим: MODE, час_першої_картки_с: +((V.tFirst - V.t0) / 1000).toFixed(2), час_усіх_карток_с: +((V.tAll - V.t0) / 1000).toFixed(2),
        longtasks_у_зборі: { кількість: довгі.length, сума_с: +(довгі.reduce((a, l) => a + l[1], 0) / 1000).toFixed(2), макс_с: +(Math.max(0, ...довгі.map(l => l[1])) / 1000).toFixed(2) },
        найдовший_розрив_пульсу_с: +(V.gap / 1000).toFixed(2),
        дотик_збір: { проб: збір.length, затримка_мс: збір.map(p => p.delay), макс_мс: Math.max(0, ...збір.map(p => p.delay)) },
        дотик_до_збору: { проб: до.length, макс_мс: Math.max(0, ...до.map(p => p.delay)) },
        cdp_відповідь_мс: мікроби,
        пам_js_макс_МБ: +(Math.max(0, ...mem.map(m => m[1] || 0)) / 1048576).toFixed(0),
        пам_wasm_макс_МБ: +(Math.max(0, ...mem.map(m => m[2] || 0)) / 1048576).toFixed(0),
        процеси: памʼять,
        від_старту_процесу_с: +((Date.now() - ПОЧАТОК) / 1000).toFixed(0),
      };
    } else var підсумок = { режим: MODE, помилка: 'мітки t0/tAll не взято', V: V && { t0: V.t0, tFirst: V.tFirst, tAll: V.tAll } };
    fs.writeFileSync(ВИХІД, JSON.stringify({ ...підсумок, сирі: V }, null, 1));
    console.log('ВИМІР', JSON.stringify(підсумок));
    process.exit(0);          // не ctx.close(): стенд побачив би закриття й вийшов би з rc 2
  };
  завершити();
  return { newContext: async () => ctx, close: async () => {} };
};
