/* Час справжнього Pyodide без пакетів на тих самих рамках, що у CPython.
   node поверхня_показ_212.js <тека Pyodide> <до.json> <вихід.json> [старий річ_з_фото.py]
   Сирі кадри й відповіді залишаються поза git; вихід містить лише час і результати. */
const fs = require('fs'), path = require('path');
const [кеш, вхід, вихід, старий] = process.argv.slice(2);
(async () => {
  const {loadPyodide} = require(path.resolve(кеш, 'pyodide.js'));
  const п = await loadPyodide({indexURL: path.resolve(кеш) + '/'});
  п.FS.mkdir('/код');
  const джерела = path.resolve(__dirname, '..');
  for (const ім of fs.readdirSync(джерела).filter(ім=>ім.endsWith('.py')))
    п.FS.writeFile('/код/' + ім, fs.readFileSync(path.join(джерела, ім)));
  if (старий) п.FS.writeFile('/код/річ_з_фото.py', fs.readFileSync(старий));
  п.FS.writeFile('/tmp/кадри.json', fs.readFileSync(вхід));
  const результат = п.runPython(`
import sys, json, time
sys.path.insert(0, '/код')
import річ_з_фото as Р
кадри = json.load(open('/tmp/кадри.json'))
вих = []
for з in кадри:
    t = time.perf_counter()
    в = Р.виміряти(з['пікселі'], рамка=True)
    вих.append(dict(ключ=з['ключ'], мс=(time.perf_counter()-t)*1000, вимір=в))
    print(з['ключ'], round(вих[-1]['мс']), flush=True)
assert 'numpy' not in sys.modules and 'cv2' not in sys.modules
json.dumps(вих, ensure_ascii=False)
`);
  fs.writeFileSync(вихід, результат);
})().catch(помилка=>{console.error(помилка); process.exit(1);});
