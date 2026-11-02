# -*- coding: utf-8 -*-
"""Приховані вади, частина (б): лічба місць, де код продукту знає більше, ніж може точно порахувати.

Наряд `аудит/наряди/Приховані-розвідка.md`, частина (б); принцип ядра (`AGENTS.md`, власник 01.10): «мовна модель веде
розмову, модель-стилістка збирає образи, код знає лише те, що може точно порахувати». Прилад не судить окреме місце,
лише лічить клас по всіх модулях `status.МОДУЛІ_ПРОДУКТУ`; кожне місце — кандидат, який читає людина чи перевірка.

Класи:
  Т1  слово як вимір: код шукає слово в тексті (регулярка з кирилицею, `"слово" in текст`, `startswith`/`endswith`/
      `find` зі словом, обхід переліку слів модуля з `in`; літерал, схожий на код — `_`, `.`, `[]`, `-` в кінці, —
      не слово) — тлумачить мову сам, а мова — справа мовної моделі;
  Т2  значення, виведене кодом із поля паспорта нагоди чи сцени (поріг, арифметика, таблиця, регулярка, підрядок,
      типове) — логіка й ключі взяті з приладу обсягу `подібні_обсяг.py` (гілка `claude/podibni-rozvidka`, частина б),
      знаменник — ядро, а не верхній рівень `джерела/`;
  Т3  заявлена певність без виміру: ключ `впевненість`/`надійність`/`confidence` з ненульовим числом-літералом — код каже,
      наскільки він певен, не порахувавши цього.

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_b_точність.py              підсумок: рядок на клас, топ модулів
  python3 джерела/прилади/приховані_b_точність.py --клас Т1    усі місця класу (файл:рядок ⇥ що)
Останній рядок — `місць: <N>` (сума класів).
"""
import argparse
import ast
import collections
import io
import json
import os
import re
import sys
import warnings

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")
sys.path.insert(0, ДЖ)
_БУКВИ = re.compile("[A-Za-zА-Яа-яІіЇїЄєҐґ]{3,}")
_КИР = re.compile("[А-Яа-яІіЇїЄєҐґ]")


def _ядро():
    """Файли модулів ядра зі `status.МОДУЛІ_ПРОДУКТУ`."""
    import status
    return [os.path.join(ДЖ, м + ".py") for м in sorted(status.МОДУЛІ_ПРОДУКТУ)]


def _ast(шлях):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(io.open(шлях, encoding="utf-8").read())


def _відн(шлях):
    return os.path.relpath(шлях, КОРІНЬ)


def _число(x):
    if isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool):
        return x.value
    if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub) and _число(x.operand) is not None:
        return -_число(x.operand)
    return None


def _докстрінги(дерево):
    """id вузлів-докстрінгів: їхні рядки — не код."""
    з = set()
    for в in [дерево] + [x for x in ast.walk(дерево)
                         if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]:
        if в.body and isinstance(в.body[0], ast.Expr) and isinstance(в.body[0].value, ast.Constant):
            з.add(id(в.body[0].value))
    return з


# ─────────────────────────────── Т1: слово як вимір ───────────────────────────────
def _слова_колекції(вузол):
    """Слова (≥3 літер) у літералах колекції чи словника."""
    с = set()
    for x in ast.walk(вузол):
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            с |= {w.lower() for w in _БУКВИ.findall(x.value)}
    return с


def _колекції_слів(дерево):
    """Імена модульного рівня, присвоєні колекції з ≥2 різними словами."""
    імена = set()
    for в in дерево.body:
        if isinstance(в, (ast.Assign, ast.AnnAssign)) and isinstance(в.value, (ast.Dict, ast.List, ast.Tuple, ast.Set,
                                                                                ast.Call)):
            if len(_слова_колекції(в.value)) >= 2:
                цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                імена |= {ц.id for ц in цілі if isinstance(ц, ast.Name)}
    return імена


def _код(т):
    """Літерал, схожий на код чи ключ (`довжина_рівень`, `образи[].виконано`, `нейтраль-`), а не на слово мови."""
    return bool(re.search(r"[_.\[\]]|-$", т))


def _літерал_колекція(x):
    return isinstance(x, (ast.Tuple, ast.List, ast.Set, ast.Dict)) or \
        isinstance(x, ast.Constant) and not isinstance(x.value, str)


