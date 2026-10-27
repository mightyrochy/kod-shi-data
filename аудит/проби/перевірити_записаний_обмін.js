/* Перевіряє відмови replay на зайвому, пропущеному та зміненому виклику моделі. */
const assert = require('node:assert/strict');
const fs = require('fs'), os = require('os'), path = require('path');
const {ЗаписанийОбмін, записатиОбмін} = require('./записаний_обмін.js');
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
  console.log('✔ точний обмін; обрізання; пропущений, зайвий і змінений виклик; захист запису');
} finally {
  for (const ім of fs.readdirSync(тека)) fs.unlinkSync(path.join(тека, ім));
  fs.rmdirSync(тека);
}
