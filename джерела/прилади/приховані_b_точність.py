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


КЛАСИ = {"Т1": клас_т1, "Т2": клас_т2, "Т3": клас_т3}


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