def клас_т1(файли):
    """Т1 по функціях ядра; одне місце — один вузол."""
    місця = []
    for ф in файли:
        д = _ast(ф)
        док = _докстрінги(д)
        колекції = _колекції_слів(д)
        for в in ast.walk(д):
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute):
                атр = в.func.attr
                корінь = в.func.value
                if атр in ("compile", "search", "match", "fullmatch", "findall", "finditer", "sub", "split") and \
                        isinstance(корінь, ast.Name) and корінь.id == "re" and в.args and \
                        isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str) and \
                        _КИР.search(re.sub(r"\\[a-zA-Z]|\(\?[a-zA-Z]+\)|\[[^]]*\]", "", в.args[0].value)):
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "регулярка зі словами: %s" % в.args[0].value[:50]))
                elif атр in ("startswith", "endswith", "find", "rfind", "index", "count") and в.args and \
                        isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str) and \
                        _БУКВИ.search(в.args[0].value) and _КИР.search(в.args[0].value) and not _код(в.args[0].value):
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "%s(%r)" % (атр, в.args[0].value[:30])))
            elif isinstance(в, ast.Compare) and any(isinstance(о, (ast.In, ast.NotIn)) for о in в.ops):
                лів = в.left
                прав = в.comparators[0]
                if isinstance(лів, ast.Constant) and isinstance(лів.value, str) and id(лів) not in док and \
                        _БУКВИ.search(лів.value) and _КИР.search(лів.value) and not _код(лів.value) and \
                        not _літерал_колекція(прав):
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "підрядок %r in %s" % (лів.value[:30],
                                                                                    ast.unparse(прав)[:40])))
            elif isinstance(в, (ast.GeneratorExp, ast.ListComp, ast.SetComp)):
                for г in в.generators:
                    if isinstance(г.iter, ast.Name) and г.iter.id in колекції and isinstance(г.target, ast.Name):
                        ім = г.target.id
                        if any(isinstance(x, ast.Compare) and isinstance(x.left, ast.Name) and x.left.id == ім and
                               any(isinstance(о, (ast.In, ast.NotIn)) for о in x.ops) for x in ast.walk(в.elt)):
                            місця.append(("%s:%d" % (_відн(ф), в.lineno), "перелік слів %s обходом in" % г.iter.id))
    return місця


# ─────────────────────────────── Т3: певність без виміру ───────────────────────────────
_ПЕВНІСТЬ = re.compile(r"^(впевненість|певність|надійність|confidence|conf)$")


def клас_т3(файли):
    """Ключ певності з ненульовим числом-літералом (0 — чесне «нема виміру»): `dict(впевненість=0.8)`, `{"впевненість": 1.0}`, `x["впевненість"] = 0.6`."""
    місця = []
    for ф in файли:
        for в in ast.walk(_ast(ф)):
            пари = []
            if isinstance(в, ast.Call):
                пари = [(к.arg, к.value) for к in в.keywords if к.arg]
            elif isinstance(в, ast.Dict):
                пари = [(k.value, v) for k, v in zip(в.keys, в.values) if isinstance(k, ast.Constant)]
            elif isinstance(в, ast.Assign):
                пари = [(ц.slice.value, в.value) for ц in в.targets if isinstance(ц, ast.Subscript)
                        and isinstance(ц.slice, ast.Constant)]
            for к, v in пари:
                if isinstance(к, str) and _ПЕВНІСТЬ.match(к) and _число(v):  # 0 — чесне «нема виміру»
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "%s=%r літералом" % (к, _число(v))))
    return місця


# ─────────────────────────────── Т2: виведене з паспорта ───────────────────────────────
def _властивості_json(вузол, шлях, вихід, defs):
    if not isinstance(вузол, dict):
        return
    if "$ref" in вузол and вузол["$ref"].startswith("#/$defs/"):
        return  # посилання на іншу форму — її поля лічить її власний обхід
    for к, в in вузол.get("properties", {}).items():
        вихід.append((шлях + "." + к, в))
        _властивості_json(в, шлях + "." + к, вихід, defs)
    for к in ("items", "additionalProperties"):
        if isinstance(вузол.get(к), dict):
            _властивості_json(вузол[к], шлях + "[]", вихід, defs)
    for к in ("anyOf", "oneOf", "allOf"):
        for x in вузол.get(к, []):
            _властивості_json(x, шлях, вихід, defs)



ЗАГАЛЬНІ = {"value", "quote", "quotes", "code", "text", "id", "kind", "type", "name", "items", "item", "answer",
            "note", "notes", "reason", "why", "ід", "назва", "текст", "код", "решта", "невідомо", "звідки", "запити"}


