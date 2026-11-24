/* Збережений образ змінюється лише після явного збереження чернетки.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/пара_чернетка.js <index.html> */
const assert = require('node:assert/strict'), fs = require('node:fs');
/* Без браузера: уповільнені читання й транзакції на вигаданих профілях.
   Запуск: node аудит/проби/пара_чернетка.js --profile-unit */
async function межаПрофілю() {
  const vm = require('node:vm'), path = require('node:path');
  const код = fs.readFileSync(path.join(__dirname, '../../джерела/показ/дзеркало/rack.js'), 'utf8');
  const річ = {id: 'piece', name: 'Річ', color: '#f0ede5', slot: 'top'};
  const новий = () => ({version: 1, closet: [], saved: [{id: 'saved', name: 'Комплект', things: [річ]}],
    outfit: {name: '', side: 0, sets: [[], []], id: ''}, compare: {}});
  for (const [дія, значення] of [['rack-own', 'piece'], ['rack-anchor', 'piece'],
    ['rack-add', 'piece'], ['rack-edit-saved', 'saved']]) {
    for (const момент of ['читання', 'запис', 'без перемикання']) {
      const стани = {A: новий(), B: новий()}, початковий = structuredClone(стани);
      const черга = {}, записано = [], прочитано = [], екран = [], обробники = {}, події = {};
      let профіль = 'A';
      const R = {activeProfile: () => профіль, currentExtra: () => 'wardrobe',
        register: (a, f) => { обробники[a] = f; }, escape: String, button: () => '', ik: () => '', tone: x => x,
        money: String, pair: {occasionLabel: () => ''}, route: () => екран.push('library'), showExtra: () => екран.push('screen'), close: () => екран.push('close'),
        dialog: () => екран.push('dialog'), say: () => екран.push('say')};
      const context = {window: {MirrorRoom: R, MirrorMaterial: {seal: () => ''}, MirrorIndex: {get: async () => null}},
        document: {addEventListener: (тип, fn) => { (події[тип] ||= []).push(fn); }, getElementById: () => null},
        FormData: class {get(k) { return {name: 'Оновлений комплект', side: '0'}[k]; }}, URL, localStorage: {getItem: () => null},
        читатиКв: ключ => new Promise(done => {
          const id = ключ.at(-1); прочитано.push(id);
          const release = () => done(structuredClone(стани[id]));
          if (момент === 'читання') черга.read = release; else release();
        }),
        дб: async () => ({transaction() {
          const tx = {objectStore: () => ({
            get(ключ) {
              const req = {result: structuredClone(стани[ключ.at(-1)])};
              queueMicrotask(() => req.onsuccess());
              return req;
            },
            put(value, ключ) {
              const id = ключ.at(-1); записано.push(id);
              const commit = () => { стани[id] = structuredClone(value); tx.oncomplete(); };
              if (момент === 'запис') черга.write = commit; else queueMicrotask(commit);
            }
          })};
          return tx;
        }})};
      vm.runInNewContext(код, context);
      const wait = обробники[дія](значення);
      if (момент === 'читання') { профіль = 'B'; черга.read(); }
      if (момент === 'запис') {
        await new Promise(resolve => setImmediate(resolve));
        assert.equal(typeof черга.write, 'function', дія + ': транзакція вже почалась');
        профіль = 'B'; черга.write();
      }
      await wait;
      assert.deepEqual(прочитано, ['A'], дія + ': читає лише початковий профіль');
      assert.deepEqual(стани.B, початковий.B, дія + ': інший профіль не змінено');
      assert.deepEqual(записано, момент === 'читання' ? [] : ['A'], дія + ': запис ізольований');
      assert.equal(екран.length > 0, момент === 'без перемикання', дія + ': екран іншого профілю не оновлено');
      if (момент !== 'читання') {
        if (дія === 'rack-own') assert.equal(стани.A.closet[0].id, 'piece');
        else assert.equal(стани.A.outfit.sets[0][0].id, 'piece');
        assert.deepEqual(стани.A.saved, початковий.A.saved, дія + ': без явного збереження оригінал цілий');
        if (дія === 'rack-edit-saved' && момент === 'без перемикання') {
          assert.notEqual(стани.A.outfit.sets[0], стани.A.saved[0].things);
          assert.notEqual(стани.A.outfit.sets[0][0], стани.A.saved[0].things[0]);
          for (const fn of події.submit) fn({target: {id: 'rack-save-form', querySelector: () => null}, preventDefault() {}});
          await new Promise(resolve => setImmediate(resolve));
          assert.equal(стани.A.saved.length, 1, 'збереження оновлює той самий запис');
          assert.equal(стани.A.saved[0].id, 'saved');
          assert.equal(стани.A.saved[0].name, 'Оновлений комплект');
          assert.equal(стани.A.outfit.id, '');
          assert.deepEqual(стани.B, початковий.B);
          assert.deepEqual(записано, ['A', 'A']);
        }
      }
    }
  }
  console.log('Пара: межа профілю — 12/12 перевірок.');
}


