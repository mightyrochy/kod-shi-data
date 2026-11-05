# -*- coding: utf-8 -*-
"""Приховані вади, частина (г) — потік інформації: обсяг значень і сигнали вад на кожне.

Наряд `аудит/наряди/Приховані-розвідка.md` (слово власника 31.10 14:26, 14:51), файл частини —
`аудит/корені/Приховані-перелік-г.md`. Прилад не судить: він лічить знаменник (кожне значення потоку
з детермінованим ід) і механічні сигнали на кожне, щоб покриття рахував скрипт, а не сесія.

Значення (ід — перша колонка):
  г:вхід:<задача>:<шлях>   поле, яке код дає моделі (оголошення `збирач_промптів.Оголошення`, поле `вхід`);
  г:вихід:<задача>:<поле>  поле, яке модель віддає коду (`поля_виходу` того самого оголошення);
  г:паспорт:<ключ>         поле паспорта нагоди (`паспорт_поля.ПОЛЯ_ПАСПОРТА`): з її слів чи від коду;
  г:каталог:<поле>         поле запису каталогу (`каталог_записи_v1.jsonl.gz`) і відповіді розбору каталогу
                           (`каталог_розбір.schema.json`, `model_answer`);
  г:показ:<ід>             поле вводу показу (`показ.html`: input, select, textarea з ід).

Сигнали (класи вад потоку; сигнал — не вердикт, вердикт — у файлі частини):
  переклад   словник-літерал «слово ядра → код» поза `внутрішня_мова.ТАБЛИЦЯ`: друге визначення перекладу;
             пара — дубль таблиці, розходження з нею чи поза нею;
  поріг      порівняння значення з числом-літералом (прямо чи через одне присвоєння) — код тлумачить значення;
             різні числа на одне значення в різних функціях — кілька визначень межі;
  типове     читання значення з непорожнім типовим (`.get(к, x)`, `… or x`, `setdefault`) — код вигадує;
  визначення функції продукту, що пишуть значення не копією того самого ключа — скільки місць його визначають;
  без_читача поле паспорта, яке поза модулями паспорта й дроту ніхто не читає — губиться до правил;
  показ_типове поле вводу показу з типовим `value` — значення, якого вона не називала.

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_h_потік.py --одиниці        рядок на значення (ід ⇥ місце ⇥ опис)
  python3 джерела/прилади/приховані_h_потік.py --сигнали        сигнали на значення і зведення класів
  python3 джерела/прилади/приховані_h_потік.py --перелік аудит/корені/Приховані-перелік-г.md
      покриття вердиктами: значення покрите, коли його ід стоїть першою клітинкою рядка таблиці
      (`| ід | … |`) чи в рядку класу після «ід:» через кому.
"""
import argparse
import ast
import glob
import gzip
import importlib
import json
import os
import re
import sys
import warnings
from collections import defaultdict

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")
НЕ_ПРОДУКТ = ("тест", "стенд", "проба", "батарея", "audit", "gate", "measure", "мутанти", "жнива", "pair_test",
              "лабораторія", "гейти", "verify_", "аудит_", "поломки", "траса", "звірка", "status", "trace",
              "build_", "покроковик", "зведення", "досяжність", "відбиток", "лічба")
# модулі, що лише несуть поле паспорта (опис, валідатор, мовний шар, картка, дріт) — не його споживачі-правила
ПРОВІД = ("паспорт_поля.py", "протокол.py", "паспорт_нагоди.py", "мовний_шар.py", "картка_запиту.py",
          "дріт_моделі.py", "внутрішня_мова.py", "пакет_моделі.py", "збирач_промптів.py", "міст_пакет.py",
          "міст_вхід.py", "паспорт_основи.py", "мовний_шар_фрази.py")
ЗАГАЛЬНІ = {"id", "ід", "н", "код", "code", "values", "тип", "type", "назва", "name", "поле", "слот", "slot",
            "шлях", "що", "як", "без", "чому", "речі", "items", "колір", "case", "day", "person", "версія"}


def _відн(ш):
    return os.path.relpath(ш, КОРІНЬ)


