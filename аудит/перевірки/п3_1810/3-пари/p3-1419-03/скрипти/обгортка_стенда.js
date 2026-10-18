/* Обгортка стенда для виміру показу (наряд ОЦІНКА-ПОКАЗУ). Стенд не міняється: обгортка підміняє
   `chromium.launch` у спільному кеші `require`, і кожна сторінка стенда пише в <вихід>:
   покриття JS (V8 precise, з гілками), покриття правил CSS, CPU-профіль, метрики Performance щосекунди
   і журнал викликів (innerHTML, JSON.parse, atob, слухачі, таймери, сховища) з іменем функції-викликача.
   Запуск: node обгортка_стенда.js <вихід> <аргументи рв6_стенд.js…>; змінні сцени — як для стенда. */
const pw = require('playwright');
const fs = require('fs'), path = require('path');
const ВИХІД = path.resolve(process.argv[2]); process.argv.splice(2, 1);
fs.mkdirSync(ВИХІД, {recursive: true});
const СТЕНД = path.resolve('аудит/проби/рв6_стенд.js');

/* Журнал у сторінці: оригінали беруться до підміни, власні таймери обгортки не лічаться. */
const ІНІТ = `(() => {
  const w = window, ориг = {sT: setTimeout.bind(w), sI: setInterval.bind(w), cT: clearTimeout.bind(w), cI: clearInterval.bind(w), parse: JSON.parse, atob: window.atob.bind(w), fetch: window.fetch.bind(w),
    add: EventTarget.prototype.addEventListener, rem: EventTarget.prototype.removeEventListener, now: performance.now.bind(performance)};
  const ж = []; let п = 0;
  const хто = () => { const р = (new Error().stack || '').split('\\n');
    for (let і = 3; і < р.length; і++){ const м = /at (?:async )?([^ (]+)/.exec(р[і]); if (м && !/^(Object\\.|Array\\.|EventTarget|JSON|Storage|Function|Reflect|eval)/.test(м[1])) return м[1]; if (м) continue; }
    return '?'; };
  const з = (в, д) => { ж.push([Math.round(ориг.now()), в, хто(), д]); };
  window.setTimeout = function(ф, мс, ...а){ з('setTimeout', мс | 0); return ориг.sT(ф, мс, ...а); };
  window.setInterval = function(ф, мс, ...а){ з('setInterval', мс | 0); return ориг.sI(ф, мс, ...а); };
  window.clearTimeout = function(і){ з('clearTimeout', 0); return ориг.cT(і); };
  window.clearInterval = function(і){ з('clearInterval', 0); return ориг.cI(і); };
  JSON.parse = function(т, ...а){ const т0 = ориг.now(); const р = ориг.parse.call(this, т, ...а);
    const д = typeof т === 'string' ? т.length : -1; if (д >= 10000) з('JSON.parse', [д, +(ориг.now() - т0).toFixed(2)]); return р; };
  window.atob = function(т){ const т0 = ориг.now(); const р = ориг.atob(т); if (т && т.length >= 10000) з('atob', [т.length, +(ориг.now() - т0).toFixed(2)]); return р; };
  EventTarget.prototype.addEventListener = function(т, ф, о){ з('add', [т, (this && (this.id || this.nodeName || (this === window ? 'window' : '?'))) || '?']); return ориг.add.call(this, т, ф, о); };
  EventTarget.prototype.removeEventListener = function(т, ф, о){ з('rem', [т, (this && (this.id || this.nodeName || (this === window ? 'window' : '?'))) || '?']); return ориг.rem.call(this, т, ф, о); };
  for (const [ім, вл] of [['innerHTML', Element.prototype], ['outerHTML', Element.prototype]]){
    const о = Object.getOwnPropertyDescriptor(вл, ім);
    Object.defineProperty(вл, ім, {configurable: true, get: о.get, set(в){ з(ім, [this.id || this.className || this.nodeName, (в || '').length]); return о.set.call(this, в); }});
  }
  const оТ = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
  for (const [ім, вл] of [['getItem', 'r'], ['setItem', 'w'], ['removeItem', 'd']]){
    const о = Storage.prototype[ім];
    Storage.prototype[ім] = function(к, в){ з('сховище', [вл, this === window.sessionStorage ? 's' : 'l', к, в == null ? 0 : String(в).length]); return о.apply(this, arguments); };
  }
  if (window.indexedDB){ const о = IDBFactory.prototype.open; IDBFactory.prototype.open = function(ім){ з('idb.open', ім); return о.apply(this, arguments); }; }
  window.fetch = function(у, о){ з('fetch', String(у && у.url || у).slice(0, 120)); return ориг.fetch(у, о); };
  /* Pyodide: підйом (loadPyodide, unpackArchive) і кожен runPythonAsync — ендпойнт мосту, довжина коду (дані
     вшиті в код рядком), довжина виходу, мс; [поч, кін] — щоб відрізнити час Python від часу JS у вікні збору */
  let lp;
  /* pyodide.js спершу кладе в loadPyodide об'єкт модуля (var), далі — функцію: обгортається лише функція */
  Object.defineProperty(window, 'loadPyodide', {configurable: true, get(){ return lp; }, set(ф){
    if (typeof ф !== 'function'){ lp = ф; return; }
    lp = async function(...а){
      const т0 = ориг.now(); const пд = await ф.apply(this, а); з('pyodide.load', [Math.round(т0), Math.round(ориг.now())]);
      const оR = пд.runPythonAsync.bind(пд), оU = пд.unpackArchive.bind(пд);
      пд.runPythonAsync = async (код, ...р) => { const т = ориг.now(); let в;
        try { в = await оR(код, ...р); return в; }
        finally { const м = /bridge\\.виклик(?:_а)?\\("([^"]*)"/.exec(код); з('py', [м ? м[1] : код.slice(0, 24), код.length, typeof в === 'string' ? в.length : -1, Math.round(т), Math.round(ориг.now())]); } };
      пд.unpackArchive = (...р) => { const т = ориг.now(); const в = оU(...р); з('py.unpack', [Math.round(т), Math.round(ориг.now())]); return в; };
      return пд; }; }});
  const мо = new MutationObserver(сп => { let д = 0, в = 0; for (const м of сп){ д += м.addedNodes.length; в += м.removedNodes.length; } п += сп.length; ж.push([Math.round(ориг.now()), 'mut', '', [сп.length, д, в]]); });
  const старт = () => мо.observe(document.documentElement, {childList: true, subtree: true});
  if (document.documentElement) старт(); else document.addEventListener('DOMContentLoaded', старт);
  ориг.sI(() => { if (ж.length && window.__вимЗвіт) window.__вимЗвіт(ж.splice(0)); }, 1000);
  ориг.add.call(window, 'pagehide', () => { if (ж.length && window.__вимЗвіт) window.__вимЗвіт(ж.splice(0)); });
})();`;

