# -*- coding: utf-8 -*-
"""Вимірює читачів записів аудит/ у повному git-дереві, незалежно від sparse-checkout.

Таблиця TSV і підсумок JSON відтворюються з SHA; самі великі таблиці в main не потрібні.
Кандидат — лише недосяжний файл. Невизначений каталог або шаблон зберігає весь
відповідний підграф з поясненням: відсутність точного статичного читача не доводить
відсутності динамічного. Посилання SHA:шлях і URL історії не є читачами дерева.
"""
import argparse
import ast
import collections
import fnmatch
import hashlib
import json
import posixpath
import re
import subprocess
import sys
import warnings
from pathlib import Path
from functools import lru_cache
from urllib.parse import unquote


ТЕКСТОВІ = {'.md', '.py', '.js', '.mjs', '.html', '.yml', '.yaml', '.json', '.ts',
            '.sh', '.ps1', '.txt', '.tsv', '.csv', '.toml', '.cfg', '.ini'}
ЗАХИЩЕНІ = ('аудит/наряди/', 'аудит/дошка/', 'аудит/корені/', 'аудит/адаптери/')
ІСТОРІЯ = re.compile(r'(?:[0-9a-f]{7,40}:|https?://[^\s`<>]+/)(?:аудит/[^\s`<>]+)')
ТОКЕНИ = re.compile(r'[\w.а-яА-ЯіїєґІЇЄҐ*?{}%+@~-]+(?:/[\w.а-яА-ЯіїєґІЇЄҐ*?{}%+@~-]*)*', re.UNICODE)
ОЗНАКИ_МАСКИ = '*?{}%['


@lru_cache(maxsize=1)
def перевірені_маски():
    """Читає уточнення після фільтрів читача; SHA не дає застосувати їх до іншого коду."""
    шлях = Path(__file__).with_name('читачі_записів_уточнення.json')
    return json.loads(шлях.read_text(encoding='utf-8')) if шлях.exists() else {}


def git(*аргументи):
    """Читає git без shell і без залежності від кодування консолі."""
    return subprocess.check_output(['git', *аргументи])


def дерево(ревізія):
    """Читає всі розміри й SHA, включно з невикладеними файлами."""
    вихід = {}
    for рядок in git('ls-tree', '-rlz', '--full-tree', ревізія).split(b'\0'):
        if рядок:
            мета, шлях = рядок.split(b'\t', 1)
            _, тип, ша, розмір = мета.split()
            if тип == b'blob':
                вихід[шлях.decode('utf-8')] = (int(розмір), ша.decode('ascii'))
    return вихід


def захищений(шлях):
    """Виключає правила, наряди, дошку, адаптери та журнали ролей із чистки."""
    return (шлях.startswith(ЗАХИЩЕНІ) or
            (шлях.startswith('аудит/') and шлях.count('/') == 1))


def тексти(файли):
    """Пакетно читає текстові blob; двійкові й сирі виходи не стають читачами."""
    обрані = [(п, ша) for п, (р, ша) in файли.items()
              if Path(п).suffix.lower() in ТЕКСТОВІ and р <= 1024 * 1024]
    for початок in range(0, len(обрані), 1024):
        пачка = обрані[початок:початок + 1024]
        вихід = subprocess.run(['git', 'cat-file', '--batch'],
                                input=''.join(ша + '\n' for _, ша in пачка).encode('ascii'),
                                stdout=subprocess.PIPE, check=True).stdout
        зсув = 0
        for шлях, _ in пачка:
            кінець = вихід.index(b'\n', зсув)
            розмір = int(вихід[зсув:кінець].split()[2])
            дані = вихід[кінець + 1:кінець + 1 + розмір]
            зсув = кінець + розмір + 2
            if b'\0' not in дані:
                yield шлях, дані.decode('utf-8-sig', errors='replace')


