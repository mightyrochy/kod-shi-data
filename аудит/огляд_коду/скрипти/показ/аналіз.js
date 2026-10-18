/* Аналіз виміру показу (наряд ОЦІНКА-ПОКАЗУ): покриття JS і CSS за всіма сценами, CPU-профіль (JS показу
   окремо від Python у Pyodide), журнал викликів (innerHTML, JSON.parse, atob, слухачі, таймери, сховища),
   метрики Performance. Запуск з кореня репозиторію:
     node аудит/огляд_коду/скрипти/показ/аналіз.js <index.html стенда> <вихід прогону> <статика.json> > аналіз.json
   Друкує зведення в stderr. */
const fs = require('fs'), path = require('path');
const [ІНДЕКС, ВИХІД, СТАТИКА] = process.argv.slice(2);
const html = fs.readFileSync(ІНДЕКС, 'utf8');
const стат = JSON.parse(fs.readFileSync(СТАТИКА, 'utf8'));
const пиши = (...а) => console.error(...а);

/* головний скрипт зібраної сторінки — найдовший inline <script> */
const скрипти = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(м => м[1]);
const ГОЛ = скрипти.reduce((а, б) => б.length > а.length ? б : а);
const сцени = fs.readdirSync(ВИХІД).filter(ім => fs.existsSync(path.join(ВИХІД, ім, 'стор1')));

/* ── покриття JS */
const функції = new Map();   // 'поч:кін' → {ім, поч, кін, к: {сцена: лічба}}
const блоки = new Map();
/* POKRYTTIA_Z=<тека прогону> — межі функцій для атрибуції профілю беруться звідти (чисті прогони без покриття) */
const джерелаПокриття = сцени.map(сц => [ВИХІД, сц]).concat(process.env.POKRYTTIA_Z ? fs.readdirSync(process.env.POKRYTTIA_Z).filter(ім => fs.existsSync(path.join(process.env.POKRYTTIA_Z, ім, 'стор1'))).map(сц => [process.env.POKRYTTIA_Z, сц]) : []);
for (const [кор, сц] of джерелаПокриття){
  for (const стор of fs.readdirSync(path.join(кор, сц)).filter(х => х.startsWith('стор'))){
    if (!fs.existsSync(path.join(кор, сц, стор, 'покриття.json'))) continue;
    const п = JSON.parse(fs.readFileSync(path.join(кор, сц, стор, 'покриття.json'), 'utf8'));
    for (const [ключ, пари] of Object.entries(п)){
      if (!ключ.endsWith('#' + ГОЛ.length)) continue;
      for (const [к, л] of пари){
        const [поч, кін, вид, ...ім] = к.split(':');
        const м = вид === 'f' ? функції : блоки, кк = поч + ':' + кін;
        let з = м.get(кк); if (!з){ з = {ім: ім.join(':'), поч: +поч, кін: +кін, к: {}}; м.set(кк, з); }
        з.к[сц] = (з.к[сц] || 0) + л;
      }
    }
  }
}
const сума = з => Object.values(з.к).reduce((а, б) => а + б, 0);
const фСп = [...функції.values()].filter(ф => ф.поч > 0 || ф.кін < ГОЛ.length).sort((а, б) => а.поч - б.поч);
/* верхні функції — не вкладені в жодну іншу */
const верхні = []; let межа = -1;
for (const ф of фСп){ if (ф.поч >= межа){ верхні.push(ф); межа = ф.кін; } }
/* рядки зібраного скрипта; рядки-вантажі (довгі літерали) — окремо */
const початки = [0]; for (let і = 0; і < ГОЛ.length; і++) if (ГОЛ.charCodeAt(і) === 10) початки.push(і + 1);
const рядокЗ = поз => { let л = 0, п = початки.length - 1; while (л < п){ const с = (л + п + 1) >> 1; if (початки[с] <= поз) л = с; else п = с - 1; } return л; };
/* лічба на позицію: найглибший діапазон (функція чи блок), що її містить */
const діап = [...функції.values(), ...блоки.values()].map(з => [з.поч, з.кін, сума(з)]).sort((а, б) => а[0] - б[0] || б[1] - а[1]);
const лічбаРядка = new Int32Array(початки.length).fill(-1);
(() => { /* обхід зі стеком: для першого непробільного символу кожного рядка */
  const перші = початки.map((п, і) => { const кін = і + 1 < початки.length ? початки[і + 1] : ГОЛ.length; let к = п; while (к < кін && /\s/.test(ГОЛ[к])) к++; return к < кін - 1 ? к : -1; });
  const стек = []; let д = 0;
  for (let р = 0; р < перші.length; р++){
    const поз = перші[р]; if (поз < 0) continue;
    while (д < діап.length && діап[д][0] <= поз){ while (стек.length && стек[стек.length - 1][1] <= діап[д][0]) стек.pop(); стек.push(діап[д]); д++; }
    while (стек.length && стек[стек.length - 1][1] <= поз) стек.pop();
    лічбаРядка[р] = стек.length ? стек[стек.length - 1][2] : 0;
  }
})();
const довжинаРядка = р => (р + 1 < початки.length ? початки[р + 1] : ГОЛ.length) - початки[р];
let ряд = 0, рядВик = 0, вантаж = 0, байтВантажу = 0;
for (let р = 0; р < початки.length; р++){
  if (лічбаРядка[р] < 0) continue;
  if (довжинаРядка(р) > 3000){ вантаж++; байтВантажу += довжинаРядка(р); continue; }
  ряд++; if (лічбаРядка[р] > 0) рядВик++;
}
/* по сценах: функції, що виконались лише в цій сцені */
const лишеТут = {}; for (const сц of сцени) лишеТут[сц] = 0;
const покрФ = {}; for (const сц of сцени) покрФ[сц] = 0;
for (const ф of фСп){ const сц = Object.keys(ф.к).filter(к => ф.к[к] > 0); for (const к of сц) покрФ[к]++; if (сц.length === 1) лишеТут[сц[0]]++; }

