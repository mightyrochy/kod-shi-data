/* Збережений образ змінюється лише після явного збереження чернетки.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/пара_чернетка.js <index.html> */
const assert = require('node:assert/strict'), fs = require('node:fs');
/* Без браузера: уповільнені читання й транзакції на вигаданих профілях.
   Запуск: node аудит/проби/пара_чернетка.js --profile-unit
   Той самий делегат кліку й дві вкладки зі спільним сховищем у JSDOM без мережі:
   NODE_PATH=джерела/node_modules node аудит/проби/пара_чернетка.js --profile-dom */
function стендПрофілів(момент, {наявнаЧернетка = false} = {}) {
  const vm = require('node:vm'), path = require('node:path');
  const код = fs.readFileSync(path.join(__dirname, '../../джерела/показ/дзеркало/rack.js'), 'utf8');
  const річ = профіль => ({id: 'piece', name: 'Річ ' + профіль, color: '#f0ede5', slot: 'top'});
  const новий = профіль => ({version: 1, closet: [], saved: [{id: 'saved', name: 'Комплект ' + профіль, things: [річ(профіль)]}],
    outfit: {name: '', side: 0, sets: [наявнаЧернетка ? [{id: 'draft-' + профіль}] : [], []], id: ''}, compare: {}});
  const стани = {A: новий('A'), B: новий('B')}, початковий = structuredClone(стани);
  const черга = {}, записано = [], прочитано = [], екран = [], обробники = {}, події = {};
  const кнопка = (дія, значення) => ({dataset: {ux: дія, value: значення}});
  let профіль = 'A', підтвердження;
  const R = {activeProfile: () => профіль, currentExtra: () => 'wardrobe',
    register: (дія, fn) => { обробники[дія] = fn; }, escape: String, ik: () => '', tone: x => x,
    button: (дія, _, __, значення) => {
      if (дія === 'rack-confirm-edit') підтвердження = значення;
      return '';
    },
    money: String, pair: {occasionLabel: () => ''}, route: () => екран.push('library'), showExtra: () => екран.push('screen'), close: () => екран.push('close'),
    dialog: title => екран.push(title), say: () => екран.push('say')};
  const context = {window: {MirrorRoom: R, MirrorMaterial: {seal: () => ''}, MirrorIndex: {get: async () => null}},
    document: {addEventListener: (тип, fn) => { (події[тип] ||= []).push(fn); }, getElementById: () => null},
    FormData: class {get(k) { return {name: 'Оновлений комплект', side: '0'}[k]; }}, URL, localStorage: {getItem: () => null},
    читатиКв: ключ => new Promise(done => {
      const id = ключ.at(-1); прочитано.push(id);
      const release = () => done(structuredClone(стани[id]));
      if (момент === 'читання' && !черга.read) черга.read = release; else release();
    }),
    дб: async () => ({transaction() {
      const tx = {abort: () => tx.onabort(), objectStore: () => ({
        get(ключ) {
          const req = {result: structuredClone(стани[ключ.at(-1)])};
          const release = () => req.onsuccess();
          if (момент === 'читання транзакції' && !черга.get) черга.get = release; else queueMicrotask(release);
          return req;
        },
        put(value, ключ) {
          const id = ключ.at(-1); записано.push(id);
          const commit = () => { стани[id] = structuredClone(value); tx.oncomplete(); };
          if (момент === 'запис' && !черга.write) черга.write = commit; else queueMicrotask(commit);
        }
      })};
      return tx;
    }})};
  vm.runInNewContext(код, context);
  return {стати: id => { профіль = id; }, стани, початковий, черга, записано, прочитано, екран,
    натиснути: (дія, значення) => обробники[дія](значення, кнопка(дія, значення)),
    підтвердження: () => підтвердження,
    перечитати: id => context.читатиКв('дзеркало:речі:1:' + id),
    зберегти: () => {
      for (const fn of події.submit) fn({target: {id: 'rack-save-form', querySelector: () => null}, preventDefault() {}});
    }};
}

const наступнийТакт = () => new Promise(resolve => setImmediate(resolve));