def частини(вузол, константи=None):
    """Добуває статичний префікс складеного Python-шляху; змінна дає wildcard."""
    константи = константи or {}
    if isinstance(вузол, ast.Name):
        return константи.get(вузол.id, '*')
    if isinstance(вузол, ast.Constant) and isinstance(вузол.value, str):
        return вузол.value
    if isinstance(вузол, ast.BinOp) and isinstance(вузол.op, (ast.Div, ast.Add)):
        ліво, право = частини(вузол.left, константи), частини(вузол.right, константи)
        return ліво + ('/' if isinstance(вузол.op, ast.Div) else '') + право
    if isinstance(вузол, ast.JoinedStr):
        return ''.join(частини(в, константи) if isinstance(в, ast.Constant) else '*' for в in вузол.values)
    if isinstance(вузол, ast.Call):
        назва = ast.unparse(вузол.func)
        if назва.endswith(('path.join', 'Path')):
            return '/'.join(частини(в, константи) for в in вузол.args)
        if isinstance(вузол.func, ast.Attribute) and вузол.func.attr in ('glob', 'rglob') and вузол.args:
            основа = частини(вузол.func.value, константи)
            if 'аудит/' in основа:
                return основа + ('/**/' if вузол.func.attr == 'rglob' else '/') + частини(вузол.args[0], константи)
        if назва.endswith(('listdir', 'walk', 'chdir')) and вузол.args:
            основа = частини(вузол.args[0], константи)
            if 'аудит/' in основа:
                return основа + ('/**' if назва.endswith(('walk', 'chdir')) else '/*')
    return '*'


def варіанти_шляху(читач, токен, від_файла=False):
    """Розв'язує шлях від файла та можливих робочих каталогів його запуску."""
    основи = {posixpath.dirname(читач)}
    if not від_файла:
        основи.add('')
        if читач.startswith('джерела/'):
            основи.add('джерела')
    return {posixpath.normpath(posixpath.join(основа, токен)) for основа in основи}


