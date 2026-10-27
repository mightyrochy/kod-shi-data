/* Відтворення межі повідомлень: справжній Python-шов і код показу, модель — запис або контрольована відповідь.
   Запуск з кореня: node аудит/проби/ремонт_шар.js [--перевірити] */
const fs = require('fs'), path = require('path'), vm = require('vm');
const {spawnSync} = require('child_process');
const корінь = path.resolve(__dirname, '../..');
const індексБази = process.argv.indexOf('--база');
const база = індексБази >= 0 ? process.argv[індексБази + 1] : null;
const читати = ім => {
  if (!база) return fs.readFileSync(path.join(корінь, ім), 'utf8');
  const р = spawnSync('git', ['show', `${база}:${ім}`], {cwd: корінь, encoding: 'utf8'});
  if (р.status !== 0) throw new Error(р.stderr);
  return р.stdout;
};
const пітон = база ? читати('джерела/мовний_шар.py') : null;
const міст = д => {
  const р = spawnSync('python', ['-X', 'utf8', '-c',
    'import sys, json; д=json.load(sys.stdin); ' + (база
      ? 'exec(compile(д["код"], "мовний_шар_до.py", "exec")); print(мова(д["вхід"]))'
      : 'import мовний_шар; print(мовний_шар.мова(д["вхід"]))')],
    {cwd: path.join(корінь, 'джерела'), input: JSON.stringify({вхід: д, код: пітон}), encoding: 'utf8'});
  if (р.status !== 0) throw new Error(р.stderr);
  return JSON.parse(р.stdout);
};
const джерело = читати('джерела/показ/мовний_шар.js');
function середовище(модель){
  const с = vm.createContext({console, МОДЕЛЬ_МОВИ_П: 'запис', містП: async (_, д) => міст(д),
    безМашинногоСліду: т => т});
  vm.runInContext(джерело, с);
  с.модельМовиП = модель;
  return с;
}
const повідомлення = і => ({kind: 'card_unchecked', statements: [{code: 'scarf_size_unknown',
  values: {item: {free_text: 'Шарф', lang: 'uk'}, item_id: і}}]});
const заяви = п => JSON.parse(п.split('ПОВІДОМЛЕННЯ:\n')[1]);
(async () => {
  const л = {};
  let викликів = 0, промптПовтору = '';
  const с = середовище(async п => {
    викликів++;
    if (викликів > 1) промптПовтору = п;
    return JSON.stringify(Object.fromEntries(заяви(п).map(з => [з.key,
      викликів === 1 ? 'The scarf size is unknown.' : 'Розміру цього шарфа я не знаю.'])));
  });
  const р = await с.повідомленнямП({рядок: повідомлення('а')}, 'replay');
  л.повторів_чужої_мови = викликів - 1;
  л.перекладено_після_повтору = р.заяви.filter(з => з.стан === 'translated').length;
  л.повтор_з_поясненням = промптПовтору.includes('foreign_language');
  const розмітка = міст({повідомлення: {рядок: повідомлення('б')}}).розмітка;
  const ключ = розмітка[0].ключ;
  const дубль = міст({розмітка_повідомлень: розмітка,
    відповідь_моделі: `{"${ключ}":"Перша відповідь.","${ключ}":"Друга відповідь."}`});
  л.прийнято_неоднозначних = дубль.заяви.filter(з => з.стан === 'translated').length;
  const без = середовище(async () => '{}');
  const к = {питання: [повідомлення('в'), повідомлення('в'), повідомлення('г')].map(повідомлення => ({повідомлення})), мова_шару: []};
  await без.питаннямиП(к, 'hand_1');
  л.питань_без_видимого_стану = к.питання.filter(п => !п.текст).length;
  const копія = {питання: к.питання.map(п => ({повідомлення: п.повідомлення})), мова_шару: []};
  await без.питаннямиП(копія, 'hand_2');
  л.помилково_з_памяті = копія.питання_з_пам_яті;
  console.log(JSON.stringify(л, null, 2));
  if (process.argv.includes('--перевірити')){
    const очікувані = {повторів_чужої_мови: 1, перекладено_після_повтору: 1, повтор_з_поясненням: true,
      прийнято_неоднозначних: 0};
    for (const [к, в] of Object.entries(очікувані)) if (л[к] !== в) throw new Error(`${к}: ${л[к]} ≠ ${в}`);
  }
})().catch(п => { console.error(п); process.exitCode = 1; });
