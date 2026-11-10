/* Другий писач назви ЇЇ речі — переклад картки в показі (`показ/мовний_шар.js`, `мовоюКарткуП`), за класом кореня
 * Річ-запис-речі (п.4 її речі): поле її картки взято з ширшого тексту, ніж сама річ.
 *
 * Скрипти показу (порядок — `показ.html`) іде в Node `vm` без браузера; код показу не змінено. Python показу —
 * справжній: `транспортМостуП` (єдиний шов сторінки з Python) кличе `bridge.виклик` окремим процесом. Замінено лише
 * виклик моделі (`модельМовиП`): відповідь моделі — чорна скринька, тож заглушка відповідає на кожен текст промпту ним
 * самим (латиниця — кирилицею, як переклад), а на текст, який перелік речей промпту називає назвою речі («назва в
 * тексті н=K»), — назвою з першим словом кожного іншого тексту промпту: так справжня модель переклала «моєї спідниці»
 * як «моєї улюбленої спідниці» з опису картки (ж4 seed3_19). Будова, яку це міряє: код кладе назву її речі в один
 * виклик з ширшим текстом картки (опис, «як носити») і пише відповідь у поле картки. Картка її речі (з
 * `річ_запис_її_річ.py`) проходить `мовоюКарткуП` двічі — з описом як є і з кожним словом опису задом наперед; назва,
 * що від цього змінилась, — порушення, місце — рядок показу, що останнім записав `назва` (пастка на записі поля).
 *
 * Вхід (stdin): {джерела, картки: [{вхід, картка}], відповіді?: {назва: переклад}}; вихід — JSON-рядок
 * [{файл, рядок, поле, значення, вхід, писач}]. З `відповіді` — повтор записаної відповіді моделі (стенд): назва — з
 * неї, без збурення, вихід — [{вхід, до, після, файл, рядок}]. Ідентифікатор, якого показ не визначив, у прогоні —
 * помилка, а не тихий нуль.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');

const вхід = JSON.parse(fs.readFileSync(0, 'utf8'));
const ДЖЕРЕЛА = path.resolve(вхід.джерела);
const ОПИС = 'Чому цей образ працює: улюблена спідниця тримає офісний образ, а лофери роблять його легким.';
const ЯК_НОСИТИ = ['Заправ блузу в спідницю, щоб талія читалася.'];
const збурене = т => т.replace(/[\p{L}\p{N}_]{2,}/gu, с => [...с].reverse().join(''));

const відсутні = new Set();
let суворо = false;
const сховище = new Map();
const база = {console, Promise, Object, Array, String, Set, Map, JSON, Math, RegExp, Error, TypeError, Number,
  Boolean, Symbol, Date, setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {},
  URL, URLSearchParams, encodeURIComponent, decodeURIComponent, structuredClone, TextEncoder, TextDecoder, AbortController, parseInt, parseFloat, isNaN, isFinite, Intl, WeakMap,
  WeakSet, Reflect, Proxy, Infinity, NaN, undefined: undefined,
  location: {hash: '#модель_мови=прилад', search: '', href: 'http://прилад/'},
  localStorage: {getItem: к => сховище.has(к) ? сховище.get(к) : null, setItem: (к, з) => сховище.set(к, String(з)),
                 removeItem: к => сховище.delete(к)}};
const заглушка = new Proxy(function () {}, {get: (_, к) => к === Symbol.toPrimitive ? () => '' : заглушка,
  apply: () => заглушка, construct: () => заглушка});
const глобал = new Proxy(база, {
  has: () => true,
  get: (ц, к) => {
    if (к in ц) return ц[к];
    if (typeof к === 'symbol') return undefined;
    if (суворо) { відсутні.add(к); throw new ReferenceError('показ не визначив ' + к); }
    return заглушка;
  }});
const контекст = vm.createContext(глобал);
const сторінка = fs.readFileSync(path.join(ДЖЕРЕЛА, 'показ.html'), 'utf8');
const скрипти = [...сторінка.matchAll(/<script src="(показ\/[^"]+\.js)"><\/script>/g)].map(м => м[1]);
if (!скрипти.includes('показ/мовний_шар.js')) throw new Error('показ.html не вантажить показ/мовний_шар.js');
for (const с of скрипти) {
  const файл = path.join(ДЖЕРЕЛА, с);
  vm.runInContext(fs.readFileSync(файл, 'utf8'), контекст, {filename: 'джерела/' + с});
}
if (typeof база.мовоюКарткуП !== 'function') throw new Error('у показі нема мовоюКарткуП');

/* Python показу — справжній (`bridge.виклик`, той самий шов, що й воркер Pyodide), окремим процесом. */
const пітон = new Map();
база.транспортМостуП = async (ім, рядок) => {
  const ключ = ім + '\u0000' + рядок;
  if (!пітон.has(ключ)) {
    const р = spawnSync('python3', ['-X', 'utf8', '-W', 'ignore', '-c',
      'import sys, json, bridge; sys.stdout.write(bridge.виклик(sys.argv[1], json.loads(sys.stdin.read())))', ім],
      {cwd: ДЖЕРЕЛА, input: рядок, encoding: 'utf8', timeout: 120000, maxBuffer: 1 << 26});
    if (р.status !== 0) throw new Error('міст ' + ім + ': ' + (р.stderr || String(р.error)).slice(-1500));
    пітон.set(ключ, р.stdout);
  }
  return пітон.get(ключ);
};
/* Модель шару — заглушка лише виклику моделі: на кожен текст промпту — він сам, а на текст, який перелік речей
   промпту називає назвою речі («назва в тексті н=K»), — назва з першим словом кожного іншого тексту промпту. */
