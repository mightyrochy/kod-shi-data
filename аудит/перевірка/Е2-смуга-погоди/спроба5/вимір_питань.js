/* Вимір проєкції питань картки на чинній функції показу, без викликів моделі. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.resolve(__dirname, '../../../..');
const source = fs.readFileSync(path.join(root, 'джерела/показ/мовний_шар.js'), 'utf8');
const start = source.indexOf('async function питаннямиП(');
const end = source.indexOf('/* Дотик розгорнув', start);
if (start < 0 || end < 0) throw new Error('Функцію показу не знайдено');
const message = {kind: 'question', statements: [{code: 'unknown_input'}]};
const original = [
  {правило: 'A', повідомлення: message},
  {правило: 'B', повідомлення: message},
  {правило: 'C', повідомлення: message, на_розгортання: true},
  {правило: 'D', повідомлення: message, для_всіх: true},
];
const context = vm.createContext({МОДЕЛЬ_МОВИ_П: false, к: {питання: original}});
vm.runInContext(source.slice(start, end) + '; питаннямиП(к, "вимір", false);', context)
  .then(() => console.log(JSON.stringify({вхід: original.length, картка: context.к.питання.length,
    одразу: context.к.питання.filter(p => !p.для_всіх && !p.на_розгортання).length,
    відкладених: context.к.питання.filter(p => p.на_розгортання).length,
    для_всіх: context.к.питання.filter(p => p.для_всіх).length})))
  .catch(error => { console.error(error); process.exitCode = 1; });
