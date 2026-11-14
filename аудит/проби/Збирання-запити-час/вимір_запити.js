/* Наряд Збирання-запити-час: секунди виклику `запити` в Pyodide 0.26.4 на записаних входах трьох сцен живого прогону
   13.11 (ж3_театр_тріада, ж2_новорічна_мороз, ж2_побачення_вечір; ДО — збірка main, ПІСЛЯ — збірка гілки).

   node аудит/проби/Збирання-запити-час/вимір_запити.js <тека pyodide> <index.html> [<index.html> …]

   Кожну сторінку — кожною сценою: `джерела/прилади/знімок_мосту_pyodide.js` піднімає Pyodide з кешу
   (`аудит/проби/стенд_pyodide_кеш.sh`), розпаковує тіло сторінки й ганяє записані виклики по черзі; звідси — мс
   виклику `запити` і sha256 його результату (однаковий SHA ДО і ПІСЛЯ — той самий вихід). Сторінка — `index.html`, зібрана
   з повним каталогом (як для стенда). Вихід — рядки «<сторінка> <сцена> запити <с> sha <12>» і `вимір.json` у поточній теці. */
const fs = require('fs'), path = require('path'), os = require('os'), crypto = require('crypto');
const { execFileSync } = require('child_process');
const [ПІДТЕКА_PYODIDE, ...СТОРІНКИ] = process.argv.slice(2);
if (!ПІДТЕКА_PYODIDE || !СТОРІНКИ.length) {
  console.error('node вимір_запити.js <тека pyodide> <index.html> [<index.html> …]');
  process.exit(2);
}
const КОРІНЬ = path.resolve(__dirname, '..', '..', '..');
const ЗНІМОК = path.join(КОРІНЬ, 'джерела', 'прилади', 'знімок_мосту_pyodide.js');
const ВХОДИ = path.join(__dirname, 'входи');
const СЦЕНИ = fs.readdirSync(ВХОДИ).filter(ф => ф.endsWith('.jsonl.gz')).sort();
const вимір = [];
for (const стор of СТОРІНКИ) {
  for (const ф of СЦЕНИ) {
    const сцена = ф.replace('.jsonl.gz', '');
    const вих = fs.mkdtempSync(path.join(os.tmpdir(), 'запити-час-'));
    const t0 = Date.now();
    execFileSync(process.execPath, [ЗНІМОК, path.resolve(стор), path.resolve(ПІДТЕКА_PYODIDE), path.join(ВХОДИ, ф), вих],
      { stdio: ['ignore', 'ignore', 'inherit'], maxBuffer: 1 << 26 });
    const час = JSON.parse(fs.readFileSync(path.join(вих, 'час.json'), 'utf8'));
    const рядки = fs.readFileSync(path.join(вих, 'знімок.jsonl'), 'utf8').split('\n').filter(Boolean);
    const виклик = час.виклики.find(в => в[1] === 'запити');
    const рядок = виклик ? рядки.find(р => { try { const з = JSON.parse(р); return з.н === виклик[0]; } catch (е) { return false; } }) : null;
    const sha = рядок ? crypto.createHash('sha256').update(рядок).digest('hex') : null;
    const запис = { сторінка: стор, сцена, запити_с: виклик ? +(виклик[2] / 1000).toFixed(1) : null, sha,
                    помилка: рядок && JSON.parse(рядок).помилка || null, разом_с: +((Date.now() - t0) / 1000).toFixed(1),
                    pyodide: час.версія_pyodide, процесор: os.cpus()[0] && os.cpus()[0].model };
    вимір.push(запис);
    console.log(`${стор} ${сцена} запити ${запис.запити_с} с sha ${sha && sha.slice(0, 12)}${запис.помилка ? ' помилка ' + запис.помилка : ''}`);
    fs.rmSync(вих, { recursive: true, force: true });
  }
}
fs.writeFileSync('вимір.json', JSON.stringify(вимір, null, 1));
