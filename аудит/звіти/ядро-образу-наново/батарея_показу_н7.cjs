/* Локальний показ після перемикання Н7. Міст і модель на межі підмінені, решта — JS продукту. */
const assert = require('node:assert/strict');
const {AsyncLocalStorage} = require('node:async_hooks');
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM, VirtualConsole} = require('jsdom');
const {IDBFactory, IDBKeyRange} = require('fake-indexeddb');

const дж = process.argv[2];
const шаблон = fs.readFileSync(path.join(дж, 'показ.html'), 'utf8');
const допомога = require(path.join(дж, 'показ_шаблон.js'));
const довідник = допомога.прочитатиДовідникJSON(дж);
const вибірка = допомога.прочитатиВибірку(дж);
const промпт = допомога.прочитатиПромптКольору(дж);
const трохи = () => new Promise((готово) => setImmediate(готово));
const варіантКонтекст = new AsyncLocalStorage();
process.on('unhandledRejection', (е) => {
  const помилки = варіантКонтекст.getStore();
  if (!помилки) throw е;
  помилки.push(е);
});

function сторінка(без, помилки) {
  const html = шаблон
    .replace(/<link rel="stylesheet" href="показ.css">/, '')
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/,
             '<script>window.loadPyodide=null;</script>')
    .replace(/<script src="показ\/([^"]+)"><\/script>/g, (рядок, ім) =>
      без.has('показ/' + ім) ? '' : рядок);
  const резерв = fs.readFileSync(path.join(дж, 'резерв_каналу.json'), 'utf8');
  const зібрано = допомога.зібратиШаблонПоказу(html, дж)
    .replace('__РЕЗЕРВ_КАНАЛУ__', () => резерв)
    .replace('__ПОШУК_РЕЧЕЙ__', 'H4sIAAAAAAAA');
  const код = допомога.підставитиШаблон(зібрано, {
    __МОДУЛІ_ПОКАЗУ__: 'Н7', __ЗБІРКА_ПОКАЗУ__: 'Н7', __ВІДБИТОК__: 'abc',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог · 24 речі',
    __ДОВІДНИК_ПОКАЗУ__: довідник, __ПРОМПТ_КОЛІР_ПОКАЗУ__: промпт, __ВИБІРКА_ПОКАЗУ__: вибірка,
  });
  const консоль = new VirtualConsole();
  консоль.on('jsdomError', (е) => помилки.push(е.cause || е));
  const дом = new JSDOM(код, {runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: консоль,
    url: 'https://example.test/показ.html', beforeParse(w) {
      w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange;
      w.fetch = () => Promise.reject(new Error('у батареї мережі нема'));
      w.scrollTo = () => {};
      w.document.execCommand = () => true;
      w.Blob = Blob; w.Response = Response; w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
      w.CompressionStream = CompressionStream; w.DecompressionStream = DecompressionStream;
      w.Element.prototype.scrollIntoView = () => {};
    }});
  return {w: дом.window, помилки};
}

