const fs = require('fs'), path = require('path'), Module = require('module');
const корінь = process.cwd(), етап = process.argv[2], вихід = path.join(process.env.TEMP, 'е2-' + етап);
fs.mkdirSync(вихід, {recursive: true});
const файл = path.join(корінь, 'джерела', 'тест_показу.js');
const префікс = fs.readFileSync(файл, 'utf8').split('(async () => {')[0]
  .replace('const ЗІБРАНИЙ = process.argv[2] ? path.resolve(process.argv[2]) : null;', 'const ЗІБРАНИЙ = null;');
const модуль = new Module(файл); модуль.filename = файл; модуль.paths = Module._nodeModulePaths(path.dirname(файл));
модуль._compile(префікс + '\nmodule.exports = {сторінка, чекатиСтарт};', файл);
(async () => {
  const {w, d, помилки} = модуль.exports.сторінка({url: 'https://mightyrochy.github.io/kod-shi-data/показ.html#модель_мови=нема'});
  await модуль.exports.чекатиСтарт(w);
  const записи = [], відхилені = [];
  for (const сцена of ['ж5_співбесіда_без', 'ж4_робота', 'ж9_побачення_вечір']) {
    const шлях = path.join(корінь, 'аудит', 'проби', 'Е1-нічний-живий-20261107', сцена, 'вердикти.txt');
    const звіт = JSON.parse(fs.readFileSync(шлях, 'utf8').replace(/^\uFEFF/, ''));
    for (const прогін of звіт.прогони) for (const вердикт of прогін.вердикти) {
      w.__картка = {речі: вердикт.речі_образу || []};
      for (const запис of вердикт.мова_шару || []) {
        if (!запис.вхід || !запис.вихід || запис.заяви) continue;
        w.__результат = {тексти: запис.вихід, без_відповіді: запис.без_відповіді || [],
          короткі: запис.короткі, виклики_договору: [{розмітка: Object.entries(запис.вхід).map(([ключ, текст]) => ({ключ, текст}))}]};
        const р = w.eval('перевіритиКінцевуВідповідьШаруП(window.__результат, назвиКаталогуКарткиП(window.__картка))');
        записи.push({сцена, де: запис.де, без: р.без_відповіді, тексти: р.тексти});
        for (const ключ of р.без_відповіді) відхилені.push({сцена, ключ, текст: р.тексти[ключ]});
      }
    }
  }
  w.__пакет = {картки: [{рука: '1', текст: 'Образ', опис: 'Wear this look today and enjoy it',
    як_носити: ['Hold the bag by its handle'], схема_жінці: 'palette_scheme_note',
    матеріал_жінці: 'Вам личить цей матеріал.', речі: [{id: 'ж-1@gepur.com', назва: 'Gepur', ціна: 3000,
      слот: 'сукня', фото: null, частина_комплекту: 'Please retry later'}],
    мітки: [], знахідки: [], питання: [], етапи: {}, свідомі: [], фото_не_ті: [], дібрав_код_слоти: []}]};
  const картка = w.eval('П = window.__пакет; рендерКартку(0)');
  const текстКартки = картка.textContent;
  const дані = {записів: записи.length, відхилено: відхилені.length,
    загальнихНаписів: відхилені.filter(з => з.текст === '— без тексту').length,
    наКартці: (текстКартки.match(/— без тексту/g) || []).length, помилки, відхилені, текстКартки};
  fs.writeFileSync(path.join(вихід, 'факт.json'), JSON.stringify(дані, null, 2));
  fs.writeFileSync(path.join(вихід, 'повтор.json'), JSON.stringify(записи, null, 2));
  console.log(JSON.stringify({...дані, відхилені: undefined, текстКартки: undefined}));
  const {зібратиШаблонПоказу, прочитатиДовідникJSON, підставитиШаблон} = require(path.join(корінь, 'джерела', 'показ_шаблон.js'));
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(корінь, 'джерела', 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'проба П8', __ВІДБИТОК__: 'проба',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(path.join(корінь, 'джерела')),
  }).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const сервер = require('http').createServer((запит, відповідь) => {відповідь.setHeader('Content-Type', 'text/html; charset=utf-8'); відповідь.end(html);});
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  const браузер = await require(path.join(корінь, 'джерела', 'node_modules', 'playwright')).chromium.launch({headless: true});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
    await сторінка.goto('http://127.0.0.1:' + сервер.address().port + '/#модель_мови=нема');
    await сторінка.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
    await сторінка.evaluate(пакет => {window.__пакет = пакет; eval('П = window.__пакет; рендер();');}, w.__пакет);
    await сторінка.locator('#картки .картка').first().scrollIntoViewIfNeeded();
    await сторінка.screenshot({path: path.join(вихід, 'картка-390x844.png')});
    console.log('Знімок 390×844 збережено.');
  } finally {await браузер.close(); сервер.close(); w.close();}
})().catch(e => {console.error(e); process.exitCode = 1;});
