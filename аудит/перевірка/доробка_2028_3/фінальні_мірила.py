"""Доводить мірила на фінальному коді, зберігаючи всі команди й журнали."""
import gzip
import json
import os
import pathlib
import subprocess
import sys
import time


def головна():
    """Перевіряє джерело трьох гам, міст 315 персон і побайтну тотожність брифу."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONHASHSEED='0')
    команди = [
        [str(тека / 'доповнення.py')],
        [str(тека / 'екрани.py'), '--звірити'],
        [str(тека / 'екрани.py'), '--звірити', '--тональна'],
        ['аудит/перевірка/доробка_2028_2/джерело_гами.py', '.', str(тека / 'гами-ПІСЛЯ.json')],
        ['аудит/проби/кольори_2028_2.py', '.', str(тека / 'ПІСЛЯ')],
    ]
    результати = []
    for і, арг in enumerate(команди, 1):
        print(f'{і}/{len(команди)}: ' + ' '.join(арг), flush=True)
        початок = time.monotonic()
        р = subprocess.run([sys.executable, *арг], cwd=корінь, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        назва = f'фінальні-{і}.txt.gz'
        (тека / назва).write_bytes(gzip.compress(р.stdout, mtime=0))
        результати.append(dict(команда=арг, код=р.returncode, секунд=round(time.monotonic() - початок, 1), журнал=назва))
        (тека / 'фінальні-команди.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('код=' + str(р.returncode), flush=True)
    if any(р['код'] for р in результати):
        return 1
    гами = json.loads((тека / 'гами-ПІСЛЯ.json').read_text(encoding='utf-8'))
    assert len(гами) == 3 and all(г['персон'] == 315 and not г['вади'] and г['координати_не_з_hex'] == 0 for г in гами)
    читати = lambda п: json.loads(gzip.decompress(п.read_bytes()))
    після = читати(тека / 'ПІСЛЯ/середні-персони.json.gz')
    причини = читати(тека / 'причини.json.gz')
    байти = lambda р: json.dumps(р, ensure_ascii=False, separators=(',', ':')).encode()
    assert len(після) == len(причини) == 315
    assert all(байти(п['бриф']) == байти(р['брифи']['усе']) for п, р in zip(після, причини))
    вимір = json.loads((тека / 'ПІСЛЯ/вимір.json').read_text(encoding='utf-8'))['гами'][0]
    assert вимір['персон'] == вимір['збіглися'] == вимір['аналогових_трійок'] == 315
    assert вимір['повторів'] == вимір['порожніх_чипів'] == вимір['тріади_поганих_пар'] == 0
    assert not вимір['вади']
    результат = dict(чип_джерело=315, аналогових=315, повторів=0, незаконних_пар=0,
                     порожніх=0, бриф_фінальний_дорівнює_причинному=315,
                     гами_без_незаконних_поєднань=3, код=0)
    (тека / 'фінальний-вимір.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(результат, ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(головна())
