/* Chromium 390×844, ті самі дотики ДО й ПІСЛЯ. Транспорт і розпізнавач підмінено;
   вузли, події та IndexedDB справжні. Запуск: node цей_файл <джерела> <префікс>. */
const path = require('path'), fs = require('fs'), assert = require('assert').strict;
const {chromium} = require('playwright');
const дж = path.resolve(process.argv[2]), пр = process.argv[3];
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест', __ВІДБИТОК__: 'abc',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch();
  try {
    const с = await б.newPage({viewport: {width: 390, height: 844}}), помилки = [], факти = {};
    с.on('pageerror', e => помилки.push(String(e)));
    await с.route('**/*', r => new URL(r.request().url()).pathname === '/'
      ? r.fulfill({contentType: 'text/html', body: html}) : r.abort());
    await с.goto('http://stend.test/');
    await с.waitForFunction(() => Екран.стан.запущено && Екран.стан.вхід > 0);
    await с.evaluate(async () => {
      режим('оцінка');
      window.__дії = []; window.__далі = null;
      містП = async (_, д) => {
        if (д.крок === 'перелік') return {hex: {а: '#663333', н1: '#336699'}, довідник: {
          слоти: [{ключ: 'сукня', код: 'dress'}, {ключ: 'взуття', код: 'shoes'}],
          кольори: [{ключ: 'червоний', код: 'red', hex: '#993333', часто: true},
            {ключ: 'синій', код: 'blue', hex: '#333399', часто: false}]}};
        if (д.крок === 'виправити') {
          window.__дії.push(...д.дії);
          let речі = д.речі.map(р => ({...р}));
          const дії = д.дії.map(х => {
            const ід = х.item || 'н1';
            if (х.op === 'add') речі.push({ід, слот: 'сукня', джерело: 'her', в_образі: true});
            if (х.op === 'remove') речі = речі.filter(р => р.ід !== ід);
            const р = речі.find(р => р.ід === ід);
            if (р && х.color) р.колір = х.color === 'blue' ? 'синій' : 'червоний';
            if (р && х.slot) р.слот = х.slot === 'shoes' ? 'взуття' : 'сукня';
            if (р && 'in_outfit' in х) р.в_образі = х.in_outfit;
            if (р && х.photo) { р.фото = х.photo; р.рамка = {ліво: 465, верх: 465, право: 535, низ: 535}; р.дотик = true; }
            return {...х, ід, поле: х.photo ? 'фото' : х.color ? 'колір' : 'слот'};
          });
          return {речі, дії, лічильник: 1};
        }
        if (д.крок === 'допит_промпт') return {промпт: 'стенд'};
        if (д.крок === 'допит') return {відповідь: 'Спробуй синю сумку.'};
        return {};
      };
      перекластиП = async () => ({внутрішня: {actions: [{op: 'set', item: 'а', in_outfit: true}]}, запис: {}});
      мовоюП = async т => ({тексти: т, записи: []});
      викликОцінкиП = async () => { if (window.__збій) throw new Error('стенд'); return 'стенд'; };
      const к = document.createElement('canvas'); к.width = к.height = 100;
      к.getContext('2d').fillRect(0, 0, 100, 100);
      ОЦ.фото = [{ід: 'ф1', тип: 'image/png', дані: к.toDataURL().split(',')[1]}];
      ОЦ.етапи = {мова_шару: []}; ОЦ.результат = null;
      await показатиПерелікП([{ід: 'а', слот: 'сукня', назва: 'Сукня', колір: 'червоний', в_образі: true}]);
      ОЦ.перелік.контекст = {пікселі: {}, пікселі_фото: {}, база: {}};
      window.__поле = document.getElementById('оц-слова-поле');
      window.SpeechRecognition = class {
        start(){ window.__мік = this; if (this.onstart) this.onstart(); }
        stop(){ window.__зупинок = (window.__зупинок || 0) + 1; if (this.onend) this.onend(); }
        abort(){ window.__зупинок = (window.__зупинок || 0) + 1; if (this.onend) this.onend(); }
      };
    });
    const знімок = async н => { if (пр){
      await с.waitForTimeout(400);
      await с.screenshot({path: пр + '_' + н + '.png', animations: 'disabled'});
    } };
    const факт = async н => { факти[н] = await с.evaluate(() => ({
      рядки: [...document.querySelectorAll('#оц-речі .оц-річ')].map(р => р.textContent),
      відкр: [...document.querySelectorAll('#оц-речі .оц-річ')].map(р => р.getAttribute('aria-expanded')),
      полеТеСаме: window.__поле === document.getElementById('оц-слова-поле'),
      слова: document.getElementById('оц-слова-поле')?.value,
      статус: document.getElementById('оц-слова-стан')?.textContent,
      коди: window.__дії})); };
    await знімок('перелік'); await факт('початок');
    await с.locator('.оц-річ').click();
    await с.locator('.оц-ред .оц-чипи').first().getByText('Взуття', {exact: true}).click();
    await с.waitForFunction(() => ОЦ.перелік.речі[0].слот === 'взуття');
    await с.locator('.оц-кола').getByText('ще', {exact: true}).click();
    await с.locator('.оц-коло[data-код="blue"]').click();
    await с.waitForFunction(() => ОЦ.перелік.речі[0].колір === 'синій');
    await с.locator('.оц-ред').getByText('Замість', {exact: true}).click();
    await с.waitForFunction(() => ОЦ.перелік.речі[0].в_образі === false);
    await факт('редактор'); await знімок('редактор');
    await с.locator('#оц-слова-мік').click();
    await с.evaluate(() => window.__мік.onresult({results: [{0: {transcript: 'залиши в образі'}, isFinal: true, length: 1}]}));
    assert.equal(await с.locator('#оц-слова-поле').inputValue(), 'залиши в образі');
    await с.locator('#оц-слова-мік').click();
    await с.locator('#оц-слова-слати').click();
    await с.waitForFunction(() => !ОЦ.перелік.словаЙде && ОЦ.перелік.речі[0].в_образі);
    await факт('голос');
    факти.голос.спосіб = await с.evaluate(() => ОЦ.перелік.звіт.слова[0].спосіб);
    assert.equal(факти.голос.спосіб, 'voice');
    await с.locator('#оц-слова-поле').fill('Залиши цю річ.');
    await с.evaluate(() => {
      малюватиПерелікП();
      перекластиП = async () => { throw new Error('стенд'); };
    });
    assert.equal(await с.locator('#оц-слова-поле').inputValue(), 'Залиши цю річ.');
    await с.locator('#оц-слова-слати').click();
    await с.waitForFunction(() => !ОЦ.перелік.словаЙде);
    факти.збійСлів = await с.evaluate(() => ({
      поле: document.getElementById('оц-слова-поле').value,
      кнопка: document.getElementById('оц-слова-слати').disabled,
      статус: document.getElementById('оц-слова-стан').textContent,
      слідів: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.filter(з => з.вид === 'items_fix_not_read').length
    }));
    assert.equal(факти.збійСлів.слідів, 1);
    await с.evaluate(() => { перекластиП = async () => ({внутрішня: {}, запис: {}}); });
    await с.locator('#оц-плюс-річ').click();
    await с.locator('#оц-додати').getByText('Сукня', {exact: true}).click();
    await с.waitForFunction(() => ОЦ.перелік.речі.length === 2);
    await с.locator('.оц-дотик img').click({position: {x: 30, y: 30}});
    await с.waitForFunction(() => ОЦ.перелік.речі.some(р => р.дотик));
    await факт('додано');
    await с.locator('.оц-річ').last().getByRole('button', {name: 'Прибрати', exact: true}).click();
    await с.waitForFunction(() => ОЦ.перелік.речі.length === 1);
    await факт('прибрано');
    await с.evaluate(() => {
      ОЦ.результат = {картка: {відповідь: 'Тобі пасує.', вдало: [{текст: 'Гарні кольори.'}],
        не_знаю: [{текст: 'Не знаю нагоди.'}]}, сценарій: {}, суд: {образ: ['а'], речі: ОЦ.перелік.речі}, допит: []};
    });
    await с.locator('#оц-слова-мік').click();
    const зупинокДоТак = await с.evaluate(() => window.__зупинок || 0);
    await с.locator('#оц-так').click();
    факти.мікрофонПісляТак = await с.evaluate(() => window.__зупинок || 0) - зупинокДоТак;
    assert.equal(факти.мікрофонПісляТак, 1);
    assert.equal(await с.locator('#оц-речі').isVisible(), false);
    assert.equal(await с.locator('#оц-картка').count(), 1);
    await с.locator('#оц-допит-поле').fill('Яку сумку взяти?');
    await с.locator('#оц-допит-слати').click();
    await с.waitForFunction(() => !ОЦ.іде && ОЦ.результат.допит[0].відповідь);
    факти.допит = await с.locator('#оц-допит-стрічка').innerText();
    await с.evaluate(() => { window.__збій = true; });
    await с.locator('#оц-допит-поле').fill('А взуття?');
    await с.locator('#оц-допит-слати').click();
    await с.waitForFunction(() => !ОЦ.іде);
    факти.збій = await с.locator('#оц-допит-стан').innerText();
    await с.locator('#ком-оц').fill('Дуже зручний образ.');
    await с.evaluate(() => {
      window.__tx = tx;
      tx = async (б, сх, режим, дія) => {
        if (сх === 'вердикти' && режим === 'readwrite') throw new Error('стенд');
        return window.__tx(б, сх, режим, дія);
      };
    });
    await с.locator('#зап-оц').click();
    await с.waitForFunction(() => ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.some(з => з.вид === 'not_written'));
    факти.збійЗапису = await с.evaluate(() => ({
      статус: document.getElementById('вст-оц').textContent,
      кнопка: document.getElementById('зап-оц').disabled,
      слідів: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.filter(з => з.вид === 'not_written').length
    }));
    assert.equal(факти.збійЗапису.слідів, 1);
    await с.evaluate(() => { tx = window.__tx; });
    await с.locator('#зап-оц').click();
    await с.waitForFunction(() => відповідь('оц').записано);
    факти.запис = await с.evaluate(async () => {
      const з = await tx(await дб(), 'вердикти', 'readonly', s => s.getAll());
      return {коментар: з[0].коментар, рука: з[0].рука, кнопка: document.getElementById('зап-оц').disabled};
    });
    await знімок('картка');
    факти.помилки = помилки; assert.deepEqual(помилки, []);
    if (пр) fs.writeFileSync(пр + '_факти.json', JSON.stringify(факти, null, 2) + '\n');
    console.log(JSON.stringify(факти, null, 2));
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
