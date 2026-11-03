/* Офлайн-огляд шаблону голови: 390×844, без викликів моделей. */
'use strict';
const fs = require('node:fs'), path = require('node:path');
const голова = path.resolve(process.argv[2]);
const вихід = path.resolve(process.argv[3]);
const код = path.join(голова, 'джерела');
const {chromium} = require(path.join(код, 'node_modules/playwright'));
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(код, 'показ_шаблон.js'));
const html = підставитиШаблон(зібратиШаблонПоказу(path.join(код, 'показ.html')), {
  __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: 'перевірка-2869',
  __ВІДБИТОК__: '9364a5ec90de9937366133f4070f05a26ee6e5c2',
  __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн-огляд',
  __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(код)
}).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/,
  '<script>window.loadPyodide=null;</script>');

(async () => {
  const браузер = await chromium.launch({headless: true, args: ['--disable-gpu'],
    ...(process.platform === 'win32' ? {executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe'} : {})});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    const помилки = [];
    стор.on('pageerror', е => помилки.push(String(е)));
    await стор.route('**/*', р => р.request().url() === 'http://offline.local/'
      ? р.fulfill({contentType: 'text/html; charset=utf-8', body: html}) : р.abort());
    await стор.goto('http://offline.local/');
    await стор.waitForFunction(() => !!document.getElementById('сцн-новий').onclick);
    await стор.evaluate(() => {
      П = {в: 'ПОКАЗ-V1', збірка: 'перевірка-2869', каталог: 'офлайн-огляд', профіль: 'Оля',
        розклад: '1', картки: [{рука: '1', текст: 'Образ на прогулянку.',
          речі: [{id: 'її-с1', назва: 'світлі джинси кльош', слот: 'низ', власна: true,
            чия: 'моя', крій: 'flared', крій_словами: 'звужений до коліна, розширений від коліна'},
          {id: 'ж-00010@gepur.com', назва: 'Підвіска', ціна: 499, слот: 'прикраса',
            колір: 'срібний', код_кольору: 'silvery'}], мітки: [], знахідки: []}]};
      рендер(); режим('образи'); window.scrollTo(0, 0);
    });
    await стор.screenshot({path: вихід, animations: 'disabled'});
    console.log(JSON.stringify({ширина: 390, висота: 844,
      ширина_документа: await стор.evaluate(() => document.documentElement.scrollWidth),
      карток: await стор.locator('#картки .картка').count(), помилки}, null, 2));
    if (помилки.length) process.exitCode = 1;
  } finally { await браузер.close(); }
})().catch(е => {console.error(е); process.exitCode = 1;});