def продукт_py():
    return sorted(ф for ф in glob.glob(os.path.join(ДЖ, "*.py")) if not os.path.basename(ф).startswith(НЕ_ПРОДУКТ))


def показ_js():
    return sorted(glob.glob(os.path.join(ДЖ, "показ", "*.js"))) + [os.path.join(ДЖ, ф) for ф in
                                                                   ("показ.html", "worker_джерело.js", "показ_шаблон.js")]


def _ast(ш):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(open(ш, encoding="utf-8").read())


def _імпорт(м):
    warnings.simplefilter("ignore")
    if ДЖ not in sys.path:
        sys.path.insert(0, ДЖ)
    return importlib.import_module(м)


# ───────────────────────────── значення ─────────────────────────────
def оголошення():
    """Усі `Оголошення` продукту: модульні імена, словники оголошень і ліниве `річ_з_фото.фото_речей()`."""
    ЗП = _імпорт("збирач_промптів")
    знайдені = {}
    for ф in продукт_py():
        if "Оголошення(" not in open(ф, encoding="utf-8").read() or ф.endswith("збирач_промптів.py"):
            continue
        м = os.path.basename(ф)[:-3]
        М = _імпорт(м)
        for к, в in list(vars(М).items()):
            for кк, вв in ([(к + "." + str(x), y) for x, y in в.items()] if isinstance(в, dict) else [(к, в)]):
                if isinstance(вв, ЗП.Оголошення):
                    знайдені.setdefault(id(вв), (м + "." + кк, вв))
    фото = _імпорт("річ_з_фото").фото_речей()
    знайдені[id(фото)] = ("річ_з_фото.фото_речей()", фото)
    return sorted(знайдені.values(), key=lambda x: x[0])


def одиниці():
    вих = []
    for де, о in оголошення_кеш():
        мітка = о.задача if sum(1 for _, х in оголошення_кеш() if х.задача == о.задача) == 1 else "%s/%s" % (
            о.задача, де.split(".", 1)[1])
        for п in о.вхід:
            вих.append(("г:вхід:%s:%s" % (мітка, п.шлях), де, (п.що or "")[:110]))
        for п in (о.поля_виходу or ()):
            вих.append(("г:вихід:%s:%s" % (мітка, п), де, "відповідь %s" % о.вихід))
    ПП = _імпорт("паспорт_поля").ПОЛЯ_ПАСПОРТА
    for к, з in ПП.items():
        ознаки = ",".join(sorted(x for x in з if x in ("лише_код", "лише_шар", "поза_розмовою", "поза_схемою",
                                                       "показ", "плитка", "її_мовою", "число")))
        вих.append(("г:паспорт:" + к, "джерела/паспорт_поля.py", "поле %s · %s" % (з.get("поле", "—"), ознаки or "—")))
    ключі = set()
    with gzip.open(os.path.join(КОРІНЬ, "каталог_записи_v1.jsonl.gz"), "rt", encoding="utf-8") as ф:
        for і, р in enumerate(ф):
            ключі.update(json.loads(р))
            if і > 3000:
                break
    for к in sorted(ключі - {"схема", "початок", "кінець"}):
        вих.append(("г:каталог:запис." + к, "каталог_записи_v1.jsonl.gz", "поле запису каталогу"))
    кат = json.load(open(os.path.join(ДЖ, "каталог_розбір.schema.json"), encoding="utf-8"))
    for к in кат["$defs"]["model_answer"].get("properties", {}):
        вих.append(("г:каталог:розбір." + к, "джерела/каталог_розбір.schema.json", "поле розбору каталогу"))
    html = open(os.path.join(ДЖ, "показ.html"), encoding="utf-8").read()
    for т in re.finditer(r"<(input|select|textarea)\b([^>]*)>", html):
        ід = re.search(r'\bid="([^"]+)"', т.group(2))
        if ід:
            знач = re.search(r'\bvalue="([^"]*)"', т.group(2))
            н = html.count("\n", 0, т.start()) + 1
            вих.append(("г:показ:" + ід.group(1), "джерела/показ.html:%d" % н,
                        "%s%s" % (т.group(1), (" value=" + знач.group(1)) if знач else "")))
    # той самий шлях двічі в одному оголошенні (`складання`: `pool` — і перелік, і таблиця) — ід з номером
    бачені = defaultdict(int)
    for і, (ід, де, опис) in enumerate(вих):
        бачені[ід] += 1
        if бачені[ід] > 1:
            вих[і] = ("%s#%d" % (ід, бачені[ід]), де, опис)
    return вих


