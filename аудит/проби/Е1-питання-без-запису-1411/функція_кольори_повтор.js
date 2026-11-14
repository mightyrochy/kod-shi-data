/* Е1-питання-без-запису-1411: ж1_кольори_повтор_профілі і ж7_прогулянка_субота (#2814) — функція в Chromium на
   зібраній сторінці index.html. Відповідь моделі й збій мосту керовані (модельП, містП); решта — код сторінки.
   Запуск: node функція_кольори_повтор.js <шлях до index.html> */
const { chromium } = require('playwright');
const шлях = require('path').resolve(process.argv[2]);
const ГОТОВО = {стан: 'готово', шкіра: ['#f2d6c4'], волосся: ['#4a4644'], очі: '#6b8cae', зони: {}};
const ВІДП = '{"photo":"usable","skin":["#f2d6c4"],"hair":["#4a4644"],"eyes":"#6b8cae"}';
let рядки = [];
const ф = (н, у, що) => { рядки.push((у ? '✓ ' : '✗ ') + н + (у ? '' : '  → ' + JSON.stringify(що))); return у; };
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({viewport: {width: 390, height: 844}})).newPage();
  const помилки = []; p.on('pageerror', e => помилки.push(String(e)));
  await p.goto('file://' + шлях + '#міст=http://localhost:8787&т=tok-a1');
  await p.waitForFunction(() => document.getElementById('сцн-новий') && typeof document.getElementById('сцн-новий').onclick === 'function', null, {timeout: 60000});
  await p.evaluate(async () => {
    await писатиКв(ключФото('портрет'), 'портрет-заглушка');
    блобВБазу = async () => ({тип: 'image/jpeg', дані: 'AAAA', ширина: 1568, висота: 1176, якість: 0.85});
  });
  const мостЦілий = ГОТОВО => p.evaluate(г => { містП = async (ім, вх) => (вх.відповідь_моделі === null ? {готово: true} : г); }, ГОТОВО);
  const мостЗлам = () => p.evaluate(() => { містП = async () => { throw new Error('збій мосту'); }; });
  const мод = () => p.evaluate(async в => { await писатиКв(ключФото('портрет'), 'портрет-заглушка'); window._викл = 0; модельРукиП = async () => { window._викл++; return в; }; }, ВІДП);
  const стан = () => p.evaluate(() => ({повтор_прихов: document.getElementById('кол-повтор').hidden, повтор_disabled: document.getElementById('кол-повтор').disabled,
    шкіра: КОЛІР.шкіра, стан: document.getElementById('кол-стан').textContent, викл: window._викл}));
  const клік = id => p.evaluate(i => document.getElementById(i).click(), id);
  const чекати = (умова, арг) => p.waitForFunction(умова, арг, {timeout: 15000}).catch(() => {});

  /* 1. збій мосту після відповіді моделі → кнопка повтору є; міст відновлено → повтор застосовує кольори А без нового виклику моделі */
  await мод(); await мостЗлам();
  await клік('кол-зчитати'); await чекати(() => !document.getElementById('кол-зчитати').disabled && !document.getElementById('кол-повтор').hidden);
  let с = await стан();
  ф('збій мосту: «Повторити читання кольорів» доступна, кольори не застосовані', !с.повтор_прихов && !с.повтор_disabled && !с.шкіра, с);
  await мостЦілий(ГОТОВО); const до = с.викл;
  await клік('кол-повтор'); await чекати(() => document.getElementById('кол-повтор').hidden);
  с = await стан();
  ф('повтор після збою застосовує кольори А без нового виклику моделі', с.шкіра === '#f2d6c4' && с.повтор_прихов && с.викл === до, с);

  /* 2. збій А → профіль Б: повтор недоступний, відповідь А Б не застосовується */
  await p.evaluate(() => { КОЛІР = {шкіра:null,волосся:null,очі:null,кільце:null,точки:null}; });
  await мостЗлам(); await клік('кол-зчитати'); await чекати(() => !document.getElementById('кол-повтор').hidden);
  const доступнийА = (await стан()).повтор_прихов === false;
  const А = await p.evaluate(() => АКТИВНИЙ);
  await p.evaluate(async () => { await створитиПрофіль(); });
  await мостЦілий(ГОТОВО);
  await p.evaluate(() => { const к = document.getElementById('кол-повтор'); return к.onclick && к.onclick({currentTarget: к}); });
  с = await стан();
  ф('збій А → профіль Б: у Б повтор прихований, кольори А не застосовані', доступнийА && с.повтор_прихов && !с.шкіра, [доступнийА, с]);
  await p.evaluate(a => перемкнути(a), А);

  /* 3. повтор у польоті → новий збій читання → кнопка повтору знову доступна, старі кольори не застосовані */
  await p.evaluate(() => { КОЛІР = {шкіра:null,волосся:null,очі:null,кільце:null,точки:null}; });
  await мод(); await мостЗлам(); await клік('кол-зчитати'); await чекати(() => !document.getElementById('кол-повтор').hidden);
  await p.evaluate(() => { window._кінець = null; містП = () => new Promise(р => { window._кінець = р; }); });
  const повтор = p.evaluate(() => { const к = document.getElementById('кол-повтор'); return к.onclick({currentTarget: к}); });
  await p.waitForFunction(() => window._кінець, null, {timeout: 15000});
  await p.evaluate(async () => { містП = async () => { throw new Error('новий збій'); }; await зчитатиКольориЗПортрета(); });
  await p.evaluate(() => window._кінець({стан: 'готово', шкіра: ['#111111'], волосся: ['#222222'], очі: '#333333', зони: {}}));
  await повтор;
  с = await стан();
  ф('новий запуск під час повтору: кнопка повтору знову доступна (не disabled), старі кольори не застосовані', !с.повтор_прихов && !с.повтор_disabled && с.шкіра !== '#111111', с);
  await мостЦілий(ГОТОВО);
  await клік('кол-повтор'); await чекати(() => document.getElementById('кол-повтор').hidden);
  с = await стан();
  ф('після нового збою повтор працює', с.шкіра === '#f2d6c4' && !с.повтор_disabled, с);

  ф('винятків сторінки нема', помилки.length === 0, помилки);
  console.log(рядки.join('\n'));
  await b.close();
  process.exit(рядки.some(р => р.startsWith('✗')) ? 1 : 0);
})();
