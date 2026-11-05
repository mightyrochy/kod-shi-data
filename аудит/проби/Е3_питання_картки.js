const fs = require('fs'), vm = require('vm'), cp = require('child_process');
const path = require('path'), root = process.cwd();
const read = file => process.argv[2] ? cp.execFileSync('git', ['show', process.argv[2] + ':' + file], {encoding: 'utf8'}) : fs.readFileSync(file, 'utf8');
const source = read('джерела/показ/мовний_шар.js');
const {питаньЗВідповіддю} = require(path.join(root, 'аудит/проби/записи_шару.js'));
const message = {kind: 'card_unchecked', statements: [{code: 'outer_shoulder_not_measured', values: {item: 'жакет'}}]};
const question = rule => ({правило: rule, повідомлення: structuredClone(message)});
async function measure(name, questions, mode, expand = false){
  const c = vm.createContext({МОДЕЛЬ_МОВИ_П: mode !== 'off', СТАНИ_НЕ_МОВИ_П: ['foreign_language'],
    НАПИС_БЕЗ_ШАРУ_П: {card_unchecked: 'Пояснення не надійшло.'}, НАПИС_БЕЗ_ТЕКСТУ_П: 'Немає тексту.',
    безМашинногоСліду: s => s});
  vm.runInContext(source.slice(source.indexOf('const ПАМ_ЯТЬ_ПИТАНЬ_П ='), source.indexOf('/* Дотик розгорнув кнопку:')), c);
  c.питатиПачкамиП = async elements => {
    const states = new Map(), rows = [], input = {};
    for (const [key, place, message] of elements){
      const translated = mode !== 'foreign';
      states.set(key, {текст: translated ? 'Плече не виміряне.' : 'Пояснення не надійшло.', стан: translated ? 'translated' : 'fallback'});
      if (translated) vm.runInContext('ПАМ_ЯТЬ_ПИТАНЬ_П', c).set(key, 'Плече не виміряне.');
      input[place] = message;
      rows.push({повідомлення: place, ключ: key, текст: translated ? 'Плече не виміряне.' : 'Shoulder unknown.', стан: translated ? 'translated' : 'foreign_language'});
    }
    return {стани: states, записи: [{напрям: 'out_messages', де: 'hand_1.code_unknowns', вхід: input, заяви: rows}]};
  };
  const card = {питання: questions};
  if (mode === 'cached') vm.runInContext('ПАМ_ЯТЬ_ПИТАНЬ_П', c).set(JSON.stringify(message), 'Плече не виміряне.');
  await c.питаннямиП(card, 'hand_1', expand);
  const count = card.питання.filter(q => !q.для_всіх && !!q.на_розгортання === expand).length;
  const answers = питаньЗВідповіддю(card.мова_шару, false), cached = card.питання_з_пам_яті || 0;
  console.log(JSON.stringify({сцена: name, пункти: count, рядки: (card.питання_жінці || []).length,
    відповіді: answers, пам_ять: cached, розбіжність: mode === 'off' ? null : count - answers - cached,
    правила: card.питання.filter(q => !q.для_всіх).flatMap(q => q.правила || [q.правило]),
    складові: card.питання.flatMap(q => q.складові || []).map(q => q.правило)}));
}
(async () => {
  for (const mode of ['foreign', 'translated', 'cached', 'off'])
    await measure(mode, [question('K-OUT-41'), question('K-OUT-42')], mode);
  await measure('розгорнуто', [question('K-OUT-41'), question('K-OUT-42')].map(q => ({...q, на_розгортання: 1})), 'foreign', true);
  await measure('різні речі', [question('K-OUT-41'), {правило: 'K-OUT-42', повідомлення: {...message, statements: [{code: 'outer_shoulder_not_measured', values: {item: 'пальто'}}]}}], 'foreign');
  await measure('для всіх', [{...question('K-OUT-41'), для_всіх: 1}, question('K-OUT-42')], 'foreign');
})().catch(e => {console.error(e); process.exitCode = 1;});