def _ключі_паспорта():
    """Ключі паспорта й сцени: записи `ПОЛЯ_ПАСПОРТА`, їхні англійські поля й властивості форм сценарію й ходу
    розмови внутрішньої мови (листки), без загальних слів (`ЗАГАЛЬНІ`)."""
    import паспорт_поля
    к = set()
    for ім, з in паспорт_поля.ПОЛЯ_ПАСПОРТА.items():
        if not ім.startswith("@"):
            к.add(ім)
        if isinstance(з, dict) and isinstance(з.get("поле"), str):
            к.add(з["поле"])
    мова = json.load(open(os.path.join(ДЖ, "внутрішня_мова.schema.json"), encoding="utf-8"))
    for ф in ("scenario", "conversation_turn"):
        вузли = []
        _властивості_json(мова["$defs"][ф], ф, вузли, мова["$defs"])
        к |= {ш.rsplit(".", 1)[-1].rstrip("[]") for ш, _ in вузли}
    return {x for x in к if x not in ЗАГАЛЬНІ and len(x) > 2}


def _читання_ключа(в, ключі):
    """Рядковий ключ паспорта, який вузол читає: `x["к"]`, `x.get("к", …)`, аксесор `ф("к", …)`."""
    if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and в.slice.value in ключі:
        return в.slice.value
    if isinstance(в, ast.Call) and в.args and isinstance(в.args[0], ast.Constant) and в.args[0].value in ключі:
        if isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "pop", "setdefault"):
            return в.args[0].value
        if isinstance(в.func, ast.Name):
            return в.args[0].value
    return None


def _ознаки_виведення(функція):
    """Ознаки, що функція виводить значення сама: поріг (порівняння з числом), арифметика, регулярка, підрядок,
    типове (`.get(к, x)` з x не None, `… or x`), таблиця відповідностей."""
    о = set()
    for в in ast.walk(функція):
        # таблиця відповідностей: `ТАБЛИЦЯ[x]` чи `ТАБЛИЦЯ.get(x…)` зі змінним ключем (ім'я великими літерами)
        if isinstance(в, ast.Subscript) and isinstance(в.value, ast.Name) and в.value.id.isupper() \
                and not isinstance(в.slice, ast.Constant):
            о.add("таблиця")
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" \
                and isinstance(в.func.value, ast.Name) and в.func.value.id.isupper() and в.args \
                and not isinstance(в.args[0], ast.Constant):
            о.add("таблиця")
        if isinstance(в, ast.Compare):
            if _порівняння_з_порогом(в):
                о.add("поріг")
            if any(isinstance(оп, (ast.In, ast.NotIn)) for оп in в.ops) and isinstance(в.left, ast.Constant) \
                    and isinstance(в.left.value, str):
                о.add("підрядок")
        elif isinstance(в, ast.BinOp) and isinstance(в.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)) \
                and not (isinstance(в.left, ast.Constant) and isinstance(в.left.value, str)):
            if _число(в.left) is not None or _число(в.right) is not None:
                о.add("арифметика")
        elif isinstance(в, ast.Call):
            ф = в.func
            if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id == "re":
                о.add("регулярка")
            if isinstance(ф, ast.Attribute) and ф.attr in ("search", "match", "fullmatch", "findall", "sub", "finditer"):
                о.add("регулярка")
            if isinstance(ф, ast.Attribute) and ф.attr in ("startswith", "endswith", "find", "split"):
                о.add("підрядок")
            if isinstance(ф, ast.Attribute) and ф.attr == "get" and len(в.args) == 2 and isinstance(в.args[1], ast.Constant) \
                    and в.args[1].value not in (None, "", 0, False):
                о.add("типове")
        elif isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or) and isinstance(в.values[-1], ast.Constant) \
                and в.values[-1].value not in (None, "", False):
            о.add("типове")
    return о


