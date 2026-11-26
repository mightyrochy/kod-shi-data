/* Мірило (б) наряду «очі називає модель»: екран профілю 390×844 після читання портрета штатним шляхом
   (`зчитатиКольориЗПортрета` → реєстр `прийняти_колір` → вимір шкіри й волосся кодом → `кольориПрофілюП`).
   Підставлено лише руку моделі (`модельРукиП`): вона повертає записану сиру відповідь `після/1/<ж>.txt`;
   міст (Pyodide), вимір, писач профілю й екран — штатні. Мережа: сама сторінка й Pyodide 0.26.4 з диска (`аудит/проби/стенд_pyodide_кеш.sh`), решта — обрив.
   Запуск (з кореня): node аудит/проби/очі-називає-модель/екран.js <index.html> <тека знімків> [<тека pyodide>] */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const ТЕКА = __dirname, НАБІР = path.join(ТЕКА, '..', 'набір-фото-жінок');
const [html, знімки, PYODIDE = '/tmp/pyodide'] = process.argv.slice(2);
const URL0 = 'http://localhost/';
const ЖІНКИ = ['ж1', 'ж3', 'ж4', 'ж7'];
(async () => {
  fs.mkdirSync(знімки, {recursive: true});
  const бр = await chromium.launch({args: ['--no-sandbox'],
    proxy: process.env.HTTPS_PROXY ? {server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1'} : undefined});
  const ctx = await бр.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, hasTouch: true,
                                   isMobile: true, reducedMotion: 'reduce', locale: 'uk-UA', ignoreHTTPSErrors: true});
  const обірвано = new Set();
  const тіло = fs.readFileSync(html);
  await ctx.route('**/*', r => {
    const u = r.request().url();
    if (u === URL0) return r.fulfill({contentType: 'text/html; charset=utf-8', body: тіло});
    if (/^(data|blob):/.test(u)) return r.continue();
    if (/^https:\/\/cdn\.jsdelivr\.net\/pyodide\//.test(u)){
      const ім = new URL(u).pathname.split('/').pop(), ф = path.join(PYODIDE, ім);
      return r.fulfill({status: fs.existsSync(ф) ? 200 : 404, body: fs.existsSync(ф) ? fs.readFileSync(ф) : '',
        contentType: ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript'
          : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream'});
    }
    обірвано.add(u.slice(0, 80)); return r.abort();
  });
  let p = await ctx.newPage(); const помилки = []; p.on('pageerror', e => помилки.push(String(e)));
  await p.goto(URL0); await p.waitForFunction(() => window.MirrorRoom?.available(), null, {timeout: 120000});
  await p.evaluate(async ж => { await писатиКв('профілі', ж.map(і => ({ід: і, назва: 'Профіль ' + і})));
                                await писатиКв('активний', ж[0]); }, ЖІНКИ);
  await p.close(); p = await ctx.newPage(); p.on('pageerror', e => помилки.push(String(e)));
  await p.goto(URL0); await p.waitForFunction(() => window.MirrorRoom?.available(), null, {timeout: 120000});
  const підсумок = {};
  for (const ж of ЖІНКИ){
    await p.evaluate(і => перемкнути(і), ж); await p.waitForTimeout(800);
    /* портрет — тим самим писачем, що й вибір файла в слоті (`зберегтиФотоП`), без діалогу вибору */
    const б64 = fs.readFileSync(path.join(НАБІР, ж + '-портрет.jpg')).toString('base64');
    await p.evaluate(async б => { const блоб = await (await fetch('data:image/jpeg;base64,' + б)).blob();
                                  await зберегтиФотоП('портрет', new File([блоб], 'портрет.jpg', {type: 'image/jpeg'})); }, б64);
    await p.waitForFunction(() => читатиПортретП().then(р => { window.__є = !!р.блоб; }) && window.__є, null, {timeout: 30000});
    const відповідь = fs.readFileSync(path.join(ТЕКА, 'після', '1', ж + '.txt'), 'utf8');
    await p.evaluate(т => { МІСТ_П.адреса = МІСТ_П.адреса || 'https://міст.невідомий'; МІСТ_П.токен = МІСТ_П.токен || 'проба';
                            window.модельРукиП = async () => т; }, відповідь);
    /* слот портрета пишеться асинхронно: «нема_портрета» одразу після вибору файла — ще раз за 2 с */
    for (let спроба = 0; спроба < 5; спроба++){
      await p.evaluate(() => зчитатиКольориЗПортрета());
      if (await p.evaluate(() => (ПОКАЗ_КОЛЬОРУ_П.напис || {}).код !== 'нема_портрета')) break;
      await p.waitForTimeout(2000);
    }
    await p.waitForFunction(() => СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан && !ПОКАЗ_КОЛЬОРУ_П.читає, null, {timeout: 240000})
      .catch(async e => { console.error('стан:', JSON.stringify(await p.evaluate(() => ({с: СТАН_КОЛЬОРУ_П, п: ПОКАЗ_КОЛЬОРУ_П}))),
                                         помилки, [...обірвано]); throw e; });
    await p.waitForTimeout(1200);
    /* аркуш «Твої кольори» — з огляду профілю, як жінка */
    await p.getByText('Мій профіль').first().click(); await p.waitForTimeout(800);
    await p.locator('button[data-аркуш="кол-блок"]').first().click(); await p.waitForTimeout(1000);
    await p.evaluate(() => $('кол-свотчі').scrollIntoView({block: 'center'}));
    await p.waitForTimeout(400);
    await p.screenshot({path: path.join(знімки, ж + '-профіль-очі.png')});
    підсумок[ж] = await p.evaluate(() => ({
      стан: СТАН_КОЛЬОРУ_П, походження: КОЛІР.походження, походження_очей: КОЛІР.походження_очей,
      колір_очей: КОЛІР.колір_очей, очі: КОЛІР.очі,
      назви: [...document.querySelectorAll('#кол-свотчі .св-назва')].map(в => в.textContent.trim()),
      напис: ($('кол-стан') || {}).textContent || '',
      виміряно_біля_очей: [...document.querySelectorAll('#кол-свотчі .св-назва')]
        .some(в => /^Очі/.test(в.textContent) && /вимір/i.test(в.textContent)),
      свотчі_видно: (r => r.width > 0 && r.height > 0 && r.top < innerHeight && r.bottom > 0)($('кол-свотчі').getBoundingClientRect())}));
    await p.keyboard.press('Escape').catch(() => {});
  }
  const вих = {підсумок, помилки_сторінки: помилки, обірвано: [...обірвано]};
  fs.writeFileSync(path.join(знімки, 'екран.json'), JSON.stringify(вих, null, 1));
  console.log(JSON.stringify(підсумок, null, 1)); console.log('помилок сторінки:', помилки.length);
  await бр.close();
})().catch(e => { console.error(e); process.exit(1); });