let номер = 0;
const ориг = pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch = async (о) => {
  const б = await ориг(о);
  const стори = [];
  const оNC = б.newContext.bind(б);
  б.newContext = async (...а) => {
    const к = await оNC(...а);
    const оNP = к.newPage.bind(к);
    к.newPage = async (...а2) => { const с = await оNP(...а2); await почати(к, с, стори); return с; };
    return к;
  };
  const оЗ = б.close.bind(б);
  б.close = async () => { for (const х of стори) await зібрати(х).catch(е => console.error('вимір: збір не вдався', е.message)); return оЗ(); };
  return б;
};

async function почати(к, с, стори){
  const х = {н: ++номер, с, журнал: [], метрики: [], покриття: new Map(), css: new Map(), т0: Date.now()};
  стори.push(х);
  /* BEZ_ZHURNALU=1 — без перехоплювачів у сторінці: чистий профіль часу (перехоплювачі додають stack на кожен виклик) */
  if (process.env.BEZ_ZHURNALU !== '1'){
    await с.exposeFunction('__вимЗвіт', (п) => { for (const з of п) х.журнал.push(з); });
    await с.addInitScript(ІНІТ);
  }
  const cdp = х.cdp = await к.newCDPSession(с);
  /* BEZ_ZHURNALU=1 — чистий час: лише CPU-профіль і метрики; BEZ_POKRYTTIA=1 — те саме плюс журнал викликів.
     Debugger, точне покриття й облік CSS уповільнюють сторінку (з Debugger Pyodide-wasm іде без оптимізації:
     сцена «база» 111 → 215 с), тож час міряють без них */
  х.чисто = process.env.BEZ_ZHURNALU === '1' || process.env.BEZ_POKRYTTIA === '1';
  /* скрипт упізнається за scriptParsed (url і довжина): перша функція знімка — не завжди верхня функція скрипта */
  х.скрипти = new Map();
  await cdp.send('Profiler.enable');
  if (!х.чисто){
    cdp.on('Debugger.scriptParsed', (п) => { if (п.url) х.скрипти.set(п.scriptId, п.url.replace(/[?#].*/, '') + '#' + п.length); });
    await cdp.send('Debugger.enable');
    await cdp.send('Profiler.startPreciseCoverage', {callCount: true, detailed: true});
  }
  await cdp.send('Profiler.setSamplingInterval', {interval: 1000});
  await cdp.send('Profiler.start');
  await cdp.send('Performance.enable', {timeDomain: 'timeTicks'});
  х.листи = new Map();
  if (!х.чисто){
    await cdp.send('DOM.enable'); await cdp.send('CSS.enable');
    cdp.on('CSS.styleSheetAdded', (п) => х.листи.set(п.header.styleSheetId, п.header));
    await cdp.send('CSS.startRuleUsageTracking');
  }
  await cdp.send('Page.enable');
  cdp.on('Page.frameStartedLoading', () => { знятиПокриття(х).catch(() => {}); });
  х.таймер = setInterval(async () => {
    try { const м = await cdp.send('Performance.getMetrics'); х.метрики.push([Date.now() - х.т0, Object.fromEntries(м.metrics.map(з => [з.name, з.value]))]); } catch (е) {}
    знятиПокриття(х).catch(() => {});
  }, 2000);
}

/* Лічильники V8 скидаються на кожному знятті, тож знімки підсумовуються: ключ скрипта — url і довжина. */
async function знятиПокриття(х){
  if (х.знімає || х.чисто) return; х.знімає = true;
  try {
    const {result} = await х.cdp.send('Profiler.takePreciseCoverage');
    for (const ск of result){
      const ключ = х.скрипти.get(ск.scriptId);
      if (!ск.functions.length || !ключ || !/index\.html|127\.0\.0\.1/.test(ключ)) continue;
      let м = х.покриття.get(ключ); if (!м){ м = new Map(); х.покриття.set(ключ, м); }
      for (const ф of ск.functions) for (const р of ф.ranges){
        const к = р.startOffset + ':' + р.endOffset + ':' + (р === ф.ranges[0] ? 'f' : 'b') + ':' + ф.functionName;
        м.set(к, (м.get(к) || 0) + р.count);
      }
    }
    const {coverage} = await х.cdp.send('CSS.takeCoverageDelta');
    for (const п of coverage){ const к = п.styleSheetId + ':' + п.startOffset + ':' + п.endOffset; х.css.set(к, (х.css.get(к) || false) || п.used); }
  } finally { х.знімає = false; }
}

async function зібрати(х){
  clearInterval(х.таймер);
  try { await х.с.evaluate(() => window.dispatchEvent(new Event('pagehide'))); } catch (е) {}
  await new Promise(р => setTimeout(р, 300));
  await знятиПокриття(х);
  const {profile} = await х.cdp.send('Profiler.stop');
  const {ruleUsage} = х.чисто ? {ruleUsage: []} : await х.cdp.send('CSS.stopRuleUsageTracking');
  for (const п of ruleUsage){ const к = п.styleSheetId + ':' + п.startOffset + ':' + п.endOffset; х.css.set(к, (х.css.get(к) || false) || п.used); }
  const листи = {};
  for (const [ід, г] of х.листи){ try { листи[ід] = {...г, текст: (await х.cdp.send('CSS.getStyleSheetText', {styleSheetId: ід})).text}; } catch (е) { листи[ід] = г; } }
  const п = path.join(ВИХІД, 'стор' + х.н);
  fs.mkdirSync(п, {recursive: true});
  fs.writeFileSync(path.join(п, 'покриття.json'), JSON.stringify(Object.fromEntries([...х.покриття].map(([к, м]) => [к, [...м]]))));
  fs.writeFileSync(path.join(п, 'css.json'), JSON.stringify({листи, правила: [...х.css]}));
  fs.writeFileSync(path.join(п, 'профіль.cpuprofile'), JSON.stringify(profile));
  fs.writeFileSync(path.join(п, 'метрики.json'), JSON.stringify(х.метрики));
  fs.writeFileSync(path.join(п, 'журнал.json'), JSON.stringify(х.журнал));
  console.error('вимір: сторінка ' + х.н + ' → ' + п + ' · подій журналу ' + х.журнал.length);
  if (process.env.OCHI === '1' && х.н === 1){
    fs.writeFileSync(path.join(п,'сирий-журнал.json'), JSON.stringify(await х.с.evaluate(() => усіВердикти())));
    await х.с.setViewportSize({width:390,height:844});
    const картка = await х.с.evaluate(() => { if (!(П && П.картки && П.картки.length)) return false; режим('образи'); return true; });
    await х.с.waitForTimeout(600);
    await х.с.screenshot({path:path.join(п,'очі-390x844.png')});
    const журнал = await х.с.evaluate(async () => {
      режим('бібліотека'); await оновитиЖурнал();
      document.getElementById('журнал').open = true;
      document.getElementById('журнал').scrollIntoView({block:'start'});
      return document.getElementById('ж-ліч').textContent;
    });
    await х.с.waitForTimeout(600);
    await х.с.screenshot({path:path.join(п,'журнал-390x844.png')});
    console.error('очі після закінчення профілю: картки=' + картка + ', журнал=' + журнал);
  }

}

/* Вихід стенда через process.exit без close — збір не встигне; помітка, щоб сцену не рахували мовчки. */
process.on('exit', (к) => { if (!fs.existsSync(path.join(ВИХІД, 'стор1'))) fs.writeFileSync(path.join(ВИХІД, 'НЕ_ЗІБРАНО'), 'код ' + к); });
require(СТЕНД);