def git_посилання(читач, код, константи):
    """Зберігає входи ls-tree → show/cat-file поточного дерева; архівні ревізії не тримають main."""
    поточні = {'HEAD', '@', 'main', 'origin/main', 'refs/heads/main',
               'refs/remotes/origin/main', 'FETCH_HEAD', 'HEAD^{tree}', 'HEAD^0', 'HEAD~0'}
    батьки = {дитина: вузол for вузол in ast.walk(код) for дитина in ast.iter_child_nodes(вузол)}
    присвоєні, цикли = {}, collections.defaultdict(list)

    def присвоїти(ціль, значення):
        """Розкладає також присвоєння ref, каталог = …, … без втрати архівного ref."""
        if isinstance(ціль, ast.Name):
            присвоєні[ціль.id] = значення
        elif isinstance(ціль, (ast.Tuple, ast.List)) and isinstance(значення, (ast.Tuple, ast.List)):
            for ч, з in zip(ціль.elts, значення.elts):
                присвоїти(ч, з)

    for вузол in ast.walk(код):
        if isinstance(вузол, ast.Assign):
            for ціль in вузол.targets:
                присвоїти(ціль, вузол.value)
    for вузол in ast.walk(код):
        if not isinstance(вузол, ast.For):
            continue
        джерело = вузол.iter
        if isinstance(джерело, ast.Name):
            джерело = присвоєні.get(джерело.id, джерело)
        пари = False
        if isinstance(джерело, ast.Call) and isinstance(джерело.func, ast.Attribute):
            пари = джерело.func.attr == 'items'
            основа = джерело.func.value
            джерело = присвоєні.get(основа.id, основа) if isinstance(основа, ast.Name) else основа
        if isinstance(джерело, ast.Dict):
            елементи = list(zip(джерело.keys, джерело.values)) if пари else джерело.keys
        elif isinstance(джерело, (ast.Tuple, ast.List, ast.Set)):
            елементи = джерело.elts
        else:
            continue
        if isinstance(вузол.target, ast.Name):
            цикли[вузол.target.id].extend(е for е in елементи if isinstance(е, ast.AST))
        elif isinstance(вузол.target, (ast.Tuple, ast.List)):
            for елемент in елементи:
                поля = елемент if isinstance(елемент, tuple) else getattr(елемент, 'elts', ())
                for ціль, значення in zip(вузол.target.elts, поля):
                    if isinstance(ціль, ast.Name):
                        цикли[ціль.id].append(значення)

    def значення(вузол, бачені=frozenset(), типові=None):
        """Розгортає сталі, типові значення CLI й невеликі переліки ревізій та каталогів."""
        if вузол is None:
            return {'*'}
        if isinstance(вузол, ast.Name):
            if вузол.id in бачені:
                return {'*'}
            далі = бачені | {вузол.id}
            if типові and вузол.id in типові and типові[вузол.id] is not None:
                return значення(типові[вузол.id], далі)
            if вузол.id in цикли:
                return set().union(*(значення(е, далі) for е in цикли[вузол.id]))
            if типові and вузол.id in типові:
                return {'*'}
            if вузол.id in присвоєні:
                return значення(присвоєні[вузол.id], далі)
            return {константи.get(вузол.id, '*')}
        if isinstance(вузол, ast.Constant):
            return {str(вузол.value)} if isinstance(вузол.value, (str, int)) else {'*'}
        if isinstance(вузол, ast.IfExp):
            return значення(вузол.orelse, бачені, типові)
        if isinstance(вузол, ast.BoolOp) and isinstance(вузол.op, ast.Or):
            return значення(вузол.values[-1], бачені, типові)
        if isinstance(вузол, ast.BinOp):
            ліві = значення(вузол.left, бачені, типові)
            if isinstance(вузол.op, ast.Mod):
                return {re.sub(r'%[a-z]', '*', л) for л in ліві}
            if isinstance(вузол.op, (ast.Add, ast.Div)):
                праві = значення(вузол.right, бачені, типові)
                if len(ліві) * len(праві) <= 128:
                    return {л + ('/' if isinstance(вузол.op, ast.Div) else '') + п for л in ліві for п in праві}
        if isinstance(вузол, ast.Call) and ast.unparse(вузол.func).endswith(('getenv', '.get')) and len(вузол.args) > 1:
            return значення(вузол.args[1], бачені, типові)
        return {частини(вузол, константи)}

    команди = []
    for вузол in ast.walk(код):
        if not isinstance(вузол, ast.Call):
            continue
        аргументи = вузол.args
        if аргументи and isinstance(аргументи[0], (ast.List, ast.Tuple)):
            аргументи = аргументи[0].elts
        for і, аргумент in enumerate(аргументи):
            if isinstance(аргумент, ast.Constant) and аргумент.value in ('ls-tree', 'show', 'cat-file'):
                команди.append((вузол, аргумент.value, аргументи[і + 1:]))
                break
    є_блоби = any(
        команда == 'cat-file' and any(isinstance(а, ast.Constant) and а.value in ('blob', '--batch') for а in аргументи)
        or команда == 'show' and any(isinstance(в, ast.Constant) and isinstance(в.value, str) and ':' in в.value
                                     for а in аргументи for в in ast.walk(а))
        for _, команда, аргументи in команди)
    if not є_блоби:
        return set()
    літерали = [в.value for в in ast.walk(код) if isinstance(в, ast.Constant) and isinstance(в.value, str)
                and not isinstance(батьки.get(в), (ast.JoinedStr, ast.Expr))]
    вихід = set()
    for виклик, команда, аргументи in команди:
        if команда != 'ls-tree':
            continue
        значущі = [а for а in аргументи if not (isinstance(а, ast.Constant)
                   and isinstance(а.value, str) and а.value.startswith('-'))]
        if len(значущі) < 2:
            continue
        типові = {}
        предок = батьки.get(виклик)
        while предок is not None and not isinstance(предок, (ast.FunctionDef, ast.AsyncFunctionDef)):
            предок = батьки.get(предок)
        if предок is not None:
            параметри = предок.args.posonlyargs + предок.args.args
            типові = {п.arg: None for п in параметри}
            типові.update({п.arg: т for п, т in zip(параметри[len(параметри) - len(предок.args.defaults):], предок.args.defaults)})
        ревізії = значення(значущі[0], типові=типові)
        if not any(р in поточні or ('*' in р and not р.startswith('origin/claude/')) for р in ревізії):
            continue
        шляхи = set().union(*(значення(а, типові=типові) for а in значущі[1:]))
        if not any('аудит' in п for п in шляхи):
            шляхи = {л for л in літерали if л.startswith(('аудит/', '../аудит/'))}
        for шлях in шляхи:
            if шлях.startswith(':/'):
                шлях = шлях[2:]
            форми = варіанти_шляху(читач, шлях)
            if 'аудит/' in шлях:
                форми.add(шлях[шлях.index('аудит/'):])
            for форма in форми:
                if форма == 'аудит' or форма.startswith('аудит/'):
                    вихід.add(форма.rstrip('/') + '/**')
    return вихід


