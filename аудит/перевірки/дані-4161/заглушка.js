/* Назви з чинного й давнього дроту: node заглушка.js <дерево>. */
const fs = require('fs'), path = require('path'), assert = require('assert');
const дерево = path.resolve(process.argv[2]);
const код = fs.readFileSync(path.join(дерево, 'аудит/проби/рв6_стенд.js'), 'utf8');

/* Межа завершеного збору стоїть перед звірками, які потребують карток.
   Змінюється лише завантажений стенд цієї архівної проби. */
function зПеревіркоюЗбору(текст) {
  const межа = '  const збій = await стор.evaluate(() => ({статус:';
  assert.equal(текст.split(межа).length, 2, 'межа завершення збору має бути одна');
  return текст.replace(межа, `  const причинаПорожньогоЗбору = await стор.evaluate(() => {
    const картки = (typeof П !== 'undefined' && П && П.картки) || [];
    if (картки.length) return '';
    const діагноз = (typeof ЗБ !== 'undefined' && ЗБ && ЗБ.діагноз) || [];
    return діагноз.find(р => /^build · failed:/.test(р)) || 'build · failed: збирання завершено без карток';
  });
  if (причинаПорожньогоЗбору) {
    if (знімкиЗб) clearInterval(знімкиЗб);
    console.error(String(причинаПорожньогоЗбору).replace(/[\\r\\n]+/g, ' '));
    await браузер.close();
    process.exit(1);
  }
` + межа);
}

/* Справжній відрізок стенда з підкладеним станом сторінки: без браузера й моделі.
   node заглушка.js . --проба-збору до|після */
if (process.argv[3] === '--проба-збору') {
  const vm = require('vm');
  const текст = (process.argv[4] === 'до' ? код : зПеревіркоюЗбору(код)).replace(/\r\n/g, '\n');
  const початок = текст.indexOf('  const причинаПорожньогоЗбору =');
  const від = початок >= 0 ? початок : текст.indexOf('  const збій = await стор.evaluate(() => ({статус:');
  const до = текст.indexOf("    console.log('   рядок 152 — закріплено:", від);
  assert(від >= 0 && до > від, 'межі відрізка проби збору');
  const контекст = {
    console, process: {env: {}, exit: код => { process.exitCode = код; throw {завершено: true}; }},
    П: null, ЗБ: {діагноз: ['build · failed: worker: мовчить 300 с, виклик запити']},
    document: {getElementById: () => null, querySelectorAll: () => [],
      createTreeWalker: () => ({nextNode: () => null})}, window: {}, NodeFilter: {SHOW_TEXT: 4},
    браузер: {close: async () => {}}, знімкиЗб: null,
    СІД: 3, ч: () => '0.0 с', намірУПаспорті: 'conventional', знімок: async () => {},
    ЗБІЙ: {післяЗбирання: async () => {}}, ВИРАЗ_ЗБОЮ: 'true', ВИРАЗ_ЗАВЕРШЕНО: 'false',
    ф: (імя, добре) => { if (!добре) console.log('✗ ' + імя); },
    setInterval: () => 0, clearInterval: () => {}, чекатиСтан: async () => {},
    ЗНІМКИ: null, СЛАБКА: {підсумок: async () => {}}, знімокПершої: Promise.resolve(),
    ЧАСИ: {звіт: async () => {}}, зведенняПланувальника: async () => {}, відЗбирання: 0,
    ДОКАЗ: {очікувати() {return this;}, факт() {return this;}}, ЧЕКАЮ_ФОТО: false,
    с1: {}, питаньЗВідповіддю: () => 0, словаНазвиТ8: () => [],
    НОМЕР: /ніколи/, HEX: /ніколи/, КОД: /ніколи/, ІД_ВИГАД: /ніколи/, РЕПР_ОБЄКТА: /ніколи/,
    ДОВІДКА_ЗАПЕР: false, ФОТО_РЕЧІ: true, ДОВІДКА_ЇЇ_РІЧ: false, ЗАМІНА_СТЕНДА: false,
  };
  контекст.стор = {evaluate: async вираз => vm.runInContext(
    typeof вираз === 'string' ? вираз : '(' + вираз.toString() + ')()', середовище)};
  const середовище = vm.createContext(контекст);
  // Відрізок кінчається всередині гілки ФОТО_РЕЧІ: закриваємо лише її дужку.
  vm.runInContext('(async () => {\n' + текст.slice(від, до) + '\n}\n})()', середовище)
    .catch(е => { if (!е.завершено) { console.error(String(е)); process.exitCode = 2; } });
  return;
}
/* Проба шляху стенда на незміненому продукті цього checkout. Архів обірваний до
   відповідей збирання: їх дає штатна заглушка. Сам продукт і звірки не підмінюються.
   node заглушка.js <дерево коду стенда> --чат <кеш Pyodide> */
