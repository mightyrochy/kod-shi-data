/* Звіряє реєстр огляду та контрприклади зі справжніми предикатами стенда. */
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
const crypto = require('crypto');
const {execFileSync} = require('child_process');
const пакет = path.dirname(require.resolve('playwright/package.json'));
const {babelParse, traverse} = require(path.join(пакет, 'lib/transform/babelBundle.js'));
const база = '7bf892f1e7de2f17e063e9d86c08bec17ccf92ce';
const файл = 'аудит/проби/рв6_стенд.js';
const корінь = path.resolve(__dirname, '../..');

function звірки(код) {
  код = код.replace(/\r\n/g, '\n');
  const результат = [];
  traverse(babelParse(код, файл, false), {CallExpression(шлях) {
    const вузол = шлях.node;
    if (вузол.callee.type !== 'Identifier' || вузол.callee.name !== 'ф') return;
    const [назва, умова] = вузол.arguments;
    const назваТекстом = код.slice(назва.start, назва.end), умоваТекстом = код.slice(умова.start, умова.end);
    const ід = crypto.createHash('sha256').update(назваТекстом + '\n' + умоваТекстом).digest('hex');
    const межі = [];
    for (let батько = шлях.parentPath; батько; батько = батько.parentPath)
      if (батько.node.type === 'IfStatement') межі.push(код.slice(батько.node.test.start, батько.node.test.end));
    результат.push({ід, рядок: вузол.loc.start.line, назва: назваТекстом, умова: умоваТекстом, умови_сцени: межі});
  }});
  return результат;
}

function обчислити(звірка, дані) {
  return Function(...Object.keys(дані), 'return (' + звірка.умова + ');')(...Object.values(дані));
}

function перевірити() {
  const старі = звірки(execFileSync('git', ['show', база + ':' + файл], {cwd: корінь, encoding: 'utf8'}));
  const код = fs.readFileSync(path.join(корінь, файл), 'utf8');
  const нові = звірки(код);
  assert.deepEqual(нові, звірки(код.replace(/\r?\n/g, '\r\n')), 'вердикти не залежать від LF/CRLF');
  const випадки = [
    {ід: 'три_кроки', знайти: з => з.назва.includes('рівно три кроки'),
      дані: {к1: {екран: 0, кнопка: 'Готово'}, к2: {екран: 1, кнопка: 'Готово'}, к3: {екран: 2, кнопка: 'Готово'}}},
    {ід: 'ціна_своєї_руки', знайти: з => з.назва.includes('картки рук 1–2 і 3–4 відрізняються') || з.назва.includes('рядок «Разом» стоїть лише'),
      дані: {с2: {картки: ['1', '2', '3', '4'].map(рука => ({рука})),
        дом: [false, false, true, true].map(разом => ({разом, кнопок_заміни: разом ? 2 : 0}))}}},
    {ід: 'точні_речі_попереднього_збору', знайти: з => з.умова.includes('шле.поле.length'),
      дані: {шле: {поле: ['чуже'], набір: ['потрібне']}}},
    {ід: 'непорожня_ошатність', знайти: з => з.назва.includes('числом моделі'),
      дані: {р: {ошатність: [], плиток: [1]}}},
  ];
  const докази = випадки.map(в => {
    const до = старі.filter(в.знайти), після = нові.filter(в.знайти);
    assert.equal(до.length, 1); assert.equal(після.length, 1);
    assert.equal(обчислити(до[0], в.дані), true);
    assert.equal(обчислити(після[0], в.дані), false);
    return {ід: в.ід, вердикт: 'хибна', до: true, після: false, контрприклад: в.дані,
      джерело_до: база + ':' + файл + ':' + до[0].рядок, рядок_після: після[0].рядок};
  });
  const заНазвою = з => з.назва.includes('кожен промпт ітерацій');
  const доJSON = старі.find(заНазвою), післяJSON = нові.find(заНазвою);
  const сім = {протокольні: Array.from({length: 7}, () => ({json: true}))};
  assert.equal(обчислити(доJSON, сім), false);
  assert.equal(обчислити(післяJSON, сім), true);
  assert.equal(обчислити(післяJSON, {протокольні: []}), false);
  assert.equal(обчислити(післяJSON, {протокольні: [{json: true}, {json: false}]}), false);
  докази.push({ід: 'json_без_вигаданої_кількості_ремонтів', вердикт: 'хибна', до: false, після: true,
    контрприклад: сім, джерело_до: база + ':' + файл + ':' + доJSON.рядок, рядок_після: післяJSON.рядок});
  const реєстр = JSON.parse(fs.readFileSync(path.join(__dirname, 'Е1-звірки.json'), 'utf8'));
  const блок = нові.find(з => з.назва.includes('переліку перекладів і запасних станів'));
  const даніБлоку = {ШАР_ВИМКНЕНО: false, с2: {дом: [{згорнуто: true, підпис_питань: 'Питання · 2'}],
    картки: [{тексти_питань: ['переклад'], чекають: 1}]}};
  assert.equal(обчислити(блок, даніБлоку), true);
  даніБлоку.с2.дом[0].підпис_питань = 'Питання · 1';
  assert.equal(обчислити(блок, даніБлоку), false);
  const переклад = нові.find(з => з.назва.includes('жива модель шару: кожне питання'));
  const даніПерекладу = {ЖИВИЙ_ШАР: true, с2: {картки: [{тексти_питань: ['текст'], питань_картці: 1, питань_без_перекладу: 0}]}};
  assert.equal(обчислити(переклад, даніПерекладу), true);
  даніПерекладу.с2.картки[0].питань_без_перекладу = 1;
  assert.equal(обчислити(переклад, даніПерекладу), false);
  докази.push({ід: 'лічба_запасних_станів', вердикт: 'правда', коректна_лічба: true, хибна_лічба: false},
    {ід: 'переклад_без_пропусків', вердикт: 'правда', усе_перекладено: true, є_пропуск: false});
  const заІдом = new Map(реєстр.звірки.map(з => [з.ід, з]));
  assert.equal(заІдом.size, реєстр.звірки.length, 'повторений ід звірки');
  const безВердикту = нові.filter(з => !заІдом.has(з.ід));
  assert.equal(безВердикту.length, 0, 'нова чи змінена звірка без огляду');
  assert.equal(нові.length, реєстр.звірки.length, 'зайвий запис огляду');
  assert(реєстр.звірки.every(з => ['правда', 'хибна'].includes(з.вердикт) && з.доказ));
  return {всього: нові.length, хибних_і_виправлено: реєстр.звірки.filter(з => з.вердикт === 'хибна').length,
    контрприкладів_предикатів: докази.length,
    без_остаточного_вердикту: безВердикту.length, докази};
}

if (require.main === module) {
  if (process.argv.includes('--інвентар')) console.log(JSON.stringify(
    звірки(fs.readFileSync(path.join(корінь, файл), 'utf8')), null, 1));
  else console.log(JSON.stringify(перевірити(), null, 1));
}
module.exports = {звірки, перевірити};