def посилання(шлях, текст):
    """Добуває повні, відносні, glob і складені шляхи, пропускаючи історію."""
    оригінал = текст
    текст = ІСТОРІЯ.sub('', текст)
    if шлях.endswith(('.yml', '.yaml')):
        # Фільтр запуску й git diff читають імена змінених файлів, не їхній вміст.
        рядки, блок, відступ = [], False, 0
        for рядок in текст.splitlines():
            н = len(рядок) - len(рядок.lstrip())
            if re.match(r'\s*(?:-\s*)?run:', рядок):
                блок, відступ = True, н
                рядки.append(рядок.split('run:', 1)[1])
            elif блок and (not рядок.strip() or н > відступ):
                if not (рядок.lstrip().startswith('#') or 'diff --name-only' in рядок or
                        ':(exclude' in рядок or
                        re.search(r'\)\s*.*;;', рядок)):
                    рядки.append(рядок)
            else:
                блок = False
        текст = '\n'.join(рядки)
    знайдені = set(ТОКЕНИ.findall(текст))
    for збіг in re.finditer(r'''[`"']([^`"'\n]+)[`"']|\]\(([^)\n]+)\)''', текст):
        значення = unquote((збіг[1] or збіг[2]).strip().strip('<>')).split('#', 1)[0]
        if '/' in значення:
            знайдені.add(значення)
    if шлях.endswith('.py'):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', SyntaxWarning)
                код = ast.parse(текст)
        except SyntaxError:
            код = None
        if код:
            документація = set()
            for вузол in ast.walk(код):
                тіло = getattr(вузол, 'body', None)
                if isinstance(тіло, list) and тіло and isinstance(тіло[0], ast.Expr):
                    значення = тіло[0].value
                    if isinstance(значення, ast.Constant) and isinstance(значення.value, str):
                        документація.add(id(значення))
            літерали = [в.value for в in ast.walk(код) if isinstance(в, ast.Constant)
                        and isinstance(в.value, str) and id(в) not in документація]
            # Приклад CLI в docstring і коментар не читають усі однойменні файли.
            знайдені = set(ТОКЕНИ.findall('\n'.join(літерали)))
            знайдені.update(в for в in літерали if '/' in в and '\n' not in в)
            константи = {}
            for _ in range(3):
                for вузол in ast.walk(код):
                    if isinstance(вузол, ast.Assign):
                        значення = частини(вузол.value, константи)
                        for ціль in вузол.targets:
                            if isinstance(ціль, ast.Name) and значення != '*':
                                константи[ціль.id] = значення
            for вузол in ast.walk(код):
                if isinstance(вузол, (ast.Call, ast.BinOp, ast.JoinedStr)):
                    значення = частини(вузол, константи)
                    if 'аудит/' in значення:
                        знайдені.add(значення)
                        # Невідома основа ROOT/__file__ може бути коренем репозиторію.
                        знайдені.add(значення[значення.index('аудит/'):])
            знайдені.update(git_посилання(шлях, код, константи))
    if шлях.endswith(('.js', '.mjs')):
        for виклик in re.finditer(r'path\.(?:join|resolve)\(__dirname,\s*([\'"])(.*?)\1', текст):
            відносний = виклик[2]
            for повний in варіанти_шляху(шлях, відносний, від_файла=True):
                if повний.startswith('аудит/'):
                    знайдені.add(повний)
                    if '.' not in posixpath.basename(повний):
                        знайдені.add(повний + '/**')
    для_читача = перевірені_маски().get(шлях)
    if для_читача and hashlib.sha256(оригінал.encode('utf-8')).hexdigest() == для_читача['sha256']:
        for обмеження in для_читача['маски']:
            if обмеження['широка'] in знайдені:
                знайдені.discard(обмеження['широка'])
                знайдені.update(обмеження['читані'])
    for збіг in re.finditer(r'(?:\bcd|Set-Location)\s+[\'\"]?((?:\.{1,2}/)*аудит/[^\s\'\";]+)', текст):
        for каталог in варіанти_шляху(шлях, збіг[1]):
            if каталог.startswith('аудит/'):
                знайдені.add(каталог.rstrip('/') + '/**')
    return знайдені