_КЕШ = []


def оголошення_кеш():
    if not _КЕШ:
        _КЕШ.extend(оголошення())
    return _КЕШ


# ───────────────────────────── сигнали ─────────────────────────────
_КИР = re.compile(r"[а-яіїєґʼ']", re.I)
_КОД = re.compile(r"^[a-z][a-z0-9_]*$")


def _str(x):
    return x.value if isinstance(x, ast.Constant) and isinstance(x.value, str) else None


def переклад():
    """Словники-літерали «слово ядра → код» поза `внутрішня_мова.ТАБЛИЦЯ` і звірка кожної пари з таблицею."""
    Т = _імпорт("внутрішня_мова").ТАБЛИЦЯ
    код_слово = defaultdict(set)    # код → слова ядра в таблиці
    слово_код = defaultdict(set)
    for поле, т in Т.items():
        for к, в in т.items():
            if isinstance(в, str):
                код_слово[к].add(в)
                слово_код[в].add(к)
    словники = []
    for ф in продукт_py():
        if ф.endswith("внутрішня_мова.py"):
            continue
        for в in ast.walk(_ast(ф)):
            if not isinstance(в, ast.Dict) or len(в.keys) < 3 or None in в.keys:
                continue
            пари = [(_str(к), _str(з)) for к, з in zip(в.keys, в.values)]
            if any(к is None or з is None for к, з in пари):
                continue
            if sum(bool(_КИР.search(к)) for к, _ in пари) * 3 < 2 * len(пари):
                continue
            if sum(bool(_КОД.match(з)) for _, з in пари) * 3 < 2 * len(пари):
                continue
            # поле таблиці, з яким словник ділить найбільше точних пар; ≥2 — словник перекладає те саме поле вдруге
            збіги = sorted(((sum(1 for к, з in пари if т.get(з) == к), поле) for поле, т in Т.items()), reverse=True)
            спільних, поле = збіги[0]
            лік = {"дубль": 0, "розходження": 0, "поза": 0}
            розх = []
            т = Т[поле] if спільних >= 2 else {}
            for к, з in пари:
                if т.get(з) == к:
                    лік["дубль"] += 1
                elif з in т or к in т.values():
                    лік["розходження"] += 1
                    розх.append("%s→%s (таблиця %s: %s)" % (к, з, поле, т.get(з) or
                                                         ",".join(x for x, y in т.items() if y == к)))
                else:
                    лік["поза"] += 1
            if спільних < 2:
                continue
            лік["поле"] = поле
            словники.append(("%s:%d" % (_відн(ф), в.lineno), len(пари), лік, розх[:3]))
    return словники


def _читання(в, ключі):
    """Ключ, який вузол читає: `x["к"]`, `x.get("к"…)`; інакше None."""
    if isinstance(в, ast.Subscript) and isinstance(в.ctx, ast.Load) and _str(в.slice) in ключі:
        return _str(в.slice)
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "pop") \
            and в.args and _str(в.args[0]) in ключі:
        return _str(в.args[0])
    return None


def _непорожнє(x):
    if isinstance(x, ast.Constant):
        return x.value not in (None, "", 0, False) or (x.value == 0 and not isinstance(x.value, bool))
    if isinstance(x, (ast.List, ast.Tuple, ast.Set)):
        return bool(x.elts)
    if isinstance(x, ast.Dict):
        return bool(x.keys)
    return False


def _число(x):
    if isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool):
        return x.value
    if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub) and _число(x.operand) is not None:
        return -_число(x.operand)
    return None


