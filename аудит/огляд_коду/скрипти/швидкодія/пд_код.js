/* голий Pyodide 0.26.4 у Chromium (з диска) — виконати python-файл і надрукувати stdout. node пд_код.js <тека pyodide> <файл.py> */
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const [PYD, ФАЙЛ] = process.argv.slice(2);
(async () => {
  const бр = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const с = await бр.newPage();
  await с.route('**/*', r => { const u = new URL(r.request().url());
    if (u.hostname === 'x.test' && u.pathname === '/') return r.fulfill({status: 200, contentType: 'text/html', body: '<!doctype html><script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>'});
    if (/pyodide/.test(u.href)){ const ім = u.pathname.split('/').pop();
      const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : 'application/octet-stream';
      return r.fulfill({status: 200, contentType: тип, body: fs.readFileSync(path.join(PYD, ім))}); }
    return r.abort(); });
  await с.goto('https://x.test/');
  const вих = await с.evaluate(async (код) => { const pd = await loadPyodide(); let out = '';
    pd.setStdout({batched: s => { out += s + '\n'; }}); await pd.runPythonAsync(код); return out; }, fs.readFileSync(ФАЙЛ, 'utf8'));
  process.stdout.write(вих); await бр.close();
})().catch(e => { console.error(e); process.exit(2); });