/* відповідність верхніх функцій зібраного скрипта реєстру статики (за іменем; повтори імені — за порядком) */
const реєстр = new Map(); for (const р of стат.реєстр) (реєстр.get(р.ім) || реєстр.set(р.ім, []).get(р.ім)).push(р);
const лічильник = new Map();
const верхніЗвіт = верхні.map(ф => {
  const н = (лічильник.get(ф.ім) || 0); лічильник.set(ф.ім, н + 1);
  const р = (реєстр.get(ф.ім) || [])[н];
  /* невиконані блоки всередині (рядки зібраного скрипта) */
  let рядів = 0, невик = 0;
  for (let р2 = рядокЗ(ф.поч); р2 <= рядокЗ(ф.кін); р2++){ if (лічбаРядка[р2] < 0 || довжинаРядка(р2) > 3000) continue; рядів++; if (лічбаРядка[р2] === 0) невик++; }
  return {ім: ф.ім, з: р ? р.з : null, по: р ? р.по : null, рядків_джерела: р ? р.рядків : null, викликів: сума(ф),
    сцен: Object.values(ф.к).filter(л => л > 0).length, рядів, невик, досяжна_статично: р ? р.досяжна : null, стенд: р ? р.стенд : null};
});
const невиконані = верхніЗвіт.filter(ф => ф.викликів === 0);
const частково = верхніЗвіт.filter(ф => ф.викликів > 0 && ф.невик > 0).sort((а, б) => б.невик - а.невик);
const рядДж = невиконані.reduce((а, ф) => а + (ф.рядків_джерела || 0), 0);
const рядДжУсі = верхніЗвіт.reduce((а, ф) => а + (ф.рядків_джерела || 0), 0);
/* вкладені функції (колбеки) */
const вкладені = фСп.filter(ф => !верхні.includes(ф));
const вклНевик = вкладені.filter(ф => сума(ф) === 0).length;

/* ── CSS: CDP віддає лише вжиті правила (зсув селектора — кінець блоку), тож правила листа перелічуються тут
   дужками (з @media/@supports усередину; @keyframes і @font-face — не правила селекторів) */