def _функції(дерево):
    вих = []

    def обхід(в, ім):
        for д in ast.iter_child_nodes(в):
            if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef)):
                вих.append((ім + д.name, д))
                обхід(д, ім + д.name + ".")
            elif isinstance(д, ast.ClassDef):
                обхід(д, ім + д.name + ".")
    обхід(дерево, "")
    вих.append(("<модуль>", дерево))
    return вих


def _власні(функція):
    """Вузли функції без вкладених функцій (їх лічить їхній власний обхід)."""
    стос = list(ast.iter_child_nodes(функція))
    while стос:
        в = стос.pop()
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield в
        стос.extend(ast.iter_child_nodes(в))


def ключі_значень():
    """Ключі, якими значення потоку ходить у коді: поля паспорта (укр. і код поля), поля випадку дроту,
    поля дня, відповіді розбору каталогу й портрета. Загальні імена (`ЗАГАЛЬНІ`, до 2 знаків) — ні."""
    ПП = _імпорт("паспорт_поля").ПОЛЯ_ПАСПОРТА
    кл = defaultdict(set)     # ключ коду → значення-власник (ід)
    for к, з in ПП.items():
        if not к.startswith("@"):
            кл[к].add("г:паспорт:" + к)
            if з.get("поле"):
                кл[з["поле"]].add("г:паспорт:" + к)
    ДР = _імпорт("дріт_моделі")
    for к, з in ДР.ПОЛЯ_ВИПАДКУ.items():
        кл[з].add("г:паспорт:" + к if к in ПП else "г:дріт:case." + з)
    П = _імпорт("протокол")
    for к in П.ДЕНЬ["поля"]:
        кл[к].add("г:дріт:day." + к)
    кат = json.load(open(os.path.join(ДЖ, "каталог_розбір.schema.json"), encoding="utf-8"))
    for к in кат["$defs"]["model_answer"].get("properties", {}):
        кл[к].add("г:каталог:розбір." + к)
    for к in П.ПОРТРЕТ_V1["поля"]:
        кл[к].add("г:вихід:колір_портрета:" + к)
    return {к: в for к, в in кл.items() if len(к) > 2 and к not in ЗАГАЛЬНІ}


def сигнали_py():
    кл = ключі_значень()
    читачі, визначення = defaultdict(set), defaultdict(set)
    типові, пороги = defaultdict(list), defaultdict(list)
    for ф in продукт_py():
        відн = _відн(ф)
        дерево = _ast(ф)
        for ім, функція in _функції(дерево):
            де = "%s:%s" % (відн, ім)
            вузли = list(_власні(функція))
            псевдо = {}       # локальне ім'я → ключ, з якого присвоєно
            if isinstance(функція, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # параметр з ім'ям значення — читач: сценарій і паспорт їдуть у правила іменованими (`**_мк`)
                for арг in функція.args.args + функція.args.kwonlyargs:
                    if арг.arg in кл:
                        читачі[арг.arg].add((відн, ім))
            for в in вузли:
                if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name):
                    for п in ast.walk(в.value):
                        к = _читання(п, кл)
                        if к:
                            псевдо[в.targets[0].id] = к
                            break
            for в in вузли:
                к = _читання(в, кл)
                if к:
                    читачі[к].add((відн, ім))
                    if isinstance(в, ast.Call) and len(в.args) > 1 and _непорожнє(в.args[1]):
                        типові[к].append("%s:%d %s" % (відн, в.lineno, ast.unparse(в.args[1])[:30]))
                if isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or) and len(в.values) >= 2:
                    к0 = _читання(в.values[0], кл)
                    if к0 and _непорожнє(в.values[-1]):
                        типові[к0].append("%s:%d or %s" % (відн, в.lineno, ast.unparse(в.values[-1])[:30]))
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "setdefault" \
                        and len(в.args) > 1 and _str(в.args[0]) in кл and _непорожнє(в.args[1]):
                    типові[_str(в.args[0])].append("%s:%d setdefault %s" % (відн, в.lineno,
                                                                              ast.unparse(в.args[1])[:30]))
                if isinstance(в, ast.Compare):
                    сторони = [в.left] + list(в.comparators)
                    числа = [_число(с) for с in сторони if _число(с) is not None]
                    if числа and not all(isinstance(о, (ast.Eq, ast.NotEq, ast.In, ast.NotIn, ast.Is, ast.IsNot))
                                         for о in в.ops):
                        for с in сторони:
                            ключ = None
                            for п in ast.walk(с):
                                ключ = _читання(п, кл) or (псевдо.get(п.id) if isinstance(п, ast.Name) else None)
                                if ключ:
                                    break
                            if ключ:
                                пороги[ключ].append((відн, ім, в.lineno, tuple(числа)))
                                break
                # визначення: dict-літерал з ключем, x["к"] = …, dict(к=…), .update(к=…)
                пари = []
                if isinstance(в, ast.Dict):
                    пари = [(_str(к), з) for к, з in zip(в.keys, в.values) if к is not None]
                elif isinstance(в, ast.Assign):
                    пари = [(_str(т.slice), в.value) for т in в.targets if isinstance(т, ast.Subscript)]
                elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "setdefault" \
                        and len(в.args) > 1:
                    пари = [(_str(в.args[0]), в.args[1])]
                elif isinstance(в, ast.Call) and (isinstance(в.func, ast.Name) and в.func.id == "dict" or
                                                   isinstance(в.func, ast.Attribute) and в.func.attr == "update"):
                    пари = [(кв.arg, кв.value) for кв in в.keywords if кв.arg]
                for к, з in пари:
                    if к in кл and not (_читання(з, {к}) or isinstance(з, ast.Name) and (псевдо.get(з.id) == к
                                                                                         or з.id == к)):
                        визначення[к].add((відн, ім))
    return кл, читачі, визначення, типові, пороги