if (process.argv[3] === '--чат') {
  const Module = require('module'), os = require('os');
  const репо = path.resolve(__dirname, '../../..');
  const архів = path.join(репо, 'аудит/проби/Тестовий-прогін-хмара-1711/ж4_213_червоний_верх_падіння');
  const повтор = JSON.parse(fs.readFileSync(path.join(архів, 'повтор.json'), 'utf8'));
  const тимчасова = fs.mkdtempSync(path.join(os.tmpdir(), 'проба-чату-'));
  /* Інша назва файла не приписує пробі реєстровий режим «+фото»: тут немає мережі фото. */
  const жінка = path.join(тимчасова, 'повтор-жінка.json');
  fs.writeFileSync(жінка, JSON.stringify(повтор.жінка));
  for (const ключ of ['MODEL', 'MODEL_MOVA', 'ZHYVA', 'SCENA', 'REPLAY_EXCHANGE']) delete process.env[ключ];
  Object.assign(process.env, {ZHINKA: жінка, CHAT_TEXT: повтор.змінні.CHAT_TEXT, OTSINKA: '0', FOTO: '0',
    REPLAY_RECORDINGS: path.join(архів, 'VIDPOVIDI')});
  const межа = "if (ЗАПИСАНИЙ_ОБМІН) {\n      const тип = типПромпту(текст);";
  const нормалізований = код.replace(/\r\n/g, '\n');
  assert(нормалізований.includes(межа), 'не знайдено межу відповідей моделі');
  const частковий = зПеревіркоюЗбору(нормалізований.replace(межа,
    "if (ЗАПИСАНИЙ_ОБМІН && ЗАПИСАНИЙ_ОБМІН.записи.some(з => з.тип === імТипу(типПромпту(текст)) && !ЗАПИСАНИЙ_ОБМІН.взято.has(з.ім))) {\n      const тип = типПромпту(текст);"));
  console.log('ПРОБА: архівні відповіді — штатним читачем; відсутні — штатною сценарною заглушкою; фото вимкнено.');
  const файл = path.join(репо, 'аудит/проби/рв6_стенд.js');
  const модуль = new Module(файл, module);
  модуль.filename = файл;
  модуль.paths = Module._nodeModulePaths(path.dirname(файл));
  process.argv = [process.execPath, файл, 'http://127.0.0.1:8765', репо, process.argv[4], String(повтор.сід)];
  модуль._compile(частковий, файл);
  return;
}
const початок = код.indexOf('function описЗПромпта(');
const кінець = код.indexOf('\n/* Перепис мови', початок);
assert(початок >= 0 && кінець > початок);
const таблиця = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../джерела/внутрішня_мова.schema.json'), 'utf8'))['x-таблиця'];
const сторінка = fs.readFileSync(path.resolve(__dirname, '../../../index.html'), 'utf8');
const назвиПоказу = JSON.parse(/const ДОВІДНИК = (\{[^\n]+\});/.exec(сторінка)[1]).показ.слоти_називний;
const опис = new Function('СЛОТ_ЯКЩО_ВПІЗНАВ', '_ПОРАДА_НОСІННЯ', 'ТАБЛИЦЯ_ВМ', 'НАЗВИ_РОДІВ_ОПИСУ',
  код.slice(початок, кінець) + '\nreturn описЗПромпта;')(
  () => null, (в, назви) => назви[в.item], таблиця, назвиПоказу);
let хиб = 0;
for (const [мітка, речі, назва] of [
  ['дріт із кольором', [{n: '#1·01', kind: 'dress', color: 'green', hex: '#2e8b57', photos: [1]}], назвиПоказу[таблиця.slot.dress]],
  ['чинний дріт', [{n: '#1·01', kind: 'dress', photos: [1]}], назвиПоказу[таблиця.slot.dress]],
  ['давній дріт', [{n: '#1·01', name: 'Лляна сукня'}], 'Лляна сукня'],
  ['порожня назва', [{n: '#1·01', name: ' ', kind: 'dress'}], назвиПоказу[таблиця.slot.dress]],
  ['невідомий рід', [{n: '#1·01', kind: 'new_kind', photos: [1]}], 'річ'],
  ['порожній склад', [], ''],
]) {
  for (const рос of [false, true]) {
    const вхід = {outfit: {items: речі}, case: {event: 'work'}, ways_to_wear: речі.length ? [{item: '#1·01'}] : []};
    const вихід = опис(вхід, рос);
    const нема = вихід.текст.includes(рос ? 'вещей в промпте нет' : 'речей у промпті нема');
    const правильно = нема === !речі.length && (!речі.length
      || (вихід.текст.includes(назва) && вихід.як_носити.includes(назва)));
    if (!правильно) хиб++;
    console.log(`${правильно ? '✔' : '✗'} ${мітка} (${рос ? 'рос' : 'укр'}): речей ${речі.length}; фраза про відсутність ${нема ? 'є' : 'нема'}; ${вихід.текст}`);
    assert.equal(вхід.outfit.items.length, речі.length);
  }
}
console.log(`звірок: 12; хиб: ${хиб}`);
process.exitCode = хиб ? 1 : 0;
