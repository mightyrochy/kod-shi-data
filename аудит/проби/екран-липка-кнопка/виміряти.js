/* Вимір вади 15984: перекриття тексту відгуку липкою кнопкою «Записати вердикт» (`.ряд-запису`, джерела/показ.css).
   Збирає показ так, як стенд (`джерела/тест_показу.js`: показ_шаблон.js → шаблон із підставленими плейсхолдерами,
   Pyodide і мережі нема), відкриває СПРАВЖНІЙ Chromium, ставить картку `П = {картки:[…]}` → `рендер()`.
   Запуск: cd джерела && NODE_PATH=node_modules node ../аудит/проби/екран-липка-кнопка/виміряти.js <тека-знімків|-> [екран: картка|оцінка|перелік]
   Стани (кожен на ширині 360, 768, 1280):
     1 «введено»   — вікно 800, текст щойно введено у поле (картка прокручена так, що поле починається вгорі);
     2 «до кінця»  — сторінку прокручено до кінця тексту: `scrollIntoView({block:'end'})` на полі (браузер зупиняє кінець поля там, де дозволяє scroll-margin-bottom поля; без нього — впритул до низу вікна);
     3 «клавіатура»— вікно заввишки 400 (відкрита клавіатура), поле у фокусі, курсор у кінці тексту, браузер сам доводить курсор до видимого.
   Перекриття, px = висота перетину прямокутника поля відгуку (textarea.поле-вердикту) з прямокутником кнопки (#зап-N),
   обрізаних вікном; кнопка видима = її прямокутник цілком у вікні й верхній елемент у її центрі — вона. */
const fs = require('fs'), path = require('path');
const корінь = path.resolve(__dirname, '../../..');
const {chromium} = require(require.resolve('playwright', {paths: [process.cwd(), '/usr/local/lib/node_modules_global']}));
const {підставитиШаблон, зібратиШаблонПоказу, прочитатиДовідникJSON} = require(path.join(корінь, 'джерела/показ_шаблон.js'));
const ТЕКСТ = Array.from({length: 14}, (_, і) => `Рядок ${і + 1}: ця сукня мені личить, але в плечах трохи тісна, а колір вечірній.`).join('\n');
const КАРТКА = {рука: '1', текст: 'Образ', опис: 'Сукня й мюлі в одному тоні.', як_носити: ['Заправити'], схема_жінці: '', матеріал_жінці: '',
  речі: [{id: 'ж-1@gepur.com', назва: 'Сукня', ціна: 3000, слот: 'сукня', фото: null}], мітки: [], знахідки: [], питання: [], етапи: {},
  свідомі: [], фото_не_ті: [], дібрав_код_слоти: []};
const екран = process.argv[3] || 'картка';