def _порівняння_з_порогом(в):
    """Порівняння <, <=, >, >= з числом-літералом чи з порогом за іменем великими літерами (`ПОРІГ`,
    `РЕЄСТР["к"]["val"]`)."""
    if not any(isinstance(оп, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for оп in в.ops):
        return False
    for x in [в.left] + в.comparators:
        if _число(x) is not None:
            return True
        корінь = x
        while isinstance(корінь, (ast.Subscript, ast.Attribute)):
            корінь = корінь.value
        if isinstance(корінь, ast.Name) and корінь.id.isupper() and корінь is not x or (
                isinstance(x, ast.Name) and x.id.isupper()):
            return True
    return False


def частина_б(файли):
    """Функція — одиниця, коли до неї доходить ключ паспорта — читанням (`x["к"]`, `.get("к")`, аксесор `ф("к")`)
    чи аргументом виклику (позиційним чи іменованим; у виклику — читання чи локальне ім'я, присвоєне з читання), потік
    між функціями — до нерухомої точки за іменем функції, — і в ній є ознака виведення."""
    ключі = _ключі_паспорта()
    функції = [(ф, в) for ф in файли for в in ast.walk(_ast(ф))
               if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))]
    читає = {}
    for ф, в in функції:
        к = {к for x in ast.walk(в) if (к := _читання_ключа(x, ключі))}
        if к:
            читає[(ф, в.lineno)] = к
    носії = {}  # ім'я функції → {позиція чи ім'я параметра: ключі}

    def мітки(вираз, мічені):
        з = {к for y in ast.walk(вираз) if (к := _читання_ключа(y, ключі))}
        for y in ast.walk(вираз):
            if isinstance(y, ast.Name) and y.id in мічені:
                з |= мічені[y.id]
        return з

    for _ in range(6):
        змін = False
        for ф, в in функції:
            мічені = {}
            параметри = в.args.posonlyargs + в.args.args
            for поз, к in носії.get(в.name, {}).items():
                ім = параметри[поз].arg if isinstance(поз, int) and поз < len(параметри) else поз
                if isinstance(ім, str):
                    мічені.setdefault(ім, set()).update(к)
            for y in ast.walk(в):
                if isinstance(y, ast.Assign):
                    з = {к for z in ast.walk(y.value) if (к := _читання_ключа(z, ключі))}
                    if з:
                        for ц in y.targets:
                            if isinstance(ц, ast.Name):
                                мічені.setdefault(ц.id, set()).update(з)
            if not (мічені or (ф, в.lineno) in читає):
                continue
            for x in ast.walk(в):
                if not isinstance(x, ast.Call):
                    continue
                ім = x.func.id if isinstance(x.func, ast.Name) else x.func.attr if isinstance(x.func, ast.Attribute) else None
                if not ім or ім in ("get", "pop", "setdefault", "int", "float", "str", "round", "len", "dict", "list",
                                    "append", "update", "join", "format", "isinstance", "set", "tuple", "sorted", "any", "all"):
                    continue
                пари = list(enumerate(x.args)) + [(кв.arg, кв.value) for кв in x.keywords if кв.arg]
                for поз, а in пари:
                    з = мітки(а, мічені)
                    if з and not з <= носії.get(ім, {}).get(поз, set()):
                        носії.setdefault(ім, {}).setdefault(поз, set()).update(з)
                        змін = True
        if not змін:
            break
    одиниці = []
    for ф, в in функції:
        прямо = читає.get((ф, в.lineno), set())
        аргументом = set().union(*носії.get(в.name, {}).values()) - прямо if в.name in носії else set()
        if not (прямо or аргументом):
            continue
        ознаки = _ознаки_виведення(в)
        if not ознаки:
            continue
        опис = "читає %s" % ",".join(sorted(прямо)[:8]) if прямо else ""
        if аргументом:
            опис += ("; " if опис else "") + "аргументом %s" % ",".join(sorted(аргументом)[:6])
        одиниці.append((в.name, "%s:%d" % (_відн(ф), в.lineno),
                        "%s · %s" % (опис, ",".join(sorted(ознаки)))))
    return одиниці


def клас_т2(файли):
    """Т2: логіка частини б приладу обсягу «Подібні», над файлами ядра."""
    return [(місце, опис) for _, місце, опис in частина_б(файли)]


# ─────────────────────────────── Т4–Т6: продовження (друга сесія частини б) ───────────────────────────────
_ОЦІНКА = re.compile(r"оцін|бал|score|ваг|сил|ймовірн|впевнен|певн|рейтинг|відповідн|схож|якіст|"
                     r"придатн|доречн|weight|prob|conf", re.I)


def _імена(вузол):
    """Імена, атрибути й рядкові ключі виразу — щоб зрозуміти, яку величину він несе."""
    з = []
    for x in ast.walk(вузол):
        if isinstance(x, ast.Name):
            з.append(x.id)
        elif isinstance(x, ast.Attribute):
            з.append(x.attr)
        elif isinstance(x, ast.Subscript) and isinstance(x.slice, ast.Constant) and isinstance(x.slice.value, str):
            з.append(x.slice.value)
        elif isinstance(x, ast.Call) and isinstance(x.func, ast.Name):
            з.append(x.func.id)
    return з


