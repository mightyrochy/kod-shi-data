/* Повтор виходу в екран на записаних текстах і контрольних відхиленнях без виклику моделей. */
const fs = require('fs'), path = require('path'), cp = require('child_process'), Module = require('module');
const корінь = process.cwd(), до = process.argv[2] === 'до', етап = до ? 'до' : 'після';
const тека = __dirname, база = 'bb5318e88974a2131db0d133f109ccb21a12d7ba';
const файли = ['випадок.js', 'розмова_з_фото.js', 'інструменти.js', 'мовний_шар.js'];
function базовийШаблон(текст){
  if (!до) return текст;
  for (const ім of файли){
    const тепер = fs.readFileSync(path.join(корінь, 'джерела', 'показ', ім), 'utf8');
    const раніше = cp.execFileSync('git', ['show', база + ':джерела/показ/' + ім], {encoding: 'utf8', maxBuffer: 1000000});
    if (!текст.includes(тепер)) throw Error('Не знайдено модуля ' + ім);
    текст = текст.replace(тепер, () => раніше);
  }
  return текст;
}
const файл = path.join(корінь, 'джерела', 'тест_показу.js');
let префікс = fs.readFileSync(файл, 'utf8').split('(async () => {')[0]
  .replace('const ЗІБРАНИЙ = process.argv[2] ? path.resolve(process.argv[2]) : null;', 'const ЗІБРАНИЙ = null;')
  .replace('const шаблон = зібратиШаблонПоказу(ЗІБРАНИЙ || path.join(__dirname, "показ.html"));',
    'const шаблон = global.__базовийШаблон(зібратиШаблонПоказу(ЗІБРАНИЙ || path.join(__dirname, "показ.html")));');
global.__базовийШаблон = базовийШаблон;
const модуль = new Module(файл); модуль.filename = файл; модуль.paths = Module._nodeModulePaths(path.dirname(файл));
модуль._compile(префікс + '\nmodule.exports = {сторінка, чекатиСтарт};', файл);
const звіт = JSON.parse(fs.readFileSync(path.join(корінь, 'аудит/проби/Е1-нічний-живий-20261107/ж5_співбесіда_без/вердикти.txt'), 'utf8'));
const вердикти = звіт.прогони.flatMap(п => п.вердикти);
const речі = вердикти.find(в => String(в.рука) === '1').речі_образу;
const тексти = вердикти.flatMap(в => (в.мова_шару || []).flatMap(з => з.заяви ? [] : Object.values(з.вихід || {})))
  .filter(т => typeof т === 'string' && т.trim());
