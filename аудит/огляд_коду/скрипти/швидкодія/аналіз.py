"""Зведення всіх вимірів у таблиці (медіани ×3). python3 аналіз.py <SP>"""
import json, sys, os, statistics as S, collections, glob
SP = sys.argv[1]; П = os.path.join(SP, 'прогони')
def j(ф):
    try: return json.load(open(os.path.join(П, ф), encoding='utf-8'))
    except Exception: return None
def мед(xs):
    xs = [x for x in xs if x is not None]
    return S.median(xs) if xs else None
def ф(x, n=0): return '—' if x is None else (('%.' + str(n) + 'f') % x)
def ут(ф_):
    try: return open(os.path.join(П, ф_)).read().split('\n')[0].split('load average:')[1].strip()
    except Exception: return '?'
вих = []
def p(*a): вих.append(' '.join(str(x) for x in a))

def події(д):
    р = collections.defaultdict(float)
    for е in д['події']:
        if е['к'] != 'містП' and 't1' in е: р[е['к']] += е['t1'] - е['t0']
    return р

# ── 1. Завантаження й підйом (boot_N, pyo_N) ──
p('## 1. Завантаження сторінки й підйом Pyodide/bridge (Chromium 141, з диска, без мережі)')
рядки = collections.defaultdict(list); ла = []
for пр in ['boot_1', 'boot_2', 'boot_3', 'pyo_1', 'pyo_2', 'pyo_3']:
    д = j(пр + '.json')
    if not д: continue
    n = д['nav']; e = події(д); м = {x['name']: x['value'] for x in д['метрики']}
    fcp = next((x['startTime'] for x in д['paint'] if x['name'] == 'first-contentful-paint'), None)
    for к, v in [('responseEnd (HTML прийнято)', n['responseEnd']), ('FCP', fcp), ('domInteractive (розбір HTML+скриптів)', n['domInteractive']),
                 ('DOMContentLoaded', n['domContentLoadedEventEnd']), ('load', n['loadEventEnd']),
                 ('CDP ScriptDuration до load', м.get('ScriptDuration', 0) * 1000), ('CDP V8CompileDuration', м.get('V8CompileDuration', 0) * 1000),
                 ('CDP TaskDuration до load', м.get('TaskDuration', 0) * 1000),
                 ('loadPyodide', e.get('loadPyodide')), ('atob(МОДУЛІ_ПОКАЗУ)', e.get('atob')), ('Uint8Array.from(...)', e.get('Uint8Array.from')),
                 ('unpackArchive (zip+bz2 → MEMFS)', e.get('unpackArchive')), ('import bridge', e.get('import_bridge')),
                 ('підйом разом (підняти_міст_показу)', д['підйом'])]:
        рядки[к].append(v)
    лт = [x for x in д['lt'] if x[0] > n['loadEventEnd']]
    if пр.startswith('boot'):
        рядки['найдовша long task підйому (лише boot_N)'].append(max([x[1] for x in лт] or [0]))
        рядки['сума long tasks підйому (лише boot_N)'].append(sum(x[1] for x in лт))
    рядки['long tasks до load (сума)'].append(sum(x[1] for x in д['lt'] if x[0] <= n['loadEventEnd']))
p('| крок | мс (медіана з %d) | усі |' % len(рядки['FCP'])); p('|---|---|---|')
for к, v in рядки.items(): p('| %s | %s | %s |' % (к, ф(мед(v)), ', '.join(ф(x) for x in v)))
p('uptime (load avg) на початку прогонів:', [ут(x) for x in []])

# ── 2. Імпорт по модулях (Pyodide) ──
p('\n## 2. Імпорт bridge у Pyodide: модулі (медіана з pyo_1..3, boot_1..3)')
імп = collections.defaultdict(lambda: [[], []]); комп_показ = []; комп_std = []; комп_n = []
for пр in ['boot_1', 'boot_2', 'boot_3', 'pyo_1', 'pyo_2', 'pyo_3']:
    д = j(пр + '.json')
    if not д or not д.get('імпорт'): continue
    for м, (cum, slf) in д['імпорт']['імп'].items(): імп[м][0].append(cum); імп[м][1].append(slf)
    т_імп = [е for е in д['події'] if е['к'] == 'import_bridge'][0]
    # компіляції, що сталися під час імпорту (час — епоха мс; беремо всі, що до кінця імпорту: перші N за порядком)
    к = д['імпорт']['комп']
    комп_показ.append(sum(x[1] for x in к if x[0].startswith('/показ')))
    комп_std.append(sum(x[1] for x in к if not x[0].startswith('/показ')))
    комп_n.append((len([x for x in к if x[0].startswith('/показ')]), len([x for x in к if not x[0].startswith('/показ')]),
                   sum(x[2] for x in к if x[0].startswith('/показ'))))
p('компіляція (source_to_code) під час імпорту: модулі показу %s мс, stdlib %s мс; файлів/байт показу: %s' % (ф(мед(комп_показ)), ф(мед(комп_std)), комп_n[:1]))
показ_мод = set(f[:-3] for f in os.listdir(os.path.join(SP, 'cpy', 'показ')) if f.endswith('.py'))
вл_пр = мед([sum(v for м, v in zip(імп.keys(), [x[1][k] for x in імп.values()]) if м.split(':')[-1] in показ_мод) for k in range(len(комп_показ))])
вл_std = мед([sum(v for м, v in zip(імп.keys(), [x[1][k] for x in імп.values()]) if м.split(':')[-1] not in показ_мод) for k in range(len(комп_показ))])
p('власний час імпорту: модулі показу %s мс, stdlib (компіляція з python_stdlib.zip всередині) %s мс' % (ф(вл_пр), ф(вл_std)))
p('| модуль | сукупно мс | власний мс |'); p('|---|---|---|')
for м, (c, s) in sorted(імп.items(), key=lambda kv: -мед(kv[1][1]))[:20]:
    p('| %s | %s | %s |' % (м, ф(мед(c)), ф(мед(s))))