def збіг_шаблону(шлях, шаблон):
    """Зіставляє glob: зірочка не переходить через '/', подвійна — переходить."""
    частки = шаблон.split('/')
    вираз = ''
    for і, ч in enumerate(частки):
        остання = і == len(частки) - 1
        if ч == '**':
            вираз += '.*' if остання else '(?:[^/]+/)*'
        else:
            сегмент = fnmatch.translate(ч)[4:-3].replace('.*', '[^/]*')
            вираз += сегмент + ('' if остання else '/')
    return re.fullmatch(вираз, шлях) is not None


def вимір(файли, читання, читати_великий=None):
    """Будує транзитивне замикання читачів; цикли самі себе не зберігають."""
    аудит = {п for п in файли if п.startswith('аудит/')}
    індекс = collections.defaultdict(set)
    каталоги = set()
    for п in аудит:
        сегменти = п.split('/')
        for і in range(len(сегменти)):
            індекс['/'.join(сегменти[і:])].add(п)
        for і in range(2, len(сегменти)):
            каталог = '/'.join(сегменти[:і])
            індекс[каталог].add(п)
            каталоги.add(каталог)
    причини = {п: 'захищено: правила/наряд/дошка/паспорт/журнал/адаптер'
               for п in аудит if захищений(п)}
    черга = collections.deque(п for п in читання if not п.startswith('аудит/') or п in причини)
    бачені = set()
    кеш = {}
    while черга:
        if len(причини) == len(аудит):
            break
        читач = черга.popleft()
        if читач in бачені:
            continue
        бачені.add(читач)
        if len(бачені) % 1000 == 0:
            print(f'Читачів оброблено: {len(бачені)}; збережено: {len(причини)}', file=sys.stderr, flush=True)
        текст = читання.get(читач, '')
        if читач not in читання and читати_великий and Path(читач).suffix.lower() in ТЕКСТОВІ:
            текст = читати_великий(читач)
        for токен in sorted(посилання(читач, текст)):
            # Одне ім'я файла неоднозначне — лишаємо всі збіги. Голі слова не шляхи.
            if '/' not in токен and '.' not in токен:
                continue
            токен = токен.rstrip('.')
            є_маска = any(с in токен for с in ОЗНАКИ_МАСКИ)
            # Зберігаємо попередні неоднозначні збіги; cwd додає лише прив'язані шляхи.
            варіанти = варіанти_шляху(читач, токен, від_файла=True)
            if токен in файли or токен.startswith('аудит/'):
                варіанти = {токен}
            варіанти.update(в for в in варіанти_шляху(читач, токен) if в.startswith('аудит/'))
            if є_маска and not ('аудит/' in токен and варіанти):
                # Маска без прив'язки до дерева — формат/змінний cwd, а не шлях читача.
                continue
            if є_маска and читач.endswith('.md') and not (
                    читач.startswith(('аудит/корені/', 'аудит/наряди/')) or читач == 'аудит/ПЛАН.md'):
                # Колективне посилання старого звіту — на історію, не на нову базу CI.
                continue
            if '/' not in токен and токен not in індекс:
                continue
            збіги = set()
            for в in варіанти:
                if в in каталоги:
                    # Саме перелік баз паспорта зобов'язує зберігати цілу теку.
                    # Навігація й назва каталогу не означають читання всіх його файлів.
                    бази = re.findall(r'^база:\s*(.+)$', читання.get(читач, ''), re.M)
                    if not any(в in б for б in бази):
                        continue
                if в not in індекс and not ('аудит/' in в and any(с in в for с in ОЗНАКИ_МАСКИ)):
                    continue
                if в not in кеш:
                    знайдені = set(індекс.get(в, ()))
                    if any(с in в for с in ОЗНАКИ_МАСКИ) and 'аудит/' in в:
                        шаблон = re.sub(r'\{[^}]*\}?|%[a-z]', '*', в)
                        префікс = re.split(r'[*?\[]', шаблон)[0].rsplit('/', 1)[0]
                        область = індекс.get(префікс, аудит if префікс == 'аудит' else ())
                        знайдені.update(п for п in область if збіг_шаблону(п, шаблон))
                    кеш[в] = знайдені
                збіги.update(кеш[в])
            if len(збіги) > 1000:
                print(f'Широкий читач: {читач}: {токен} — {len(збіги)}', file=sys.stderr, flush=True)
            for п in sorted(збіги):
                if п == читач or п in причини:
                    continue
                невизначене = п not in варіанти
                причини[п] = f'{читач}: {токен}' + (' (сумнів: шаблон/каталог/неповний шлях)' if невизначене else '')
                черга.append(п)
    return причини