(async () => {
  if (process.argv[2] === '--profile-unit') return межаПрофілю();
  const {chromium} = require('playwright');
  const браузер = await chromium.launch({...(process.env.CHROMIUM ? {executablePath: process.env.CHROMIUM} : {}), args: ['--no-sandbox']});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}, reducedMotion: 'reduce'});
    const адреса = 'http://localhost/';
    await стор.route('**/*', р => р.request().url() === адреса
      ? р.fulfill({contentType: 'text/html; charset=utf-8', body: fs.readFileSync(process.argv[2])}) : р.abort());
    const відкрити = async () => { await стор.goto(адреса); await стор.waitForFunction(() => window.MirrorRoom?.available()); };
    const дія = (ключ, значення) => стор.locator('[data-ux="' + ключ + '"]' +
      (значення === undefined ? '' : '[data-value="' + значення + '"]') + ':visible').first().click();
    const дані = () => стор.evaluate(() => читатиКв('дзеркало:речі:1:' + АКТИВНИЙ));
    await відкрити();
    await стор.evaluate(async () => {
      const речі = ['a', 'b', 'c'].map((id, i) => ({id, name: ['Сорочка', 'Спідниця', 'Штани'][i],
        color: '#f0ede5', price: null, image: '', url: '', shop: '', slot: i ? 'bottom' : 'top'}));
      await писатиКв('дзеркало:речі:1:' + АКТИВНИЙ, {version: 1, closet: речі,
        saved: [{id: 'saved', name: 'Збережений комплект', things: [речі[0]], worn: false, date: 1}],
        outfit: {name: '', side: 0, sets: [[], []], id: ''}, compare: {left: null, right: null, decision: ''}});
    });
    await відкрити();
    await дія('library'); await дія('rack-saved', 'saved'); await дія('rack-edit-saved', 'saved');
    await дія('rack-add-side', '0'); await дія('rack-set-own'); await дія('rack-item', 'b'); await дія('rack-add', 'b');
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.sets[0].length === 2);
    let стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'додавання до чернетки не змінює збережене');
    await відкрити();
    стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'початковий образ цілий після перезавантаження');
    assert.deepEqual(стан.outfit.sets[0].map(р => р.id), ['a', 'b'], 'чернетка збережена окремо');
    await дія('compose');
    await дія('rack-edit', '0|a'); await дія('rack-replace', '0|a'); await дія('rack-set-own');
    await дія('rack-item', 'c'); await дія('rack-add', 'c'); await дія('rack-accept-replacement');
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.sets[0][0].id === 'c');
    стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'підтверджена заміна теж лишається в чернетці');
    await дія('rack-save-outfit');
    await стор.locator('#rack-save-form button').click();
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.id === '');
    await відкрити();
    стан = await дані();
    assert.equal(стан.saved.length, 1, 'оновлено той самий образ');
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['c', 'b'], 'лише збереження переносить зміни до образу');
    console.log('Пара: додавання, заміна, перезавантаження та явне збереження — пройдено.');
  } finally { await браузер.close(); }
})().catch(помилка => { console.error(помилка); process.exitCode = 1; });