# ── 3. PYC ──
p('\n## 3. Імпорт з .pyc (compileall перед імпортом) у Pyodide')
for пр in ['pyc_1', 'pyc_2', 'pyc_3']:
    д = j(пр + '.json')
    if not д: continue
    e = події(д)
    p('%s: compileall %s мс · import bridge %s мс · компіляцій під час імпорту %d (%s мс)' % (пр, ф(e.get('compileall')), ф(e.get('import_bridge')),
      len(д['імпорт']['комп']) if д.get('імпорт') else -1, ф(sum(x[1] for x in д['імпорт']['комп']) if д.get('імпорт') else None)))

# ── 4. Відтворення: Pyodide vs CPython ──
p('\n## 4. Ті самі 127 викликів bridge: Pyodide (Chromium) проти CPython 3.12')
def за_іменем(в):
    р = collections.defaultdict(float)
    for x in в: р[x['ім']] += x['мс']
    return р
pyo = [за_іменем(j('pyo_%d.json' % i)['відтворення']['р']['виклики']) for i in (1, 2, 3) if j('pyo_%d.json' % i)]
cx = [за_іменем(j('cpy_х_%d.json' % i)['відтворення']['виклики']) for i in (1, 2, 3) if j('cpy_х_%d.json' % i)]
ct = [за_іменем(j('cpy_т_%d.json' % i)['відтворення']['виклики']) for i in (1, 2, 3) if j('cpy_т_%d.json' % i)]
c13 = [за_іменем(j('cpy13_х_1.json')['відтворення']['виклики'])] if j('cpy13_х_1.json') else []
імена = sorted(set().union(*pyo), key=lambda к: -мед([x[к] for x in pyo]))
p('| виклик bridge | Pyodide мс | CPython 3.12 мс | коеф. | CPython 3.13 мс |'); p('|---|---|---|---|---|')
for к in імена + ['РАЗОМ']:
    a = мед([sum(x.values()) if к == 'РАЗОМ' else x.get(к, 0) for x in pyo]); b = мед([sum(x.values()) if к == 'РАЗОМ' else x.get(к, 0) for x in cx])
    c = мед([sum(x.values()) if к == 'РАЗОМ' else x.get(к, 0) for x in c13]) if c13 else None
    p('| %s | %s | %s | %s | %s |' % (к, ф(a), ф(b), ф(a / b, 2) if a and b else '—', ф(c)))
p('імпорт bridge CPython холодний (без .pyc): %s мс; теплий (__pycache__): %s мс' % (
    ф(мед([j('cpy_х_%d.json' % i)['імпорт_bridge_мс'] for i in (1, 2, 3) if j('cpy_х_%d.json' % i)])),
    ф(мед([j('cpy_т_%d.json' % i)['імпорт_bridge_мс'] for i in (1, 2, 3) if j('cpy_т_%d.json' % i)]))))
p('компіляція під час холодного імпорту CPython: %s мс' % ф(мед([sum(x[1] for x in j('cpy_х_%d.json' % i)['комп']) for i in (1, 2, 3) if j('cpy_х_%d.json' % i)])))

# ── 5. Стенд: шлях жінки ──
p('\n## 5. Стенд рв6 (шлях жінки, заглушка моделі миттєва), 3 прогони')
for i in (1, 2, 3):
    д = j('вим_%d.кінець.json' % i); ч = j('часи_%d.json' % i)
    if not д or not ч: continue
    py = д['python']; lt = д['lt']
    сума = collections.defaultdict(float)
    for x in py: сума[x['ім']] += x['мс']
    збір = (ч['кінець'] - ч['т0']) / 1000; код = sum(b - a for _, a, b in ч['python']) / 1000
    e = події(д)
    try: up = open(os.path.join(П, 'стенд_%d.uptime' % i)).read().split('\n')
    except Exception: up = ['?']
    p('прогін %d (%s): збір %.1f с, з них Python %.1f с; викликів моделі %d; усього bridge за шлях %.1f с у %d викликах; long tasks: %d, сума %.1f с, макс %.1f с, >1 с: %d; підйом: loadPyodide %s, unpack %s, import %s мс' % (
        i, up[0].split('load average:')[-1].strip(), збір, код, len([з for з in ч['події'] if з['к'] == 'модель']), sum(сума.values()) / 1000, len(py),
        len(lt), sum(x[1] for x in lt) / 1000, max(x[1] for x in lt) / 1000, len([x for x in lt if x[1] > 1000]),
        ф(e.get('loadPyodide')), ф(e.get('unpackArchive')), ф(e.get('import_bridge'))))
    p('   bridge за іменем (с): ' + ', '.join('%s %.1f' % (к, v / 1000) for к, v in sorted(сума.items(), key=lambda kv: -kv[1])))
    p('   10 найдовших long tasks (с): ' + ', '.join('%.1f' % (x[1] / 1000) for x in sorted(lt, key=lambda x: -x[1])[:10]))
print('\n'.join(вих))
