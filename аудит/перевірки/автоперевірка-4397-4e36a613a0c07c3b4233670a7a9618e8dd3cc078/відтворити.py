"""Незалежне відтворення мірила #4397 на точних деревах бази та голови."""
import collections
import gzip
import json
import os
import pathlib
import subprocess
import sys
import time

ДОКАЗИ = pathlib.Path(__file__).resolve().parent
РОБОТА = ДОКАЗИ.parents[2]
ТИМЧАСОВО = РОБОТА.parent / 'tmp'
БАЗА = ТИМЧАСОВО / 'check4397-base'
ГОЛОВА = ТИМЧАСОВО / 'check4397-head'
ЖУРНАЛ = []


def виконати(назва, команда, тека):
    if команда[0] == sys.executable:
        команда = [sys.executable, '-X', 'utf8', *команда[1:]]
    початок = time.monotonic()
    процес = subprocess.run([str(x) for x in команда], cwd=тека,
                            capture_output=True, encoding='utf-8', errors='replace',
                            env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    запис = dict(назва=назва, команда=[str(x) for x in команда], тека=str(тека),
                 код=процес.returncode, секунд=round(time.monotonic()-початок, 2),
                 stdout=процес.stdout, stderr=процес.stderr)
    ЖУРНАЛ.append(запис)
    (ТИМЧАСОВО / (назва + '.log')).write_text(процес.stdout + процес.stderr, encoding='utf-8')
    print(назва, 'код', процес.returncode, 'секунд', запис['секунд'], flush=True)
    with gzip.open(ДОКАЗИ / 'команди.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(ЖУРНАЛ, ф, ensure_ascii=False, indent=2)
    return запис


def головна():
    вимірник = ГОЛОВА / 'джерела/прилади/корінь_е3_сила_правила.py'
    for назва, дерево in [('ДО', БАЗА), ('ПІСЛЯ', ГОЛОВА)]:
        виконати('прилад-' + назва, [sys.executable, вимірник, '--корінь', дерево], дерево)
    for ім in ['стенд_знімок.py', 'тест_живого_шляху.py', 'тест_протоколу.py',
               'прилади/розділи_гейтів.py', 'audit_contracts.py']:
        команда = [sys.executable, ім] + (['--дим'] if ім == 'стенд_знімок.py' else [])
        виконати('батарея-' + pathlib.Path(ім).stem, команда, ГОЛОВА / 'джерела')
    # CLI-проби канону й спеки приймають JSON каталогу, а не XML чи gzip.
    код = """
import gzip, json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path.cwd()/'джерела'))
import feed as Ф
кеш=pathlib.Path(os.environ['TMP'])/'е3_каталог.json.gz'
if not кеш.exists():
    каталог=Ф.база_прогону(Ф.каталог_на_диску('каталог_повний.xml'),ліміт_фото=0)['каталог']
    with gzip.open(кеш,'wt',encoding='utf-8') as ф: json.dump(каталог,ф,ensure_ascii=False)
кеш.with_suffix('').write_bytes(gzip.decompress(кеш.read_bytes()))
print('каталог JSON підготовлено')
"""
    виконати('каталог-вхід', [sys.executable, '-c', код], БАЗА)
    проби = sorted({п for маска in ['wea_*.py', 'погода_*.py', 'сила_*.py']
                    for п in (ГОЛОВА / 'джерела/проби').glob(маска)})
    for проба in проби:
        аргументи = ([ГОЛОВА/'джерела'] if проба.stem == 'wea_вхід' else
                     [ГОЛОВА/'джерела', ТИМЧАСОВО/'е3_каталог.json']
                     if проба.stem in ('wea_канон', 'wea_спека') else [])
        виконати('проба-' + проба.stem, [sys.executable, проба, *аргументи], ГОЛОВА/'джерела')
    сітка = ГОЛОВА / 'джерела/проби/е3_панчішні_сітка.py'
    for назва, дерево in [('ДО', БАЗА), ('ПІСЛЯ', ГОЛОВА)]:
        виконати('панчішні-' + назва, [sys.executable, сітка, дерево, ТИМЧАСОВО / (назва+'.json')], дерево)
    виконати('панчішні-звірка', [sys.executable, сітка, '--звірити',
                               ТИМЧАСОВО/'ДО.json', ТИМЧАСОВО/'ПІСЛЯ.json'], ГОЛОВА)
    for назва, дерево in [('ДО', БАЗА), ('ПІСЛЯ', ГОЛОВА)]:
        виконати('каталог-' + назва, [sys.executable, дерево/'джерела/проби/е3_погода_знімок.py',
                                    ТИМЧАСОВО/(назва+'.json.gz')], дерево)
    до, після = [json.load(gzip.open(ТИМЧАСОВО/(н+'.json.gz'), 'rt', encoding='utf-8'))
                 for н in ['ДО', 'ПІСЛЯ']]
    зміни = collections.Counter()
    склад = 0
    for а, б in zip(до, після):
        склад += а[:5] != б[:5]
        if а[5:] != б[5:]:
            зміни[(а[2], а[3], str(а[5:]), str(б[5:]))] += 1
    підсумок = dict(знахідок_до=len(до), знахідок_після=len(після), зміни_складу=склад,
                    зміни=[dict(правило=к[0], суть=к[1], до=к[2], після=к[3], кількість=в)
                           for к, в in зміни.items()])
    (ДОКАЗИ/'каталог-звірка.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(підсумок, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    головна()
