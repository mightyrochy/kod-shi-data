/* Chromium 390×844, зріз 10а: панель сповіщення збою (`збій-панель`) — ті самі збої ДО й ПІСЛЯ. Збій викликано
   підміною сховища (`писатиАктивний`, `писатиКв`, `читатиКв`, `дб`), решта — справжнє: вузли, аркуш, дотик
   «Зрозуміло». Друга сторінка — сховище недоступне на старті.
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
  const б = await chromium.launch();
  try {
    const помилки = [], факти = {};
    const сторінка = async підготувати => {
      const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
      const с = await к.newPage();
      с.on('pageerror', e => помилки.push(String(e)));
      if (підготувати) await с.addInitScript(підготувати);
      await с.route('**/*', r => { const у = new URL(r.request().url());
        if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
        return у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
      return с;
    };
    const с = await сторінка();
    await с.goto('http://stend.test/');
    await с.waitForFunction(() => Екран.стан.запущено && Екран.стан.вхід > 0, null, {timeout: 60000});
    const стан = () => с.evaluate(() => {
      const п = document.getElementById('збій-панель');
      return {текст: document.getElementById('збій-стан').textContent,
        видно: getComputedStyle(п).display !== 'none', батько: п.parentNode.id || п.parentNode.tagName,
        неактивна: п.hasAttribute('inert') || !!п.closest('[inert]'),
        аркуш_відкрито: !document.getElementById('аркуш').hidden,
        сліди: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.вид + ': ' + з.причина)};
    });
    const зрозуміло = async () => { await с.locator('#збій-прибрати').tap(); return стан(); };
    const знімок = async назва => { if (пр){ await с.waitForTimeout(200); await с.screenshot({path: пр + '_' + назва + '.png'}); } };
    await с.evaluate(() => { window.__справжнє = {писатиАктивний, писатиКв, читатиКв, дб};
      window.__збій = ім => { const е = () => { throw new Error('проба: ' + ім); };
        if (ім === 'писатиАктивний') писатиАктивний = async () => е();
        if (ім === 'писатиКв') писатиКв = async () => е();
        if (ім === 'читатиКв') читатиКв = async () => е();
        if (ім === 'дб') дб = async () => е(); };
      window.__лагодити = () => { ({писатиАктивний, писатиКв, читатиКв, дб} = window.__справжнє); };
      режим('профіль'); });

    /* 1. запис кольорів не вдався */
    await с.evaluate(async () => { window.__збій('писатиАктивний'); await писатиКолір(); });
    факти.колір = await стан(); await знімок('колір');
    факти.колір_зрозуміло = await зрозуміло();
    /* 2. запис відповідей драпірування */
    await с.evaluate(async () => { await писатиДрап(); });
    факти.драп = await стан(); await зрозуміло();
    /* 3. запис кадру фото */
    await с.evaluate(async () => { window.__лагодити(); window.__збій('писатиКв'); await писатиКадр(); });
    факти.кадр = await стан(); await зрозуміло();
    /* 4. фото не збереглось */
    await с.evaluate(async () => { window.__лагодити(); window.__збій('дб');
      await зберегтиФотоП('портрет', new Blob(['x'], {type: 'image/jpeg'})); });
    факти.фото = await стан(); await зрозуміло();
    /* 5. сховище не прочиталось */
    await с.evaluate(async () => { window.__лагодити(); window.__збій('читатиКв');
      await читатиКв_('кадр').catch(e => { window.__далі = String(e.message); }); });
    факти.читання = Object.assign(await стан(), {виняток_далі: await с.evaluate(() => window.__далі)});
    await зрозуміло();
    /* 6. збій запису оцінки («загальне») — слід лишає логіка, панель малює екран оцінки */
    await с.evaluate(() => { window.__лагодити(); показатиЗбійФотоОцінки('загальне', 'not_written', new Error('проба: оцінка')); });
    факти.оцінка_загальне = await стан(); await зрозуміло();
    /* 7. редактор відкрито аркушем: сповіщення всередині аркуша й доступне */
    await с.evaluate(() => відкритиПрофіль('кол-блок'));
    await с.waitForFunction(() => !document.getElementById('аркуш').hidden, null, {timeout: 10000});
    await с.evaluate(async () => { window.__збій('писатиАктивний'); await писатиКолір(); window.__лагодити(); });
    факти.в_аркуші = await стан(); await знімок('в_аркуші');
    факти.в_аркуші_зрозуміло = await зрозуміло();
    await с.evaluate(async () => { window.__збій('писатиАктивний'); await писатиКолір(); window.__лагодити(); });
    await с.evaluate(() => закритиАркуш());
    await с.waitForFunction(() => document.getElementById('аркуш').hidden, null, {timeout: 10000});
    факти.після_аркуша = await стан();
    факти.після_аркуша_зрозуміло = await зрозуміло();
    /* 8. збій, показаний з екрана (знімок слота не прочитався), і ще раз без аркуша */
    await с.evaluate(() => { показатиЗбійЗапису('photo_unreadable', new Error('проба: слот')); });
    факти.з_екрана = await стан(); await зрозуміло();

    /* 9. сховище недоступне на старті */
    const д = await сторінка(() => { Object.defineProperty(window, 'indexedDB', {get(){
      return {open(){ throw new Error('проба: сховище недоступне'); }}; }}); });
    await д.goto('http://stend.test/');
    await д.waitForFunction(() => document.getElementById('збій-стан').textContent !== '', null, {timeout: 60000});
    факти.збій_старту = await д.evaluate(() => ({текст: document.getElementById('збій-стан').textContent,
      батько: document.getElementById('збій-панель').parentNode.tagName, вхід: Екран.стан.вхід > 0,
      сліди: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.вид)}));
    await д.locator('#збій-прибрати').tap();
    факти.збій_старту_прибрано = await д.evaluate(() => document.getElementById('збій-стан').textContent);

    /* 10. чужа адреса мосту в посиланні: питання над усім, «Так» / «Ні» / Esc і що лишилось у сховищі */
    for (const [назва, дія] of [['так', 1], ['ні', 0], ['esc', null]]){
      const м = await сторінка();
      await м.goto('http://stend.test/#міст=' + encodeURIComponent('https://чужий.test/api'));
      await м.waitForSelector('dialog[open]', {timeout: 60000});
      const питання = await м.evaluate(() => { const д = document.querySelector('dialog');
        return {заголовок: д.querySelector('h2').textContent, підпис: д.getAttribute('aria-labelledby'),
          адреса: д.querySelector('p').textContent, кнопки: [...д.querySelectorAll('button')].map(к => к.textContent),
          модальне: д.matches(':modal'), вхід_до_відповіді: Екран.стан.вхід > 0}; });
      if (назва === 'так') await м.screenshot({path: пр + '_міст_питання.png'});
      if (дія === null) await м.keyboard.press('Escape');
      else await м.locator('dialog button').nth(дія).tap();
      await м.waitForFunction(() => Екран.стан.запущено && Екран.стан.вхід > 0, null, {timeout: 60000});
      факти['міст_' + назва] = Object.assign(питання, await м.evaluate(() => ({
        діалогів: document.querySelectorAll('dialog').length,
        збережено: localStorage.getItem('міст:адреса'), міст: МІСТ_П.адреса})));
    }

    факти.помилок_сторінки = помилки;
    if (пр) fs.writeFileSync(пр + '_факти.json', JSON.stringify(факти, null, 1) + '\n');
    console.log(помилки.length ? 'ПОМИЛКИ СТОРІНКИ: ' + помилки.join(' | ') : 'усі дії пройдено, помилок сторінки 0');
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exit(1); });
