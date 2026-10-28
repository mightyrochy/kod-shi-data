"""Команди повтору цієї перевірки, поза батареєю CI.

Запуск: python повтор.py <окреме-дерево-af7bc598> <режим> [параметр].
Для Windows перед запуском установити PYTHONUTF8=1 і PYTHONIOENCODING=utf-8.
Режими: база, порівняти, тріади, відтворити, насиченість база|голова,
батарея, проби, pal16-база, utf8-120, повтор-utf8.
До порівняння потрібен запуск кольори_9858_доробка.py з PR у вихід
scratch/автоперевірка-2028/після; база створюється однойменним режимом.
Усі результати записуються лише в scratch дерева перевірки.
"""
import gzip
import json
import os
import pathlib
import runpy
import subprocess
import sys
import time

корінь = pathlib.Path(sys.argv.pop(1)).resolve()
ціль = 'af7bc598994a5422e7e7d3b82c862a01b866f820'
if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=корінь).decode().strip() != ціль:
    raise SystemExit('Потрібне окреме дерево саме перевіреної голови #2028')
вихід = корінь / 'scratch/автоперевірка-2028'
вихід.mkdir(parents=True, exist_ok=True)
база = 'd89adca79624ccd4513da93cb932c02fbb99d3e1'

if sys.argv[1] == 'база':
    накладка = вихід / 'база-модулі'
    накладка.mkdir(exist_ok=True)
    for ім in ('palettes.py', 'міст_основи.py'):
        (накладка / ім).write_bytes(subprocess.check_output(
            ['git', 'show', f'{база}:джерела/{ім}'], cwd=корінь))
    sys.path[:0] = [str(накладка), str(корінь / 'джерела')]
    import palettes
    import міст_основи
    sys.argv = ['кольори_9858.py', str(вихід / 'база.json')]
    початок = time.monotonic()
    runpy.run_path(str(корінь / 'аудит/проби/кольори_9858.py'), run_name='__main__')
    print(f'Тривалість бази: {time.monotonic() - початок:.1f} с', flush=True)
elif sys.argv[1] == 'порівняти':
    до = json.loads((вихід / 'база.json').read_text(encoding='utf-8'))
    після = json.loads(gzip.decompress((вихід / 'після/персони.json.gz').read_bytes()))
    архів = json.loads(gzip.decompress((корінь / 'аудит/перевірка/кольори_9858/персони.json.gz').read_bytes()))
    результат = {'персон': len(до), 'бриф_змінено': 0, 'бриф_незмінний': 0,
                 'база_тотожна_архіву_поєднань': 0, 'порожніх_чипів_бази': 0,
                 'без_аналогової_в_джерелі_бази': 0}
    for а, б, в in zip(до, після, архів):
        assert а['вхід'] == б['вхід'] == в['вхід']
        зміна = а['бриф'] != б['бриф_ПІСЛЯ']
        результат['бриф_змінено' if зміна else 'бриф_незмінний'] += 1
        результат['база_тотожна_архіву_поєднань'] += а['поєднання'] == в['поєднання']
        результат['порожніх_чипів_бази'] += sum(not г['зразки'] for г in а['екран']['гілки'])
        без = not any(п['прийом'] == 'аналогова' for п in а['поєднання'][0])
        результат['без_аналогової_в_джерелі_бази'] += без
        assert bool(зміна) == bool(без)
    (вихід / 'порівняння.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(результат, ensure_ascii=False), flush=True)
elif sys.argv[1] == 'проби':
    результати = []
    проби = sorted((корінь / 'джерела/проби').glob('pal_*.py'))
    проби = [п for п in проби if п.stem not in ('pal_вердикт', 'pal_вимір')]
    for індекс, шлях in enumerate(проби):
        команда = [sys.executable, str(шлях)]
        початок = time.monotonic()
        р = subprocess.run(команда, cwd=корінь / 'джерела', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (вихід / f'проба-{шлях.stem}.txt').write_bytes(р.stdout)
        результати.append(dict(команда=команда, rc=р.returncode, секунд=round(time.monotonic()-початок, 1)))
        print(f'{індекс+1}/{len(проби)} {шлях.name}: rc={р.returncode}', flush=True)
    (вихід / 'проби.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'проб': len(результати), 'rc0': sum(р['rc']==0 for р in результати),
                      'невдалі': [р for р in результати if р['rc'] != 0]}, ensure_ascii=False), flush=True)
