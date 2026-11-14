/* Chromium 390×844, форма «Оціни мій образ»: ті самі дотики ДО й ПІСЛЯ. Міст і мовний шар підмінено;
   вузли, події, файли й клавіші справжні. Запуск: node цей_файл <джерела> <префікс знімків і фактів>. */
const path = require('path'), fs = require('fs');
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
    /* два справжні файли-картинки: їх читає той самий шлях, що й фото з телефона */
    const файл = async (назва, колір) => ({name: назва, mimeType: 'image/png', buffer: Buffer.from(await с.evaluate(к => {
      const п = document.createElement('canvas'); п.width = 60; п.height = 80;
      const х = п.getContext('2d'); х.fillStyle = к; х.fillRect(0, 0, 60, 80);
      return п.toDataURL('image/png').split(',')[1];
    }, колір), 'base64')});
    const перше = await файл('перше.png', '#993333'), друге = await файл('друге.png', '#336699');
    await с.evaluate(() => { режим('оцінка'); });
    const знімок = async н => { if (пр){
      await с.waitForTimeout(300);
      await с.screenshot({path: пр + '_' + н + '.png', animations: 'disabled'});
    } };
    const факт = async н => { факти[н] = await с.evaluate(() => {
      const $$ = і => document.getElementById(і);
      return {
        мініатюр: document.querySelectorAll('#оц-фото .вкладення').length,
        плюс: !!document.querySelector('#оц-фото .оц-плюс'),
        хрестиківВимкнено: [...document.querySelectorAll('#оц-фото .вкладення button')].filter(к => к.disabled).length,
        кнопка: [$$('оц-оцінити').textContent, $$('оц-оцінити').disabled],
        питання: $$('оц-питання').value, нагода: $$('оц-нагода').value, смуга: $$('оц-смуга').value,
        нагоди: [...$$('оц-нагода').options].map(о => о.textContent),
        опади: [...document.querySelectorAll('#оц-опади .чип')].map(ч =>
          [ч.textContent, ч.classList.contains('вибр'), ч.getAttribute('aria-pressed')]),
        стан: $$('оц-стан').textContent,
        сценарій: JSON.stringify(сценарійОцінкиП()),
        фокус: document.activeElement && document.activeElement.id,
        поле_файлів: $$('оц-файл').value,
        фото_моделі: ОЦ.фото.map(ф => ф.ід), іде: ОЦ.іде};
    }); };
    await факт('порожня'); await знімок('порожня');

    /* фото: два файли полем, перше прибрано хрестиком, ще одне — клавішею Enter на «+» */
    await с.setInputFiles('#оц-файл', [перше, друге]);
    await с.waitForFunction(() => ОЦ.фото.length === 2 && document.querySelectorAll('#оц-фото .вкладення').length === 2);
    await факт('два_фото');
    await с.locator('#оц-фото .вкладення button').first().click();
    await с.waitForFunction(() => document.querySelectorAll('#оц-фото .вкладення').length === 1);
    await факт('хрестик');
    const [вибір] = await Promise.all([с.waitForEvent('filechooser'),
      с.locator('#оц-фото .оц-плюс').focus().then(() => с.keyboard.press('Enter'))]);
    await вибір.setFiles([перше]);
    await с.waitForFunction(() => document.querySelectorAll('#оц-фото .вкладення').length === 2);
    await факт('плюс_клавішею');

    /* слова, нагода, погода: рука пише, обирає, торкає чип і знімає його другим дотиком і клавішею */
    await с.fill('#оц-питання', 'чи пасує це на побачення?');
    await с.selectOption('#оц-нагода', 'побачення');
    await с.selectOption('#оц-смуга', 'cool');
    await с.locator('#оц-опади .чип').first().click();
    await факт('названо'); await знімок('названо');
    await с.locator('#оц-опади .чип').first().click();
    await факт('чип_знято');
    await с.locator('#оц-опади .чип').nth(1).focus();
    await с.keyboard.press('Enter');
    await факт('чип_клавішею');
    await с.selectOption('#оц-нагода', {index: 8});
    await факт('інше');
    await с.selectOption('#оц-нагода', 'побачення');

    /* «Оцінити»: порожній профіль — чого бракує; профіль є, токена нема; токен є — хід, збій і відмова */
    await с.locator('#оц-оцінити').click();
    await с.waitForFunction(() => document.getElementById('оц-стан').textContent !== '');
    await факт('бракує');
    await с.evaluate(() => { чогоБракує = () => []; мостуНемаП = () => true; });
    await с.locator('#оц-оцінити').click();
    await с.waitForFunction(() => /токена/.test(document.getElementById('оц-стан').textContent));
    await факт('нема_токена'); await знімок('нема_токена');
    await с.evaluate(() => {
      мостуНемаП = () => false;
      ходомРозмовиП = async () => ({внутрішня: {}, запис: {напрям: 'turn', де: 'review'}});
      містП = (_, д) => new Promise((так, ні) => { window.__кінець = () => ні(window.__кидок); });
      window.__кидок = new Error('стенд');
    });
    await с.locator('#оц-оцінити').click();
    await с.waitForFunction(() => /Роздивляюсь/.test(document.getElementById('оц-стан').textContent));
    /* фокус із вимкненої кнопки браузер знімає на наступному кадрі — факт читаємо після нього */
    await с.evaluate(() => new Promise(р => requestAnimationFrame(() => requestAnimationFrame(р))));
    await факт('іде'); await знімок('іде');
    await с.evaluate(() => window.__кінець());
    await с.waitForFunction(() => !ОЦ.іде);
    await факт('збій'); await знімок('збій');
    await с.evaluate(() => {
      window.__кидок = Object.assign(new Error('відмова'), {повідомлення: {код: 'стенд'}});
      повідомленнямП = async () => ({тексти: {відмова: 'На цих фото я не бачу одягу.'}, записи: []});
    });
    await с.locator('#оц-оцінити').click();
    await с.waitForFunction(() => /Роздивляюсь/.test(document.getElementById('оц-стан').textContent));
    await с.evaluate(() => window.__кінець());
    await с.waitForFunction(() => !ОЦ.іде && /не бачу одягу/.test(document.getElementById('оц-стан').textContent));
    await факт('відмова');

    /* вихід і повернення в режим: форма та сама, що лишила рука */
    await с.evaluate(() => { режим('сценарій'); режим('оцінка'); });
    await факт('повернулась');
    факти.помилки_сторінки = помилки;
    const текст = JSON.stringify(факти, null, 1) + '\n';
    if (пр) fs.writeFileSync(пр + '_факти.json', текст);
    console.log(текст);
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exit(1); });
