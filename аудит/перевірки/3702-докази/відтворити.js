/* Прицільна проба PR #3702 без викликів моделей.
   node відтворити.js <дерево f5fc056> <тека результатів>
   NODE_PATH має вказувати на встановлений playwright; CHROMIUM — за потреби. */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const дерево = path.resolve(process.argv[2]), вихід = path.resolve(process.argv[3]);
const {знімокРук} = require(path.join(дерево, 'аудит/проби/живий-як-людина-1/стенд/руки_зі_сторінки.js'));
(async () => {
  fs.mkdirSync(вихід, {recursive: true});
  const браузер = await chromium.launch({headless: true, ...(process.env.CHROMIUM ? {executablePath: process.env.CHROMIUM} : {})});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}});
    await стор.route('**/*', r => r.request().url() === 'http://127.0.0.1:8765/index.html'
      ? r.fulfill({contentType: 'text/html; charset=utf-8', body: fs.readFileSync(path.join(дерево, 'index.html'))}) : r.abort());
    await стор.goto('http://127.0.0.1:8765/index.html');
    const записи = [];
    async function запис(мітка) {
      const з = await знімокРук(стор);
      записи.push({мітка, ...з});
      console.log(мітка + ': ' + JSON.stringify({прогін: з.прогін, сід: з.сід, ключ: з.ключ,
        готово: з.готово, позицій: з.позиції.length, руки: з.позиції.map(п => п.рука)}));
    }
    await стор.evaluate(() => {
      ЗБ = {ключ: ['3', '1', '2', '4'], вхід_рук: {сід: 111}, картки: [], діагноз: [], готово: false};
      П = null;
    });
    await запис('А-збирається');
    await стор.evaluate(() => {
      const фото = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
      П = {прогін: 'А', розклад: '3124', картки: ЗБ.ключ.map((рука, i) => ({рука,
        речі: [{id: 'річ-' + i, назва: 'Верх', слот: 'top', фото, фото_усі: [фото]}]}))};
      ЗБ.картки = П.картки; ЗБ.готово = true;
      const м = document.createElement('div'); м.id = 'проба'; document.body.prepend(м);
      П.картки.forEach((_, i) => м.appendChild(рендерКартку(i)));
    });
    await запис('А-готово');
    await стор.locator('#к-0').scrollIntoViewIfNeeded();
    await стор.screenshot({path: path.join(вихід, '390x844.png')});
    // Так координатор змінює ЗБ перед новими руками; П і DOM замінює лише після завершення всіх рук.
    await стор.evaluate(() => {
      ЗБ = {ключ: ['4', '2', '1', '3'], вхід_рук: {сід: 222}, картки: [], діагноз: [], готово: false};
    });
    await запис('Б-збирається-П-ще-А');
    await стор.evaluate(() => {
      П = {прогін: 'Б', розклад: '4213', картки: П.картки.map((к, i) => ({...к, рука: ЗБ.ключ[i]}))};
      ЗБ.картки = П.картки; ЗБ.готово = true;
      document.getElementById('проба').replaceChildren(...П.картки.map((_, i) => рендерКартку(i)));
    });
    await запис('Б-готово');
    const службове = path.join(вихід, 'службове', 'с1_проба');
    fs.mkdirSync(службове, {recursive: true});
    fs.writeFileSync(path.join(службове, 'руки.jsonl'), записи.map(з => JSON.stringify(з)).join('\n') + '\n');
    const хибний = записи[2].позиції.filter((п, i) => п.рука !== записи[1].позиції[i].рука).length;
    console.log('Змінено руку старих карток А під час Б: ' + хибний + '/4');
  } finally { await браузер.close(); }
})().catch(e => {console.error(e); process.exitCode = 1;});