const ПРОБИ = {
  'показ.відкриття': [`ЯДРО_П && !!document.body && typeof режим === 'function'`, true],
  'ядро.показ_збирає': [`(async () => {
    const виклики = [];
    містП = async (ім, д) => {
      виклики.push(ім + ':' + д.дія);
      return {кінець: true, картки: [{рука: 1, речі: [{ід:'d1', слот:'сукня', назва:'Сукня'}]}]};
    };
    await зібратиОбразиП();
    if (!ЗБ?.готово) throw new Error(ЗБ?.діагноз.join(' / ') || 'збір не дійшов до картки');
    return [виклики[0], ЗБ.картки[0].речі[0].id];
  })()`, ['ядро:почати', 'd1']],
  'ядро.показ_палітри': [`(async () => {
    const виклики = [];
    містП = async (ім, д) => { виклики.push(ім + ':' + д.дія); return {кінець: true, палітра: {нічого: true}}; };
    const р = await стилісткаОбираєП();
    return [виклики[0], р.нічого];
  })()`, ['ядро:палітра', true]],
  'ядро.показ_ситуації': [`(async () => {
    const виклики = [];
    містП = async (ім, д) => { виклики.push([ім, д.дія, д.вхід.поле]); return {ситуація: {версія: 9}}; };
    await тапЯдромП('нагода', 'робота');
    return [виклики[0], ситуаціяЯдраП().версія];
  })()`, [['ядро', 'тап', 'подія'], 9]],
  'купівля.показ_пошуку': [`(async () => {
    містП = async (ім, д) => [ім, д.опис.slot, д.каталог];
    return знайтиРічП({slot:'dress'});
  })()`, ['пошук_речі', 'dress', 'каталог_brief.xml']],
  'оцінка_з_фото.показ_переліку': [`(async () => {
    містП = async (ім, д) => ({hex:{x:[ім, д.крок]}});
    ОЦ.етапи = {};
    await показатиПерелікП([{ід:'x'}]);
    return [ОЦ.перелік.речі[0].ід, ОЦ.перелік.hex.x];
  })()`, ['x', ['оцінка', 'перелік']]],
  'профіль_і_палітра.показ_кольору': [`(async () => {
    містП = async (ім, д) => [ім, д.відповідь_моделі];
    return читатиВідповідьКольоруП('фікстура');
  })()`, ['колір', 'фікстура']],
  'чат_із_фото.показ_розмови': [`(async () => {
    режим('сценарій'); показатиРозмову();
    return [typeof стилісткаП, typeof помічникП, typeof мовоюП];
  })()`, ['function', 'function', 'function']],
  'примірка.дія_картки': [`typeof приміряти === 'function' && typeof повернутиП === 'function'`, true],
  'каталог.полиця': [`typeof вхідМостаП === 'function' && вхідМостаП().каталог`, 'каталог_brief.xml'],
  'показ.початковий_стан': [`(async () => {
    for (let і = 0; і < 30 && !Екран.стан.запущено; і++) await new Promise(р => setTimeout(р, 10));
    return Екран.стан.запущено;
  })()`, true],
  'показ.відкрити_перегляд': [`(() => {
    const к = document.createElement('button');
    к.appendChild(document.createElement('img'));
    Екран.виконати('перегляд-відкрити', null, к);
    const відкрито = !document.getElementById('перегляд').hidden;
    Екран.виконати('перегляд-закрити');
    return відкрито && document.getElementById('перегляд').hidden;
  })()`, true],
  'показ.тема': [`(() => {
    const до = Екран.стан.тема; Екран.виконати('тема-перемкнути');
    return до !== Екран.стан.тема && localStorage.getItem('люстерко-тема') === Екран.стан.тема;
  })()`, true],
  'показ.дії_зібраної_картки': [`(() => {
    показатиПідписОбразів(); показатиБібліотеку(); показатиРядокШапки();
    const к = document.createElement('button');
    виглядКнопкиЗаміниП(к, true);
    return к.getAttribute('aria-pressed') === 'true';
  })()`, true],
  'показ.діагностика_моста': [`(() => {
    показатиПідйомМосту(); виставитиПанельЗбою();
    return задачаПромптаП({task:{answer_schema:{outfits:[]}}});
  })()`, 'OUTFITS_V1'],
  'показ.запис_профілю_й_журнал': [`(async () => {
    const б = await дб();
    await оновитиЖурнал();
    return Boolean(б?.name) && записЖінкиП({коментар:"Мій запис"}) && !записЖінкиП({рука_впала:true});
  })()`, true],
  'чат_із_фото.картка_інструмента': [`карткаІнструментаП({name:'Фікстура',tool:'save_scenario',done:true}).textContent.includes('Фікстура')`, true],
  'оцінка_з_фото.форма_оцінки': [`(() => {
    const в = Екран.стан.оцінка;
    показатиОцінку();
    return Екран.стан.оцінка === в + 1;
  })()`, true],
  'профіль_і_палітра.чип_драпу': [`(() => {
    const к = document.createElement('button'); чипДрапу(к, 'ясність', 'так');
    return к instanceof HTMLButtonElement;
  })()`, true],
  'профіль_і_палітра.повтор_опису_кольорів': [`(() => {
    показатиПалітру(); показатиЧитанняКольорів(); показатиПрофіль();
    const п = JSON.parse(промптПовторуП('{"task":{}}','{"missing":"eyes"}'));
    return п.format_error.missing;
  })()`, 'eyes'],
  'примірка.екран_картки': [`(() => {
    показатиПримірку(0); return Object.keys(Екран.стан.примірка).length;
  })()`, 1],
  'каталог.дзеркало': [`(() => [
    window.MirrorIndex.count > 0,
    typeof window.Rack.library,
    window.MirrorFiles['catalog.json.gz'].startsWith('data:application/gzip;base64,')
  ])()`, [true, 'function', true]],
};

function причина(е) {
  const вираз = String(е.message || е);
  const імʼя = вираз.match(/([\p{L}\p{N}_ʼ]+) is not defined/u)?.[1];
  return {помилка: е.name || 'Error', текст: вираз.replace(/\s+/g, ' ').slice(0, 450), імʼя: імʼя || null};
}

async function варіант(вилучено) {
  const помилки = [];
  return варіантКонтекст.run(помилки, async () => {
    const {w} = сторінка(new Set(вилучено), помилки);
    const тести = {};
    try {
      await трохи();
      for (const [назва, [код, чекаємо]] of Object.entries(ПРОБИ)) {
        if (помилки.length && назва === 'показ.відкриття') {
          тести[назва] = причина(помилки[0]);
          continue;
        }
        try {
          let таймер;
          const межа = new Promise((_, відмова) => {
            таймер = setTimeout(() => відмова(new Error('дія не завершилася за 2 секунди')), 2000);
          });
          const в = await Promise.race([Promise.resolve().then(() => w.eval(код)), межа])
            .finally(() => clearTimeout(таймер));
          assert.deepEqual(JSON.parse(JSON.stringify(в)), чекаємо);
          тести[назва] = {вихід: чекаємо};
        } catch (е) {
          тести[назва] = причина(е);
        }
      }
    } finally {
      w.close();
    }
    await new Promise((готово) => setTimeout(готово, 30));
    if (помилки.length) тести['показ.відкриття'] = причина(помилки[0]);
    return тести;
  });
}

(async () => {
  const варіанти = JSON.parse(fs.readFileSync(0, 'utf8'));
  for (const в of варіанти) console.log(JSON.stringify([в, await варіант(в)]));
})().catch((е) => { console.error(е); process.exitCode = 1; });
