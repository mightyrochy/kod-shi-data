/* Перевіряє приймання на справжніх 77 звірках живого концерту. */
const assert = require('node:assert/strict');
const fs = require('fs'), path = require('path'), os = require('os');
const {знімок, порівняти, затягнути} = require('./храповик_записів.js');
const тека = path.join(__dirname, 'нічні/20261027/б1_концерт_стримано');
const база = JSON.parse(fs.readFileSync(path.join(тека, 'база.json'), 'utf8'));
const після = знімок(fs.readFileSync(path.join(тека, 'лог.txt'), 'utf8'),
  JSON.parse(fs.readFileSync(path.join(тека, 'знімки/доказ.json'), 'utf8')), 1);
assert.equal(після.звірки.length, 77);
assert.equal(порівняти(база, після).стан, 'без регресу');
const додатковийПровал = знімок(fs.readFileSync(path.join(тека, 'лог.txt'), 'utf8').replace(/^ВПАЛО 1 ·/m, 'ВПАЛО 2 ·'),
  JSON.parse(fs.readFileSync(path.join(тека, 'знімки/доказ.json'), 'utf8')), 1);
assert.equal(порівняти(база, додатковийПровал).стан, 'регрес', 'провал поза звірками не ховається');
const змінити = () => structuredClone(після);
let злам = змінити();
злам.звірки.find(з => з.зелена).зелена = false;
assert.equal(порівняти(база, злам).регресії.length, 1);
злам = змінити(); злам.звірки.shift();
assert.equal(порівняти(база, злам).стан, 'регрес');
for (const rc of [0, 1, 2, 3, null]) {
  const обірваний = знімок('', null, rc);
  assert.equal(порівняти(база, обірваний).стан, 'регрес');
}
злам = змінити(); злам.завершено = false; злам.застарілий = {виклик: 5};
злам.звірки = злам.звірки.slice(0, 2);
assert.equal(порівняти(база, злам).стан, 'запис застарів');
злам.звірки[0].зелена = false;
assert.equal(порівняти(база, злам).стан, 'регрес');
const покращено = змінити();
покращено.звірки.find(з => !з.зелена).зелена = true;
assert.equal(порівняти(база, покращено).покращення.length, 1);
assert.equal(порівняти(затягнути(база, покращено), після).стан, 'регрес');
assert.throws(() => порівняти({...база, звірки: []}, після), /живого виміру/);
assert.throws(() => порівняти({...база, звірки: база.звірки.map(({вада, ...з}) => з)}, після), /номера дошки/);
const {перелік, серіяДва, свіжіЗаписи, записатиБазу} = require('./приймання_записів.js');
assert.equal(серіяДва().length, 30);
assert(перелік().some(с => с.id === 'б1_концерт_стримано'));
assert(перелік().every(с => с.обмін && !с.записи));
assert.throws(() => записатиБазу(тека, []), /Кожній червоній/);
assert.throws(() => записатиБазу(тека, ['10231']), /EEXIST/, 'наявна база не переписується');
const тимчасова = fs.mkdtempSync(path.join(os.tmpdir(), 'Е1-набір-'));
try {
  for (const [дата, id] of [['20261027', 'концерт'], ['20261028', 'концерт'], ['20261027', 'робота']]) {
    const місце = path.join(тимчасова, дата, id);
    fs.mkdirSync(місце, {recursive: true});
    fs.copyFileSync(path.join(тека, 'повтор.json'), path.join(місце, 'повтор.json'));
  }
  const нові = свіжіЗаписи(тимчасова);
  assert.equal(нові.length, 2);
  assert(нові.find(с => с.id === 'концерт').тека.includes('20261028'));
  assert(нові.find(с => с.id === 'робота').тека.includes('20261027'));
} finally {
  assert.equal(path.dirname(path.resolve(тимчасова)), path.resolve(os.tmpdir()));
  fs.rmSync(тимчасова, {recursive: true, force: true});
}
console.log('✔ 77 живих звірок; відома вада; регрес; зникла звірка; обрив; застарілий запис; затягування бази; архів окремо');
