/* Перевіряє відмови replay на зайвому, пропущеному та зміненому виклику моделі. */
const assert = require('node:assert/strict');
const fs = require('fs'), os = require('os'), path = require('path');
const {ЗаписанийОбмін, ТекстовіВідповіді, записатиОбмін} = require('./записаний_обмін.js');
const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'replay-'));
try {
  const запит = {model: 'запис', messages: [{role: 'user', content: [{type: 'text', text: 'слова'}]}]};
  const відповідь = {status: 200, contentType: 'application/json', headers: {'x-model': 'жива'},
    body: JSON.stringify({content: [{type: 'text', text: 'відповідь'}], stop_reason: 'max_tokens'})};
  записатиОбмін(тека, 1, запит, відповідь);
  let replay = new ЗаписанийОбмін(тека);
  assert.throws(() => replay.завершити(), /Неповне відтворення/);
  replay = new ЗаписанийОбмін(тека);
  assert.deepEqual(replay.взяти({...запит, model: 'запис'}), відповідь);
  assert.deepEqual(replay.завершити(), {взято: 1, записів: 1});
  assert.throws(() => replay.взяти(запит), /Нема невзятої відповіді/);
  assert.throws(() => replay.завершити(), /Неповне відтворення/);
  replay = new ЗаписанийОбмін(тека);
  assert.throws(() => replay.взяти({...запит, messages: []}), /Нема невзятої відповіді/);
  assert.throws(() => записатиОбмін(тека, 1, запит, відповідь), /EEXIST/);
  const архів = path.join(тека, 'архів'), тексти = path.join(архів, 'VIDPOVIDI');
  fs.mkdirSync(тексти, {recursive: true});
  fs.writeFileSync(path.join(архів, 'лог.txt'), '');
  fs.writeFileSync(path.join(тексти, 'seed3_01_архів.txt'),
    '── ПРОМПТ (5 симв.) ──\nархів\n\n── ВІДПОВІДЬ (5 симв., 0 с, HTTP 200) ──\nархів\n');
  записатиОбмін(path.join(архів, 'доповнення'), 1, запит, відповідь);
  let доповнений = new ТекстовіВідповіді(тексти);
  assert.throws(() => доповнений.завершити(), /Неповне відтворення/);
  assert.deepEqual(доповнений.взяти(запит, 'новий промпт', 'новий тип'), відповідь);
  assert.equal(доповнений.завершити().взято, 0, 'доповнення не видається за старий запис');
  assert.throws(() => доповнений.взяти(запит, 'новий промпт', 'новий тип'), /Нема невзятої відповіді/);
  доповнений = new ТекстовіВідповіді(тексти);
  assert.throws(() => доповнений.взяти({...запит, messages: []}, 'новий промпт', 'новий тип'), /Нема невзятої текстової відповіді/);
  console.log('✔ точний обмін; обрізання; пропущений, зайвий і змінений виклик; захист запису');
  console.log('✔ живе доповнення: точний запит, окремий облік, відмова на невикористаному та зміненому обміні');
} finally {
  assert.equal(path.dirname(path.resolve(тека)), path.resolve(os.tmpdir()));
  fs.rmSync(тека, {recursive: true, force: true});
}
