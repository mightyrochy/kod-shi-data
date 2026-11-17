/* Відтворення 16322: node заглушка.js <дерево голови PR #4161>. */
const fs = require('fs'), path = require('path'), assert = require('assert');
const дерево = path.resolve(process.argv[2]);
const код = fs.readFileSync(path.join(дерево, 'аудит/проби/рв6_стенд.js'), 'utf8');
const початок = код.indexOf('function описЗПромпта(');
const кінець = код.indexOf('\n/* Перепис мови', початок);
assert(початок >= 0 && кінець > початок);
const опис = new Function('СЛОТ_ЯКЩО_ВПІЗНАВ', '_ПОРАДА_НОСІННЯ',
  код.slice(початок, кінець) + '\nreturn описЗПромпта;')(
  () => { throw Error('неочікуваний виклик класифікатора'); },
  () => { throw Error('неочікувана порада'); });
for (const [мітка, річ] of [
  ['ДО', {n: '#1·01', kind: 'dress', color: 'green', hex: '#2e8b57', photos: [1]}],
  ['ПІСЛЯ', {n: '#1·01', kind: 'dress', photos: [1]}],
]) {
  const вхід = {outfit: {items: [річ]}, case: {event: 'work'}};
  const вихід = опис(вхід, false);
  assert.equal(вхід.outfit.items.length, 1);
  assert(вихід.текст.includes('речей у промпті нема'));
  console.log(`${мітка}: речей у вході 1; заглушка: ${вихід.текст}`);
}