def звіт(ревізія, вихід):
    """Пише повну таблицю, кандидатів і підсумок з виміряним розподілом розмірів."""
    ревізія = git('rev-parse', '--verify', ревізія + '^{commit}').decode().strip()
    файли = дерево(ревізія)
    print(f'Дерево: {len(файли)} файлів; читання blob...', file=sys.stderr, flush=True)
    читання = dict(тексти(файли))
    print(f'Текстів: {len(читання)}; пошук читачів...', file=sys.stderr, flush=True)
    def читати_великий(шлях):
        """Читає великий досяжний текст окремо, не тримаючи гігабайти сирих логів у пам'яті."""
        дані = git('cat-file', 'blob', файли[шлях][1])
        return '' if b'\0' in дані else дані.decode('utf-8-sig', errors='replace')

    причини = вимір(файли, читання, читати_великий)
    вихід.mkdir(parents=True, exist_ok=True)
    кандидати = sorted(п for п in файли if п.startswith('аудит/') and п not in причини)
    (вихід / 'кандидати.txt').write_text('\n'.join(кандидати) + '\n', encoding='utf-8')
    теки = collections.defaultdict(lambda: {'файлів': 0, 'байтів': 0, 'кандидатів': 0, 'байтів_кандидатів': 0})
    with (вихід / 'читачі.tsv').open('w', encoding='utf-8', newline='') as ф:
        ф.write('файл\tрозмір\tчитач\n')
        for п, (розмір, _) in sorted(файли.items()):
            if not п.startswith('аудит/'):
                continue
            ф.write(f'{п}\t{розмір}\t{причини.get(п, "КАНДИДАТ: читача не знайдено")}\n')
            т = теки['/'.join(п.split('/')[:2])]
            т['файлів'] += 1
            т['байтів'] += розмір
            if п not in причини:
                т['кандидатів'] += 1
                т['байтів_кандидатів'] += розмір
    межі = [0, 4096, 65536, 262144, 1048576, 4194304, 16777216, 10**15]
    розподіл = []
    for низ, верх in zip(межі, межі[1:]):
        група = [р for п, (р, _) in файли.items() if п.startswith('аудит/') and not захищений(п) and низ <= р < верх]
        розподіл.append({'від': низ, 'до': верх, 'файлів': len(група), 'байтів': sum(група)})
    результат = {'ревізія': ревізія,
                 'дерево_файлів': len(файли), 'дерево_байтів': sum(р for р, _ in файли.values()),
                 'кандидатів': len(кандидати), 'байтів_кандидатів': sum(файли[п][0] for п in кандидати),
                 'теки': dict(sorted(теки.items())), 'розподіл': розподіл}
    (вихід / 'підсумок.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({к: в for к, в in результат.items() if к not in ('теки',)}, ensure_ascii=False))


def main():
    """Запускає лише вимір: нічого не видаляє й не змінює в індексі git."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--ревізія', default='HEAD')
    парсер.add_argument('--вихід', type=Path, required=True)
    а = парсер.parse_args()
    звіт(а.ревізія, а.вихід)


if __name__ == '__main__':
    main()
