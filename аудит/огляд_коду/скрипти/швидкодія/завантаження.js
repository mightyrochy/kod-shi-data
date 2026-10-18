/* Чисте завантаження ЗІБРАНОЇ сторінки в Chromium + підйом Pyodide/bridge + (необов'язково) відтворення
   записаних викликів bridge у тому самому Pyodide. Мережа — з диска, як у рв6_стенд.js.
   node завантаження.js <корінь зі index.html> <тека pyodide> <вихід.json> [виклики.json] [профіль=0|1] [pyc=0|1]
   pyc=1 — перед імпортом bridge компілює всі .py з /показ у __pycache__ (compileall) і міряє імпорт з .pyc. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ВІ = require(path.join(__dirname, 'вимір_ін.js'));
const [КОРІНЬ, PYD, ВИХІД, ВИКЛИКИ, ПРОФІЛЬ, PYC] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
(async () => {
  const бр = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const стор = await (await бр.newContext({viewport: {width: 390, height: 844}})).newPage();
  const cdp = await стор.context().newCDPSession(стор);
  await cdp.send('Performance.enable');
  await стор.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (u.origin === БАЗА){
      const ф = path.join(КОРІНЬ, decodeURIComponent(u.pathname));
      if (fs.existsSync(ф) && fs.statSync(ф).isFile())
        return route.fulfill({status: 200, contentType: ф.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/octet-stream', body: fs.readFileSync(ф)});
      return route.fulfill({status: 404, body: ''});
    }
    if (/cdn\.jsdelivr\.net\/pyodide\//.test(u.href)){
      const ім = u.pathname.split('/').pop();
      const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
      return route.fulfill({status: 200, contentType: тип, body: fs.readFileSync(path.join(PYD, ім))});
    }
    return route.abort();
  });
  await ВІ.ставити(стор);
  const t0 = Date.now();
  await стор.goto(БАЗА + '/index.html', {waitUntil: 'load', timeout: 180000});
  const тLoad = Date.now() - t0;
  await стор.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, {timeout: 180000});
  const тГотово = Date.now() - t0;
  const метрики = (await cdp.send('Performance.getMetrics')).metrics;
  await ВІ.післяЗавантаження(стор);
  await new Promise(р => setTimeout(р, 500));
  /* PYC: підкласти .pyc до імпорту bridge — обгорткою unpackArchive, яка після розпаковки кличе compileall */
  if (PYC === '1') await стор.evaluate(() => { window.__PYC = true; });
  const підйом = await стор.evaluate(async () => {
    const t0 = performance.now();
    await підняти_міст_показу();
    return performance.now() - t0;
  });
  let відтворення = null;
  if (ВИКЛИКИ){
    const код = fs.readFileSync(path.join(__dirname, 'відтворення.py'), 'utf8');
    const дані = fs.readFileSync(ВИКЛИКИ, 'utf8');
    відтворення = await стор.evaluate(async ([код, дані, проф, дамп]) => {
      const pd = pyodide_показу;
      pd.FS.writeFile('/tmp/відтворення.py', код); pd.FS.writeFile('/tmp/виклики.json', дані);
      const t0 = performance.now();
      if (дамп) pd.runPython('import os\nos.makedirs("/tmp/дамп", exist_ok=True)\nos.environ["VIDTV_DUMP"] = "/tmp/дамп"');
      const р = await pd.runPythonAsync('import sys\nsys.path.insert(0, "/tmp")\nimport відтворення\nawait відтворення.прогнати("/tmp/виклики.json", ' + (проф ? 'True' : 'False') + ')');
      const разом_мс = performance.now() - t0;
      const файли = {};
      if (дамп) for (const ф of pd.FS.readdir('/tmp/дамп')) if (!ф.startsWith('.')) файли[ф] = pd.FS.readFile('/tmp/дамп/' + ф, {encoding: 'utf8'});
      return {разом_мс, р: JSON.parse(р), файли};
    }, [код, дані, ПРОФІЛЬ === '1', !!process.env.DUMP_DIR]);
    if (process.env.DUMP_DIR){ for (const [ф, т] of Object.entries(відтворення.файли)) fs.writeFileSync(path.join(process.env.DUMP_DIR, ф), т); }
    delete відтворення.файли;
  }
  const д = await ВІ.зняти(стор, ВИХІД + '.tmp');
  fs.unlinkSync(ВИХІД + '.tmp');
  fs.writeFileSync(ВИХІД, JSON.stringify({тLoad, тГотово, метрики, підйом, відтворення, ...д}));
  console.log('load', тLoad, 'готово', тГотово, 'підйом', Math.round(підйом), відтворення ? 'відтворення ' + Math.round(відтворення.разом_мс) : '');
  await бр.close();
})().catch(e => { console.error(e); process.exit(2); });
