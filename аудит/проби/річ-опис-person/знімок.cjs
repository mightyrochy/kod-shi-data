// Поточна повна збірка з записаним виходом ендпойнта попереднього кроку, без мережі.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const {pathToFileURL} = require('url');
const джерело = path.join(__dirname, '../річ-утримання/шлях-після.json.gz');
const записи = JSON.parse(zlib.gunzipSync(fs.readFileSync(джерело)));
const запис = записи.find(з => з.профіль.startsWith('ж4') && !Object.keys(з.самозвіт).length);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
  const помилки = [];
  page.on('pageerror', e => помилки.push(String(e)));
  await page.route(/^https?:/, route => route.abort());
  await page.goto(pathToFileURL(process.argv[2]).href);
  await page.waitForFunction(() => typeof оновитиПалітруП === 'function');
  await page.evaluate(async р => {
    Object.assign(КОЛІР, {шкіра: '#d7b59c', волосся: ['#30251e'], очі: '#493024'});
    містП = async ім => ім === 'палітри' ? р : {};
    режим('палітра');
    await оновитиПалітруП();
  }, запис.палітра);
  await page.locator('#пал-схема .чип').first().waitFor();
  await page.locator('#пал-вступ').scrollIntoViewIfNeeded();
  await page.screenshot({path: path.join(__dirname, 'палітра-390.png')});
  fs.writeFileSync(path.join(__dirname, 'знімок.json'), JSON.stringify({помилки, ширина: 390,
    висота: 844, дані: джерело, збірка: process.argv[2]}, null, 2));
  await browser.close();
  console.log('знімок 390×844; помилок сторінки:', помилки.length);
  if (помилки.length) process.exitCode = 1;
})().catch(e => {console.error(e); process.exitCode = 1;});
