/* Відтворює вибір місця й форму повтору на фактах першого запису, без моделі. */
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('node:assert/strict');
const корінь = path.resolve(__dirname, '../../..');
function функція(файл, імʼя){
  const код = fs.readFileSync(path.join(корінь, 'джерела/показ', файл), 'utf8');
  const поч = код.indexOf('function ' + імʼя + '(');
  return код.slice(поч, код.indexOf('\n}', поч) + 2);
}
const паспорт = {місце: 'клуб', джерело_полів: {}, картка_запиту: {
  місце: {значення: 'клуб', джерело: 'her', уривок: 'рок-концерт у клубі'}}};
const контекст = {ДОВІДНИК: {місця: [{ключ: 'клуб'}]}, ТИПОВЕ_ПОЛЕ_ФОРМИ_П: 'типове_форми',
  $: () => ({value: ''}), знайти: (список, ключ) => список.find(р => р.ключ === ключ),
  паспортКартки: () => паспорт, чиннеМісце: () => null};
vm.createContext(контекст);
vm.runInContext(функція('голос_помада.js', 'місцеКартки'), контекст);
const місце = контекст.місцеКартки();
assert.equal(місце.м.ключ, 'клуб');
assert.equal(місце.типово, false);
паспорт.картка_запиту.місце.джерело = 'default';
assert.equal(контекст.місцеКартки().м, null);
vm.runInContext(функція('збирання_руки.js', 'промптПовторуП'), контекст);
const запис = fs.readFileSync(path.join(__dirname, 'відповіді/seed3_25_ВЕРДИКТ_V1_ВИБІР_V1_повтор_.txt'), 'utf8').replace(/\r\n/g, '\n');
const промпт = запис.split('──\n')[1].split('\n\n── ВІДПОВІДЬ')[0];
const [основа, причина] = промпт.trim().split('\n');
assert.throws(() => JSON.parse(промпт));
const після = JSON.parse(контекст.промптПовторуП(основа, причина));
assert.deepEqual(після.format_error, JSON.parse(причина));
delete після.format_error;
assert.deepEqual(після, JSON.parse(основа));
console.log('Місце з чинного факту: клуб; типове не підміняє факт. Повтор: два JSON → один; завдання, дані й причина збережені.');
