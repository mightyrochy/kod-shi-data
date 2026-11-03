/* Незалежний огляд PR #2842: запуск node <цей файл> <дерево призначеної голови>. */
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const корінь = path.resolve(process.argv[2]);
const git = (...а) => execFileSync('git', а, {cwd: корінь, encoding: 'utf8'}).trim();
const голова = '4d3e81a9f88c78334ed5db5cf4447711c83d3624';
assert.equal(git('rev-parse', 'HEAD'), голова);
const пакет = path.dirname(require.resolve('playwright/package.json', {paths: [path.join(корінь, 'джерела')]}));
const {chromium} = require(пакет);
const {babelParse, traverse} = require(path.join(пакет, 'lib/transform/babelBundle.js'));
const файл = 'аудит/проби/рв6_стенд.js', реєстр = 'аудит/проби/Е1-звірки.json';
const код = fs.readFileSync(path.join(корінь, файл), 'utf8').replace(/\r\n/g, '\n');
const старийТекст = git('show', 'c4df8ac3aaa2f2291f973a52f1521bc9d35a58df:' + реєстр);
const старі = JSON.parse(старийТекст).звірки;
const нові = JSON.parse(fs.readFileSync(path.join(корінь, реєстр), 'utf8')).звірки;
const додані = нові.filter(з => !старі.some(с => с.ід === з.ід));
assert.equal(старі.length, 215); assert.equal(нові.length, 217); assert.equal(додані.length, 2);
for (const с of старі) assert.deepEqual(нові.find(з => з.ід === с.ід), с);
const прилад = require(path.join(корінь, 'аудит/проби/звірки_Е1.js'));
const читати = fs.readFileSync;
let до;
fs.readFileSync = function(ф, ...а) {
  return path.resolve(String(ф)) === path.join(корінь, реєстр) ? старийТекст : читати.call(this, ф, ...а);
};
try { прилад.перевірити(); assert.fail('ДО мало відхилити два записи без огляду'); }
catch (е) { assert.equal(е.actual, 2); assert.match(е.message, /нова чи змінена звірка без огляду/); до = е.actual; }
finally { fs.readFileSync = читати; }
const після = прилад.перевірити();
const старийКод = git('show', '1ec705fc99e4d32aea783e3ae5ed80e5d3fcc148:' + файл);
const лічити = текст => {
  let число = 0;
  traverse(babelParse(текст, файл, false), {CallExpression(ш) {
    if (ш.node.callee.name !== 'чекатиСтан') return;
    const назва = ш.node.arguments[1];
    if (!назва) return;
    if (/позначка «не ця»|кінець заміни речі|запис заміни в етапи\.заміни руки/.test(текст.slice(назва.start, назва.end))) число++;
  }});
  return число;
};
const клас = {до: лічити(старийКод), після: лічити(код)};
assert.deepEqual(клас, {до: 3, після: 0});
const функції = {}, гілки = [];
traverse(babelParse(код, файл, false), {
  FunctionDeclaration(ш) { if (ш.node.id) функції[ш.node.id.name] = код.slice(ш.node.start, ш.node.end); },
  IfStatement(ш) { if (код.slice(ш.node.test.start, ш.node.test.end) === 'замінаДійшла') гілки.push(код.slice(ш.node.start, ш.node.end)); }
});
assert.equal(гілки.length, 1);
const доказ = JSON.parse(fs.readFileSync(path.join(корінь, 'аудит/проби/розбір-очікувань-bdc922db/CI-огляд-звірок.json'), 'utf8'));
assert.equal(доказ.blob, git('rev-parse', голова + ':' + файл));
assert.equal(доказ.джерело_помічника, функції.чекатиЗаміну);
assert.equal(доказ.джерело_гілки, гілки[0]);
const {чекатиСтан} = require(path.join(корінь, 'джерела/проби/очікування.js'));
const створити = Function('стор', 'чекатиСтан', 'діагностикаОчікування', 'МЕЖА_МОСТУ',
  функції.чекатиКартку + '\n' + функції.чекатиЗаміну + '\nreturn {чекатиКартку, чекатиЗаміну};');
const гілка = Function('замінаДійшла', 'ф', 'речіЗаміни', 'до', 'рука1', гілки[0]);

(async () => {
  const браузер = await chromium.launch({headless: true});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
    await сторінка.goto('about:blank');
    const сире = {evaluate: сторінка.evaluate.bind(сторінка), waitForFunction: сторінка.waitForFunction.bind(сторінка)};
    const {чекатиКартку, чекатиЗаміну} = створити({показПідЧасМоста: сире}, чекатиСтан, async () => {}, 2000);
    await сторінка.evaluate(() => { window.П = {картки: [{етапи: {заміни: []}}]};
      window.ЗАМІНИ_П = new Set(); window.НЕ_ЦЯ_П = new Set(['відхилена']); window.містЗайнятий = true; });
    let стареВпало = false;
    try { await сире.waitForFunction(() => НЕ_ЦЯ_П.size > 0 && !містЗайнятий, null, {timeout: 100}); }
    catch (е) { assert.match(е.message, /Timeout/); стареВпало = true; }
    assert.equal(стареВпало, true);
    await чекатиКартку(0, 'позначка при зайнятому мості', () => НЕ_ЦЯ_П.size > 0, null, 100);
    assert.equal(await сире.evaluate(() => містЗайнятий), true);
    const випадки = доказ.випадки.map(в => ({...в}));
    const результати = [];
    for (const в of випадки) {
      await сире.evaluate(в => {
        П.картки[0] = {етапи: в.етапи}; ЗАМІНИ_П.add(П.картки[0]);
        setTimeout(() => ЗАМІНИ_П.delete(П.картки[0]), 50);
      }, в);
      const завершено = await чекатиЗаміну(0, в.до);
      assert.equal(завершено, в.очікується, в.назва);
      const звірки = [];
      гілка(завершено, (назва, зелена) => звірки.push({назва, зелена}), ['нова', 'інша'], ['стара', 'інша'], 0);
      assert.equal(звірки.length, 1); assert.equal(звірки[0].зелена, в.очікується);
      результати.push({назва: в.назва, завершено, зелена: звірки[0].зелена});
    }
    const стан = JSON.parse(fs.readFileSync(path.join(корінь, 'аудит/проби/розбір-очікувань-bdc922db/діагностика-ДО/ж1/очікування.json'), 'utf8')).стан;
    assert(Object.values(стан.не_ця).some(з => з.length > 0));
    const сцени = ['ж1_побачення_день_червоне', 'ж4_робота_стримано'].map(назва => {
      const тека = path.join(корінь, 'аудит/проби/розбір-очікувань-bdc922db/ПІСЛЯ', назва);
      const р = JSON.parse(fs.readFileSync(path.join(тека, 'результат.json'), 'utf8'));
      const лог = fs.readFileSync(path.join(тека, 'лог.txt'), 'utf8');
      assert.equal(р.rc, 1); assert.match(лог, /ДОКАЗ · рв6_стенд .* · доведено →/);
      assert.match(лог, /ВПАЛО [25] ·/);
      return {назва, rc: р.rc, секунд: р.секунд};
    });
    console.log(JSON.stringify({голова, старі_очікування_класу: клас, реєстр: {до, після: після.без_остаточного_вердикту,
      старих_незмінних: старі.length, додано: додані.length, всього: після.всього,
      контрприкладів: після.контрприкладів_предикатів}, позначка_без_тиші: true,
      браузерні_випадки: результати, архівні_сцени: сцени}, null, 2));
  } finally { await браузер.close(); }
})().catch(е => { console.error(е); process.exitCode = 1; });
