/* Парний вимір трьох оригінальних версій у справжньому Pyodide, без пакетів. */
const fs = require('fs'), path = require('path');
const [кеш, вхід, вихід, стара, ядроДо, річДо] = process.argv.slice(2);
(async () => {
  const {loadPyodide} = require(path.resolve(кеш, 'pyodide.js'));
  const п = await loadPyodide({indexURL: path.resolve(кеш) + '/'});
  п.FS.mkdir('/код');
  const джерела = path.resolve(__dirname, '..');
  for (const ім of fs.readdirSync(джерела).filter(ім => ім.endsWith('.py')))
    п.FS.writeFile('/код/' + ім, fs.readFileSync(path.join(джерела, ім)));
  for (const [ім, шлях] of [['стара.py', стара], ['ядро_до.py', ядроДо], ['річ_до.py', річДо], ['кадри.json', вхід]])
    п.FS.writeFile('/tmp/' + ім, fs.readFileSync(шлях));
  const результат = п.runPython(`
import sys, json, time, types
sys.path.insert(0, '/код')
import річ_з_фото as Р

def модуль(імʼя, шлях):
    """Ізольований оригінальний модуль без зміни поточної версії."""
    м = types.ModuleType(імʼя)
    exec(compile(open(шлях, encoding='utf-8').read(), шлях, 'exec'), м.__dict__)
    return м

стара = модуль('річ_стара', '/tmp/стара.py')
до = модуль('річ_до', '/tmp/річ_до.py')
до._ПОВ = модуль('ядро_до', '/tmp/ядро_до.py')
версії = [('стара', стара), ('до', до), ('після', Р)]
вих = []
for i, з in enumerate(json.load(open('/tmp/кадри.json'))):
    ряд = dict(ключ=з['ключ'])
    for імʼя, р in версії[i%3:] + версії[:i%3]:
        t = time.perf_counter()
        вимір = р.виміряти(з['пікселі'], рамка=True)
        ряд[імʼя] = dict(мс=(time.perf_counter()-t)*1000, вимір=вимір)
    вих.append(ряд)
    print('Pyodide', з['ключ'], *(round(ряд[v]['мс']) for v in ('стара', 'до', 'після')), flush=True)
assert 'numpy' not in sys.modules and 'cv2' not in sys.modules
json.dumps(вих, ensure_ascii=False)
`);
  fs.writeFileSync(вихід, результат);
})().catch(помилка => {console.error(помилка); process.exit(1);});
