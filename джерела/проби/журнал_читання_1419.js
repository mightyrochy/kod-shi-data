/* Журнал П3: повтори, зміни, вкладки й стара збірка. Запуск із кореня: NODE_PATH=джерела/node_modules node джерела/проби/журнал_читання_1419.js */
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const {indexedDB, IDBObjectStore} = require('fake-indexeddb');
const джерело = fs.readFileSync(path.join(__dirname, '..', 'показ.html'), 'utf8');
const уривок = (поч, кін) => джерело.slice(джерело.indexOf(поч), джерело.indexOf(кін, джерело.indexOf(поч)));
const код = уривок('function tx(d,', 'async function пристрій_Id(')
  + уривок('const КЛЮЧ_РЕВІЗІЇ_ЖУРНАЛУ_П', '/* ── ПОВТОРНЕ ВИВАНТАЖЕННЯ')
  + уривок('function копіяРозборуП(', 'function розібратиПоле(');
let читань = 0;
const оригінал = IDBObjectStore.prototype.getAll;
IDBObjectStore.prototype.getAll = function(...а){ if (this.name === 'вердикти') читань++; return оригінал.apply(this, а); };
(async()=>{
  const d = await new Promise((рез, від)=>{
    const r = indexedDB.open('проба-журналу-1419', 3); r.onupgradeneeded = ()=>{ r.result.createObjectStore('вердикти', {autoIncrement:true}); r.result.createObjectStore('кв'); };
    r.onsuccess = ()=>рез(r.result); r.onerror = ()=>від(r.error);
  });
  const читач = ()=>{
    const події = {};
    const апі = new Function('дб', 'window', код + ';return {tx,усіВердикти,читатиЖурналП};')
      (async()=>d, {addEventListener:(назва, дія)=>{ події[назва] = дія; }});
    return {...апі, події};
  };
  const перший = читач(), другий = читач();
  await перший.tx(d,'вердикти','readwrite',s=>s.add({етапи:'{}', вкладене:{код:'свій'}}));
  const [один, два, ключі] = await Promise.all([перший.усіВердикти(), перший.усіВердикти(), перший.читатиЖурналП()]);
  assert.equal(читань,1); assert.equal(ключі[0].ключ,1); один[0].вкладене.код='читач';
  for (let і=0;і<16;і++) assert.equal((await перший.усіВердикти())[0].вкладене.код,'свій');
  assert.equal(читань,1); assert.equal(два[0].вкладене.код,'свій');
  await перший.tx(d,'вердикти','readwrite',s=>s.put({етапи:'{"код":"новий"}'},1)); assert.equal((await перший.усіВердикти())[0].етапи,'{"код":"новий"}');
  await перший.tx(d,'вердикти','readwrite',s=>s.add({рука:'оцінка',етапи:'{}'})); assert.equal((await перший.усіВердикти()).length,2);
  await перший.tx(d,'вердикти','readwrite',s=>{ const r=s.get(1); r.onsuccess=()=>s.put({...r.result,вивантажено:['час']},1); return r; }); assert.deepEqual((await перший.усіВердикти())[0].вивантажено,['час']);
  await другий.tx(d,'вердикти','readwrite',s=>s.add({етапи:'{}',рука:'інша вкладка'})); assert.equal((await перший.усіВердикти()).length,3); assert.equal(читань,5);
  await assert.rejects(перший.tx(d,'вердикти','readwrite',s=>{ s.add({рука:'відкочено'}); s.transaction.abort(); })); assert.equal((await перший.усіВердикти()).length,3);
  const доФокусу=читань, почате=перший.усіВердикти(); перший.події.focus(); await почате; await перший.усіВердикти(); assert.equal(читань,доФокусу+2);
  const старий=d.transaction('вердикти','readwrite'); старий.objectStore('вердикти').add({етапи:'{}',рука:'стара збірка'}); await new Promise(рез=>{ старий.oncomplete=рез; });
  перший.події.focus(); assert.equal((await перший.усіВердикти()).length,4);
  await перший.tx(d,'вердикти','readwrite',s=>s.add({етапи:'x'.repeat(9*1024*1024)})); const до=читань;
  assert.equal((await перший.усіВердикти()).length,5); await перший.усіВердикти(); assert.equal(читань,до+2);
  console.log('Журнал: 16 повторів → 1 повне читання; зміни, оцінка, позначка, інша вкладка, відкат, ізоляція, межа — пройдено'); d.close();
})().catch(помилка=>{ console.error(помилка); process.exitCode=1; });
