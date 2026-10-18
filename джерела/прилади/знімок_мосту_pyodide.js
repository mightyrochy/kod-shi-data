/* Pyodide 0.26.4 під Node для `знімок_мосту.py` (без браузера): тіло сторінки розпаковується в /показ так само, як це робить
   `підняти_міст_показу`, далі виконується той самий `знімок_мосту.py`, що й під CPython.
   node знімок_мосту_pyodide.js <index.html> <тека pyodide> <входи.jsonl[.gz]> <тека виходу> [лише N]
   Виходи: <тека виходу>/знімок.jsonl, час.json. Мережі нема: `loadPyodide` бере 5 файлів кешу
   (`аудит/проби/стенд_pyodide_кеш.sh`) з диска. */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const [СТОРІНКА, ТЕКА_PYODIDE, ВХОДИ, ВИХІД, ЛИШЕ] = process.argv.slice(2);

(async () => {
  const { loadPyodide } = require(path.resolve(ТЕКА_PYODIDE, 'pyodide.js'));
  const html = fs.readFileSync(СТОРІНКА, 'utf8');
  const м = html.match(/МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"/);
  if (!м) throw new Error('у ' + СТОРІНКА + ' нема МОДУЛІ_ПОКАЗУ');
  const бін = Buffer.from(м[1], 'base64');
  const сирі = fs.readFileSync(ВХОДИ);
  const входи = (ВХОДИ.endsWith('.gz') ? zlib.gunzipSync(сирі) : сирі).toString('utf8');

  const t0 = Date.now();
  const пд = await loadPyodide({ indexURL: path.resolve(ТЕКА_PYODIDE) + '/' });
  пд.unpackArchive(бін.buffer.slice(бін.byteOffset, бін.byteOffset + бін.byteLength), 'zip', { extractDir: '/показ' });
  пд.FS.writeFile('/tmp/знімок_мосту.py', fs.readFileSync(path.join(__dirname, 'знімок_мосту.py')));
  пд.FS.writeFile('/tmp/входи.jsonl', входи);
  const підйом_мс = Date.now() - t0;
  const вих = await пд.runPythonAsync(
    'import sys, json\n' +
    'sys.path.insert(0, "/tmp")\n' +
    'import знімок_мосту as З\n' +
    'З.підготувати("/показ")\n' +
    'знімок, час = await З.прогнати(open("/tmp/входи.jsonl", encoding="utf-8").read(), ' + (Number(ЛИШЕ) || 'None') + ')\n' +
    'час.update({"середовище": "pyodide", "версія": sys.version})\n' +
    'json.dumps([знімок, час], ensure_ascii=False)\n');
  const [знімок, час] = JSON.parse(вих);
  час.версія_pyodide = пд.version;
  час.підйом_мс = підйом_мс;
  fs.mkdirSync(ВИХІД, { recursive: true });
  fs.writeFileSync(path.join(ВИХІД, 'знімок.jsonl'), знімок);
  fs.writeFileSync(path.join(ВИХІД, 'час.json'), JSON.stringify(час));
})().catch(е => { console.error(е); process.exit(2); });