_JS = []


def _у_js(ключ):
    """Ключ стоїть рядком у коді показу (`показ/*.js`, `показ.html`, воркер) — показ його читає чи пише."""
    if not ключ:
        return False
    if not _JS:
        _JS.append("\n".join(open(ф, encoding="utf-8").read() for ф in показ_js() if os.path.exists(ф)))
    return bool(re.search(r"[\"'.]%s(?![\w])" % re.escape(ключ), _JS[0]))


def таблиця_паспорта():
    """Рядок на поле паспорта: звідки значення (модель / панель / код / нема), читачі-правила, дріт, показ,
    сигнали типового й порогу — і сигнал класу. Клас — механічний; вердикт очима — у файлі частини."""
    кл, читачі, визначення, типові, пороги = сигнали_py()
    ПП = _імпорт("паспорт_поля").ПОЛЯ_ПАСПОРТА
    ДР = _імпорт("дріт_моделі")
    день = set(_імпорт("протокол").ДЕНЬ["поля"])
    рядки = []
    for к, з in ПП.items():
        ключі = [x for x in (к, з.get("поле")) if x]
        пишуть = {x for кк in ключі for x in визначення.get(кк, ()) if os.path.basename(x[0]) not in
                  ("паспорт_поля.py", "profile.py")}
        модель = bool(з.get("мова") or з.get("схема") or з.get("вісь")) and not з.get("лише_код")
        панель = bool(з.get("показ")) or bool(з.get("плитка"))
        джерело = "/".join(x for x, т in (("модель", модель), ("панель", панель), ("код", bool(пишуть))) if т) \
            or "нема"
        правила = {x for кк in ключі for x in читачі.get(кк, ()) if os.path.basename(x[0]) not in ПРОВІД}
        дріт = к in ДР.ПОЛЯ_ВИПАДКУ or з.get("поле") in день
        показ = bool(з.get("показ")) or any(_у_js(x) for x in ключі)
        тп = sum(len(типові.get(x, ())) for x in ключі)
        пр = sorted({ч for x in ключі for *_, чч in пороги.get(x, ()) for ч in чч})
        if к.startswith("@"):
            сигнал = "вісь мовного шару"
        elif джерело == "нема" and правила:
            сигнал = "Г1 вхід правила без джерела"
        elif джерело == "нема":
            сигнал = "Г1 поле без джерела й читача"
        elif not правила and not дріт and not показ:
            сигнал = "губиться"
        elif пр and len({ф for x in ключі for ф, *_ in пороги.get(x, ())}) > 1:
            сигнал = "Г4 поріг у кількох модулях"
        elif тп:
            сигнал = "Г3 типове коду"
        else:
            сигнал = "—"
        рядки.append((к, джерело, len(правила), дріт, показ, тп, пр, сигнал))
    return рядки