elif sys.argv[1] == 'батарея':
    os.environ.setdefault('NODE_PATH', str(корінь / 'джерела/node_modules'))
    команди = [
        [sys.executable, 'стенд_знімок.py', '--дим'],
        [sys.executable, 'тест_живого_шляху.py'],
        [sys.executable, 'тест_протоколу.py'],
        [sys.executable, 'прилади/розділи_гейтів.py'],
        [sys.executable, 'audit_contracts.py'],
        ['node', 'тест_показу.js'],
        [sys.executable, 'прилади/згорнути_дошку.py', '--лише-перевірити'],
        [sys.executable, 'проби/поділ_palette_ast.py'],
        [sys.executable, 'проби/поділ_bridge_ast.py'],
    ]
    результати = []
    for індекс, команда in enumerate(команди):
        print('Початок: ' + ' '.join(команда), flush=True)
        початок = time.monotonic()
        р = subprocess.run(команда, cwd=корінь / 'джерела', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (вихід / f'батарея-{індекс:02}.txt').write_bytes(р.stdout)
        результати.append(dict(команда=команда, rc=р.returncode, секунд=round(time.monotonic()-початок, 1)))
        print(f'Кінець: rc={р.returncode}, {результати[-1]["секунд"]} с', flush=True)
        print('\n'.join(р.stdout.decode('utf-8', errors='replace').splitlines()[-5:]), flush=True)
        (вихід / 'батарея.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
elif sys.argv[1] == 'pal16-база':
    sys.path[:0] = [str(вихід / 'база-модулі'), str(корінь / 'джерела')]
    import palettes
    import міст_основи
    runpy.run_path(str(корінь / 'джерела/проби/pal_K-PAL-16.py'), run_name='__main__')
elif sys.argv[1] == 'тріади':
    from itertools import combinations
    sys.path.insert(0, str(корінь / 'джерела'))
    import colorspace as КС
    import колір_річ as КР
    import колір_відношення as КВ
    після = json.loads(gzip.decompress((вихід / 'після/персони.json.gz').read_bytes()))
    кількість = пар = 0
    вади = []
    for і, персона in enumerate(після):
        for г in персона['чипи']:
            if г['схема'] != 'тріада':
                continue
            кількість += 1
            кольори = [dict(lab=КС.hx(h)) for h in г['зразки']]
            if len(кольори) != 3:
                вади.append(dict(персона=і, причина='не три зразки'))
            for а, б in combinations(кольори, 2):
                пар += 1
                сім = КР.та_сама_сім_я(а, б)
                сила = КВ.сила(КР.запис_кольору(а), КР.запис_кольору(б), 'triadic')[0]
                if сім != 'ні' or сила < 0.5:
                    вади.append(dict(персона=і, сім=сім, сила=сила, зразки=г['зразки']))
    р = dict(тріад=кількість, пар_кінцевого_sRGB=пар, вади=вади)
    (вихід / 'тріади.json').write_text(json.dumps(р, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(р, ensure_ascii=False), flush=True)
elif sys.argv[1] == 'відтворити':
    import importlib.util
    from itertools import combinations
    sys.path.insert(0, str(корінь / 'джерела'))
    import palettes as П
    import colorspace as КС
    import колір_річ as КР
    import колір_відношення as КВ
    import міст_основи as МО
    мод = importlib.util.spec_from_file_location('мірило_2028', корінь / 'аудит/проби/кольори_9858.py')
    в = importlib.util.module_from_spec(мод)
    мод.loader.exec_module(в)
    після = json.loads(gzip.decompress((вихід / 'після/персони.json.gz').read_bytes()))
    вхід = після[139]['вхід']
    пакети = []
    ориг = МО.пакет
    def запис(*а, **к):
        п = ориг(*а, **к)
        пакети.append(п)
        return п
    МО.пакет = запис
    результат = в.зняти(вхід)
    МО.пакет = ориг
    г = next(г for г in пакети[-1]['палітри']['розвилка'] if г['схема'] == 'тріада')
    практична = г['спец']['палітра_практична']
    трійка = П.поєднання_схеми(практична, 'тріада')
    def сила(а, б):
        return КВ.сила(КР.запис_кольору(dict(lab=tuple(а['lab']))),
                      КР.запис_кольору(dict(lab=tuple(б['lab']))), 'triadic')[0]
    факт = dict(вхід=вхід, кольори=[dict(hex=к['hex'], lab_джерела=к['lab'],
                    lab_sRGB=КС.hx(к['hex'])) for к in трійка],
        пари=[dict(hex=[а['hex'], б['hex']], сила_Lab=сила(а, б),
                   сила_sRGB=сила(dict(lab=КС.hx(а['hex'])), dict(lab=КС.hx(б['hex']))))
              for а, б in combinations(трійка, 2)],
        чип=next(г['зразки'] for г in результат['екран']['гілки'] if г['схема'] == 'тріада'))
    (вихід / 'відтворення.json').write_text(json.dumps(факт, ensure_ascii=False, indent=2), encoding='utf-8')
    до = json.loads((вихід / 'база.json').read_text(encoding='utf-8'))[139]
    assert до['вхід'] == вхід
    (вихід / 'екран-139.json').write_text(json.dumps([dict(сцена='персона139',
        ДО=до['екран'], ПІСЛЯ=результат['екран'])], ensure_ascii=False), encoding='utf-8')
    (вихід / 'палітра-ДО.js').write_bytes(subprocess.check_output(
        ['git', 'show', f'{база}:джерела/показ/палітра.js'], cwd=корінь))
    print(json.dumps(факт, ensure_ascii=False), flush=True)
elif sys.argv[1] == 'насиченість':
    режим = sys.argv[2]
    if режим == 'база':
        sys.path[:0] = [str(вихід / 'база-модулі'), str(корінь / 'джерела')]
        import palettes
        import міст_основи
    else:
        sys.path.insert(0, str(корінь / 'джерела'))
    import bridge
    факти = []
    for нас in ('приглушені', 'середні', 'насичені'):
        вхід = dict(шкіра=['#f1d0b5'], очі='#3b2417', волосся=['#16110e'],
                     обхвати={}, зріст=168, вибір_кольору=dict(насиченість=нас))
        р = json.loads(bridge.палітри(вхід))
        г = next(г for г in р['гілки'] if г['схема'] == 'аналогова')
        факти.append(dict(насиченість=нас, чип=г['зразки'],
                        низ=next(с['зразок'] for с in г['ролі'] if с['слот'] == 'низ')))
    (вихід / f'насиченість-{режим}.json').write_text(json.dumps(факти, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(режим=режим, факти=факти), ensure_ascii=False), flush=True)
elif sys.argv[1] == 'utf8-120':
    р = subprocess.run([sys.executable, 'audit_contracts.py'], cwd=корінь / 'джерела',
                       capture_output=True, text=True, check=True)
    assert 'КОНТРАКТИ ЦІЛІ' in р.stdout
    факт = f'rc={р.returncode}; stdout={type(р.stdout).__name__}; секція 120: stdout прочитаний у UTF-8'
    (вихід / 'utf8-120.txt').write_text(факт + '\n', encoding='utf-8')
    print(факт, flush=True)
elif sys.argv[1] == 'повтор-utf8':
    результати = []
    for назва in ('поділ_palette_ast.py', 'поділ_bridge_ast.py'):
        команда = [sys.executable, 'проби/' + назва]
        р = subprocess.run(команда, cwd=корінь / 'джерела', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (вихід / ('utf8-' + назва + '.txt')).write_bytes(р.stdout)
        результати.append(dict(команда=команда, rc=р.returncode))
        print(f'{назва}: rc={р.returncode}; ' + р.stdout.decode('utf-8').splitlines()[0], flush=True)
    (вихід / 'повтор-utf8.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
