const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const run = process.argv[2];
const output = path.resolve(process.argv[3] || path.join(__dirname, run));
if (run !== 'do' && run !== 'pislia') throw new Error('Вкажи do або pislia й теку зі зібраним index.html.');
const isAfter = run === 'pislia';
const themes = ['kahlia', 'vytynanka', 'klyny'];
const html = path.join(output, 'index.html');
const server = http.createServer((req, res) => {
  if (req.url !== '/index.html') {
    res.writeHead(404).end();
    return;
  }
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  fs.createReadStream(html).pipe(res);
});

const visiblePage = page => page.evaluate(() => document.documentElement.dataset.pairPage);
const introOpen = page => page.evaluate(() => document.querySelector('#mirror-intro')?.open);
const save = page => page.locator('[data-ux=pair-profile-done]');
const screenshot = (page, theme, step) => page.screenshot({path: path.join(output, theme + '-' + step + '.png'), animations: 'disabled'});

async function buttonMeasure(page) {
  return save(page).evaluate(button => {
    const rect = button.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(button);
    const lines = new Set([...range.getClientRects()].map(rect => Math.round(rect.top))).size;
    const inside = rect.width > 0 && rect.height > 0 && rect.left >= 0 && rect.right <= innerWidth &&
      rect.top >= 0 && rect.bottom <= innerHeight && document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2)?.closest('button') === button;
    return {inside, lines, width: Math.round(rect.width)};
  });
}

async function themeChange(page, theme) {
  await page.locator('#mirror-style').click();
  await page.locator('button[data-swatch=' + theme + ']').click();
  await page.waitForFunction(theme => document.documentElement.dataset.hand === theme, theme);
  return introOpen(page);
}

async function profileCompleted(page) {
  return page.evaluate(async () => {
    const snapshot = зрізПрофіляП();
    const saved = await читатиКв_('профіль:' + snapshot.профілі.активний);
    return { memory: snapshot.профілі.створено, storage: Boolean(saved?.створено) };
  });
}