(async () => {
  const тека = process.argv[2] && process.argv[2] !== '-' ? path.resolve(process.argv[2]) : null;
  if (тека) fs.mkdirSync(тека, {recursive: true});
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(корінь, 'джерела/показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'вимір', __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml',
    __КАТАЛОГ_ПОКАЗУ__: 'вимір', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(path.join(корінь, 'джерела'))})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch(), вихід = [];
  for (const ш of [360, 768, 1280]) for (const стан of ['введено', 'до кінця', 'клавіатура']) {
    const вис = стан === 'клавіатура' ? 400 : 800;
    const к = await б.newContext({viewport: {width: ш, height: вис}, deviceScaleFactor: 1, hasTouch: ш < 1000, isMobile: ш < 1000});
    const с = await к.newPage(); const АДРЕСА = 'https://mightyrochy.github.io/kod-shi-data/показ.html';
    await с.route('**/*', р => decodeURI(р.request().url()) === АДРЕСА ? р.fulfill({contentType: 'text/html', body: html}) : р.abort());
    await с.goto(АДРЕСА); await с.waitForFunction(() => typeof Екран !== "undefined" && Екран.стан.запущено === true, null, {timeout: 20000});
    await с.evaluate(({к, т, екр}) => {
      if (екр === 'картка') { П = {картки: [к]}; П.прогін = новийІдПрогону(); рендер(); }
      else if (екр === 'оцінка') {   /* справжній будівник блоку вердикту оцінки фото в порожній колонці */
        document.querySelectorAll('.екран').forEach(е => { е.style.display = 'none'; });
        const к = document.createElement('div'); к.className = 'колонка'; к.id = 'вимір-оцінка'; document.body.prepend(к);
        к.appendChild(вердиктОцінкиП());
      }
      else if (екр === 'перелік') {  /* справжні рядки переліку речей (`блокРечіП`) і кнопка «Так, оцінюй» (`.оц-так`) */
        document.querySelectorAll('.екран').forEach(е => { е.style.display = 'none'; });
        const к = document.createElement('div'); к.className = 'колонка оц-речі'; к.id = 'оц-речі'; document.body.prepend(к);
        for (let і = 0; і < 12; і++) { const б = блокРечіП('р' + і); б.слот.textContent = 'слот ' + і; б.назва.textContent = 'Річ номер ' + і + ' із довгою назвою'; к.appendChild(б.блок); }
        const так = document.createElement('button'); так.className = 'далі головна оц-так'; так.id = 'оц-так'; так.textContent = 'Так, оцінюй'; к.appendChild(так);
      }
      const та = document.getElementById(екр === 'перелік' ? 'оц-так' : 'ком-' + (екр === 'картка' ? 0 : 'оц'));
      if (екр !== 'перелік') { та.value = т; та.dispatchEvent(new Event('input', {bubbles: true})); ростиПолеП(та); }
    }, {к: КАРТКА, т: ТЕКСТ, екр: екран});
    await с.waitForTimeout(500);
    const id = екран === 'картка' ? '0' : 'оц', перелік = екран === 'перелік';
    await с.evaluate(({стан, id, перелік}) => {
      const рядки = [...document.querySelectorAll('.оц-річ')];
      const та = перелік ? рядки[рядки.length - 1] : document.getElementById('ком-' + id), р = та.getBoundingClientRect();
      if (перелік) { if (стан === 'введено') scrollTo(0, scrollY + document.getElementById('оц-речі').getBoundingClientRect().top - 8); else if (стан === 'до кінця') та.scrollIntoView({block: 'end'}); else { scrollTo(0, 0); та.focus(); } return; }
      if (стан === 'введено') scrollTo(0, scrollY + р.top - 8);
      else if (стан === 'до кінця') та.scrollIntoView({block: 'end'}); /* так браузер показує кінець поля: повага до scroll-margin */
      else { scrollTo(0, scrollY + р.top - 8); та.focus(); та.setSelectionRange(та.value.length, та.value.length); }
    }, {стан, id, перелік});
    if (стан === 'клавіатура' && !перелік) { await с.keyboard.press('End'); await с.keyboard.type(' ще слово'); }
    await с.waitForTimeout(500);
    const м = await с.evaluate(({id, перелік}) => {
      const та = перелік ? document.getElementById('оц-речі') : document.getElementById('ком-' + id), кн = document.getElementById(перелік ? 'оц-так' : 'зап-' + id);
      const а = та.getBoundingClientRect(), в = кн.getBoundingClientRect(), H = innerHeight;
      let верх = Math.max(а.top, в.top, 0), низ = Math.min(а.bottom, в.bottom, H);
      if (перелік) { верх = 0; низ = 0; for (const р of document.querySelectorAll('.оц-річ')) { const q = р.getBoundingClientRect(); низ += Math.max(0, Math.min(q.bottom, в.bottom, H) - Math.max(q.top, в.top, 0)); } }
      const ц = document.elementFromPoint(в.left + в.width / 2, Math.min(Math.max(в.top + в.height / 2, 0), H - 1));
      return {перекриття: Math.max(0, Math.round(низ - верх)), поле: [Math.round(а.top), Math.round(а.bottom)], кнопка: [Math.round(в.top), Math.round(в.bottom)],
        видима: в.top >= 0 && в.bottom <= H && !!ц && (ц === кн || кн.contains(ц)), прокрутка: Math.round(scrollY), вікно: H};
    }, {id, перелік});
    вихід.push({ширина: ш, стан, ...м});
    if (тека && стан === 'до кінця' && (ш === 360 || ш === 1280)) await с.screenshot({path: path.join(тека, `${екран}_${ш}_до-кінця.png`)});
    await к.close();
  }
  await б.close();
  console.log(JSON.stringify(вихід));
  const найб = Math.max(...вихід.map(х => х.перекриття));
  console.log(`перекриття: найбільше ${найб} px; нуль у ${вихід.filter(х => !х.перекриття).length} з ${вихід.length}; кнопка видима ${вихід.filter(х => х.видима).length} з ${вихід.length}`);
})();