def клас_т4(файли):
    """Т4 число точніше за вимір: `round(x, n≥2)`, формат `:.Nf`/`%.Nf` (N≥2) над оцінкою, вагою, силою, часткою чи
    певністю — величиною, яку код не міряв, а склав із правил (ім'я виразу за `_ОЦІНКА`). Округлення фізичної
    величини (Lab, ΔE, частка пікселів — виміряні) місцем не є і в лічбу не йде."""
    місця = []
    for ф in файли:
        for в in ast.walk(_ast(ф)):
            вираз, знаків = None, 0
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "round" and len(в.args) == 2 \
                    and isinstance(в.args[1], ast.Constant) and isinstance(в.args[1].value, int) and в.args[1].value >= 2:
                вираз, знаків = в.args[0], в.args[1].value
            elif isinstance(в, ast.FormattedValue) and в.format_spec is not None:
                спец = ast.unparse(в.format_spec)
                м = re.search(r"\.(\d)f", спец)
                if м and int(м.group(1)) >= 2:
                    вираз, знаків = в.value, int(м.group(1))
            if вираз is None:
                continue
            імена = _імена(вираз)
            if any(_ОЦІНКА.search(і) for і in імена) and not any(re.search(r"(^|_)(de|lab|delta|ΔE|de00|L|hue|chroma|"
                                                                          r"піксел|площ|світлот|насич)", і, re.I)
                                                                for і in імена):
                місця.append(("%s:%d" % (_відн(ф), в.lineno), "%d знаків над %s" % (знаків, ast.unparse(вираз)[:40])))
    return місця


_СВІТ = re.compile(r"(^|_)(місяц\w*|month|температ\w*|темп|temp|temperature\w*|t_?min|t_?max|зріст\w*|height|вік|age|ваг[аи]_тіла|"
                   r"weight_kg|ціна|price|годин\w*|hour|weekday|день_тижня|широт\w*|lat|сезон_номер|uv\w*|"
                   r"вологіст\w*|humidity|вітер|wind\w*|опади_мм|precip\w*)($|_)", re.I)


def _світовий(x):
    if isinstance(x, ast.Name):
        return _СВІТ.search(x.id) and x.id
    if isinstance(x, ast.Attribute):
        return _СВІТ.search(x.attr) and x.attr
    if isinstance(x, ast.Subscript) and isinstance(x.slice, ast.Constant) and isinstance(x.slice.value, str):
        return _СВІТ.search(x.slice.value) and x.slice.value
    if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "get" and x.args \
            and isinstance(x.args[0], ast.Constant) and isinstance(x.args[0].value, str):
        return _СВІТ.search(x.args[0].value) and x.args[0].value
    return None


def _корінь_великий(x):
    """Поріг за іменем великими літерами: `ПОРІГ`, `_НАГОДА.МОРОЗ_ДО_C`, `РЕЄСТР["к"]`."""
    while isinstance(x, (ast.Subscript, ast.Attribute)):
        if isinstance(x, ast.Attribute) and x.attr.isupper():
            return True
        x = x.value
    return isinstance(x, ast.Name) and x.id.lstrip("_").isupper()


def клас_т5(файли):
    """Т5 стала світу в коді: виміряний вхід світу (місяць, температура, вітер, зріст, вік, ціна, година) код
    переводить у висновок порогом (літерал — без джерела; ім'я реєстру — джерело є, правило звіряє частина в) чи
    таблицею місяців — знання світу й стилю живе в коді, а не в базі
    знань чи моделі (сезон за місяцем бреше в теплий жовтень)."""
    місця = []
    for ф in файли:
        for в in ast.walk(_ast(ф)):
            if isinstance(в, ast.Compare) and any(isinstance(о, (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.In))
                                                  for о in в.ops):
                сторони = [в.left] + в.comparators
                світ = [с for с in сторони if _світовий(с)]
                числа = [с for с in сторони if _число(с) is not None] + [
                    x for с in сторони if isinstance(с, (ast.Tuple, ast.List, ast.Set)) for x in с.elts
                    if _число(x) is not None]
                реєстр = [с for с in сторони if not _світовий(с) and _корінь_великий(с)]
                if світ and числа:
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "поріг світу %s ⋚ %r літералом" % (
                        _світовий(світ[0]), _число(числа[0]))))
                elif світ and реєстр:
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "поріг світу %s ⋚ %s (реєстр)" % (
                        _світовий(світ[0]), ast.unparse(реєстр[0])[:30])))
            elif isinstance(в, ast.Dict) and len(в.keys) >= 3 and all(
                    isinstance(k, ast.Constant) and isinstance(k.value, int) and not isinstance(k.value, bool)
                    and 1 <= k.value <= 12 for k in в.keys) and any(isinstance(v, ast.Constant) and
                                                                    isinstance(v.value, str) for v in в.values):
                місця.append(("%s:%d" % (_відн(ф), в.lineno), "таблиця місяців → %r" % (в.values[0].value
                              if isinstance(в.values[0], ast.Constant) else "…")))
    return місця