async function fillColors(page) {
  // Виміряні кольори як фікстура на вході профілю. Заставка, кнопки, мірки й навігація працюють у браузері.
  await page.evaluate(() => {
    КОЛІР = {шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', джерело: 'чат'};
    показатиПрофіль();
  });
}

async function fillMeasurements(page) {
  const values = {'мр-зріст':'167','мр-плечі':'96','мр-груди':'92','мр-талія':'74','мр-стегна':'100'};
  for (const [id, value] of Object.entries(values)) await page.locator('#' + id).fill(value);
}

async function measureTheme(browser, theme, activeTheme) {
  const context = await browser.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale:'uk-UA'});
  await context.route('**/*', route => route.request().url().startsWith('http://127.0.0.1:') ? route.continue() : route.abort());
  await context.addInitScript(theme => localStorage.setItem('liusterko-material', theme), theme);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:' + server.address().port + '/index.html');
  await page.locator('#mirror-intro[open]').waitFor();
  const startIntro = await introOpen(page);
  assert.equal(await page.evaluate(() => document.documentElement.dataset.hand), theme);
  await page.locator('#mirror-intro button').click();
  await page.waitForFunction(() => document.documentElement.dataset.pairPage === 'профіль');
  const profileMeasures = {огляд: await buttonMeasure(page)};
  await screenshot(page, theme, 'профіль');
  for (const [step, selector] of Object.entries({імя:'[data-ux=pair-name]', фото:'[data-ux=pair-photos]', кольори:'[data-аркуш=кол-блок]', лице:'[data-аркуш=др-блок]', обхвати:'[data-аркуш=мір-блок]', розширені:'[data-аркуш=мр-розширені]', налаштування:'[data-аркуш=пф-блок]'})) {
    await page.locator(selector).first().click();
    await page.locator('#аркуш:not([hidden])').waitFor();
    await page.locator('#аркуш').evaluate(sheet => Promise.all(sheet.getAnimations().map(animation => animation.finished)));
    profileMeasures[step] = await buttonMeasure(page);
    if (isAfter && step === 'обхвати' && theme === 'kahlia') await screenshot(page, theme, 'аркуш-обхватів');
    await page.keyboard.press('Escape');
    await page.locator('#аркуш[hidden]').waitFor({state: 'hidden'});
  }
  await page.evaluate(() => document.getElementById('mirror-work').scrollTop = 0);
  await save(page).click();
  await page.waitForFunction(after => after ? document.querySelector('#аркуш-тіло>#кол-блок') : document.documentElement.dataset.pairPage === 'mirror', isAfter);
  const empty = {page: await visiblePage(page), ...(await profileCompleted(page))};
  let hint = '';
  let complete = null;
  if (isAfter) {
    hint = await page.locator('#pair-profile-missing').textContent();
    if (theme === 'kahlia') await screenshot(page, theme, 'бракує-даних');
    assert.match(hint, /кольори.*обхвати й зріст/);
    assert.deepEqual(empty, {page:'профіль',memory:false,storage:false});
    await fillColors(page);
    await page.waitForFunction(() => document.querySelector('#pair-profile-missing').textContent === 'Ще треба: обхвати й зріст.');
    await save(page).click();
    await page.waitForFunction(() => document.querySelector('#аркуш-тіло>#мір-блок'));
    await fillMeasurements(page);
    await page.waitForFunction(() => document.querySelector('#pair-profile-missing').textContent === '');
    await save(page).click();
    await page.waitForFunction(() => document.documentElement.dataset.pairPage === 'mirror');
    complete = await profileCompleted(page);
    assert.deepEqual(complete, {memory:true,storage:true});
  }
  const welcome = page.locator('#pair-chat-welcome');
  const greeting = await welcome.isVisible() ? await welcome.innerText() : '';
  const icons = await page.locator('.pair-shortcuts svg use').evaluateAll(uses => uses.map(use => use.getAttribute('href')));
  const iconPairs = icons.length - new Set(icons).size;
  await screenshot(page, theme, 'головна');
  await page.locator('.pair-shortcuts [data-ux=library]').click();
  const beforeStyle = await visiblePage(page);
  const introAfterTheme = await themeChange(page, activeTheme);
  const afterStyle = await visiblePage(page);
  if (theme === 'kahlia') await screenshot(page, theme, 'зміна-стилю');
  if (introAfterTheme) await page.locator('#mirror-intro button').click();
  const resume = await page.evaluate(() => {
    let hidden = false;
    let elapsed = 0;
    const now = Date.now;
    Object.defineProperty(document, 'hidden', {configurable: true, get: () => hidden});
    Date.now = () => now() + elapsed;
    const change = value => {
      hidden = value;
      document.dispatchEvent(new Event('visibilitychange'));
      return document.querySelector('#mirror-intro').open;
    };
    change(true);
    elapsed += 60000;
    const short = change(false);
    change(true);
    elapsed += 301000;
    const afterFive = change(false);
    Date.now = now;
    delete document.hidden;
    return {short, afterFive};
  });
  await page.locator('#mirror-intro button').click();
  await page.locator('#mirror-person').click();
  await page.locator('#е-огляд [data-аркуш=пф-блок]').click();
  await page.locator('#пф-новий').click();
  await page.waitForFunction(() => document.documentElement.dataset.pairPage === 'старт');
  for (let step = 0; step < 3; step++) {
    await page.waitForFunction(step => Екран.стан.крок === step, step);
    await page.evaluate(() => document.getElementById('mirror-work').scrollTop = 0);
    profileMeasures['крок_нового_' + (step + 1)] = await buttonMeasure(page);
    if (step < 2) await page.locator('#н-далі').click();
  }
  if (isAfter) {
    assert.ok(Object.values(profileMeasures).every(measure => measure.inside && measure.lines === 1), JSON.stringify(profileMeasures));
    assert.match(greeting, /я Ші[^\n]*\s+Куди збираєшся/);
    assert.equal(iconPairs, 0);
    assert.equal(introAfterTheme, false);
    assert.equal(beforeStyle, afterStyle);
  } else {
    assert.equal(empty.page, 'mirror');
    assert.equal(iconPairs, 2);
    assert.equal(introAfterTheme, true);
  }
  assert.equal(startIntro, true);
  assert.deepEqual(resume, {short:false, afterFive:true});
  assert.deepEqual(errors, []);
  await context.close();
  return {theme, empty, hint, complete, profileMeasures, startIntro, activeTheme, introAfterTheme, beforeStyle, afterStyle, resume, greeting, icons, iconPairs, errors};
}

(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM || '/usr/bin/chromium', args:['--no-sandbox']});
  try {
    const evidence = [];
    for (const [index, theme] of themes.entries()) evidence.push(await measureTheme(browser, theme, themes[(index + 1) % themes.length]));
    fs.writeFileSync(path.join(output, 'vymir.json'), JSON.stringify(evidence, null, 2) + '\n');
  } finally {
    await browser.close();
    server.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; server.close(); });
