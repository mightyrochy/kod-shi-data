/* Прицільна перевірка показу без мережі й моделей; аргумент — корінь перевірюваного дерева. */
const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
const дж = path.join(path.resolve(process.argv[2]), 'джерела');
const ш = require(path.join(дж, 'показ_шаблон.js'));
const html = ш.підставитиШаблон(fs.readFileSync(path.join(дж, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'перевірка 2136', __ВІДБИТОК__: 'a97ceb1',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: ш.прочитатиДовідникJSON(дж)
}).replace(/<script [^>]*src="https:\/\/cdn[^>]*><\/script>/, '');
(async () => {
  const браузер = await chromium.launch({headless: true});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}}), помилки = [];
    сторінка.on('pageerror', п => помилки.push(String(п)));
    await сторінка.route('**/*', р => р.request().url() === 'http://127.0.0.1:9876/'
      ? р.fulfill({contentType: 'text/html; charset=utf-8', body: html}) : р.abort());
    await сторінка.goto('http://127.0.0.1:9876/');
    await сторінка.waitForFunction(() => typeof $('сцн-новий').onclick === 'function');
    await сторінка.evaluate(() => {
      ПРОФІЛЬ_СТВОРЕНО = true;
      КОЛІР.шкіра = '#d7b29b'; КОЛІР.волосся = '#503727'; КОЛІР.очі = '#536149';
      for (const [ід, значення] of Object.entries({'мр-зріст': '170', 'мр-плечі': '40',
        'мр-груди': '92', 'мр-талія': '72', 'мр-стегна': '98'})) $(ід).value = значення;
      ПАСПОРТ_П = {джерело: 'модель', нагода: 'робота', місце: 'парк',
        цитати_полів: {місце: 'у парку'}, джерело_полів: {місце: 'conversation'},
        картка_запиту: {місце: {значення: 'парк', джерело: 'her', уривок: 'у парку'}}};
      застосуватиПаспортДоЕкрана(ПАСПОРТ_П); режим('сценарій');
    });
    await сторінка.locator('#сц-картка').scrollIntoViewIfNeeded();
    await сторінка.screenshot({path: path.join(__dirname, '2136-паспорт-до.png'), animations: 'disabled'});
    const до = await сторінка.evaluate(() => ({паспорт: ПАСПОРТ_П, текст: $('сц-картка').innerText}));
    await сторінка.evaluate(() => { $('сц-місце').value = 'офіс'; рукаТоркнуласьП('сц-місце'); });
    await сторінка.screenshot({path: path.join(__dirname, '2136-паспорт-після.png'), animations: 'disabled'});
    const після = await сторінка.evaluate(() => ({паспорт: ПАСПОРТ_П,
      картка: КАРТКА_ЗАПИТУ_П, текст: $('сц-картка').innerText}));
    assert.equal(до.паспорт.місце, 'парк'); assert.equal(після.паспорт.місце, 'офіс');
    assert.deepStrictEqual(після.картка.місце, {значення: 'офіс', джерело: 'hand', уривок: ''});
    assert.deepStrictEqual(після.паспорт.картка_запиту.місце, після.картка.місце);
    assert.deepStrictEqual(після.паспорт.цитати_полів, {}); assert.deepStrictEqual(помилки, []);
    fs.writeFileSync(path.join(__dirname, '2136-паспорт-екран.json'), JSON.stringify({до, після, помилки}, null, 2) + '\n');
    console.log('Chromium 390×844: парк → офіс; факт hand; уривок порожній; проєкції тотожні; помилок 0.');
  } finally { await браузер.close(); }
})().catch(п => { console.error(п); process.exitCode = 1; });