const дані = {річ: речі.find(р => р.фото && р.урл), тексти};
if (!дані.річ) throw Error('У записі немає речі каталогу з фото');
const проба = `(() => {
  const {річ, тексти} = window.__дані;
  const відхилення = ['Please retry later', 'Вам личить ця річ.', 'palette_scheme_note', ''];
  const повтор = [];
  for (const текст of тексти){
    ЧАТ_П = [{хто: 'ші', текст}]; малюватиЧатП();
    повтор.push({текст, стан: станТекстуЖінціП(текст, своїЕкрануП()),
      екран: document.querySelector('#чат-стрічка .репліка').textContent});
  }
  const чат = [];
  for (const текст of відхилення){
    ЧАТ_П = [{хто: 'людина', текст: 'My own words'}, {хто: 'ші', текст}]; малюватиЧатП();
    чат.push({вхід: текст, вона: document.querySelector('#чат-стрічка .вона').textContent,
      відповідь: document.querySelector('#чат-стрічка .ші').textContent, пілюля: $('ші-пілюля-текст').textContent});
  }
  const швидкі = ШВИДКІ_ВІДПОВІДІ.пора, слати = слатиЧатП;
  window.__надіслано = 0; слатиЧатП = () => {window.__надіслано++;};
  РЕЖИМ = 'сценарій'; ПАСПОРТ_П = {невідомо: ['пора']}; ЧАТ_П = [{хто: 'ші', текст: 'Коли?'}];
  ШВИДКІ_ВІДПОВІДІ.пора = () => ['palette_scheme_note']; малюватиШвидкіП();
  $('сц-швидкі').firstElementChild.click();
  const хибнаПідказка = {надіслано: window.__надіслано, поле: $('чат-поле').value};
  ШВИДКІ_ВІДПОВІДІ.пора = () => ['ввечері']; малюватиШвидкіП(); $('сц-швидкі').firstElementChild.click();
  const чистаПідказка = {надіслано: window.__надіслано, поле: $('чат-поле').value};
  ШВИДКІ_ВІДПОВІДІ.пора = швидкі; слатиЧатП = слати;
  const інструменти = ['save_scenario', 'open_scenario', 'delete_scenario'].map(tool => ({tool,
    текст: карткаІнструментаП({tool, done: true, name: 'palette_scheme_note'}).textContent}));
  інструменти.push({tool: 'set_weather_feel', текст: карткаІнструментаП({tool: 'set_weather_feel', done: true, feel: 'weather_code_unknown'}).textContent});
  ОЦ.перелік = {так: true}; ОЦ.фото = []; ОЦ.етапи = {};
  const картка = (хибна) => {
    ОЦ.результат = {сценарій: {}, допит: [{питання: 'My own question', відповідь: хибна ? 'Вам личить.' : 'Тримай сумку в руці.'}],
      картка: {відповідь: хибна ? 'Please retry later' : 'Ці речі поєднуються.',
        вдало: [{текст: хибна ? 'palette_scheme_note' : 'Кольори спокійні.'}],
        не_знаю: [{текст: хибна ? 'Ви обрали сумку.' : 'Матеріал не перевірено.'}],
        змінити: [{текст: хибна ? 'Please retry later' : 'Спробуй цю річ.', зміна: {звідки: 'shop', річ}}]}};
    малюватиКарткуОцінкиП(); return $('оц-картка').textContent;
  };
  const чистаКартка = картка(false), хибнаКартка = картка(true);
  return {повтор, чат, хибнаПідказка, чистаПідказка, інструменти, чистаКартка, хибнаКартка,
    шаблониЧисті: Object.entries(ШАБЛОНИ_ЗБОЮ_П).filter(([к]) => /^(case_|chat_|tool_|evaluation_)/.test(к))
      .every(([, т]) => станТекстуЖінціП(т) === 'translated')};
})()`;
(async () => {
  const {w, помилки} = модуль.exports.сторінка({url: 'https://example.test/показ.html#модель_мови=нема'});
  await модуль.exports.чекатиСтарт(w); w.__дані = дані;
  const результат = w.eval(проба); результат.помилки = помилки;
  fs.writeFileSync(path.join(тека, етап + '.json'), JSON.stringify(результат, null, 2)); w.close();
  const {зібратиШаблонПоказу, підставитиШаблон, прочитатиДовідникJSON} = require(path.join(корінь, 'джерела/показ_шаблон.js'));
  let html = базовийШаблон(зібратиШаблонПоказу(path.join(корінь, 'джерела/показ.html')));
  html = підставитиШаблон(html, {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'проба розмови',
    __ВІДБИТОК__: 'проба', __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(path.join(корінь, 'джерела'))})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const сервер = require('http').createServer((з, в) => {в.setHeader('Content-Type', 'text/html; charset=utf-8'); в.end(html);});
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  let браузер;
  try {
    браузер = await require(path.join(корінь, 'джерела/node_modules/playwright')).chromium.launch({headless: true});
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
    await сторінка.route('**/*', р => р.request().url().startsWith('http://127.0.0.1:') ||
      (process.env.FOTO === '1' && р.request().resourceType() === 'image') ? р.continue() : р.abort());
    await сторінка.goto('http://127.0.0.1:' + сервер.address().port + '/#модель_мови=нема');
    await сторінка.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
    await сторінка.evaluate(д => {window.__дані = д;}, дані);
    await сторінка.evaluate(проба);
    await сторінка.evaluate(() => {eval("режим('оцінка'); малюватиКарткуОцінкиП();");});
    await сторінка.evaluate(async () => {
      await Promise.all([...document.querySelectorAll('#оц-картка img')].map(і => і.complete ? null : new Promise(р => {
        і.addEventListener('load', р, {once: true}); і.addEventListener('error', р, {once: true}); setTimeout(р, 12000);
      })));
      window.scrollTo(0, document.querySelector('#оц-картка').getBoundingClientRect().top + scrollY);
    });
    результат.браузер = await сторінка.evaluate(() => ({фото: [...document.querySelectorAll('#оц-картка img')].map(і => ({адреса: і.src, ширина: і.naturalWidth})),
      переповнення: document.documentElement.scrollWidth > innerWidth}));
    await сторінка.screenshot({path: path.join(тека, етап + '-390x844.png')});
    fs.writeFileSync(path.join(тека, етап + '.json'), JSON.stringify(результат, null, 2));
  } finally {if (браузер) await браузер.close(); сервер.close();}
  if (помилки.length || (!до && (!результат.шаблониЧисті || результат.хибнаПідказка.надіслано !== 0
    || результат.чистаПідказка.надіслано !== 1 || /— без тексту|palette_scheme_note|Please retry|Вам личить|Ви обрали/.test(результат.хибнаКартка))))
    throw Error('Проба виходу в екран не пройшла');
  console.log(JSON.stringify({етап, повтор: результат.повтор.length, помилки, хибнаПідказка: результат.хибнаПідказка,
    фото: результат.браузер.фото, переповнення: результат.браузер.переповнення}));
})().catch(е => {console.error(е); process.exitCode = 1;});