def показ_типові():
    html = open(os.path.join(ДЖ, "показ.html"), encoding="utf-8").read()
    вих = []
    for т in re.finditer(r"<(input|textarea)\b([^>]*)>", html):
        ід, знач = re.search(r'\bid="([^"]+)"', т.group(2)), re.search(r'\bvalue="([^"]+)"', т.group(2))
        тип = re.search(r'\btype="([^"]+)"', т.group(2))
        if ід and знач and (not тип or тип.group(1) not in ("button", "submit", "hidden", "file", "color")):
            вих.append((ід.group(1), знач.group(1), html.count("\n", 0, т.start()) + 1))
        elif ід and знач and тип and тип.group(1) == "color":
            вих.append((ід.group(1), знач.group(1), html.count("\n", 0, т.start()) + 1))
    return вих


# ───────────────────────────── вивід ─────────────────────────────
def друк_одиниць():
    од = одиниці()
    for ід, де, опис in од:
        print("%s\t%s\t%s" % (ід, де, опис))
    види = defaultdict(int)
    for ід, _, _ in од:
        види[ід.split(":")[1]] += 1
    print("значень: %d · %s" % (len(од), " · ".join("%s %d" % кв for кв in sorted(види.items()))))


def друк_сигналів():
    кл, читачі, визначення, типові, пороги = сигнали_py()
    print("== переклад: словники «слово ядра → код» поза внутрішня_мова.ТАБЛИЦЯ, що перекладають її поле вдруге (≥2 точні пари)")
    сл = переклад()
    сума = defaultdict(int)
    for де, н, лік, розх in сл:
        for к, в in лік.items():
            if к != "поле":
                сума[к] += в
        print("  %s поле %s · пар %d · дубль %d · розходження %d · поза %d%s" % (де, лік["поле"], н, лік["дубль"], лік["розходження"],
              лік["поза"], ("  ⇒ " + "; ".join(розх)) if розх else ""))
    print("  словників: %d · пар: дубль %d, розходження %d, поза таблицею %d" % (len(сл), сума["дубль"],
          сума["розходження"], сума["поза"]))
    print("== поріг: значення, яке код порівнює з числом (різні числа в різних функціях — кілька визначень межі)")
    кілька = 0
    for к in sorted(пороги, key=lambda x: -len(пороги[x])):
        функції = {(ф, ім) for ф, ім, _, _ in пороги[к]}
        числа = sorted({ч for *_, чч in пороги[к] for ч in чч})
        if len(функції) > 1 and len(числа) > 1:
            кілька += 1
        print("  %-22s %s · порівнянь %d у %d функціях · числа %s · %s" % (к, ",".join(sorted(кл[к]))[:60],
              len(пороги[к]), len(функції), числа[:12], "; ".join("%s:%d" % (ф, р) for ф, _, р, _ in пороги[к][:3])))
    print("  значень з порогом: %d · з різними числами в кількох функціях: %d" % (len(пороги), кілька))
    print("== типове: читання з непорожнім типовим")
    for к in sorted(типові, key=lambda x: -len(типові[x])):
        print("  %-22s %d · %s" % (к, len(типові[к]), "; ".join(типові[к][:3])))
    print("  значень з типовим: %d · місць: %d" % (len(типові), sum(map(len, типові.values()))))
    print("== визначення: функції, що пишуть значення не копією (≥3)")
    for к in sorted(визначення, key=lambda x: -len(визначення[x])):
        if len(визначення[к]) >= 3:
            print("  %-22s %d · %s" % (к, len(визначення[к]), "; ".join("%s:%s" % x for x in
                                                                          sorted(визначення[к])[:4])))
    print("  значень з ≥2 визначеннями: %d з %d ключів" % (sum(1 for в in визначення.values() if len(в) >= 2),
                                                           len(кл)))
    print("== без_читача: поле паспорта без читача-правила поза провідником; дріт — у ПОЛЯ_ВИПАДКУ чи день, "
          "картка — `показ`, модель — питають у мовної моделі (`мова`/`схема`, не `лише_код`)")
    ПП = _імпорт("паспорт_поля").ПОЛЯ_ПАСПОРТА
    ДР = _імпорт("дріт_моделі")
    день = set(_імпорт("протокол").ДЕНЬ["поля"])
    без, губиться = [], []
    for к, з in ПП.items():
        if к.startswith("@"):
            continue
        ч = {x for кк in (к, з.get("поле")) if кк in читачі for x in читачі[кк] if os.path.basename(x[0]) not in ПРОВІД}
        if ч:
            continue
        дріт = к in ДР.ПОЛЯ_ВИПАДКУ or з.get("поле") in день
        картка = bool(з.get("показ")) or _у_js(к) or _у_js(з.get("поле"))
        модель = bool(з.get("мова") or з.get("схема")) and not з.get("лише_код")
        без.append(к)
        if модель and not дріт and not картка:
            губиться.append(к)
        print("  %-20s дріт %s · картка %s · модель %s · читачі-провідники %d" % (
            к, "так" if дріт else "ні", "так" if картка else "ні", "так" if модель else "ні",
            len({x for кк in (к, з.get("поле")) if кк in читачі for x in читачі[кк]})))
    print("  без читача-правила: %d · з них питають у моделі, а нема ні на дроті, ні на картці: %d — %s" % (
        len(без), len(губиться), ", ".join(губиться)))
    print("== показ_типове: поле вводу з типовим value")
    пт = показ_типові()
    for ід, з, н in пт:
        print("  %s = %s (показ.html:%d)" % (ід, з, н))
    print("сигналів: переклад %d · поріг %d · типове %d · без_читача %d · показ_типове %d" % (
        len(сл), len(пороги), len(типові), len(без), len(пт)))


