// Живе приймання #4805, сцена 17009: портрет з #4627 → вимір → плашка; модель — справжній Sonnet через `claude -p`.
// node живий.cjs <index.html> <тека Pyodide> <тека результату> <мітка> ; NODE_PATH=/opt/node-tools/node_modules
const fs = require('fs'), path = require('path'), cp = require('child_process');
const {chromium} = require('playwright');
const [PAGE, PYO, OUT, LABEL] = process.argv.slice(2);
const repo = path.resolve(__dirname, '../../..');
const portrait = fs.readFileSync(path.join(repo, 'аудит/проби/Прохід-через-міст-2026-11-21/вхід/portrait.jpg'));
const site = 'http://127.0.0.1:4362';
const SYS = 'You are the model behind a mobile styling app. The user message is the application prompt, verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, no tools, no questions back.';
const FLAGS = ['-p', '--model', 'sonnet', '--effort', 'low', '--tools', '', '--strict-mcp-config', '--no-session-persistence',
  '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose', '--system-prompt', SYS];
const cwd = fs.mkdtempSync('/tmp/zhyva-');
function claude(body) {
  const blocks = [];
  const msgs = body.messages || [];
  for (const m of msgs) {
    if (msgs.length > 1) blocks.push({type: 'text', text: '[' + m.role + ']'});
    if (!Array.isArray(m.content)) { blocks.push({type: 'text', text: String(m.content ?? '')}); continue; }
    for (const b of m.content) blocks.push(b.type === 'image' ? b : {type: 'text', text: b.text || ''});
  }
  return new Promise(res => {
    const p = cp.spawn('/opt/node22/bin/claude', FLAGS, {cwd, stdio: ['pipe', 'pipe', 'pipe']});
    let out = ''; const t = setTimeout(() => p.kill('SIGKILL'), 300000);
    p.stdout.on('data', x => out += x); p.on('close', () => { clearTimeout(t); res(out); });
    p.stdin.end(JSON.stringify({type: 'user', message: {role: 'user', content: blocks}}) + '\n', 'utf8');
  });
}
(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  const browser = await chromium.launch({args: ['--no-sandbox']});
  const ctx = await browser.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1, isMobile: true, hasTouch: true, serviceWorkers: 'block'});
  const calls = []; let inflight = 0;
  await ctx.route('**/*', async route => {
    const url = new URL(route.request().url()); const file = path.basename(url.pathname);
    if (url.host === 'cdn.jsdelivr.net' && url.pathname.startsWith('/pyodide/')) return route.fulfill({path: path.join(PYO, file), headers: {'access-control-allow-origin': '*'}});
    if (url.origin !== site) return route.abort();
    if (url.pathname === '/index.html') return route.fulfill({path: PAGE});
    if (file === 'build.txt') return route.fulfill({status: 200, body: ''});
    if (decodeURIComponent(url.pathname) !== '/міст') return route.fulfill({status: 404});
    inflight++;
    const body = route.request().postDataJSON();
    const ev = (await claude(body)).split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    const r = ev.find(o => o.type === 'result');
    const text = r && !r.is_error ? String(r.result || '') : '';
    const model = r?.modelUsage ? Object.keys(r.modelUsage).join(',') : null;
    const content = (body.messages || []).flatMap(x => Array.isArray(x.content) ? x.content : [{type: 'text', text: x.content}]);
    calls.push({n: calls.length + 1, кадрів: content.filter(x => x.type === 'image').length, модель: model, помилка: !r || r.is_error,
      промпт: content.filter(x => x.type === 'text').map(x => x.text).join('\n'), відповідь: text});
    inflight--;
    if (!r || r.is_error) return route.fulfill({status: 599, json: {error: {type: 'стенд', message: 'claude -p без result'}}});
    route.fulfill({json: {id: 'ст-' + calls.length, type: 'message', role: 'assistant', model, content: [{type: 'text', text}], stop_reason: 'end_turn', usage: {input_tokens: 0, output_tokens: 0}},
      headers: {'x-model': model || '', 'x-images-dropped': '0'}});
  });
  const page = await ctx.newPage(); const errs = [];
  page.on('pageerror', e => errs.push(String(e).slice(0, 300)));
  await page.goto(site + '/index.html#міст=' + encodeURIComponent(site + '/міст') + '&т=live&службове=1');
  await page.waitForFunction(() => typeof Екран !== 'undefined' && Екран.стан.запущено && Екран.стан.вхід > 0, undefined, {timeout: 120000});
  if (await page.locator('#mirror-studio').count()) { await page.locator('#mirror-person').click(); await page.locator('[data-аркуш="ф-блок"]:visible').click(); }
  await page.locator('#ф-портрет input[type=file]').setInputFiles({name: 'portrait.jpg', mimeType: 'image/jpeg', buffer: portrait});
  let ok = true;
  try { await page.waitForFunction(() => !document.querySelector('#кол-зчитати').disabled && typeof СТАН_КОЛЬОРУ_П === 'object' && СТАН_КОЛЬОРУ_П?.стан === 'готово', undefined, {timeout: 240000}); } catch (e) { ok = false; }
  for (let i = 0, quiet = 0; i < 120 && quiet < 4; i++) { await new Promise(r => setTimeout(r, 1500)); quiet = inflight ? 0 : quiet + 1; }
  const screen = await page.evaluate(async () => {
    const n = document.querySelector('#ф-світло-портрета'); const b = n?.getBoundingClientRect();
    return {стан: typeof СТАН_КОЛЬОРУ_П === 'object' ? СТАН_КОЛЬОРУ_П : null, плашка: n?.textContent ?? null,
      видно: !!(b && b.height > 0 && b.top >= 0 && b.bottom <= innerHeight), кол_стан: document.querySelector('#кол-стан')?.textContent,
      текст_екрана: document.body.innerText.slice(0, 4000)};
  });
  await page.screenshot({path: path.join(OUT, LABEL + '.png')});
  await page.screenshot({path: path.join(OUT, LABEL + '-весь.png'), fullPage: true});
  fs.writeFileSync(path.join(OUT, LABEL + '.json'), JSON.stringify({дійшло: ok, помилки_сторінки: errs, екран: screen, обміни: calls}, null, 1));
  console.log(LABEL, 'дійшло=' + ok, 'видно=' + screen.видно, 'викликів=' + calls.length, 'моделі=' + calls.map(c => c.модель), '\nплашка:', screen.плашка);
  await browser.close();
})().catch(e => { console.error(e); process.exit(2); });