let записані = null;
/* «переклад» заглушки: латинські літери — кирилицею (модель перекладає «Blouse»; заглушка — лише літерами) */
const ЛІТЕРИ = Object.fromEntries([...'abcdefghijklmnopqrstuvwxyz'].map((л, і) => [л, 'абцдефгхіжклмнопкрстуввксиз'[і]]));
const кирилицею = т => т.replace(/[a-z]/gi, л => { const к = ЛІТЕРИ[л.toLowerCase()];
  return л === л.toLowerCase() ? к : к.toUpperCase(); });
база.модельМовиП = async (промпт) => {
  const тексти = JSON.parse(промпт.slice(промпт.lastIndexOf('ТЕКСТИ:\n') + 8).replace(/^[^{]*/, ''));
  const назви = new Set([...промпт.matchAll(/назва в тексті н=(\d+)/g)].map(м => м[1]));
  const текст = з => typeof з === 'string' ? з : String((з || {}).текст || '');
  const перші = Object.entries(тексти).map(([н, з]) => [н, (текст(з).match(/[\p{L}\p{N}_]{2,}/u) || [''])[0]]);
  const вих = {};
  for (const [н, з] of Object.entries(тексти)) {
    const свій = кирилицею(текст(з));
    вих[н] = записані ? (записані[текст(з)] !== undefined ? записані[текст(з)] : текст(з)) : !назви.has(н) ? свій
      : [свій, ...перші.filter(([і, с]) => і !== н && с).map(([, с]) => с)].join(' ');
  }
  return JSON.stringify(вих);
};
база.повідомленнямП = async () => ({тексти: {}, записи: [], заяви: [], чужою: []});
база.питаннямиП = async () => ({тексти: {}, записи: []});

function місцеЗапису() {
  for (const р of String(new Error().stack).split('\n').slice(2)) {
    const м = р.match(/\(?(джерела\/показ[^:()]*\.js):(\d+):\d+\)?\s*$/);
    if (м) return {файл: м[1], рядок: Number(м[2])};
  }
  return null;
}

async function прогін(картка, опис) {
  const річ = JSON.parse(JSON.stringify(картка));
  const записи = [];
  const пастка = new Proxy(річ, {set(ц, к, з) {
    if (к === 'назва') записи.push(місцеЗапису());
    ц[к] = з; return true; }});
  const к = {опис, як_носити: ЯК_НОСИТИ.map(р => опис === ОПИС ? р : збурене(р)), речі: [пастка]};
  суворо = true;
  try { await база.мовоюКарткуП(к, 'прилад'); } finally { суворо = false; }
  return {назва: (к.речі[0] || {}).назва, місце: записи.filter(Boolean).pop() || null};
}

(async () => {
  /* таймери запуску сторінки не біжать; обіцянки, початі під час завантаження, добігають до прогону */
  await new Promise(р => setImmediate(р));
  база.setTimeout = setTimeout; база.clearTimeout = clearTimeout;
  const вих = [];
  for (const {вхід: джерело, картка} of вхід.картки) {
    if (!картка || !картка.власна || !картка.назва) continue;
    if (вхід.відповіді) {
      записані = вхід.відповіді;
      const п = await прогін(картка, ОПИС);
      вих.push({вхід: джерело, до: картка.назва, після: п.назва, ...(п.місце || {})});
      continue;
    }
    const а = await прогін(картка, ОПИС), б = await прогін(картка, збурене(ОПИС));
    if (а.назва === б.назва) continue;
    if (!а.місце) throw new Error(`${джерело}: назва «${картка.назва}» залежить від опису, але запису поля не видно`);
    вих.push({файл: а.місце.файл, рядок: а.місце.рядок, поле: 'назва', значення: а.назва, вхід: джерело,
              писач: 'переклад картки'});
  }
  if (відсутні.size) throw new Error('показ не визначив: ' + [...відсутні].join(', '));
  process.stdout.write(JSON.stringify(вих) + '\n');
})().catch(е => { process.stderr.write(String(е && е.stack || е) + '\n'); process.exit(1); });