def друк_покриття(шлях):
    текст = open(шлях, encoding="utf-8").read()
    ід_у_таблиці = set(re.findall(r"^\|\s*`?(г:[^|`\s]+)`?\s*\|", текст, re.M))
    for р in re.findall(r"ід:\s*([^\n]+)", текст):
        ід_у_таблиці.update(x.strip(" `.;") for x in р.split(",") if x.strip(" `.;").startswith("г:"))
    од = одиниці()
    покриті = [x for x in од if x[0] in ід_у_таблиці]
    види = defaultdict(lambda: [0, 0])
    for ід, _, _ in од:
        види[ід.split(":")[1]][1] += 1
        if ід in ід_у_таблиці:
            види[ід.split(":")[1]][0] += 1
    print("покриття вердиктами: %d з %d (%.0f %%) · %s" % (len(покриті), len(од), 100.0 * len(покриті) / len(од),
          " · ".join("%s %d/%d" % (к, а, б) for к, (а, б) in sorted(види.items()))))


def main():
    п = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    п.add_argument("--одиниці", action="store_true")
    п.add_argument("--сигнали", action="store_true")
    п.add_argument("--перелік")
    п.add_argument("--паспорт", action="store_true", help="таблиця полів паспорта з сигналом класу (markdown)")
    а = п.parse_args()
    os.chdir(ДЖ)
    if а.одиниці:
        друк_одиниць()
    if а.сигнали:
        друк_сигналів()
    if а.паспорт:
        print("| ід | джерело | читачів-правил | дріт | показ | типових | пороги | сигнал |")
        print("|---|---|---|---|---|---|---|---|")
        for к, дж, ч, д, п_, т, пр, сг in таблиця_паспорта():
            print("| г:паспорт:%s | %s | %d | %s | %s | %d | %s | %s |" % (к, дж, ч, "так" if д else "ні",
                  "так" if п_ else "ні", т, ",".join(map(str, пр)) or "—", сг))
    if а.перелік:
        друк_покриття(os.path.join(КОРІНЬ, а.перелік))
    return 0


if __name__ == "__main__":
    sys.exit(main())