_КОД_КЛЮЧ = re.compile(r"^[a-z0-9_\-]+$|^[а-яіїєґ0-9]+(_[а-яіїєґ0-9]+)+$")
_РЕЧЕННЯ = re.compile(r"[А-ЯІЇЄҐа-яіїєґʼ'’]{2,}")


def _фраза(т, слів):
    return isinstance(т, str) and len(_РЕЧЕННЯ.findall(т)) >= слів and " " in т.strip()


def клас_т6(файли):
    """Т6 код пише текст жінці сам: (а) таблиця «код → фраза» (словник ≥3 записів, ключі — коди, значення — кирилична
    фраза ≥2 слів) — переклад коду моделі текстом, якого модель не бачила, друге визначення значення; (б) речення
    (≥4 кириличні слова) значенням поля, що зветься як текст для людини (`текст`, `репліка`, `чому`, `пояснення`,
    `питання`, `порада`, `підказка`, `повідомлення`, `заголовок`, `причина`) — фразу складає код, не мовна модель."""
    поля = re.compile(r"^(текст|репліка|чому|пояснення|питання|порада|підказка|повідомлення|заголовок|причина|"
                      r"text|message|hint|why|reason|label|title|рядок_жінці|для_жінки|жінці)(_|$)", re.I)
    місця = []
    for ф in файли:
        д = _ast(ф)
        док = _докстрінги(д)
        for в in ast.walk(д):
            if isinstance(в, ast.Dict) and len(в.keys) >= 3:
                пари = [(k.value, v.value) for k, v in zip(в.keys, в.values)
                        if isinstance(k, ast.Constant) and isinstance(k.value, str) and isinstance(v, ast.Constant)]
                коди = [k for k, v in пари if _КОД_КЛЮЧ.match(k) and _фраза(v, 2)]
                if len(коди) >= 3 and len(коди) >= len(в.keys) // 2:
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "таблиця код→фраза, %d записів (%s…)" % (
                        len(коди), коди[0][:20])))
            пари = []
            if isinstance(в, ast.Call):
                пари = [(к.arg, к.value) for к in в.keywords if к.arg]
            elif isinstance(в, ast.Dict):
                пари = [(k.value, v) for k, v in zip(в.keys, в.values) if isinstance(k, ast.Constant)
                        and isinstance(k.value, str)]
            for к, v in пари:
                if not поля.match(к) or id(v) in док:
                    continue
                текст = v.value if isinstance(v, ast.Constant) else " ".join(
                    x.value for x in v.values if isinstance(x, ast.Constant) and isinstance(x.value, str)) \
                    if isinstance(v, ast.JoinedStr) else None
                if _фраза(текст, 4):
                    місця.append(("%s:%d" % (_відн(ф), в.lineno), "%s= речення коду: %s" % (к, текст[:40])))
    return місця


КЛАСИ = {"Т1": клас_т1, "Т2": клас_т2, "Т3": клас_т3, "Т4": клас_т4, "Т5": клас_т5, "Т6": клас_т6}


def main():
    п = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    п.add_argument("--клас", default=None, choices=sorted(КЛАСИ))
    а = п.parse_args()
    файли = _ядро()
    if а.клас:
        місця = КЛАСИ[а.клас](файли)
        for м, що in місця:
            print("%s\t%s" % (м, що))
        print("місць: %d" % len(місця))
        return 0
    разом = 0
    for к, ф in КЛАСИ.items():
        місця = ф(файли)
        разом += len(місця)
        модулі = collections.Counter(м.split(":")[0].rsplit("/", 1)[-1] for м, _ in місця)
        print("%s місць %-5d модулів %-3d топ: %s" % (к, len(місця), len(модулі),
                                                   ", ".join("%s %d" % x for x in модулі.most_common(6))))
    print("модулів ядра обійдено: %d" % len(файли))
    print("місць: %d" % разом)
    return 0


if __name__ == "__main__":
    sys.exit(main())
