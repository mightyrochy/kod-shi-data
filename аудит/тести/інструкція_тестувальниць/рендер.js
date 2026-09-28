/* Рендер інструкції в PDF: Chromium друкує `інструкція.html` як A4.
   Запуск:
     CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=/opt/node22/lib/node_modules \
       node рендер.js інструкція.html ../інструкція_тестувальниць_2026-09.pdf
   Мережа потрібна: шрифт Fixel тягнеться з jsDelivr (той самий, що в продукті). */
const { chromium } = require('playwright');
const path = require('path');
const ВХІД = path.resolve(process.argv[2] || 'інструкція.html');
const ВИХІД = path.resolve(process.argv[3] || 'інструкція.pdf');

(async () => {
  const бр = await chromium.launch({executablePath: process.env.CHROMIUM});
  const стор = await (await бр.newContext()).newPage();
  стор.on('console', м => { if (м.type() === 'error') console.log('   консоль:', м.text().slice(0, 160)); });
  await стор.goto('file://' + ВХІД, {waitUntil: 'networkidle', timeout: 120000});
  /* шрифти мають доїхати ДО друку, інакше сторінки ляжуть за системним шрифтом
     і розкладка в PDF поїде проти того, що видно у вікні */
  await стор.evaluate(() => document.fonts.ready);
  const шрифти = await стор.evaluate(() => [...document.fonts].map(ф => ф.family + ' ' + ф.status));
  console.log('шрифти:', JSON.stringify(шрифти));
  await стор.emulateMedia({media: 'print'});
  await стор.pdf({
    path: ВИХІД, format: 'A4', printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;font:9px sans-serif;color:#6B665C;'
      + 'padding:0 16mm;display:flex;justify-content:space-between">'
      + '<span>Люстерко · інструкція для тестувальниць</span>'
      + '<span class="pageNumber"></span></div>',
    margin: {top: '17mm', right: '16mm', bottom: '18mm', left: '16mm'}
  });
  console.log('✔ PDF:', ВИХІД);
  await бр.close();
})().catch(e => { console.error('ПАДІННЯ', e); process.exit(1); });
