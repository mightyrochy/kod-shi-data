"""Проба: смужка «Є новіша версія» у справжньому Chromium 390×844 на зібраній сторінці з локального HTTP-сервера.
(а) штамп той самий — нема; (б) штамп змінено → є, «Оновити» → ?v=<нова>, перезавантажено, хеш на місці; (в) файлу нема — нема, без винятків.
Запуск: NODE_PATH=<тека з playwright> python3 смужка_оновлення.py <зібраний.html>"""
import subprocess, sys, tempfile, os, shutil
js = r"""
const { chromium } = require('playwright'), http = require('http'), fs = require('fs'), path = require('path');
const dir = process.argv[2], page = process.argv[3];
const srv = http.createServer((q, r) => { const u = new URL(q.url, 'http://x').pathname;
  fs.readFile(path.join(dir, u === '/' ? page : u.slice(1)), (e, d) => { r.writeHead(e ? 404 : 200); r.end(d); }); });
(async()=>{
  await new Promise(r => srv.listen(0, r)); const base = 'http://127.0.0.1:' + srv.address().port + '/';
  const html = fs.readFileSync(path.join(dir, page), 'utf8');
  const own = (html.match(/const ЗБІРКА_ПОКАЗУ = "([^"]*)"/) || [])[1];
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'}); const out = {}; const w = f => fs.writeFileSync(path.join(dir, 'build.txt'), f);
  async function відкрити(){
    const p = await b.newPage({viewport:{width:390,height:844}}); p.errs = [];
    p.on('pageerror', e => p.errs.push(String(e)));
    await p.route(/^https?:\/\/(?!127\.)/, r => r.abort());
    await p.goto(base + page + '#пакет123'); await p.waitForTimeout(2500); return p;
  }
  const видно = p => p.evaluate(() => { const e = document.getElementById('нова-версія'); return !!e && !e.hidden && e.offsetHeight > 0; });
  const візит = async p => { await p.evaluate(() => document.dispatchEvent(new Event('visibilitychange'))); await p.waitForTimeout(600); };
  w(own);
  let p = await відкрити(); await візит(p); out.а_смужка = await видно(p); out.а_помилок = p.errs.length;
  const нова = '2099-01-01 00:00 · модулів 1 · показ ПОВНИЙ';
  w(нова); await візит(p);
  out.б_смужка = await видно(p);
  if (out.б_смужка) {
    await p.evaluate(() => { window.__мітка = 1; });
    await Promise.all([p.waitForNavigation(), p.click('#нова-версія-кн')]); await p.waitForTimeout(2500);
    const u = new URL(p.url());
    out.б_v = u.searchParams.get('v') === нова; out.б_хеш = decodeURIComponent(u.hash); 
    out.б_перезавантажено = await p.evaluate(() => window.__мітка === undefined);
  }
  await p.close();
  fs.unlinkSync(path.join(dir, 'build.txt'));
  p = await відкрити(); await візит(p); out.в_смужка = await видно(p); out.в_помилок = p.errs.length;
  console.log(JSON.stringify(out)); await b.close(); srv.close();
})();
"""
d = tempfile.mkdtemp(); shutil.copy(sys.argv[1], os.path.join(d, "index.html"))
f = os.path.join(d, "t.js"); open(f, "w").write(js)
r = subprocess.run(["node", f, d, "index.html"], capture_output=True, text=True, timeout=200); print(r.stdout or r.stderr[-400:])