const вжитіCSS = new Set(); let текстCSS = null;
for (const сц of сцени){
  for (const стор of fs.readdirSync(path.join(ВИХІД, сц)).filter(х => х.startsWith('стор'))){
    const ф = path.join(ВИХІД, сц, стор, 'css.json'); if (!fs.existsSync(ф)) continue;
    const {листи, правила} = JSON.parse(fs.readFileSync(ф, 'utf8'));
    const гол = Object.entries(листи).filter(([, л]) => л.текст).sort((а, б) => б[1].текст.length - а[1].текст.length)[0];
    if (!гол) continue; текстCSS = гол[1].текст;
    for (const [к, вжите] of правила){ const [ід, п] = к.split(':'); if (ід === гол[0] && вжите) вжитіCSS.add(+п); }
  }
}
function правилаЛиста(т){
  const р = []; let і = 0;
  const блок = (кін) => {
    while (і < кін){
      while (і < кін && /\s/.test(т[і])) і++;
      if (т.startsWith('/*', і)){ і = т.indexOf('*/', і) + 2; continue; }
      if (і >= кін || т[і] === '}') return і++;
      const поч = і; const д = т.indexOf('{', і); if (д < 0) return (і = кін);
      const сел = т.slice(поч, д).trim();
      let г = 1, к = д + 1; while (к < т.length && г){ if (т[к] === '{') г++; else if (т[к] === '}') г--; к++; }
      if (/^@(media|supports|layer|container)/.test(сел)){ і = д + 1; блок(к - 1); і = к; continue; }
      if (!/^@/.test(сел)) р.push([поч, к, сел.replace(/\s+/g, ' ')]);
      і = к;
    }
  };
  блок(т.length); return р;
}
const правилаCSS = текстCSS ? правилаЛиста(текстCSS) : [];
const невжитіCSS = правилаCSS.filter(([п]) => !вжитіCSS.has(п));
const байтНевжитих = невжитіCSS.reduce((а, [п, к]) => а + (к - п), 0);
/* статично: класи й id селектора, яких нема ніде поза <style> (розмітка й JS зібраної сторінки) */
const безСтилів = html.replace(/<style[\s\S]*?<\/style>/g, '');
const імена = new Set((безСтилів.match(/[\w\u0400-\u04FF-]+/g) || []));
const безЧитача = невжитіCSS.filter(([, , с]) => { const т = [...с.replace(/\[[^\]]*\]|:not\(|::?[\w-]+(\([^)]*\))?/g, ' ').matchAll(/[.#]([\w\u0400-\u04FF-]+)/g)].map(м => м[1]); return т.length && т.some(х => !імена.has(х)); });
const селектор = ([, , с]) => с.slice(0, 90);

/* кадр профілю → верхня функція головного скрипта за зсувом (рядок і стовпець кадру — у координатах документа);
   асинхронні продовження й анонімні колбеки так лягають на свою верхню функцію */
const початкиHTML = [0]; for (let і = 0; і < html.length; і++) if (html.charCodeAt(і) === 10) початкиHTML.push(і + 1);
const початокГОЛ = html.indexOf(ГОЛ);
function верхняЗа(cf){
  const поз = початкиHTML[cf.lineNumber] + cf.columnNumber - початокГОЛ;
  if (поз < 0 || поз > ГОЛ.length) return '(інший скрипт)';
  let л = 0, п = верхні.length - 1, з = null;
  while (л <= п){ const с = (л + п) >> 1; if (верхні[с].поч <= поз){ з = верхні[с]; л = с + 1; } else п = с - 1; }
  return з && поз < з.кін ? (з.ім || '(анонімна)') : '(верхній рівень)';
}
/* ── профіль: самочас за категоріями, по вікнах «старт» і «збір» (сцена «база») */
function профіль(сц){
  const ф = path.join(ВИХІД, сц, 'стор1', 'профіль.cpuprofile'); if (!fs.existsSync(ф)) return null;
  const пр = JSON.parse(fs.readFileSync(ф, 'utf8'));
  const вузли = new Map(пр.nodes.map(н => [н.id, н])); const батько = new Map();
  for (const н of пр.nodes) for (const д of (н.children || [])) батько.set(д, н.id);
  const кат = н => { const {url, functionName: ім} = н.callFrame;
    if (ім === '(idle)') return 'простій'; if (ім === '(garbage collector)') return 'збирач сміття'; if (ім === '(program)') return 'браузер (рушій, розкладка)';
    if (/pyodide\.asm\.(js|wasm)|^wasm:/.test(url) || (!url && /^\$|wasm-function|^wasm-to-js|^js-to-wasm/.test(ім))) return 'Python (Pyodide)';
    if (/pyodide\.js/.test(url)) return 'завантажувач Pyodide';
    if (/index\.html|127\.0\.0\.1/.test(url)) return 'JS показу';
    return url ? 'інше JS' : 'вбудовані (native)'; };
  /* стек імен на вузол (для вікон): чи є в предках ім'я */
  const маєПредка = (ід, імена) => { for (let в = ід; в != null; в = батько.get(в)){ if (імена.has(вузли.get(в).callFrame.functionName)) return true; } return false; };
  const т = []; let час = пр.startTime; for (const д of пр.timeDeltas){ час += д; т.push(час); }
  const вікно = імена => { let п = Infinity, к = -Infinity; пр.samples.forEach((ід, і) => { if (маєПредка(ід, імена)){ п = Math.min(п, т[і]); к = Math.max(к, т[і]); } }); return [п, к]; };
  const збір = вікно(new Set(['зібратиОбразиП']));
  const підсумок = (п, к) => { const с = {}; const ф = {}; for (let і = 0; і < пр.samples.length; і++){ if (т[і] < п || т[і] > к) continue;
      const дт = (т[і + 1] || т[і]) - т[і]; const н = вузли.get(пр.samples[і]); const кк = кат(н); с[кк] = (с[кк] || 0) + дт;
      /* самочас JS показу: на найближчу іменовану функцію показу в стеку (внутрішні вбудовані — на неї ж) */
      if (кк === 'JS показу' || кк === 'вбудовані (native)' || кк === 'збирач сміття'){ for (let в = пр.samples[і]; в != null; в = батько.get(в)){ const cf = вузли.get(в).callFrame; if (/index\.html|127\.0\.0\.1/.test(cf.url)){ const ім = верхняЗа(cf); ф[ім] = (ф[ім] || 0) + дт; break; } } } }
    const мс = Object.fromEntries(Object.entries(с).map(([к, в]) => [к, Math.round(в / 1000)]).sort((а, б) => б[1] - а[1]));
    return {мс_вікна: Math.round((к - п) / 1000), мс, топ_JS: Object.entries(ф).sort((а, б) => б[1] - а[1]).slice(0, 15).map(([к, в]) => [к, Math.round(в / 1000)])}; };
  return {усе: підсумок(пр.startTime, пр.endTime), до_збору: підсумок(пр.startTime, isFinite(збір[0]) ? збір[0] : пр.endTime),
    збір: isFinite(збір[0]) ? підсумок(...збір) : null, після_збору: isFinite(збір[1]) ? підсумок(збір[1], пр.endTime) : null};
}
const профілі = {}; for (const сц of сцени) профілі[сц] = профіль(сц);

/* ── журнал */
function журнал(сц){
  const ж = []; for (const стор of fs.readdirSync(path.join(ВИХІД, сц)).filter(х => х.startsWith('стор'))){ const ф = path.join(ВИХІД, сц, стор, 'журнал.json'); if (fs.existsSync(ф)) ж.push(...JSON.parse(fs.readFileSync(ф, 'utf8'))); }
  const гр = (в, ключ) => { const м = {}; for (const з of ж.filter(з => з[1] === в)){ const к = ключ(з); м[к] = (м[к] || 0) + 1; } return Object.entries(м).sort((а, б) => б[1] - а[1]); };
  const свої = new Set(стат.реєстр.map(р => р.ім));
  const парси = ж.filter(з => з[1] === 'JSON.parse' && свої.has(з[2]));
  const пі = ж.filter(з => з[1] === 'py' && з[3].length === 5);
  const поЕнд = {}; for (const з of пі){ const [е, код, вих, п, к] = з[3]; const р = поЕнд[е] || (поЕнд[е] = {разів: 0, мс: 0, код: 0, вих: 0, макс_мс: 0}); р.разів++; р.мс += к - п; р.код += код; р.вих += Math.max(0, вих); р.макс_мс = Math.max(р.макс_мс, к - п); }
  const підйом = {load: ж.filter(з => з[1] === 'pyodide.load').map(з => з[3]), unpack: ж.filter(з => з[1] === 'py.unpack').map(з => з[3]), import_bridge: пі.filter(з => /^import sys/.test(з[3][0])).map(з => [з[3][3], з[3][4]])};
  const мутації = ж.filter(з => з[1] === 'mut').reduce((а, з) => [а[0] + з[3][0], а[1] + з[3][1], а[2] + з[3][2]], [0, 0, 0]);
  const innerHTML = ж.filter(з => з[1] === 'innerHTML');
  return {подій: ж.length, python: Object.fromEntries(Object.entries(поЕнд).sort((а, б) => б[1].мс - а[1].мс)), python_мс: пі.reduce((а, з) => а + з[3][4] - з[3][3], 0), python_викликів: пі.length, підйом,
    python_інтервали: пі.map(з => [з[3][0], з[3][3], з[3][4]]),
    JSON_великі: {разів: парси.length, символів: парси.reduce((а, з) => а + з[3][0], 0), мс: Math.round(парси.reduce((а, з) => а + з[3][1], 0)),
      від_1МБ: парси.filter(з => з[3][0] >= 1e6).map(з => [з[2], з[3][0], з[3][1]]), хто: гр('JSON.parse', з => з[2]).slice(0, 10)},
    atob: ж.filter(з => з[1] === 'atob').map(з => [з[2], з[3][0], з[3][1]]),
    innerHTML: {разів: innerHTML.length, символів: innerHTML.reduce((а, з) => а + з[3][1], 0), хто: гр('innerHTML', з => з[2]).slice(0, 12), куди: гр('innerHTML', з => з[3][0]).slice(0, 12)},
    мутацій: {записів: мутації[0], додано: мутації[1], знято: мутації[2]},
    слухачі: {додано: ж.filter(з => з[1] === 'add').length, знято: ж.filter(з => з[1] === 'rem').length, хто: гр('add', з => з[2] + ' → ' + з[3][1] + '.' + з[3][0]).slice(0, 15)},
    таймери: {setTimeout: ж.filter(з => з[1] === 'setTimeout').length, clearTimeout: ж.filter(з => з[1] === 'clearTimeout').length, setInterval: гр('setInterval', з => з[2] + '/' + з[3]), хто: гр('setTimeout', з => з[2]).slice(0, 12)},
    сховище: гр('сховище', з => з[3][0] + з[3][1] + ' ' + з[3][2]).slice(0, 30),
    idb: гр('idb.open', з => з[3]), fetch: гр('fetch', з => з[3].replace(/\?.*/, '')).slice(0, 8)};
}
const журнали = {}; for (const сц of сцени) журнали[сц] = журнал(сц);
/* ── метрики: перша й остання точка */
const метрики = {}; for (const сц of сцени){ const ф = path.join(ВИХІД, сц, 'стор1', 'метрики.json'); if (!fs.existsSync(ф)) continue; const м = JSON.parse(fs.readFileSync(ф, 'utf8')); if (!м.length) continue;
  const к = ['Nodes', 'JSEventListeners', 'LayoutCount', 'RecalcStyleCount', 'JSHeapUsedSize', 'ScriptDuration', 'LayoutDuration', 'RecalcStyleDuration', 'TaskDuration', 'Documents'];
  const ост = м[м.length - 1][1]; const макс = {}; for (const ім of к) макс[ім] = Math.max(...м.map(т => т[1][ім] || 0));
  метрики[сц] = {точок: м.length, с: Math.round(м[м.length - 1][0] / 1000), останнє: Object.fromEntries(к.map(ім => [ім, Math.round(ост[ім] * (/Duration/.test(ім) ? 1000 : 1))])), макс: Object.fromEntries(к.map(ім => [ім, Math.round(макс[ім] * (/Duration/.test(ім) ? 1000 : 1))])),
    слухачі_по_часу: м.filter((_, і) => і % Math.max(1, Math.floor(м.length / 12)) === 0).map(т => [Math.round(т[0] / 1000), т[1].JSEventListeners, т[1].Nodes])}; }

const рез = {сцени, довжина_скрипта: ГОЛ.length,
  JS: {функцій: фСп.length, верхніх: верхні.length, верхніх_невиконаних: невиконані.length, рядків_джерела_невиконаних: рядДж, рядків_джерела_верхніх: рядДжУсі,
    вкладених: вкладені.length, вкладених_невиконаних: вклНевик, рядків_зібраного: ряд, рядків_виконаних: рядВик, рядків_вантажу: вантаж, байт_вантажу: байтВантажу,
    по_сценах: покрФ, лише_в_сцені: лишеТут},
  невиконані: невиконані.sort((а, б) => (б.рядків_джерела || 0) - (а.рядків_джерела || 0)), частково: частково.slice(0, 40),
  CSS: {правил: правилаCSS.length, невжитих: невжитіCSS.length, байт_листа: текстCSS ? текстCSS.length : 0, байт_невжитих: байтНевжитих, без_читача: безЧитача.length, байт_без_читача: безЧитача.reduce((а, [п, к]) => а + (к - п), 0), без_читача_приклади: безЧитача.map(селектор), приклади: невжитіCSS.slice(0, 400).map(селектор)},
  профілі, журнали, метрики};
process.stdout.write(JSON.stringify(рез, null, 1));
пиши('сцен', сцени.length, '·', сцени.join(' '));
пиши('JS: функцій', фСп.length, '· верхніх', верхні.length, '· невиконаних верхніх', невиконані.length, '(' + рядДж + ' з ' + рядДжУсі + ' рядків джерела)', '· вкладених невиконаних', вклНевик, 'з', вкладені.length);
пиши('рядки зібраного коду: виконано', рядВик, 'з', ряд, '=', (100 * рядВик / ряд).toFixed(1) + '%', '· рядків-вантажу', вантаж, байтВантажу, 'Б');
пиши('CSS: правил', правилаCSS.length, '· невжитих у жодній сцені', невжитіCSS.length, '(' + байтНевжитих + ' Б з', текстCSS && текстCSS.length, ') · з них без читача в розмітці й JS', безЧитача.length);
пиши('лише в сцені:', JSON.stringify(лишеТут));
