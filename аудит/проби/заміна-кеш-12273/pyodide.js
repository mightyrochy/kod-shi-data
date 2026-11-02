/* Справжній Pyodide й вантаж c71cc075. --точний відтворює тільки записані входи обох замін. */
const fs = require('fs'), path = require('path');
const zlib = require('zlib');

async function головна(){
  const [кеш, сторінка, входи, вихід, режим] = process.argv.slice(2);
  if (режим && режим !== '--точний') throw new Error('Невідомий режим виміру: ' + режим);
  const {loadPyodide} = require(path.resolve(кеш, 'pyodide.js'));
  const py = await loadPyodide({indexURL: path.resolve(кеш) + path.sep});
  const html = fs.readFileSync(сторінка, 'utf8');
  const b64 = /МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"/.exec(html)[1];
  py.unpackArchive(new Uint8Array(Buffer.from(b64, 'base64')), 'zip', {extractDir:'/показ'});
  for (const ім of ['міст_пакет.py', 'міст_запити.py', 'міст_відповіді.py']) {
    py.FS.writeFile('/показ/' + ім, fs.readFileSync(path.resolve('джерела', ім)));
    const pyc = '/показ/__pycache__/' + ім.slice(0, -3) + '.cpython-312.pyc';
    if (py.FS.analyzePath(pyc).exists) py.FS.unlink(pyc);
  }
  const запис = fs.readFileSync(входи);
  py.FS.writeFile('/входи.jsonl', входи.endsWith('.gz') ? zlib.gunzipSync(запис) : запис);
  py.FS.writeFile('/вимір.py', fs.readFileSync(path.join(__dirname, 'вимір.py')));
  await py.runPythonAsync(`
__name__ = 'дим'
exec(open('/вимір.py', encoding='utf-8').read())
sys.path.insert(0, '/показ')
import міст_запити as _МЗ
assert 'вже_були_прогону' in _МЗ.пул_руки_1.__code__.co_consts
входи = [json.loads(р) for р in open('/входи.jsonl', encoding='utf-8')]
вибрані = [next(р for р in входи if р['ім'] == 'запити')]
вибрані += [р for р in входи if р['ім'] == 'від_моделі' and json.loads(р['вхід']).get('заміна')]
результат = виміряти(вибрані, Path('/показ'), Path('/показ'), сценарний=${режим === '--точний' ? 'False' : 'True'})
open('/результат.json', 'w', encoding='utf-8').write(json.dumps(результат, ensure_ascii=False, indent=2))
`);
  fs.writeFileSync(вихід, py.FS.readFile('/результат.json'));
}

головна().catch(e => { console.error(e); process.exitCode = 1; });
