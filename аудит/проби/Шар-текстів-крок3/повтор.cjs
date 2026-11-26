const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');

/* Повтор сцени 17009 з двох збірок, за записом #4627. Моделі й зовнішня мережа вимкнені.
   node повтор.cjs <index-ДО.html> <index-ПІСЛЯ.html> <тека Pyodide 0.26.4> <тека результату> */
const {execFileSync} = require('node:child_process');
const [before, after, pyodide, output] = process.argv.slice(2);
assert.ok(before && after && pyodide && output, 'Задай дві збірки, теку Pyodide і теку результату');
const repo = path.resolve(__dirname, '../../..');
const source = 'аудит/проби/Прохід-через-міст-2026-11-21';
const recording = name => execFileSync('git', ['show', 'HEAD:' + source + '/' + name], {cwd: repo, maxBuffer: 4 * 1024 ** 2});
const portrait = recording('вхід/portrait.jpg');
const [vision, prose] = recording('ч3_фото_примірка/обміни.jsonl').toString().split('\n').slice(0, 2)
  .map(line => JSON.parse(JSON.parse(line).відповідь));
const recordedWarning = Object.values(JSON.parse(prose.content[0].text))[0];
const site = 'http://127.0.0.1:4362';
const pages = {before, after};
fs.mkdirSync(output, {recursive: true});

async function pass(browser, phase, name) {
  const context = await browser.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1,
    isMobile: true, hasTouch: true, serviceWorkers: 'block'});
  const calls = [];
  await context.route('**/*', async route => {
    const url = new URL(route.request().url());
    const file = path.basename(url.pathname);
    if (url.host === 'cdn.jsdelivr.net' && url.pathname.startsWith('/pyodide/')) {
      const local = path.join(pyodide, file);
      return route.fulfill({path: local, headers: {'access-control-allow-origin': '*'}});
    }
    if (url.origin !== site) return route.abort();
    if (url.pathname === '/index.html') return route.fulfill({path: pages[phase]});
    if (file === 'build.txt') return route.fulfill({status: 200, body: ''});
    if (decodeURIComponent(url.pathname) !== '/міст') return route.fulfill({status:404});
    const request = route.request().postDataJSON();
    const content = request.messages.flatMap(x => Array.isArray(x.content) ? x.content : [{type: 'text', text: x.content}]);
    const prompt = content.filter(x => x.type === 'text').map(x => x.text).join('\n');
    const photos = content.filter(x => x.type === 'image').length;
    let result, representation;
    if (photos) {
      result = vision;
      if (name === 'без-причини') {
        const payload = JSON.parse(vision.content[0].text);
        payload.zones = {};
        result = {...vision, content: [{type: 'text', text: JSON.stringify(payload)}]};
      }
      representation = 'запис ч3[0]' + (result === vision ? '' : ' без рамок');
    } else if (prompt.includes('\nФАКТИ:\n')) {
      const facts = JSON.parse(prompt.split('\nФАКТИ:\n').at(-1));
      const reasons = {
        portrait_uneven_light: recordedWarning,
        portrait_skin_unmeasured: 'Зроби портрет прямо в камеру, щоб було видно обидві щоки.',
        portrait_hair_unmeasured: 'Зроби портрет, на якому добре видно волосся.'
      };
      result = {...prose, content: [{type: 'text', text: JSON.stringify({text: Object.entries(facts).flatMap(([n, f]) =>
        reasons[f.state].split(/(?<=[.!?])\s+(?=[А-ЯІЇЄҐ])/u).map(says => ({about: {[n]: f.state}, says}))), unknown: []})}]};
      representation = 'текст ч3[1] у новій формі';
    } else {
      result = prose;
      representation = 'запис ч3[1]';
    }
    calls.push({проба: name, виклик: calls.length + 1, кадрів: photos, модель_запису: result.model,
      джерело: representation, промпт: prompt, відповідь: result.content[0].text});
    await route.fulfill({json: result, headers: {'x-model': result.model, 'x-images-dropped': '0'}});
  });
  const page = await context.newPage();
  page.on('console', msg => { if (msg.type() === 'error') console.error(msg.text().slice(0, 300)); });
  page.on('requestfailed', request => console.error(request.url().slice(0, 125), request.failure()?.errorText));
  page.on('pageerror', error => console.error(String(error)));
  await page.goto(site + '/index.html#міст=' + encodeURIComponent(site + '/міст') + '&т=recording&службове=1');
  await page.waitForFunction(() => typeof Екран !== 'undefined' && Екран.стан.запущено && Екран.стан.вхід > 0,
    undefined, {timeout: 90000});
  if (await page.locator('#mirror-studio').count()) {
    await page.locator('#mirror-person').click();
    await page.locator('[data-аркуш="ф-блок"]:visible').click();
  }
  await page.locator('#ф-портрет input[type=file]').setInputFiles({name: 'portrait.jpg', mimeType: 'image/jpeg', buffer: portrait});
  try { await page.waitForFunction(() => !document.querySelector('#кол-зчитати').disabled
    && typeof СТАН_КОЛЬОРУ_П === 'object' && СТАН_КОЛЬОРУ_П?.стан === 'готово', undefined, {timeout: 90000}); }
  catch (error) {
    console.error(calls.map(call => [call.кадрів, call.джерело]));
    console.error(await page.evaluate(() => ({міст: МІСТ_П.адреса, токен: Boolean(МІСТ_П.токен),
      колір: СТАН_КОЛЬОРУ_П, етап: document.querySelector('#кол-стан').textContent,
      збої: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.slice(-5)})));
    throw error;
  }
  const screen = await page.evaluate(async () => {
    const notice = document.querySelector('#ф-світло-портрета');
    const bounds = notice?.getBoundingClientRect();
    const taken = (await читатиКв('профіль:' + АКТИВНИЙ)).колір;
    return {стан: СТАН_КОЛЬОРУ_П, оцінка: taken.походження, вимір: taken.вимір, плашка: notice?.textContent,
      видно: !!(bounds && bounds.height > 0 && bounds.top >= 0 && bounds.bottom <= innerHeight),
      підказка_прихована: document.querySelector('#ф-блок > .підказка').hidden,
      кол_стан: document.querySelector('#кол-стан').textContent, viewport: [innerWidth, innerHeight]};
  });
  assert.equal(screen.оцінка, 'оцінка_моделі');
  if (name !== 'без-причини') assert.ok(screen.стан.причини_виміру.includes('portrait_uneven_light'));
  if (phase === 'after') {
    assert.equal(screen.видно, true);
    assert.match(screen.плашка, /оцінка моделі, не вимір/);
    if (name !== 'без-причини') assert.ok(screen.плашка.includes(recordedWarning));
  }
  await page.screenshot({path: path.join(output, phase + '-' + name + '.png')});
  fs.writeFileSync(path.join(output, phase + '-' + name + '.json'), JSON.stringify({екран: screen, обміни: calls}, null, 2));
  console.log(phase, name, JSON.stringify(screen), 'calls=' + calls.length);
  await context.close();
}

(async () => {
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM || '/usr/bin/chromium', args: ['--no-sandbox']});
  try {
    for (const phase of Object.keys(pages)) {
      for (const name of ['1', '2', 'без-причини']) await pass(browser, phase, name);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
