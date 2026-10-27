/* Повтор записаних запитів серії 2: один JSON, той самий вхід і схема. Без мережі. */
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const корінь = path.resolve(__dirname, '../..');
const контекст = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(корінь, 'джерела/показ/збирання_руки.js'), 'utf8'), контекст);
const повтор = контекст.повторнийЗапитРукиП;
const тека = path.join(__dirname, 'б1/ДО-2710');
let запитів = 0, повторів = 0, до = 0, після = 0;
const форми = new Set();
for (const сцена of fs.readdirSync(тека)){
  const файл = path.join(тека, сцена, 'вердикти.txt');
  if (!fs.existsSync(файл)) continue;
  for (const прогін of JSON.parse(fs.readFileSync(файл, 'utf8')).прогони)
    for (const рука of прогін.вердикти)
      for (const крок of рука.етапи.виклики){
        if (!['assembly', 'repair', 'choice', 'description'].includes(крок.крок)) continue;
        const текст = (крок.запит || {}).текст;
        if (!текст) continue;
        if ((крок.запит.чого || '').includes('_retry')){
          повторів++;
          try { JSON.parse(текст); } catch (_) { до++; }
          continue;
        }
        let вхід;
        try { вхід = JSON.parse(текст); } catch (_) { continue; }
        if (!вхід.task) continue;
        const помилка = {error: 'format_error', instead: 'Return one object matching answer_schema.'};
        const новий = JSON.parse(повтор(текст, JSON.stringify(помилка)));
        assert.deepEqual(новий.format_errors, помилка);
        delete новий.format_errors;
        assert.deepEqual(новий, JSON.parse(JSON.stringify(вхід)));
        assert.deepEqual(Object.keys(новий), Object.keys(вхід));
        запитів++; форми.add(крок.крок);
        try { JSON.parse(повтор(текст, JSON.stringify(помилка))); } catch (_) { після++; }
      }
}
assert.equal(форми.size, 4);
assert.ok(до > 0 && запитів > 0);
console.log(`Серія 2: записаних повторів ${повторів}, не один JSON ДО ${до}; нових повторів ${запитів}, не один JSON ПІСЛЯ ${після}; форм ${форми.size}.`);
