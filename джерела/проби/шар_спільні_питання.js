/* Доставка спільної відповіді: журнал кожної картки, окремо від допуску мови. */
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const {питаньЗВідповіддю} = require('../../аудит/проби/записи_шару.js');
const питання = code => ({повідомлення: {kind: 'card_unchecked', statements: [{code}]}});
async function вимір(стан){
  const к = vm.createContext({МОДЕЛЬ_МОВИ_П: 'stub', безМашинногоСліду: т => т});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../показ/мовний_шар.js'), 'utf8'), к);
  let завершити, викликів = 0;
  const готово = new Promise(р => { завершити = р; });
  к.питатиПачкамиП = async (елементи, де) => {
    викликів++; await готово;
    const заяви = елементи.map(([ключ, повідомлення, пов]) => ({ключ,
      повідомлення, заяви: пов.statements, текст: стан === 'missing_text' ? null : 'An answer.', стан}));
    return {стани: new Map(елементи.map(([ключ]) => [ключ,
      {текст: '— без тексту', стан: стан === 'translated' ? стан : 'fallback'}])),
      записи: [{напрям: 'out_messages', де: де + '.code_unknowns',
        вхід: Object.fromEntries(елементи.map(([, ім, пов]) => [ім, пов])), заяви}]};
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
  assert.strictEqual(перша.мова_шару.length, 1);
  assert.deepStrictEqual(Array.from(друга.мова_шару[1].заяви, з => з.повідомлення), ['питання.1', 'кнопка']);
  assert(!JSON.stringify(друга.мова_шару).includes('source_only'));
}
(async () => { for (const стан of ['translated', 'foreign_language', 'latin_remainder', 'missing_text']) await вимір(стан); })()
  .catch(п => { console.error(п); process.exitCode = 1; });
