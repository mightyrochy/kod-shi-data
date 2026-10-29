/* П2: паралельні читачі ділять з'єднання; зміна версії та збій дозволяють відкрити знову.
   Запуск: node проби/показ_дб.js [показ.html]. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const assert = require('node:assert/strict');
const {IDBFactory} = require('fake-indexeddb');
const html = fs.readFileSync(process.argv[2] || path.join(__dirname, '../показ.html'), 'utf8');
const поч = html.indexOf('function дб(){'), кін = html.indexOf('\nfunction tx(', поч);
const джерело = html.slice(html.indexOf('let зʼєднанняДбП') >= 0 ? html.indexOf('let зʼєднанняДбП') : поч, кін);
const фабрика = new IDBFactory();
let відкриттів = 0, збоїти = false;
const indexedDB = {open(...арг){
  відкриттів++;
  if (збоїти){ збоїти = false; throw new Error('перервано відкриття'); }
  return фабрика.open(...арг);
}};
const контекст = vm.createContext({indexedDB});
vm.runInContext(джерело, контекст);
(async () => {
  const сполуки = await Promise.all(Array.from({length: 109}, () => контекст.дб()));
  assert.equal(відкриттів, 1);
  assert(сполуки.every(д => д === сполуки[0]));
  const база = сполуки[0];
  assert.deepEqual([...база.objectStoreNames].sort(), ['вердикти', 'кв', 'образи', 'сценарії'].sort());
  const запис = база.transaction('кв', 'readwrite'); запис.objectStore('кв').put('збережено', 'ключ');
  await new Promise((рез, від) => { запис.oncomplete = рез; запис.onerror = від; });
  const відкат = база.transaction('кв', 'readwrite'); відкат.objectStore('кв').put('втрачено', 'ключ'); відкат.abort();
  await new Promise(рез => { відкат.onabort = рез; });
  база.close();
  const знову = await контекст.дб();
  const читання = знову.transaction('кв').objectStore('кв').get('ключ');
  assert.equal(await new Promise(рез => { читання.onsuccess = () => рез(читання.result); }), 'збережено');
  const запит = фабрика.open('показ', 4);
  const нове = await new Promise((рез, від) => { запит.onsuccess = () => рез(запит.result); запит.onerror = () => від(запит.error); });
  нове.close(); // versionchange має закрити попереднє з'єднання, не блокуючи міграцію.
  await assert.rejects(контекст.дб()); // v3 вже застаріла: наступний виклик не кешує відмову.
  await assert.rejects(контекст.дб());
  assert.equal(відкриттів, 4);
  const видалення = фабрика.deleteDatabase('показ');
  await new Promise((рез, від) => { видалення.onsuccess = рез; видалення.onerror = () => від(видалення.error); });
  збоїти = true;
  await assert.rejects(контекст.дб());
  const д = await контекст.дб();
  д.onclose(); // примусове закриття очищає спільний Promise.
  const після = await контекст.дб();
  assert.notEqual(після, д);
  д.close(); після.close();
  console.log('П2: 109 паралельних читачів → 1 open; versionchange не блокує; відмова й close дозволяють повторити.');
})().catch(е => { console.error(е); process.exitCode = 1; });
