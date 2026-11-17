/* Назви з чинного й давнього дроту: node заглушка.js <дерево>. */
const fs = require('fs'), path = require('path'), assert = require('assert');
const дерево = path.resolve(process.argv[2]);
const код = fs.readFileSync(path.join(дерево, 'аудит/проби/рв6_стенд.js'), 'utf8');
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
