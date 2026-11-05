/* Е2: вигляд звичайного стану й наведеної відмови на телефоні.
   node проби/збій_знімки.js <тека знімків>; мережа й моделі не використовуються. */
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {підставитиШаблон, прочитатиДовідникJSON} = require('../показ_шаблон');
const src = path.resolve(__dirname, '..'), вихід = path.resolve(process.argv[2]);
const html = підставитиШаблон(fs.readFileSync(path.join(src, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'проба', __ВІДБИТОК__: 'abc',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(src),
});
(async () => {
  fs.mkdirSync(вихід, {recursive:true});
  const browser = await chromium.launch({headless:true});
  try{
    const page = await browser.newPage({viewport:{width:390, height:844}, deviceScaleFactor:1});
    await page.route('**/*', route => route.request().url() === 'https://example.test/'
      ? route.fulfill({contentType:'text/html; charset=utf-8', body:html}) : route.abort());
    await page.goto('https://example.test/');
    await page.waitForFunction(() => !!document.getElementById('сц-новий').onclick);
    await page.evaluate(() => { режим('бібліотека'); });
    await page.getByText("Ще порожньо. Образи з'являться тут після першого збирання.").waitFor();
    await page.screenshot({path:path.join(вихід, '01-порожня-бібліотека.png'), animations:'disabled'});
    await page.evaluate(async () => {
      window._дб = дб; дб = async () => { throw new Error('storage_read_failed'); };
      await оновитиБібліотеку();
    });
    await page.getByText('Бібліотека не відкрилась. Спробуй ще раз.').waitFor();
    await page.screenshot({path:path.join(вихід, '02-збій-бібліотеки.png'), animations:'disabled'});
    await page.evaluate(async () => {
      дб = window._дб; режим('профіль');
      відкритиАркушПрофілю('др-блок');
      писатиКв = async () => { throw new Error('storage_write_failed'); };
      await писатиКадр();
    });
    assert(await page.getByRole('alert').isVisible());
    assert(await page.getByRole('button', {name:'Зрозуміло', exact:true}).isEnabled());
    await page.screenshot({path:path.join(вихід, '03-збій-запису-в-редакторі.png'), animations:'disabled'});
    await page.getByRole('button', {name:'Зрозуміло', exact:true}).click();
    assert(!(await page.getByRole('alert').isVisible()));
    console.log('390×844: 3 знімки; відмова читання й запису видимі; повідомлення закривається.');
  }finally{ await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