async function межаПрофілю() {
  for (const [дія, значення] of [['rack-own', 'piece'], ['rack-anchor', 'piece'],
    ['rack-add', 'piece'], ['rack-edit-saved', 'saved']]) {
    for (const момент of ['читання', 'запис', 'без перемикання']) {
      const {стати, початковий, черга, записано, прочитано, екран, натиснути, перечитати, зберегти} = стендПрофілів(момент);
      const wait = натиснути(дія, значення);
      if (момент === 'читання') {
        assert.equal(typeof черга.read, 'function', дія + ': перше читання вже почалось');
        стати('B'); черга.read();
      }
      if (момент === 'запис') {
        await наступнийТакт();
        assert.equal(typeof черга.write, 'function', дія + ': транзакція вже почалась');
        стати('B'); черга.write();
      }
      await wait;
      assert.deepEqual(прочитано, ['A'], дія + ': читає лише початковий профіль');
      const уА = await перечитати('A');
      assert.deepEqual(await перечитати('B'), початковий.B, дія + ': інший профіль не змінено');
      const скасовано = дія === 'rack-anchor' && момент === 'читання';
      assert.deepEqual(записано, скасовано ? [] : ['A'], дія + ': запис ізольований');
      assert.equal(екран.length > 0, момент === 'без перемикання', дія + ': екран іншого профілю не оновлено');
      if (скасовано) assert.deepEqual(уА, початковий.A);
      else {
        const запис = дія === 'rack-own' ? уА.closet[0] : уА.outfit.sets[0][0];
        assert.equal(запис.id, 'piece');
        assert.equal(запис.name, 'Річ A');
        assert.deepEqual(уА.saved, початковий.A.saved, дія + ': без явного збереження оригінал цілий');
        if (дія === 'rack-edit-saved') {
          assert.equal(уА.outfit.id, 'saved');
          assert.notEqual(уА.outfit.sets[0], уА.saved[0].things);
          assert.notEqual(уА.outfit.sets[0][0], уА.saved[0].things[0]);
          стати('A'); зберегти();
          await наступнийТакт();
          const після = await перечитати('A');
          assert.equal(після.saved.length, 1, 'збереження оновлює той самий запис');
          assert.equal(після.saved[0].id, 'saved');
          assert.equal(після.saved[0].name, 'Оновлений комплект');
          assert.equal(після.outfit.id, '');
          assert.deepEqual(await перечитати('B'), початковий.B);
          assert.deepEqual(записано, ['A', 'A']);
        }
      }
    }
  }
  console.log('Пара: межа профілю — 12/12 перевірок.');

  for (const [момент, крок] of [['читання транзакції', 'get'], ['запис', 'write']]) {
    const явне = стендПрофілів(момент, {наявнаЧернетка: true});
    явне.зберегти();
    await наступнийТакт();
    assert.equal(typeof явне.черга[крок], 'function', 'явне збереження вже почалося');
    явне.стати('B'); явне.черга[крок]();
    await наступнийТакт();
    const уА = await явне.перечитати('A');
    assert.deepEqual(уА.saved[0].things, [{id: 'draft-A'}]);
    assert.equal(уА.saved[0].name, 'Оновлений комплект');
    assert.deepEqual(уА.outfit.sets, [[], []]);
    assert.deepEqual(await явне.перечитати('B'), явне.початковий.B);
    assert.deepEqual(явне.записано, ['A']);
    assert.deepEqual(явне.екран, []);
  }
  console.log('Пара: явне збереження — 2/2 при перемиканні під час транзакції.');

  const доПідтвердження = стендПрофілів('читання', {наявнаЧернетка: true});
  const очікування = доПідтвердження.натиснути('rack-edit-saved', 'saved');
  доПідтвердження.стати('B'); доПідтвердження.черга.read();
  await очікування;
  assert.deepEqual(доПідтвердження.екран, [], 'Б не отримує діалог про чернетку А');
  assert.deepEqual(доПідтвердження.записано, []);
  assert.deepEqual(доПідтвердження.стани, доПідтвердження.початковий);

  const післяДіалогу = стендПрофілів('запис', {наявнаЧернетка: true});
  await післяДіалогу.натиснути('rack-edit-saved', 'saved');
  assert.deepEqual(післяДіалогу.екран, ['Замінити чернетку комплекту?']);
  const токен = післяДіалогу.підтвердження();
  assert.ok(токен);
  післяДіалогу.стати('B');
  const чужаЗгода = післяДіалогу.натиснути('rack-confirm-edit', токен);
  await наступнийТакт();
  assert.deepEqual(післяДіалогу.прочитано, ['A']);
  assert.deepEqual(післяДіалогу.записано, []);
  assert.deepEqual(післяДіалогу.стани, післяДіалогу.початковий);
  await чужаЗгода;
  післяДіалогу.стати('A');
  await післяДіалогу.натиснути('rack-edit-saved', 'saved');
  const стараЗгода = післяДіалогу.натиснути('rack-confirm-edit', токен);
  await наступнийТакт();
  assert.deepEqual(післяДіалогу.записано, [], 'діалог приймає лише власний токен');
  await стараЗгода;
  const згода = післяДіалогу.натиснути('rack-confirm-edit', післяДіалогу.підтвердження());
  await наступнийТакт();
  assert.equal(typeof післяДіалогу.черга.write, 'function');
  післяДіалогу.стати('B'); післяДіалогу.черга.write();
  await згода;
  assert.deepEqual(післяДіалогу.записано, ['A']);
  assert.deepEqual(післяДіалогу.екран, ['Замінити чернетку комплекту?', 'Замінити чернетку комплекту?']);
  assert.equal((await післяДіалогу.перечитати('A')).outfit.id, 'saved');
  assert.deepEqual(await післяДіалогу.перечитати('B'), післяДіалогу.початковий.B);

  const паралельнаЧернетка = стендПрофілів('читання');
  const заміна = паралельнаЧернетка.натиснути('rack-edit-saved', 'saved');
  паралельнаЧернетка.черга.read();
  паралельнаЧернетка.стани.A.outfit.sets[0].push({id: 'нова-річ'});
  await заміна;
  assert.deepEqual(паралельнаЧернетка.записано, [], 'не замінює чернетку, що виникла після першого читання');
  assert.deepEqual(паралельнаЧернетка.стани.A.outfit.sets[0], [{id: 'нова-річ'}]);
  assert.deepEqual(паралельнаЧернетка.екран, ['Не вдалося зберегти']);

  const післяПеремикання = стендПрофілів('читання транзакції', {наявнаЧернетка: true});
  await післяПеремикання.натиснути('rack-edit-saved', 'saved');
  післяПеремикання.стани.A.outfit.sets[0] = [];
  const застарілаЗгода = післяПеремикання.натиснути('rack-confirm-edit', післяПеремикання.підтвердження());
  await наступнийТакт();
  assert.equal(typeof післяПеремикання.черга.get, 'function');
  післяПеремикання.стати('B'); післяПеремикання.черга.get();
  await застарілаЗгода;
  assert.deepEqual(післяПеремикання.записано, []);
  assert.deepEqual((await післяПеремикання.перечитати('A')).outfit.sets, [[], []]);
  assert.deepEqual(await післяПеремикання.перечитати('B'), післяПеремикання.початковий.B);
  assert.deepEqual(післяПеремикання.екран, ['Замінити чернетку комплекту?'], 'Б не отримує повідомлення про конфлікт А');
  console.log('Пара: підтвердження належить початковому профілю, нова чернетка захищена.');
}

