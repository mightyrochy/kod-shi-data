/* Доставка спільної відповіді: журнал кожної картки, окремо від допуску мови. */
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const {питаньЗВідповіддю} = require('../../аудит/проби/записи_шару.js');
const питання = code => ({повідомлення: {kind: 'card_unchecked', statements: [{code}, {code: code + '_detail'}]}});
async function вимір(стан){
  const к = vm.createContext({МОДЕЛЬ_МОВИ_П: 'stub', безМашинногоСліду: т => т});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../показ/мовний_шар.js'), 'utf8'), к);
  let завершити, викликів = 0;
  const готово = new Promise(р => { завершити = р; });
  к.питатиПачкамиП = async (елементи, де) => {
    викликів++; await готово;
    const заяви = елементи.flatMap(([ключ, повідомлення, пов]) => пов.statements.map((з, і) => ({ключ: ключ + і,
      повідомлення, заяви: [з], текст: стан === 'missing_text' || стан === 'retry' && і ? null : 'An answer.',
      стан: стан === 'retry' ? і ? 'missing_text' : 'foreign_language' : стан})));
    const запис = {напрям: 'out_messages', де: де + '.code_unknowns',
      вхід: Object.fromEntries(елементи.map(([, ім, пов]) => [ім, пов])),
      вихід: Object.fromEntries(елементи.map(([, ім]) => [ім, '— без тексту'])), заяви};
    const записи = [запис];
    if (стан === 'retry') записи.push({...запис,
      вхід: Object.fromEntries(елементи.map(([, ім, пов]) => [ім, {...пов, statements: пов.statements.slice(1)}])),
      заяви: заяви.filter(з => з.стан === 'missing_text').map(з => ({...з, текст: 'An answer.', стан: 'foreign_language'}))});
    return {стани: new Map(елементи.map(([ключ]) => [ключ,
      {текст: '— без тексту', стан: стан === 'translated' ? стан : 'fallback'}])),
      записи};
  };
  const перша = {питання: [питання('shared'), питання('source_only')]};
  const друга = {питання: [питання('own'), питання('shared')]};
  const а = к.питаннямиП(перша, 'hand_1'), б = к.питаннямиП(друга, 'hand_2');
  завершити(); await Promise.all([а, б]);
  const доставка = [перша, друга].map(р => питаньЗВідповіддю(р.мова_шару, false));
  console.log(JSON.stringify({стан, доставка, викликів}));
  assert.deepStrictEqual(доставка, стан === 'missing_text' ? [0, 0] : [2, 2]);
  assert.strictEqual(викликів, 2);
  assert(друга.питання.every(п => п.стан_перекладу === (стан === 'translated' ? стан : 'fallback')));
  assert(!друга.питання_з_пам_яті);
  assert.strictEqual(перша.мова_шару.length, стан === 'retry' ? 2 : 1);
  const спільні = друга.мова_шару.filter(з => з.спільний_виклик);
  assert.deepStrictEqual([...new Set(спільні.flatMap(з => Array.from(з.заяви, р => р.повідомлення)))], ['питання.1', 'кнопка']);
  assert(спільні.every(з => Object.keys(з.вхід).every(кв => з.вихід[кв] === '— без тексту')));
  assert(!JSON.stringify(друга.мова_шару).includes('source_only'));
}
(async () => { for (const стан of ['translated', 'foreign_language', 'latin_remainder', 'missing_text', 'retry']) await вимір(стан); })()
  .catch(п => { console.error(п); process.exitCode = 1; });
