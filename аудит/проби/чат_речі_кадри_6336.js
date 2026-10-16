/* Рядок 6336: чат — кожна річ з фото (`оцінитиРечіЗФотоП`) розкодовує фото заново. Справжній Chromium, ЗІБРАНА сторінка,
   міст `річ_з_фото` — заглушка (2 мс), Pyodide не піднімається. Фото — шум 1568×1176 (стеля `МАКС_СТОРОНА_П`, ~260 тис.
   симв. base64), у репліці 2 фото, речей N (3, 5, 8) на першому з рамкою: міряє `performance.now()` навколо циклу речей
   холодним (як є) і з кадрами, розкодованими наперед (`прогрітиКадриП`, як в оцінці), і одне розкодування фото.
   Запуск: NODE_PATH=<тека з playwright> node аудит/проби/чат_речі_кадри_6336.js <тека зі зібраним index.html> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const КОРІНЬ = process.argv[2], БАЗА = 'http://127.0.0.1:8766';
(async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const стор = await (await б.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await стор.route(u => u.origin === БАЗА, r => r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(path.join(КОРІНЬ, 'index.html')) }));
  await стор.route(u => u.origin !== БАЗА, r => r.abort());
  await стор.goto(БАЗА + '/index.html', { waitUntil: 'load', timeout: 180000 });
  await стор.waitForFunction(() => typeof оцінитиРечіЗФотоП === 'function', null, { timeout: 60000 });
  const вих = await стор.evaluate(async () => {
    const фото = ['ф1', 'ф2'].map((ід, i) => { const к = document.createElement('canvas'); к.width = 1568; к.height = 1176;
      const x = к.getContext('2d'), д = x.createImageData(1568, 1176);
      for (let j = 0; j < д.data.length; j += 4){ const v = (j * 2654435761 + i) >>> 24; д.data[j] = v; д.data[j + 1] = (v * 7) & 255; д.data[j + 2] = (v * 13) & 255; д.data[j + 3] = 255; }
      x.putImageData(д, 0, 0); return {ід, тип: 'image/jpeg', дані: к.toDataURL('image/jpeg', 0.6).split(',')[1], ширина: 1568, висота: 1176}; });
    window.містП = async () => { await new Promise(р => setTimeout(р, 2)); return {вердикт: null}; };
    ЧАТ_П.length = 0; ЧАТ_П.push({хто: 'вона', текст: 'ось', фото});
    const т = performance.now(); await розкодуватиФотоП(фото[0]); const одне = performance.now() - т;
    const рядки = [];
    for (const N of [3, 5, 8]){
      const речі = () => Array.from({length: N}, (_, k) => ({ід: 'ф1·' + (k + 1), фото: 'ф1', колір: 'black', рамка: {ліво: 50 * k, верх: 100, право: 50 * k + 300, низ: 700}}));
      ПАСПОРТ_П = {речі_з_фото: речі()};
      let т0 = performance.now(); await оцінитиРечіЗФотоП(); const холодно = performance.now() - т0;
      ПАСПОРТ_П = {речі_з_фото: речі()}; прогрітиКадриП(фото);
      т0 = performance.now(); await оцінитиРечіЗФотоП(); const кеш = performance.now() - т0; звільнитиКадриП();
      рядки.push({речей: N, холодно_мс: Math.round(холодно), з_кадрами_наперед_мс: Math.round(кеш), різниця_мс: Math.round(холодно - кеш)});
    }
    return {символів_фото: фото[0].дані.length, одне_розкодування_мс: Math.round(одне), рядки};
  });
  console.log(JSON.stringify(вих));
  await б.close();
})();
