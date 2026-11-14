/* Chromium 390×844, приміряння на картці образу: ті самі дотики ДО й ПІСЛЯ. Підмінено лише те, чого в сторінці без
   середовища нема: її фото зі сховища (`читатиКв`), міст `приміряння`, модель картинки (`модельП_блоки` — відповідає,
   коли скрипт її відпустить), повернення людини на кадр і мовний шар підпису. Вузли, дотики, гортання, полотно,
   вимір пропорцій кадру (`createImageBitmap`) і збереження образу — справжні.
   Запуск: NODE_PATH=джерела/node_modules node цей_файл <джерела> <префікс знімків і фактів>. */
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
  const річСвг = '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160"><rect width="120" height="160" fill="#eee7df"/>'
    + '<path d="M45 20h30l-6 30 22 90H29l22-90z" fill="#735449"/></svg>';
  const б = await chromium.launch();
  try {
    const с = await б.newPage({viewport: {width: 390, height: 844}, hasTouch: true}), помилки = [], факти = {};
    с.on('pageerror', e => помилки.push(String(e)));
    await с.route('**/*', r => { const у = new URL(r.request().url());
      if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
      if (/\.jpg$/.test(у.pathname)) return r.fulfill({contentType: 'image/svg+xml', body: річСвг});
      return у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
    await с.goto('http://stend.test/');
    await с.waitForFunction(() => Екран.стан.запущено && Екран.стан.вхід > 0, null, {timeout: 60000});

    /* ── образи й підміни ── */
    await с.evaluate(async () => {
      const полотноП = (ш, в, тло) => { const п = document.createElement('canvas'); п.width = ш; п.height = в;
        const к = п.getContext('2d'); к.fillStyle = тло; к.fillRect(0, 0, ш, в);
        const кадрів = Math.max(1, Math.round(ш / (в * 2 / 3)));
        for (let і = 0; і < кадрів; і++){ const х = (і + 0.5) * ш / кадрів;
          к.fillStyle = '#c9a58f'; к.beginPath(); к.arc(х, в * 0.17, в * 0.07, 0, 7); к.fill();
          к.fillStyle = '#5d4a5c'; к.fillRect(х - в * 0.11, в * 0.26, в * 0.22, в * 0.5);
          к.fillStyle = '#23345c'; к.fillRect(х - в * 0.08, в * 0.76, в * 0.16, в * 0.2); }
        return п; };
      window.__пнг = (ш, в) => полотноП(ш, в, '#e9e2d8').toDataURL('image/png').split(',')[1];
      window.__їїФото = await new Promise(r => полотноП(400, 600, '#d8dde2').toBlob(r, 'image/jpeg', 0.8));
      window.__фото = 'є'; window.__запитів = 0; window.__мосту = []; window.__черга = []; window.__ворота = {};
      window.__повернення = 'так'; window.__мова = null;
      window.__відпустити = н => { const в = window.__ворота[н]; if (в) в(); };
      читатиКв = async () => { if (window.__фото === 'збій') throw new Error('пробний збій читання');
        return window.__фото === 'є' ? window.__їїФото : null; };
      const справжнійМіст = містП;
      містП = async (ім, дані) => { if (ім !== 'приміряння') return справжнійМіст(ім, дані);
        window.__мосту.push(JSON.parse(JSON.stringify(дані)));
        return {промпт: JSON.stringify({task: 'ПРИМІРЯННЯ', retry: !!дані.повтор, makeup: дані.макіяж || null})}; };
      модельП_блоки = async (блоки, модель, _, заголовки) => {
        window.__запитів++;
        const в = window.__черга.shift() || {};
        if (в.ворота) await new Promise(r => { window.__ворота[в.ворота] = r; });
        if (в.випало != null && заголовки) заголовки['x-images-dropped'] = String(в.випало);
        if (в.помилка) throw new Error(в.помилка);
        if (в.слова != null) return в.слова ? [{type: 'text', text: в.слова}] : [];
        const [ш, вис] = в.розмір || [400, 600];
        return [{type: 'image', source: {media_type: 'image/png', data: window.__пнг(ш, вис)}}];
      };
      підготуватиПоверненняП = () => Promise.resolve({о: {}});
      повернутиЛюдинуП = async (підготовка, джерело) => {
        await підготовка;
        if (window.__повернення !== 'так') return {звіт: {чому: 'head_mismatch'}};
        const кадр = 'data:' + джерело.media_type + ';base64,' + джерело.data;
        return {кадр, звіт: {збіг_голови: 0.97, символів: кадр.length}};
      };
      const справжняМова = мовоюП;
      мовоюП = async (тексти, де, ...решта) => { if (де !== 'try_on') return справжняМова(тексти, де, ...решта);
        if (window.__мова) await new Promise(r => { window.__ворота[window.__мова] = r; });
        return {тексти: {}, записи: []}; };

      const річ = (ід, назва, слот, фото) => ({id: ід + '@g.com', назва, ціна: 2400, слот, фото,
        урл: 'https://g.com/' + ід});
      const к = (рука, поз, речі) => ({рука, ітерацій: 1, викликів: 1, текст: 'образ ' + рука, опис: 'образ ' + рука,
        підпис: 'образ ' + рука, як_носити: поз === 0 ? ['Пасок — поверх кардигана.'] : [],
        речі, мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
        різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: [],
        збирання: {сід: 7, ключ: '2143', позиція: поз, рука}});
      window.__образи = () => { П = {в: 'ПОКАЗ-V1', збірка: 'тест-8г', каталог: 'каталог_стенд.xml · 639 речей',
        профіль: 'Оля', розклад: '2143', випадок_шматки: [{ключ: 'нагода', текст: 'Робота'}], пул: 100,
        прогін: новийІдПрогону(), картки: [
          к('2', 0, [річ('ж-1', 'Сукня винна', 'сукня', 'https://img.example/1.jpg'),
                     річ('п-1', 'Пасок шкіряний', 'пояс', 'https://img.example/2.jpg')]),
          к('1', 1, [{назва: 'Сукня кольору вина', слот: 'сукня'}]),
          к('4', 2, [річ('ж-3', 'Жакет сірий', 'верх', 'https://img.example/3.jpg'),
                     річ('ч-3', 'Чоботи чорні', 'взуття', 'https://img.example/4.jpg'),
                     річ('ш-3', 'Шарф вовняний', 'шарф', null)])]};
        рендер(); };
      window.__образи();
    });
    await с.waitForSelector('#прмк-0');

    const стан = поз => с.evaluate(поз => {
      const к = document.getElementById('к-' + поз), кн = document.getElementById('прмк-' + поз);
      const пол = document.getElementById('пол-' + поз), кадр = пол.querySelector('img');
      return {рядок: document.getElementById('прм-' + поз).textContent, кнопка_мовчить: кн.disabled,
        туман: пол.querySelectorAll('.туман-примірки').length, кадрів: пол.querySelectorAll('img').length,
        кадр_ширший: кадр ? кадр.naturalWidth > кадр.naturalHeight : null,
        питань_та_сама_річ: к.querySelectorAll('.ряд[data-поле="річ"]').length,
        міток_питання: [...к.querySelectorAll('.мітка')].filter(м => /та сама річ/.test(м.textContent)).length,
        примірка: П.картки[поз].примірка ? {режим: П.картки[поз].примірка.режим, речей: П.картки[поз].примірка.речей,
          всього: П.картки[поз].примірка.всього, без_фото: П.картки[поз].примірка.без_фото,
          кадрів_кілька: П.картки[поз].примірка.кадрів_кілька} : null,
        є_картинка: !!П.картки[поз].картинка, запитів: window.__запитів, мосту: window.__мосту.length,
        слідів: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.вид).filter(в => /tryon|photo_unreadable/.test(в))};
    }, поз);
    const кінець = () => с.evaluate(() => (window.ОСТАННЯ_ДІЯ_П || {}).назва === 'приміряння' ? window.ЯДРО_ДІЯ_П : 0);
    const торкнути = async поз => { const було = await кінець();
      await с.locator('#прмк-' + поз).scrollIntoViewIfNeeded(); await с.locator('#прмк-' + поз).tap(); return було; };
    const дочекатись = було => с.waitForFunction(б => (window.ОСТАННЯ_ДІЯ_П || {}).назва === 'приміряння'
      && window.ЯДРО_ДІЯ_П > б, було, {timeout: 30000});
    const черга = ч => с.evaluate(ч => { window.__черга = ч; }, ч);
    const відпустити = н => с.evaluate(н => window.__відпустити(н), н);
    const чекатиРядок = (поз, зразок) => с.waitForFunction(([поз, зразок]) =>
      new RegExp(зразок).test(document.getElementById('прм-' + поз).textContent), [поз, зразок], {timeout: 30000});
    const знімок = async (назва, поз) => { if (!пр) return;
      await с.locator('#прмк-' + поз).scrollIntoViewIfNeeded(); await с.waitForTimeout(300);
      await с.screenshot({path: пр + '_' + назва + '.png'}); };
    const далі = async () => { await с.locator('#пж-далі').scrollIntoViewIfNeeded(); await с.locator('#пж-далі').tap(); };
    const назад = async () => { await с.locator('#пж-назад').scrollIntoViewIfNeeded(); await с.locator('#пж-назад').tap(); };

    /* 1. фото на повний зріст нема */
    await с.evaluate(() => { window.__фото = 'нема'; });
    let б0 = await торкнути(0); await дочекатись(б0);
    факти.нема_фото = await стан(0);
    /* 2. фото не прочиталось */
    await с.evaluate(() => { window.__фото = 'збій'; });
    б0 = await торкнути(0); await дочекатись(б0);
    факти.фото_не_прочиталось = await стан(0);
    await с.evaluate(() => { window.__фото = 'є'; });

    /* 3. «за фото»: модель малює (ворота), потім кадр, підпис і питання «та сама річ?» */
    await черга([{ворота: 'а'}]);
    б0 = await торкнути(0); await чекатиРядок(0, 'Одягаю');
    факти.за_фото_малює = await стан(0);
    await знімок('малює', 0);
    /* дотик по кнопці, поки приміряння в дорозі, нічого не пускає */
    await с.locator('#прмк-0').tap({force: true});
    факти.дотик_у_дорозі_запитів = (await стан(0)).запитів;
    await с.evaluate(() => { window.__мова = 'м'; });
    await відпустити('а');
    await с.waitForFunction(() => document.querySelectorAll('#пол-0 img').length === 1 && !!window.__ворота['м']);
    await с.waitForTimeout(150);
    факти.за_фото_мова = await стан(0);
    await с.evaluate(() => { window.__мова = null; });
    await відпустити('м'); await дочекатись(б0);
    факти.за_фото_готово = await стан(0);
    await знімок('за_фото', 0);
    /* дотик «так» у питанні «та сама річ?» */
    await с.locator('#к-0 .ряд[data-поле="річ"] .чип').first().scrollIntoViewIfNeeded();
    await с.locator('#к-0 .ряд[data-поле="річ"] .чип').first().tap();
    факти.та_сама_річ = await с.evaluate(() => ({відповідь: В[0].річ,
      обрано: [...document.querySelectorAll('#к-0 .ряд[data-поле="річ"] .чип.вибр')].map(ч => ч.textContent)}));
    /* 4. ще раз на тій самій картці: питання одне, відповідь на місці */
    б0 = await торкнути(0); await дочекатись(б0);
    факти.вдруге = await стан(0);
    факти.вдруге_відповідь = await с.evaluate(() => В[0].річ);

    /* 5. приміряння вдруге падає, коли кадр уже був: що на полотні */
    await черга([{помилка: 'пробний збій моделі'}]);
    б0 = await торкнути(0); await дочекатись(б0);
    факти.збій_після_кадру = await стан(0);
    await знімок('збій_після_кадру', 0);

    /* 6. картку перебудовано, поки приміряння в дорозі (заміна речі перемальовує картку) */
    await черга([{ворота: 'б'}]);
    б0 = await торкнути(0); await чекатиРядок(0, 'Одягаю');
    await с.evaluate(() => перемалюватиКартку(0));
    факти.перебудовано_в_дорозі = await стан(0);
    await знімок('перебудовано_в_дорозі', 0);
    await відпустити('б'); await дочекатись(б0);
    факти.перебудовано_готово = await стан(0);
    await с.evaluate(() => перемалюватиКартку(0));
    факти.перебудовано_після = await стан(0);

    /* 7. «за описом»: речей каталогу нема */
    await далі(); await с.waitForFunction(() => Екран.стан.образ.поз === 1);
    await черга([{ворота: 'в'}]);
    let б1 = await торкнути(1); await чекатиРядок(1, 'Малюю');
    факти.за_описом_малює = await стан(1);
    await відпустити('в'); await дочекатись(б1);
    факти.за_описом_готово = await стан(1);
    await знімок('за_описом', 1);

    /* 8. третя картка: одна річ без фото, крамниця не віддала один знімок */
    await далі(); await с.waitForFunction(() => Екран.стан.образ.поз === 2);
    await черга([{випало: 1}]);
    let б2 = await торкнути(2); await дочекатись(б2);
    факти.без_фото_й_недоїхало = await стан(2);
    await знімок('без_фото', 2);
    /* 9. крамниці не віддали жодного фото */
    await черга([{випало: 2}]);
    б2 = await торкнути(2); await дочекатись(б2);
    факти.крамниці_не_віддали = await стан(2);
    /* 10. модель відповіла словами без картинки; без картинки й без слів */
    await черга([{слова: 'I can not draw this person.'}]);
    б2 = await торкнути(2); await дочекатись(б2);
    факти.слова_без_картинки = await стан(2);
    await черга([{слова: ''}]);
    б2 = await торкнути(2); await дочекатись(б2);
    факти.ні_картинки_ні_слів = await стан(2);
    /* 11. триптих: перший кадр утричі ширший, повтор (ворота) — теж широкий */
    await черга([{розмір: [1200, 600]}, {ворота: 'г', розмір: [900, 600]}]);
    б2 = await торкнути(2); await чекатиРядок(2, 'кілька поруч');
    факти.триптих_повтор = await стан(2);
    await відпустити('г'); await дочекатись(б2);
    факти.триптих_готово = await стан(2);
    await знімок('триптих', 2);
    /* 12. повернути її на кадр не вдалось */
    await с.evaluate(() => { window.__повернення = 'ні'; });
    б2 = await торкнути(2); await дочекатись(б2);
    факти.не_повернуто = await стан(2);
    await знімок('не_повернуто', 2);
    await с.evaluate(() => { window.__повернення = 'так'; });
    /* 13. збій моделі на картці без кадру */
    await черга([{помилка: 'пробний збій моделі'}]);
    б2 = await торкнути(2); await дочекатись(б2);
    факти.збій_без_кадру = await стан(2);

    /* 14. дві картки в дорозі водночас: кожна каже своє */
    await назад(); await с.waitForFunction(() => Екран.стан.образ.поз === 1);
    await черга([{ворота: 'д'}, {ворота: 'е'}]);
    б1 = await торкнути(1); await чекатиРядок(1, 'Малюю');
    await далі(); await с.waitForFunction(() => Екран.стан.образ.поз === 2);
    await с.locator('#прмк-2').scrollIntoViewIfNeeded(); await с.locator('#прмк-2').tap();
    await чекатиРядок(2, 'Одягаю');
    факти.дві_в_дорозі = [await стан(1), await стан(2)];
    await відпустити('д');
    await с.waitForFunction(() => /Намальовано за описом/.test(document.getElementById('прм-1').textContent));
    факти.перша_готова_друга_в_дорозі = [await стан(1), await стан(2)];
    б2 = await кінець(); await відпустити('е'); await дочекатись(б2);
    await с.waitForFunction(() => /Фото речей/.test(document.getElementById('прм-2').textContent));
    факти.обидві_готові = [await стан(1), await стан(2)];

    /* 15. нове збирання, поки приміряння старої картки в дорозі: нова картка на тій самій позиції чиста */
    await черга([{ворота: 'є'}]);
    б2 = await торкнути(2); await чекатиРядок(2, 'Одягаю');
    await с.evaluate(() => window.__образи());
    await с.waitForSelector('#прмк-0');
    б0 = await кінець(); await відпустити('є'); await дочекатись(б0);
    await далі(); await далі(); await с.waitForFunction(() => Екран.стан.образ.поз === 2);
    факти.нове_збирання = await стан(2);

    факти.помилок_сторінки = помилки;
    if (пр) fs.writeFileSync(пр + '_факти.json', JSON.stringify(факти, null, 1) + '\n');
    console.log(JSON.stringify(факти, null, 1));
    console.log(помилки.length ? 'ПОМИЛКИ СТОРІНКИ: ' + помилки.length : 'усі дії пройдено, помилок сторінки 0');
    process.exitCode = помилки.length ? 1 : 0;
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exit(1); });