async function клікЗБібліотеки() {
  const path = require('node:path');
  const {JSDOM, VirtualConsole} = require('jsdom'), {IDBFactory, IDBKeyRange} = require('fake-indexeddb');
  const {підставитиШаблон, прочитатиДовідникJSON} = require('../../джерела/показ_шаблон.js');
  const джерела = path.resolve(__dirname, '../../джерела');
  const html = підставитиШаблон(path.join(джерела, 'показ.html'), {
    __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'проба', __ВІДБИТОК__: 'проба',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(джерела),
    __ПРОМПТ_КОЛІР_ПОКАЗУ__: '', __ВИБІРКА_ПОКАЗУ__: '{}'
  });
  const сховище = new IDBFactory(), запити = [], помилки = [], вікна = [];
  const тихо = new VirtualConsole().on('jsdomError', помилка => помилки.push(помилка));
  const чекати = async (умова, мітка) => {
    const межа = Date.now() + 2000;
    while (Date.now() < межа) {
      const результат = await умова();
      if (результат) return результат;
      await new Promise(resolve => setTimeout(resolve, 10));
    }
    assert.fail(помилки[0]?.message || мітка);
  };
  const відкрити = async () => {
    const {window: w} = new JSDOM(html, {runScripts: 'dangerously', pretendToBeVisual: true,
      url: 'https://wardrobe.invalid/', virtualConsole: тихо,
      beforeParse(w) {
        w.indexedDB = сховище; w.IDBKeyRange = IDBKeyRange;
        w.fetch = async адреса => { запити.push(адреса); throw Error('Мережі у пробі немає.'); };
        w.XMLHttpRequest.prototype.send = () => { запити.push('XHR'); throw Error('Мережі у пробі немає.'); };
        w.scrollTo = () => {};
        w.HTMLElement.prototype.scrollIntoView = () => {};
        w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
        w.HTMLDialogElement.prototype.close = function () { this.open = false; };
      }});
    вікна.push(w);
    await чекати(() => w.MirrorRoom?.available(), 'показ не запустився');
    return w;
  };
  const ключ = профіль => 'дзеркало:речі:1:' + профіль;
  const кнопка = (w, селектор) => чекати(() => w.document.querySelector(селектор), 'немає ' + селектор);
  const натиснути = async (w, селектор) => (await кнопка(w, селектор)).click();
  const редагуватиЗбережене = async (w, id) => {
    w.MirrorRoom.route('бібліотека');
    await натиснути(w, '.rack-saved-card[data-value="' + id + '"] span');
    await натиснути(w, '[data-ux="rack-edit-saved"][data-value="' + id + '"]');
  };
  const дані = профіль => ({version: 1, closet: [], compare: {}, outfit: {name: '', id: '', side: 0, sets: [[], []]},
    saved: [{id: 'saved', name: 'Комплект ' + профіль, things: [{id: 'piece', name: 'Річ ' + профіль, slot: 'top'}]}]});
  try {
    const початкове = await відкрити();
    await початкове.писатиКв('профілі', [{ід: 'A', назва: 'Профіль А'}, {ід: 'B', назва: 'Профіль Б'}]);
    await початкове.писатиКв('активний', 'A');
    await початкове.писатиКв(ключ('A'), дані('A'));
    await початкове.писатиКв(ключ('B'), дані('B'));

    const w = await відкрити(), {document: d} = w;
    assert.equal(w.MirrorRoom.activeProfile(), 'A');
    w.MirrorRoom.route('бібліотека');
    await натиснути(w, '.rack-saved-card[data-value="saved"] span');
    const редагувати = await чекати(() => d.querySelector('[data-ux="rack-edit-saved"][data-value="saved"]'), 'клік не відкрив збережений образ');
    assert.equal(w.MirrorRoom.currentExtra(), 'saved');
    assert.equal(d.querySelector('#mirror-heading h1').textContent, 'Комплект A');
    редагувати.click();
    await натиснути(w, '[data-ux="rack-save-outfit"]');
    const форма = await чекати(() => d.querySelector('#rack-save-form'), 'немає форми явного збереження');
    const доЗапису = await w.читатиКв(ключ('A'));
    assert.deepEqual(доЗапису.saved, дані('A').saved);
    assert.equal(доЗапису.outfit.id, 'saved');
    форма.elements.name.value = 'Оновлений комплект А';
    форма.querySelector('button').click();
    await чекати(async () => (await w.читатиКв(ключ('A'))).saved[0].name === 'Оновлений комплект А', 'форма не зберегла образ');

    const після = await відкрити();
    const збережено = await після.читатиКв(ключ('A'));
    assert.equal(збережено.saved.length, 1);
    assert.equal(збережено.saved[0].id, 'saved');
    assert.equal(збережено.saved[0].name, 'Оновлений комплект А');
    assert.equal(збережено.outfit.id, '');
    assert.deepEqual(await після.читатиКв(ключ('B')), дані('B'));
    console.log('Пара: клік у бібліотеці, явне збереження та повторне відкриття сховища у JSDOM пройшли.');

    const річ = id => ({id, name: 'Річ ' + id, slot: 'top'});
    const синтетика = дані('A');
    синтетика.saved.push({id: 'інший', name: 'Інший образ', things: [річ('one'), річ('two')]});
    синтетика.outfit = {id: 'чернетка', name: 'Початкова чернетка', side: 0, sets: [[річ('one'), річ('two')], []]};
    const підтвердити = '#mirror-sheet[open] [data-ux="rack-confirm-edit"]';
    for (const зміна of ['інша чернетка', 'та сама чернетка', 'порожня чернетка']) {
      await початкове.писатиКв(ключ('A'), синтетика);
      const перша = await відкрити(), друга = await відкрити();
      await редагуватиЗбережене(перша, 'saved');
      const стараЗгода = await кнопка(перша, підтвердити);

      const новийІд = зміна === 'інша чернетка' ? 'інший' : 'чернетка';
      if (зміна === 'інша чернетка') {
        await редагуватиЗбережене(друга, 'інший');
        await натиснути(друга, підтвердити);
      } else {
        друга.MirrorRoom.route('бібліотека');
        await натиснути(друга, '#mirror-saved-manual [data-ux="compose"]');
      }
      const видалити = async (id, решта) => {
        await натиснути(друга, '[data-ux="rack-edit"][data-value="0|' + id + '"]');
        await натиснути(друга, '#mirror-sheet[open] [data-ux="rack-drop"][data-value="0|' + id + '"]');
        await чекати(async () => (await друга.читатиКв(ключ('A'))).outfit.sets[0].length === решта, 'чернетка не змінилася');
      };
      await видалити('two', 1);
      if (зміна === 'порожня чернетка') await видалити('one', 0);
      const змінена = await друга.читатиКв(ключ('A'));
      assert.equal(змінена.outfit.id, новийІд);
      assert.equal(стараЗгода.closest('dialog').open, true);
      стараЗгода.click();
      const повідомлення = () => перша.document.querySelector('#mirror-sheet-title').textContent;
      await чекати(() => повідомлення() === 'Не вдалося зберегти' || перша.MirrorRoom.currentExtra() === 'compose', 'стара згода не завершилася');
      assert.equal(перша.MirrorRoom.currentExtra(), 'saved', зміна + ' не повинна бути перезаписана');
      assert.match(перша.document.querySelector('#mirror-sheet-content').textContent, /Чернетка змінилася.*підтвердити заміну/);
      const відновлена = await відкрити();
      assert.deepEqual(await відновлена.читатиКв(ключ('A')), змінена, зміна + ' переживає повторне відкриття');
      assert.deepEqual(await відновлена.читатиКв(ключ('B')), дані('B'));

      await редагуватиЗбережене(перша, 'saved');
      if (зміна !== 'порожня чернетка') await натиснути(перша, підтвердити);
      await чекати(() => перша.MirrorRoom.currentExtra() === 'compose', 'нова спроба не перейшла до редагування');
      const нова = await перша.читатиКв(ключ('A'));
      assert.equal(нова.outfit.id, 'saved');
      assert.deepEqual(нова.saved, синтетика.saved);
    }
    assert.deepEqual(помилки, []);
    assert.deepEqual(запити, []);
    console.log('Пара: дві вкладки — 3/3 застарілих згод відхилено, нове редагування працює.');
  } finally {
    for (const w of вікна) w.close();
  }
}

(async () => {
  if (process.argv[2] === '--profile-unit') return межаПрофілю();
  if (process.argv[2] === '--profile-dom') return клікЗБібліотеки();
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
