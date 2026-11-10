'use strict';
/* _замок_важких.js — той самий спільний на ноутбук замок важких кроків, що й `_замок_важких.py`, для Node
   (Pyodide у процесі node). Чому, де діє, черга й звідки N — у докстрінгу `_замок_важких.py`.

   Слот і квиток черги — файли, відкриті з UV_FS_O_EXLOCK: libuv на Windows відкриває файл без спільного доступу
   (share mode 0, include/uv/win.h), як CreateFileW у Python, тож обидві мови бачать ті самі зайняті слоти й ту саму
   чергу. Дескриптор тримає процес до смерті; дочірні процеси його не успадковують. Чекання синхронне
   (Atomics.wait): крок бере замок до завантаження Pyodide. */
const fs = require('fs');
const path = require('path');

const ЗМІННА_ТЕКИ = 'KODSHI_HEAVY_DIR';
const ЗМІННА_ТРИМАЮ = 'KODSHI_HEAVY_HELD';
const ФАЙЛ_N = path.join(__dirname, '..', 'аудит', 'адаптери', 'gemini', 'важкі.json');
const UV_FS_O_EXLOCK = 0x10000000;  // libuv include/uv/win.h; у fs.constants Node 22 його нема
// Частота опитування, коли всі слоти зайняті: механізм, не межа роботи — як ОПИТУВАННЯ_С у Python.
const ОПИТУВАННЯ_МС = 2000;
const тримаю = [];

/** N з важкі.json; null — файла нема чи N не ціле додатне (тоді без замка). */
function межа() {
  let n;
  try { n = JSON.parse(fs.readFileSync(ФАЙЛ_N, 'utf8')).n; } catch (е) {
    process.stderr.write(`замок важкого кроку: N не прочитано (${е.message}) — без замка\n`);
    return null;
  }
  return Number.isInteger(n) && n > 0 ? n : null;
}

/** Дескриптор файла без спільного доступу або null — його тримає інший процес; інша помилка — виняток. */
function відкрити(шлях) {
  try { return fs.openSync(шлях, fs.constants.O_RDONLY | fs.constants.O_CREAT | UV_FS_O_EXLOCK); } catch (е) {
    if (е.code === 'EBUSY') return null;
    throw е;
  }
}

/** Скільки живих квитків черги старші за `мій` (null — у черзі мене нема); мертві квитки прибирає. */
function попереду(тека, мій) {
  let живі = 0;
  for (const ім of fs.readdirSync(тека).sort()) {
    if (!ім.startsWith('heavy-q-') || (мій !== null && ім >= мій)) continue;
    const fd = відкрити(path.join(тека, ім));
    if (fd === null) { живі++; continue; }
    fs.closeSync(fd);
    try { fs.unlinkSync(path.join(тека, ім)); } catch (е) { /* прибере наступний */ }
  }
  return живі;
}

/** Номер узятого вільного місця (дескриптор — у тримаю) або null. */
function слот(тека, n) {
  for (let i = 1; i <= n; i++) {
    const fd = відкрити(path.join(тека, `heavy-${i}.lock`));
    if (fd !== null) { тримаю.push(fd); return i; }
  }
  return null;
}

/** Чекає своєї черги й вільного слота з N і тримає слот до кінця процесу; без KODSHI_HEAVY_DIR — одразу null. */
function взяти(крок) {
  const тека = process.env[ЗМІННА_ТЕКИ] || '';
  if (!тека || process.env[ЗМІННА_ТРИМАЮ]) return null;
  if (process.platform !== 'win32') {
    process.stderr.write('замок важкого кроку: лише Windows — без замка\n');
    return null;
  }
  const n = межа();
  if (n === null) return null;
  let квиток = null, дескриптор = null, почато = null, i = null;
  try {
    for (;;) {
      if (попереду(тека, квиток) === 0 && (i = слот(тека, n)) !== null) break;
      if (квиток === null) {
        почато = Date.now();
        квиток = `heavy-q-${String(почато).padStart(15, '0')}-${process.pid}.lock`;
        дескриптор = відкрити(path.join(тека, квиток));
        process.stderr.write(`чекаю замок важкого кроку ${крок}: зайнято ${n} з ${n}, у черзі ${попереду(тека, квиток) + 1}-й, з ${new Date().toTimeString().slice(0, 8)}\n`);
      }
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ОПИТУВАННЯ_МС);
    }
  } catch (е) {
    process.stderr.write(`замок важкого кроку недоступний (${е.message}) — без замка\n`);
    return null;
  }
  if (дескриптор !== null) {
    fs.closeSync(дескриптор);
    try { fs.unlinkSync(path.join(тека, квиток)); } catch (е) { /* прибере наступний */ }
  }
  process.env[ЗМІННА_ТРИМАЮ] = `${крок}:${i}`;
  if (почато !== null) process.stderr.write(`замок важкого кроку взято: слот ${i} з ${n}, чекав ${Math.round((Date.now() - почато) / 1000)} с\n`);
  return i;
}

module.exports = {взяти};
