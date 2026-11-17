"""Незалежна звірка доробки п.5 на одному дереві продукту; реалізацію не змінює."""
import ast
import collections
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import time

ДОКАЗИ = Path(__file__).resolve().parent
ДЕРЕВО = Path(sys.argv[1]).resolve()
ПРИЛАД = 'джерела/прилади/корінь_е3_сила_правила.py'
sys.path.insert(0, str(ДЕРЕВО / 'джерела/прилади'))


def прочитати(ref):
    return subprocess.check_output(['git', 'show', f'{ref}:{ПРИЛАД}']).decode('utf-8')


def завантажити(ref, назва):
    код = прочитати(ref)
    мод = importlib.util.module_from_spec(importlib.util.spec_from_loader(назва, loader=None))
    мод.__file__ = str(ДЕРЕВО / ПРИЛАД)
    sys.modules[назва] = мод
    exec(compile(код, мод.__file__, 'exec'), мод.__dict__)
    return мод, код


def лічити(мод, назва):
    print('лічба:', назва, flush=True)
    початок = time.monotonic()
    п = мод.Продукт(str(ДЕРЕВО))
    місця, відкинуті, констант, емісії = мод.лічба(п)
    рядки = sorted(set(місця))
    (ДОКАЗИ / (назва + '.txt')).write_text('\n'.join(
        f'{пункт} · {де} · {чому}' for де, пункт, чому in рядки
    ) + '\n' + '\n'.join(f'не місце · {де} · {чому}' for де, чому in sorted(set(відкинуті))), encoding='utf-8')
    return рядки, {
        'секунд': round(time.monotonic() - початок, 2),
        'місць': len({де for де, _, _ in рядки}),
        'пункти': dict(collections.Counter(пункт for _, пункт, _ in рядки)),
        'відкинутих_п5': sum(чому.startswith('п5:') for _, чому in set(відкинуті)),
        'модулів': len(п.М), 'JS': len(п.js), 'констант': констант, 'емісій': len(емісії),
    }


старий, старий_код = завантажити('e04b320be6b6b09112a06195dc26c9f0a2f2bbb9', 'базовий')
перший, перший_код = завантажити('d154f81b62c4f1efabca08647b107a6c44e8c1ec', 'первісний')
новий, новий_код = завантажити('5ac13f75f0c913ef8feb5721a246e468d824c8aa', 'дороблений')
дані = {}
множини = {}
for мод, назва in [(старий, 'база'), (перший, 'до'), (новий, 'після')]:
    множини[назва], дані[назва] = лічити(мод, назва)
    вивід = io.StringIO()
    with contextlib.redirect_stdout(вивід):
        вихід = мод.самоперевірка()
    дані[назва]['самоперевірка'] = вивід.getvalue().strip()
    дані[назва]['код_самоперевірки'] = вихід
    print(назва, дані[назва], flush=True)

п14 = lambda записи: {з for з in записи if з[1] != 'п5'}
дані['пп1_4_зникло'] = sorted(п14(множини['база']) - п14(множини['після']))
дані['пп1_4_додано'] = sorted(п14(множини['після']) - п14(множини['база']))
дані['п5_додано'] = sorted(з for з in set(множини['після']) - set(множини['до']) if з[1] == 'п5')
дані['п5_зникло'] = sorted(з for з in set(множини['до']) - set(множини['після']) if з[1] == 'п5')
вузли = lambda код: {в.name: ast.dump(в, include_attributes=False) for в in ast.parse(код).body
                    if isinstance(в, (ast.FunctionDef, ast.ClassDef))}
а, б = вузли(старий_код), вузли(новий_код)
дані['змінені_старі_функції'] = [ім for ім in а if а[ім] != б.get(ім)]

# Повтор відомої 16121: лише перейменування імпортного аліаса, без зміни семантики.
стенд = dict(новий._СТЕНД)
стенд['суд_п5а'] = стенд['суд_п5а'].replace('as Р\n', 'as УНІКАЛЬНИЙ_АЛІАС\n').replace("Р['", "УНІКАЛЬНИЙ_АЛІАС['")
п = новий.Продукт('/неіснує', модулі={м: (f'джерела/{м}.py', т) for м, т in стенд.items()}, js=новий._JS)
дані['16121_аліас_п5'] = sorted(де for де, пункт, _ in новий.лічба(п)[0] if пункт == 'п5' and 'реєстр_п5.py' in де)
(ДОКАЗИ / 'звірка.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(дані, ensure_ascii=False, indent=2))
