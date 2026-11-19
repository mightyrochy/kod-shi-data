/* Незалежна проба записувача #3702 без моделей.
   node відтворити.js <дерево голови PR> <тека результатів> */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const дерево = path.resolve(process.argv[2]), вихід = path.resolve(process.argv[3]);
const {знімокРук, доЗавантажитиФото} = require(path.join(дерево, 'аудит/проби/живий-як-людина-1/стенд/руки_зі_сторінки.js'));
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
      if (з) записи.push({мітка, ...з});
      console.log(мітка + ': ' + JSON.stringify(з && {прогін: з.прогін, сід: з.сід, ключ: з.ключ,
        діагноз: з.поломка_руки_2.діагноз, готово: з.готово, руки: з.позиції.map(п => п.рука)}));
      return з;
    }
    await стор.evaluate(() => { П = null; ЗБ = null; });
    await запис('Без-П');
    const сіди = await стор.evaluate(() => {
      const ключ = перемішатиП(['1', '2', '3', '4'], 4242).join('');
      let інший = 0, відмінний = 0;
      while (інший === 4242 || перемішатиП(['1', '2', '3', '4'], інший).join('') !== ключ) інший++;
      while (перемішатиП(['1', '2', '3', '4'], відмінний).join('') === ключ) відмінний++;
      return {а: 4242, б: інший, відмінний, ключ};
    });
    console.log('Сіди справжньої перемішатиП: ' + JSON.stringify(сіди));
    await стор.evaluate(({а}) => {
      const фото = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
      const ключ = перемішатиП(['1', '2', '3', '4'], а);
      П = {прогін: 'А', розклад: ключ.join(''), картки: ключ.map((_, i) => ({
        речі: [{id: 'річ-' + i, назва: 'Верх ' + i, слот: 'top', фото, фото_усі: [фото]}]}))};
      ЗБ = {ключ, картки: П.картки, вхід_рук: {сід: а}, готово: true,
        діагноз: ['control · hand_2_broken=K-CRA-01'], поломка: {коди: ['K-CRA-01']}};
      const м = document.createElement('div'); м.id = 'проба'; document.body.prepend(м);
      П.картки.forEach((_, i) => м.appendChild(рендерКартку(i)));
    }, сіди);
    await доЗавантажитиФото(стор);
    await стор.waitForTimeout(100);
    const а = await запис('А-готово');
    await стор.locator('#к-0').scrollIntoViewIfNeeded();
    await стор.screenshot({path: path.join(вихід, '390x844.png')});
    await стор.evaluate(({відмінний}) => {
      ЗБ = {ключ: перемішатиП(['1', '2', '3', '4'], відмінний), вхід_рук: {сід: відмінний},
        картки: [], діагноз: [], готово: false};
    }, сіди);
    const різні = await запис('Інший-ключ-П-ще-А');
    await стор.evaluate(({б}) => {
      ЗБ = {ключ: перемішатиП(['1', '2', '3', '4'], б), вхід_рук: {сід: б}, картки: [], готово: false,
        діагноз: ['control · hand_2_broken=K-SIL-03'], поломка: {коди: ['K-SIL-03']}};
    }, сіди);
    const колізія = await запис('Б-однаковий-ключ-П-ще-А');
    console.log('Руки А при іншому ключі: ' + різні.позиції.filter((п, i) => п.рука === а.позиції[i].рука).length + '/4 правильні');
    console.log('Сід А підмінено: ' + а.сід + ' -> ' + колізія.сід);
    console.log('Поломку А підмінено: ' + а.поломка_руки_2.діагноз.join('') + ' -> ' + колізія.поломка_руки_2.діагноз.join(''));
    const службове = path.join(вихід, 'службове', 'с1_проба');
    fs.mkdirSync(службове, {recursive: true});
    fs.writeFileSync(path.join(службове, 'руки.jsonl'), записи.map(з => JSON.stringify(з)).join('\n') + '\n');
  } finally { await браузер.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
