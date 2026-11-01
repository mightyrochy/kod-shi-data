# -*- coding: utf-8 -*-
"""прилади/корінь_е2_межі_дріт.py — п.6 приладу кореня Е2-межі: «дріт без виду» (паспорт `аудит/корені/Е2-межі.md`,
«Наступний крок»; рішення менеджера 31.10: Г6, рядок 12009, і певність літералом, рядок 11935). Помічник
`корінь_е2_межі.py`: той кличе `місця_п6` і додає місця пунктом 6.

КЛАС (паспорт): поле входу моделі (оголошення збирача), підпис якого приписує значення їй чи факту, коли писач —
функція коду, що дає значення не копією її слова чи дотику (типове `or`, поріг, вивід з іншого поля, вимір коду).

ЯК ЛІЧИТЬ (від значення, а не від імен):
  1. Підмети — поля `Оголошення.вхід` усіх модулів `джерела/` (імпорт модулів, що їх пишуть) і легенди ключів дроту
     (словник «ключ → опис англійською»), чий підпис `що` каже «her …», «she chose / named / kept …», «what she …»,
     «inside her palette», «as fact», а `як` — «her own», «against her …», і ніде не каже, що значення дав код, модель
     чи типове (`МІТКА_КОДУ`). Поле, що несе поля з власними підписами (`case`, `day`), — контейнер: його поля лічаться
     кожне за своїм підписом.
  2. Писачі ключа поля (присвоєння `x["k"]`, словник, `dict(k=…)`, `.setdefault`, `.update`, пари в циклі над
     літералом) → потік значення назад: присвоєння, параметр (типове, аргументи викликачів), повернення функції
     продукту, читання ключа (запис тієї самої функції, інакше писачі того ключа — межа функцій), реекспорт.
     Джерело коду — стала (рядок чи число), типове `.get`/параметра, поріг чи вивід порівнянням, вимір (арифметика,
     `max`/`min`/`sum`/`len`/`Counter`/`median`). Копія її слова чи дотику — не джерело: потік іде далі, а де значення
     приходить з її поля, не стаючи сталою коду, місця нема.
  3. `x.setdefault("<поле паспорта>", <значення коду>)` — код ставить у її паспорт те, чого вона не дала.
  4. `впевненість=<число>` літералом у записі без виду (`бік`, `джерело`, `правило`) — певність, яку поставив код.
  5. Вид губиться: зворотний зріз писача поля з підписом «її» читає вид значення (`джерело_полів`, `типові_поля`, суд
     виду факту), а дріт несе відібране без виду.
МІСЦЕ — функція-писач джерела коду, на рядку першого такого джерела в ній (правила 3–5 — рядок самого виразу).
Індекс — усі модулі `джерела/` (потік іде і через модулі поза списком продукту, напр. реекспорт `pipeline`); місця —
лише в модулях продукту (`корінь_е2_межі.модулі_продукту`), як і решта пунктів приладу.

МЕЖІ ПОТОКУ (числа нижче — щоб загальні ключі не зливали чужих потоків): виклики — до 4 рівнів, стрибки ключем —
до 3; ключ, який пишуть понад 12 місць, — лише з модулів, повʼязаних імпортом із читачем, чи писачі тієї самої форми
запису; ключ без перекладу на дріт, не підмет і не приватний (`_гілка`) — лише якщо його пишуть ≤3 місця.
"""
import ast
import importlib
import os
import re
import sys
import warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

ДІЯ_ЇЇ = r"(?:chose|named|kept|asked|said|wants|tapped|picked|wrote|described|refused|rejected|changed|holds)"
ЇЙ_ПІДПИС = re.compile(
    r"\bher\s+(?:own\s+|exact\s+)?«?(?:words?|wish(?:es)?|request|style|intent|choice|registers?)\b|"
    r"\bwhat she\s+(?:\w+\s+)?%s\b|\b\w+ she %s\b|\bshe (?:kept|did)\b|\bwith the tiles\b|"
    r"\binside her palette\b|\bas facts?\b" % (ДІЯ_ЇЇ, ДІЯ_ЇЇ), re.I)
ЇЙ_ПІДПИС_ЯК = re.compile(r"\bher own\b|\binside her palette\b|\bagainst her\s+«?[a-z_]+", re.I)
МІТКА_КОДУ = re.compile(r"\bthe code\b|\bcode's\b|\bby (?:the )?code\b|"
                        r"\bcode (?:chose|set|picked|suggested|derived|computed|measured|estimated)\b|"
                        r"\bmeasur|\bdefault|\bassum|\bnot her\b|\bshe did not\b|\bshe neither\b|"
                        r"\bestimat|\bguess|\binterpret|\bderived\b|\bcomputed\b|\bmodel's\b|\blanguage model\b", re.I)
НЕВІДОМЕ = {"", "unknown", "невідомо", "не_знаю", "none", "null", "—", "-"}
ВИМІР_ФУНКЦІЇ = {"max", "min", "sum", "len", "Counter", "most_common", "mean", "median"}  # round/abs — копія числа
КОПІЯ_ФУНКЦІЇ = {"str", "list", "tuple", "set", "sorted", "reversed", "frozenset", "dict", "int", "float", "bool",
                 "next", "iter", "filter", "map", "enumerate", "zip", "deepcopy", "copy"}
ТЕКСТ_МЕТОДИ = {"strip", "lstrip", "rstrip", "lower", "upper", "casefold", "split", "rsplit", "splitlines", "title",
                "capitalize", "copy", "items", "values", "keys", "get", "pop", "replace",
                "removeprefix", "removesuffix"}
ГЛИБИНА_ВИКЛИКІВ = 4
ГЛИБИНА_КЛЮЧІВ = 3
ПИСАЧІВ_КЛЮЧА = 12          # ключ, який пишуть більше місць, — загальний: стрибок по ньому зливав би чужі потоки


def _ім(в):
    if isinstance(в, ast.Name):
        return в.id
    if isinstance(в, ast.Attribute):
        л = _ім(в.value)
        return (л + "." if л else "") + в.attr
    return ""


def _рядок(в):
    return в.value if isinstance(в, ast.Constant) and isinstance(в.value, str) else None


def _значуща_стала(в):
    """Стала, яку код ставить значенням: не порожня, не «невідомо», не опис (з пробілами)."""
    if not isinstance(в, ast.Constant) or в.value is None:
        return False
    if isinstance(в.value, str):
        с = в.value.strip()
        return bool(с) and с.lower() not in НЕВІДОМЕ and " " not in с
    # прапор `True/False` — так/ні про факт (копія умови), не значення поля
    return isinstance(в.value, (int, float)) and not isinstance(в.value, bool)


def _значення_коду(з):
    """Значення `.setdefault`, яке ставить код: не копія змінної чи поля, не порожнє (`[]`, `{}`, `""`, None)."""
    if isinstance(з, (ast.Name, ast.Subscript, ast.Attribute)):
        return False
    if isinstance(з, (ast.List, ast.Tuple, ast.Set)) and not з.elts or isinstance(з, ast.Dict) and not з.keys:
        return False
    return not isinstance(з, ast.Constant) or _значуща_стала(з)


class ДрітБезВиду:
    """Поле входу моделі, чий підпис приписує значення їй чи факту (без мітки коду), і писач — функція коду, що дає
    значення не копією її слова чи дотику. Місце — функція-писач (рядок першого джерела коду в ній)."""

    def __init__(self, а, джерела):
        self.а, self.дж = а, джерела
        self.писачі = {}            # ключ → [(мод, функція, вираз, рядок)]
        self.псевдоніми = {}        # ключ дроту → {внутрішній ключ}
        self.функція_вузла = {}     # (мод, ім) → вузол
        self.присвоєння = {}        # (мод, ім) → {імʼя: [вираз]}
        self.сховища = {}           # (мод, ім) → {(змінна, ключ): [вираз]}
        self.цикли = {}             # (мод, ім) → {імʼя: вираз ітерації}
        self.параметри = {}         # (мод, ім) → {імʼя: типове | None}
        self.сталі = {}             # мод → {імʼя: вираз верхнього рівня}
        self.сусідні = {}           # id(вираз писача) → ключі того самого запису
        self.запис = {}             # id(вираз писача) → інші значення того самого запису
        self.заповнення = set()     # id(вираз) у `.setdefault(ключ, вираз)`: значення, коли поля нема
        self.індекс()
        self.паспорт = set()
        дер = self.а.м.get("паспорт_поля")
        for в in (дер.дерево.body if дер else []):
            if isinstance(в, ast.Assign) and _ім(в.targets[0]) == "ПОЛЯ_ПАСПОРТА" and isinstance(в.value, ast.Dict):
                self.паспорт = {_рядок(к) for к in в.value.keys if _рядок(к) and not _рядок(к).startswith("@")}
        переклад = {д for д, вн in self.псевдоніми.items() if вн & self.паспорт}
        self.паспорт |= переклад
        self.дозволені = set()

    # ── індекс ──
    def індекс(self):
        for мод in self.а.м.values():
            сталі = {}
            for в in мод.дерево.body:
                if isinstance(в, ast.Assign):
                    for ц in в.targets:
                        if isinstance(ц, ast.Name):
                            сталі[ц.id] = в.value
                        elif isinstance(ц, ast.Tuple) and isinstance(в.value, ast.Tuple) \
                                and len(ц.elts) == len(в.value.elts):
                            for ім_, з_ in zip(ц.elts, в.value.elts):
                                if isinstance(ім_, ast.Name):
                                    сталі[ім_.id] = з_
                    if isinstance(в.value, ast.Dict) and в.value.keys and all(
                            _рядок(к) and _рядок(з) for к, з in zip(в.value.keys, в.value.values)):
                        пари = [(_рядок(к), _рядок(з)) for к, з in zip(в.value.keys, в.value.values)]
                        if all(re.match(r"^[a-z][a-z0-9_]*$", з) for _, з in пари) and \
                                sum(bool(re.search(r"[а-яіїєґ]", к)) for к, _ in пари) * 2 > len(пари):
                            for к, з in пари:
                                self.псевдоніми.setdefault(з, set()).add(к)
            self.сталі[мод.ім] = сталі
            for ім, ф in мод.функції.items():
                self.індекс_функції(мод, ім, ф)

    def індекс_функції(self, мод, ім, ф):
        к = (мод.ім, ім)
        self.функція_вузла[к] = ф
        прис, схов, цикл, пізні = {}, {}, {}, []
        а = ф.args
        типові = [None] * (len(а.posonlyargs + а.args) - len(а.defaults)) + list(а.defaults)
        пар = {x.arg: д for x, д in zip(а.posonlyargs + а.args, типові)}
        пар.update({x.arg: д for x, д in zip(а.kwonlyargs, а.kw_defaults)})
        self.параметри[к] = пар
        for в in ast.walk(ф):
            if isinstance(в, ast.Assign):
                for ц in в.targets:
                    self.ціль_присвоєння(ц, в.value, прис, схов)
                    if isinstance(ц, ast.Subscript) and _рядок(ц.slice):
                        self.писачі.setdefault(_рядок(ц.slice), []).append((мод.ім, ім, в.value, в.lineno))
                        if isinstance(ц.value, ast.Name):
                            пізні.append((в.value, ц.value.id))
            elif isinstance(в, (ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                self.ціль_присвоєння(в.target, в.value, прис, схов)
            elif isinstance(в, ast.NamedExpr):
                прис.setdefault(в.target.id, []).append(в.value)
            elif isinstance(в, ast.For):
                пари_ = isinstance(в.target, ast.Tuple) and isinstance(в.iter, (ast.Tuple, ast.List)) and в.iter.elts \
                    and all(isinstance(е, ast.Tuple) and len(е.elts) == len(в.target.elts) for е in в.iter.elts)
                if пари_:
                    # `for ключ, v in (("register", …), …)`: змінна — лише свій елемент кожної пари
                    for і, н in enumerate(в.target.elts):
                        if isinstance(н, ast.Name):
                            цикл.setdefault(н.id, []).extend(е.elts[і] for е in в.iter.elts)
                else:
                    for н in ast.walk(в.target):
                        if isinstance(н, ast.Name):
                            цикл.setdefault(н.id, []).append(в.iter)
                # пари «ключ — значення» в циклі над літералом: (("register", вираз), ("branch", вираз))
                if isinstance(в.iter, (ast.Tuple, ast.List)):
                    пари = frozenset(_рядок(е.elts[0]) for е in в.iter.elts
                                     if isinstance(е, ast.Tuple) and len(е.elts) == 2 and _рядок(е.elts[0]))
                    for е in в.iter.elts:
                        if isinstance(е, ast.Tuple) and len(е.elts) == 2 and _рядок(е.elts[0]):
                            self.сусідні[id(е.elts[1])] = пари
                        if isinstance(е, ast.Tuple) and len(е.elts) == 2 and _рядок(е.elts[0]) \
                                and not isinstance(е.elts[1], ast.Constant):
                            self.писачі.setdefault(_рядок(е.elts[0]), []).append((мод.ім, ім, е.elts[1], е.lineno))
            elif isinstance(в, ast.Dict):
                кк = frozenset(_рядок(x) for x in в.keys if _рядок(x))
                for кл, з in zip(в.keys, в.values):
                    self.сусідні[id(з)] = кк
                    self.запис[id(з)] = [x for x in в.values if x is not з]
                    if _рядок(кл):
                        self.писачі.setdefault(_рядок(кл), []).append((мод.ім, ім, з, з.lineno))
            elif isinstance(в, ast.Call):
                н = _ім(в.func)
                if н == "dict" or н.endswith(".setdefault") or н.endswith(".update"):
                    кк = frozenset(кл.arg for кл in в.keywords if кл.arg)
                    for кл in в.keywords:
                        self.сусідні[id(кл.value)] = кк
                        self.запис[id(кл.value)] = [x.value for x in в.keywords if x is not кл]
                        if н != "dict" and isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                            пізні.append((кл.value, в.func.value.id))
                    for кл in в.keywords:
                        if кл.arg:
                            self.писачі.setdefault(кл.arg, []).append((мод.ім, ім, кл.value, кл.value.lineno))
                if н.endswith(".setdefault") and len(в.args) == 2 and _рядок(в.args[0]):
                    self.писачі.setdefault(_рядок(в.args[0]), []).append((мод.ім, ім, в.args[1], в.lineno))
                    self.заповнення.add(id(в.args[1]))
                    if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                        пізні.append((в.args[1], в.func.value.id))
                    if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                        схов.setdefault((в.func.value.id, _рядок(в.args[0])), []).append(в.args[1])
        self.присвоєння[к], self.сховища[к], self.цикли[к] = прис, схов, цикл
        # сусідні ключі запису, який функція пише по ключу в змінну: усі ключі цієї змінної
        for з, змінна in пізні:
            self.сусідні[id(з)] = self.сусідні.get(id(з), frozenset()) | frozenset(
                кл for (зм, кл) in схов if зм == змінна)

    @staticmethod
    def ціль_присвоєння(ц, значення, прис, схов):
        if isinstance(ц, ast.Name):
            прис.setdefault(ц.id, []).append(значення)
        elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and _рядок(ц.slice):
            схов.setdefault((ц.value.id, _рядок(ц.slice)), []).append(значення)
        elif isinstance(ц, (ast.Tuple, ast.List)):
            for е in ц.elts:
                if isinstance(е, ast.Name):
                    прис.setdefault(е.id, []).append(значення)

    # ── походження значення ──
    def походження(self, к, в, бажані, глибина, ключів, бачені, ланцюг, зв=None):
        """Джерела коду для виразу `в` у функції `к`: [(мод, функція, рядок, вид, ланцюг)].
        `бажані` — ключі, які шукаємо всередині значення (None — значення цілком)."""
        мітка = (к, id(в), frozenset(бажані or ()))
        if мітка in бачені or в is None:
            return []
        бачені.add(мітка)
        мод, ім = к
        вих = []
        дод = lambda рядок, вид: вих.append((мод, ім, рядок, вид, ланцюг))
        if isinstance(в, ast.Constant):
            if бажані is None and _значуща_стала(в):
                дод(в.lineno, "стала %r" % (в.value,))
            return вих
        if isinstance(в, ast.Name) and зв and ("@" + в.id) in зв:
            # змінна генератора: лише ітерація свого генератора
            return self.походження(к, зв["@" + в.id], бажані, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(в, ast.Name):
            зв = self.пар(зв)
            # записи ключами в цю змінну (`о["chosen_by"] = …`) — теж її значення
            for (зм, кл), зз_ in self.сховища.get(к, {}).items():
                if зм == в.id and (бажані is None or кл in бажані):
                    for з in зз_[:6]:
                        вих += self.походження(к, з, None, глибина, ключів, бачені, ланцюг, зв)
            if в.id in self.присвоєння.get(к, {}):
                for з in self.присвоєння[к][в.id][:6]:
                    вих += self.походження(к, з, бажані, глибина, ключів, бачені, ланцюг, зв)
                if в.id not in self.параметри.get(к, {}):
                    return вих
            if в.id in self.цикли.get(к, {}):
                for іт in self.цикли[к][в.id][:12]:
                    вих += self.походження(к, іт, бажані, глибина, ключів, бачені, ланцюг, зв)
                return вих
            if в.id in self.параметри.get(к, {}):
                д = self.параметри[к][в.id]
                if зв is not None and в.id in зв:
                    кк, арг, зз = зв[в.id]
                    return вих + self.походження(кк, арг, бажані, глибина, ключів, бачені, ланцюг, зз)
                # типове параметра — значення, лише коли виклик його не дає (цей чи хоч один із відомих)
                сайти = self.виклики_функції().get(к, []) if зв is None else []
                діє = зв is not None or not сайти or any(в.id not in self.привʼязати(к, кк, вк, None)
                                                          for кк, вк in сайти)
                if діє and бажані is None and д is not None and _значуща_стала(д):
                    дод(д.lineno, "типове параметра `%s=%r`" % (в.id, д.value))
                if зв is None:
                    вих += self.викликачі(к, в.id, бажані, глибина, ключів, бачені, ланцюг)
                return вих
            з = self.стала(мод, в)
            if бажані is None and isinstance(з, ast.Constant) and _значуща_стала(з):
                дод(в.lineno, "стала модуля `%s`" % в.id)
            return вих
        if isinstance(в, ast.Attribute):
            з = self.стала(мод, в)
            if бажані is None and isinstance(з, ast.Constant) and _значуща_стала(з):
                дод(в.lineno, "стала модуля `%s`" % _ім(в))
            return вих
        if isinstance(в, ast.Subscript):
            ключ = _рядок(в.slice)
            if isinstance(в.slice, (ast.Constant, ast.Slice, ast.UnaryOp)) and ключ is None:
                return self.походження(к, в.value, бажані, глибина, ключів, бачені, ланцюг, зв)
            if ключ is not None:
                return self.читання_ключа(к, в.value, ключ, None, бажані, глибина, ключів, бачені, ланцюг, в.lineno, зв)
            # таблиця перекладу: МАПА[змінна] — копія змінної; інше динамічне читання — без джерела
            таблиця = _ім(в.value).rsplit(".", 1)[-1]
            if таблиця.isupper() or таблиця.lstrip("_").isupper():
                return self.походження(к, в.slice, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, ast.BoolOp):
            for з in в.values:
                вих += self.походження(к, з, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, ast.IfExp):
            return self.походження(к, в.body, бажані, глибина, ключів, бачені, ланцюг, зв) + \
                self.походження(к, в.orelse, бажані, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(в, ast.Compare):
            if бажані is None:
                чис = any(isinstance(с, ast.Constant) and isinstance(с.value, (int, float)) and not isinstance(с.value, bool)
                          for с in [в.left] + в.comparators)
                дод(в.lineno, "поріг" if чис else "вивід порівнянням")
            return вих
        if isinstance(в, ast.BinOp):
            if бажані is None and isinstance(в.op, (ast.Mult, ast.Div, ast.Sub, ast.FloorDiv, ast.Pow)) and not (
                    isinstance(в.op, ast.Mult) and (_рядок(в.left) is not None or isinstance(в.left, (ast.List, ast.Tuple)))):
                дод(в.lineno, "вимір коду (арифметика)")
                return вих
            # шаблон рядка (`МІТКА % значення`, `"…" + значення`) — копія значення; сам шаблон — не значення
            for бік in (в.left, в.right):
                if _рядок(бік) is None:
                    вих += self.походження(к, бік, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, ast.JoinedStr):
            for ч in в.values:
                if isinstance(ч, ast.FormattedValue):
                    вих += self.походження(к, ч.value, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, ast.Dict):
            for кл, з in zip(в.keys, в.values):
                if кл is None:
                    вих += self.походження(к, з, бажані, глибина, ключів, бачені, ланцюг, зв)
                elif бажані is None or _рядок(кл) in бажані:
                    вих += self.походження(к, з, None, глибина, ключів, бачені, ланцюг, зв)
                elif isinstance(з, (ast.Dict, ast.Call, ast.Name)):
                    вих += self.походження(к, з, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
            for е in в.elts:
                вих += self.походження(к, е, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            зв2 = dict(зв or {})
            for г in в.generators:
                for н in ast.walk(г.target):
                    if isinstance(н, ast.Name):
                        зв2["@" + н.id] = г.iter
            return self.походження(к, в.value if isinstance(в, ast.DictComp) else в.elt, бажані, глибина, ключів,
                                   бачені, ланцюг, зв2)
        if isinstance(в, (ast.Starred, ast.Await, ast.NamedExpr)):
            return self.походження(к, в.value, бажані, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(в, ast.Call):
            return self.виклик(к, в, бажані, глибина, ключів, бачені, ланцюг, зв)
        return вих

    def ціль(self, мод, виклик):
        """Функція продукту, яку кличе виклик, — і через реекспорт (`pipeline.вердикт_v1` з `вердикт_моделі`)."""
        ц = self.а.ціль(мод, виклик)
        if ц or not isinstance(виклик.func, ast.Attribute) or not isinstance(виклик.func.value, ast.Name):
            return ц
        м = мод.модулі.get(виклик.func.value.id)
        ім = виклик.func.attr
        for _ in range(4):
            х = self.а.м.get(м)
            if х is None:
                return None
            if ім in х.функції:
                return (м, ім)
            if ім not in х.імена:
                return None
            м, ім = х.імена[ім]
        return None

    def будівник_запису(self, ц):
        """Функція, що повертає цілий запис (≥5 ключів): поля запису мають власні підписи, тож значення поля
        цілком через неї не простежується."""
        for п in self.повернення(self.функція_вузла[ц]):
            в = п.value
            if isinstance(в, ast.Dict) and len(в.keys) >= 5:
                return True
            if isinstance(в, ast.Call) and _ім(в.func) == "dict" and len(в.keywords) >= 5:
                return True
            if isinstance(в, ast.Name) and len({кл for (зм, кл) in self.сховища.get(ц, {}) if зм == в.id}) >= 5:
                return True
        return False

    @staticmethod
    def пар(зв):
        """Привʼязки параметрів без змінних генераторів; нема — None (параметр вільний)."""
        if not зв:
            return None
        п = {к: v for к, v in зв.items() if not к.startswith("@")}
        return п or None

    def стала_виміру(self, к, з):
        """Стала в записі, де поруч лежить вимір коду тієї самої функції (`_відстань=d`, `d = min(…)`): стала —
        клас виміру, не значення без нього."""
        if not (isinstance(з, ast.Constant) or isinstance(self.стала(к[0], з), ast.Constant)):
            return False
        for с in self.запис.get(id(з), ()):
            for в in [с] + (self.присвоєння.get(к, {}).get(с.id, []) if isinstance(с, ast.Name) else []):
                if any(isinstance(н, ast.Call) and _ім(н.func).rsplit(".", 1)[-1] in ВИМІР_ФУНКЦІЇ
                       for н in ast.walk(в)):
                    return True
        return False

    def стала(self, мод, в):
        """Стала верхнього рівня за імʼям: своя, імпортована `from м import ІМʼЯ` чи `_М.ІМʼЯ`."""
        м = self.а.м.get(мод)
        if isinstance(в, ast.Name):
            if в.id in self.сталі.get(мод, {}):
                return self.сталі[мод][в.id]
            for _ in range(4):          # повторний експорт: `from а import Х` в модулі, звідки імпортують Х
                if not (м and в.id in м.імена):
                    return None
                дм, ім = м.імена[в.id]
                if ім in self.сталі.get(дм, {}):
                    return self.сталі[дм][ім]
                м, в = self.а.м.get(дм), ast.Name(id=ім)
        elif isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name) and м and в.value.id in м.модулі:
            return self.сталі.get(м.модулі[в.value.id], {}).get(в.attr)
        return None

    def читання_ключа(self, к, зві, ключ, типове, бажані, глибина, ключів, бачені, ланцюг, рядок, зв=None):
        мод, ім = к
        вих = []
        if типове is not None and бажані is None and _значуща_стала(типове):
            вих.append((мод, ім, рядок, "типове `.get(%r, %r)`" % (ключ, типове.value), ланцюг))
        if isinstance(зві, ast.Name) and (зві.id, ключ) in self.сховища.get(к, {}):
            for з in self.сховища[к][(зві.id, ключ)][:6]:
                вих += self.походження(к, з, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(зві, ast.Name) and зві.id in self.присвоєння.get(к, {}):
            # ключ зі змінної, яку функція складає сама: лише цей ключ її значення
            return вих + self.походження(к, зві, бажані or {ключ}, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(зві, ast.Name) and зв and ("@" + зві.id) in зв:
            return вих + self.походження(к, зв["@" + зві.id], бажані or {ключ}, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(зві, ast.Name) and зв is not None and зві.id in зв:
            кк, арг, зз = зв[зві.id]
            if isinstance(арг, (ast.Dict, ast.Call, ast.Name)):
                return вих + self.походження(кк, арг, бажані or {ключ}, глибина, ключів, бачені, ланцюг, зз)
        if (isinstance(зві, ast.Name) and self.пар(зв) is None and зві.id in self.параметри.get(к, {})
                and 0 < len(self.виклики_функції().get(к, [])) <= ПИСАЧІВ_КЛЮЧА):
            # параметр-словник без привʼязки: ключ — з аргументів викликачів, а не від усіх писачів ключа
            з_викликачів = self.викликачі(к, зві.id, бажані or {ключ}, глибина, ключів, бачені, ланцюг)
            if з_викликачів:
                return вих + з_викликачів
        читані = self.прочитані(к, зві.id) if isinstance(зві, ast.Name) else frozenset()
        return вих + self.стрибок(ключ, бажані, глибина, ключів, бачені, ланцюг, читані, мод)

    def прочитані(self, к, змінна):
        """Ключі, які функція читає з тієї самої змінної: форма запису, що його вона чекає."""
        вих = set()
        for в in ast.walk(self.функція_вузла[к]):
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" \
                    and isinstance(в.func.value, ast.Name) and в.func.value.id == змінна and в.args and _рядок(в.args[0]):
                вих.add(_рядок(в.args[0]))
            elif isinstance(в, ast.Subscript) and isinstance(в.value, ast.Name) and в.value.id == змінна \
                    and _рядок(в.slice):
                вих.add(_рядок(в.slice))
        return frozenset(вих)

    def стрибок(self, ключ, бажані, глибина, ключів, бачені, ланцюг, читані=frozenset(), мод_ч=None):
        """Значення з ключа словника, якого функція не пише сама, — від писачів цього ключа (межа функцій)."""
        if ключів >= ГЛИБИНА_КЛЮЧІВ:
            return []
        писачі = self.писачі_ключа(ключ)
        інші = читані - {ключ} - self.псевдоніми.get(ключ, set())
        if len(писачі) > 3 and len(інші) >= 2 and not ключ.startswith("_"):
            # тезки ключа в інших записах: лише писачі запису, що має й інші ключі, які читач бере
            # (більшість інших ключів запису писача читач теж бере)
            def схожий(п):
                с = self.сусідні.get(id(п[2]), frozenset()) - {ключ} - self.псевдоніми.get(ключ, set())
                return len(с & інші) >= 2 and len(с & інші) * 2 >= len(с)
            писачі = [п for п in писачі if схожий(п)]
        elif len(писачі) > 3 and мод_ч and not ключ.startswith("_"):
            # без форми запису — лише писачі в модулях, повʼязаних імпортом із модулем читача
            с = сусіди(self, мод_ч)
            писачі = [п for п in писачі if п[0] in с]
        if not писачі or len(писачі) > ПИСАЧІВ_КЛЮЧА:
            return []
        # контейнер (випадок, сценарій, день) цілком — лише першим стрибком від писача поля: глибше він
        # несе все підряд, і джерела вже не цього поля
        if бажані is None and ключів > 0 and self.контейнер(ключ):
            return []
        if not (self.конкретний(ключ) or len(писачі) <= 3 and not контейнер_писачів(писачі)):
            # ключ, який пишуть ≤3 місця тієї самої форми запису, — теж конкретний: потік не зливає чужих
            return []
        вих = []
        for мод, ім, з, рядок in писачі:
            if id(з) in self.заповнення and ключ in self.паспорт and _значення_коду(з):
                # `.setdefault` поля її паспорта: значення коду, коли вона його не назвала
                вих.append((мод, ім, рядок, "типове коду в полі паспорта `setdefault(%r, …)`" % ключ,
                            ланцюг + ("ключ «%s» ← %s:%d" % (ключ, мод, рядок),)))
                continue
            if self.стала_виміру((мод, ім), з):
                continue
            вих += self.походження((мод, ім), з, бажані, глибина, ключів + 1, бачені,
                                   ланцюг + ("ключ «%s» ← %s:%d" % (ключ, мод, рядок),))
        return вих

    def конкретний(self, ключ):
        """Ключ, через який значення переходить межу функцій: поле її паспорта (чи його переклад на дріт), ключ
        підмета, приватний ключ (`_гілка`) чи ключ з ≤3 писачами, що не контейнер. Загальні ключі (випадок,
        сценарій, питання, місця) несуть усе підряд — через них потік не йде."""
        if ключ in self.дозволені or ключ.startswith("_"):
            return True
        return False

    def контейнер(self, ключ):
        """Ключ, який хоч один писач пише словником."""
        return any(isinstance(з, (ast.Dict, ast.DictComp)) or (isinstance(з, ast.Call) and _ім(з.func) == "dict")
                   for _, _, з, _ in self.писачі_ключа(ключ))

    def писачі_ключа(self, ключ):
        return [п for к in [ключ] + sorted(self.псевдоніми.get(ключ, ())) for п in self.писачі.get(к, [])]

    def виклик(self, к, в, бажані, глибина, ключів, бачені, ланцюг, зв=None):
        мод, ім = к
        н = _ім(в.func)
        кінець = н.rsplit(".", 1)[-1]
        вих = []
        if isinstance(в.func, ast.Attribute) and кінець == "get" and в.args and _рядок(в.args[0]) is not None:
            return self.читання_ключа(к, в.func.value, _рядок(в.args[0]), в.args[1] if len(в.args) > 1 else None,
                                      бажані, глибина, ключів, бачені, ланцюг, в.lineno, зв)
        if isinstance(в.func, ast.Attribute) and кінець in ("join", "fromkeys"):
            return sum((self.походження(к, а, бажані, глибина, ключів, бачені, ланцюг, зв) for а in в.args), [])
        if кінець in ВИМІР_ФУНКЦІЇ:
            if бажані is None:
                вих.append((мод, ім, в.lineno, "вимір коду `%s(…)`" % кінець, ланцюг))
            return вих
        if кінець == "dict":
            for кл in в.keywords:
                if кл.arg and (бажані is None or кл.arg in бажані):
                    вих += self.походження(к, кл.value, None, глибина, ключів, бачені, ланцюг, зв)
                elif кл.arg and isinstance(кл.value, (ast.Dict, ast.Call, ast.Name)):
                    вих += self.походження(к, кл.value, бажані, глибина, ключів, бачені, ланцюг, зв)
            for а in в.args:
                вих += self.походження(к, а, бажані, глибина, ключів, бачені, ланцюг, зв)
            return вих
        if isinstance(в.func, ast.Name) and в.func.id in КОПІЯ_ФУНКЦІЇ or кінець in {"deepcopy", "copy"}:
            return sum((self.походження(к, а, бажані, глибина, ключів, бачені, ланцюг, зв) for а in в.args), [])
        if isinstance(в.func, ast.Attribute) and кінець in ТЕКСТ_МЕТОДИ:
            return self.походження(к, в.func.value, бажані, глибина, ключів, бачені, ланцюг, зв)
        if isinstance(в.func, ast.Name) and any(isinstance(x, ast.Lambda)
                                                for x in self.присвоєння.get(к, {}).get(в.func.id, [])):
            # місцева `lambda` (назва з довідника, переклад коду) — значення з її аргументів
            return sum((self.походження(к, а, бажані, глибина, ключів, бачені, ланцюг, зв) for а in в.args), [])
        ц = self.ціль(self.а.м[мод], в)
        if ц and глибина < ГЛИБИНА_ВИКЛИКІВ and ц in self.функція_вузла and not (бажані is None and self.будівник_запису(ц)):
            ф = self.функція_вузла[ц]
            зв_ц = self.привʼязати(ц, к, в, зв)
            ланц = ланцюг + ("%s.%s ← %s:%d" % (ц[0], ц[1], мод, в.lineno),)
            for п in self.повернення(ф):
                вих += self.походження(ц, п.value, бажані, глибина + 1, ключів, бачені, ланц, зв_ц)
            вих += self.канал_рядка(ц, бажані, глибина, ключів, бачені, ланц)
        return вих

    @staticmethod
    def повернення(ф):
        """`return` самої функції (не вкладених)."""
        вих, черга = [], list(ф.body)
        while черга:
            в = черга.pop()
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(в, ast.Return) and в.value is not None:
                вих.append(в)
            черга.extend(ast.iter_child_nodes(в))
        return вих

    def привʼязати(self, ц, к, виклик, зв):
        """Параметри викликаної функції → (контекст викликача, вираз аргументу, привʼязки викликача)."""
        ф = self.функція_вузла[ц]
        імена = [x.arg for x in ф.args.posonlyargs + ф.args.args]
        if імена and імена[0] in {"self", "cls"}:
            імена = імена[1:]
        вих = {}
        for і, а in enumerate(виклик.args):
            if isinstance(а, ast.Starred):
                break
            if і < len(імена):
                вих[імена[і]] = (к, а, зв)
        for кл in виклик.keywords:
            if кл.arg:
                вих[кл.arg] = (к, кл.value, зв)
        return вих

    def викликачі(self, к, параметр, бажані, глибина, ключів, бачені, ланцюг):
        """Параметр кореневої функції — від аргументів її викликачів (межа функцій), якщо їх небагато."""
        if ключів >= ГЛИБИНА_КЛЮЧІВ:
            return []
        сайти = self.виклики_функції().get(к, [])
        if not сайти or len(сайти) > ПИСАЧІВ_КЛЮЧА:
            return []
        вих = []
        for кк, виклик in сайти:
            зв = self.привʼязати(к, кк, виклик, None)
            if параметр in зв:
                _, арг, _ = зв[параметр]
                вих += self.походження(кк, арг, бажані, глибина, ключів + 1, бачені,
                                       ланцюг + ("параметр `%s` ← %s:%d" % (параметр, кк[0], виклик.lineno),), None)
        return вих

    def виклики_функції(self):
        if not hasattr(self, "_виклики"):
            self._виклики = {}
            for (м, ім), ф in self.функція_вузла.items():
                for в in ast.walk(ф):
                    if isinstance(в, ast.Call):
                        ц = self.ціль(self.а.м[м], в)
                        if ц:
                            self._виклики.setdefault(ц, []).append(((м, ім), в))
        return self._виклики

    def канал_рядка(self, ц, бажані, глибина, ключів, бачені, ланцюг):
        """Читач рядка-каналу (`рядок.startswith(МІТКА)`) — від функцій, що пишуть рядок з тією самою сталою
        модуля (`МІТКА % …`): значення переходить межу функцій текстом."""
        if ключів >= ГЛИБИНА_КЛЮЧІВ:
            return []
        мод = ц[0]
        мітки = set()
        for в in ast.walk(self.функція_вузла[ц]):
            if isinstance(в, ast.Name) and в.id in self.сталі.get(мод, {}) and _рядок(self.сталі[мод][в.id]) is not None \
                    and в.id.isupper():
                мітки.add(в.id)
        if not мітки:
            return []
        вих = []
        for (м, ім), ф in self.функція_вузла.items():
            if м != мод or (м, ім) == ц:
                continue
            пише = any(isinstance(в, ast.BinOp) and isinstance(в.op, (ast.Mod, ast.Add)) and isinstance(в.left, ast.Name)
                       and в.left.id in мітки for в in ast.walk(ф))
            if пише:
                for п in self.повернення(ф):
                    вих += self.походження((м, ім), п.value, бажані, глибина + 1, ключів + 1, бачені,
                                           ланцюг + ("рядок-канал ← %s.%s" % (м, ім),), None)
        return вих


# ── підписи ──
def оголошення(дж):
    """[(задача, модуль, Поле)] усіх `Оголошення` продукту (імпорт модулів, що їх пишуть)."""
    warnings.simplefilter("ignore")
    if дж not in sys.path:
        sys.path.insert(0, дж)
    ЗП = importlib.import_module("збирач_промптів")
    знайдені = {}
    for ф in sorted(os.listdir(дж)):
        if not ф.endswith(".py") or ф.startswith(("тест", "стенд", "батарея")) or ф == "збирач_промптів.py":
            continue
        if "Оголошення(" not in open(os.path.join(дж, ф), encoding="utf-8").read():
            continue
        try:
            М = importlib.import_module(ф[:-3])
        except Exception as е:
            ОБСЯГ.непрочитано("джерела/" + ф, "імпорт: %s: %s" % (type(е).__name__, е))
            continue
        for к, в in list(vars(М).items()):
            for вв in (в.values() if isinstance(в, dict) else [в]):
                if isinstance(вв, ЗП.Оголошення):
                    знайдені.setdefault(id(вв), (ф[:-3], вв))
    try:
        фото = importlib.import_module("річ_з_фото").фото_речей()
        знайдені[id(фото)] = ("річ_з_фото", фото)
    except Exception as е:
        ОБСЯГ.непрочитано_модуль(дж, "річ_з_фото", "фото_речей(): %s: %s" % (type(е).__name__, е))
    вих = []
    for мод, о in знайдені.values():
        for п in о.вхід:
            вих.append((о.задача, мод, п))
    return sorted(вих, key=lambda x: (x[0], x[2].шлях))


def приписує(текст):
    """Підпис приписує значення їй чи факту й ніде не каже, що його дав код."""
    return bool(ЇЙ_ПІДПИС.search(текст)) and not МІТКА_КОДУ.search(текст)


def підмети(дріт, дж):
    """[(задача, шлях, ключ, бажані, підпис)]: поле входу, чий підпис приписує значення їй чи факту."""
    вих = []
    for задача, мод, п in оголошення(дж):
        текст = " ¦ ".join(x for x in (п.що, п.як) if x)
        if not (ЇЙ_ПІДПИС.search(п.що or "") or ЇЙ_ПІДПИС_ЯК.search(п.як or "")) or МІТКА_КОДУ.search(текст):
            continue
        ключ = re.sub(r"\[\]$", "", п.шлях.split(".")[-1])
        # «her intent» усередині підпису поля — ключ усередині його значення
        частини = [(задача, п.шлях, ключ, {м.group(1)}, текст, мод) for м in re.finditer(r"\bher\s+«?([a-z_]+)»?", текст)
                   if м.group(1) != ключ and дріт.писачі_ключа(м.group(1)) and not дріт.контейнер(ключ)]
        # поле цілком — коли «її» каже сам опис (`що`); правило в `як` («Edge is inside her palette», «against her
        # intent») приписує їй лише назване в ньому, а решта значення (обмеження коду) — не її
        if ЇЙ_ПІДПИС.search(п.що or "") or not частини:
            вих.append((задача, п.шлях, ключ, None, текст, мод))
        вих += частини
    # легенди ключів дроту: словник верхнього рівня «ключ → опис англійською»
    for мод in дріт.а.м.values():
        for в in мод.дерево.body:
            if isinstance(в, ast.Assign) and isinstance(в.value, ast.Dict) and len(в.value.keys) >= 3:
                пари = [(_рядок(к), _рядок(з)) for к, з in zip(в.value.keys, в.value.values)]
                if all(к and з and re.match(r"^[A-Za-z][A-Za-z0-9_]*$", к) and len(з.split()) >= 3 for к, з in пари):
                    for к, з in пари:
                        if приписує(з):
                            вих.append(("легенда %s.%s" % (мод.ім, _ім(в.targets[0])), к, к, None, з, мод.ім))
    return вих


def сусіди(дріт, мод):
    """Модуль оголошення, модулі, які він імпортує, і модулі, що імпортують його."""
    м = дріт.а.м.get(мод)
    вих = {мод}
    if м:
        вих |= set(м.модулі.values()) | {x[0] for x in м.імена.values()}
    вих |= {ім for ім, х in дріт.а.м.items() if мод in set(х.модулі.values()) | {y[0] for y in х.імена.values()}}
    return вих


def писачі_підмета(дріт, задача, ключ, мод_о):
    """Писачі ключа підмета: оголошення (легенда) описує ключ дроту свого модуля — є там писачі, то лише вони;
    інакше загальний ключ (понад ПИСАЧІВ_КЛЮЧА) — лише в модулях, повʼязаних імпортом з оголошенням."""
    писачі = дріт.писачі_ключа(ключ)
    if задача.startswith("легенда ") or any(п[0] == мод_о for п in писачі):
        return [п for п in писачі if п[0] == мод_о]
    if len(писачі) > ПИСАЧІВ_КЛЮЧА:
        с = сусіди(дріт, мод_о)
        return [п for п in писачі if п[0] in с]
    return писачі


def має_поля(шлях, шляхи):
    """Оголошення несе й поля всередині цього (`case` → `case.formality`): поле — контейнер."""
    return any(ш.startswith((шлях + ".", шлях + "[].")) for ш in шляхи)


def контейнер_писачів(писачі):
    return any(isinstance(з, (ast.Dict, ast.DictComp)) or (isinstance(з, ast.Call) and _ім(з.func) == "dict")
               for _, _, з, _ in писачі)


def місця(дріт, пд, шляхи):
    """{(мод, функція): [(рядок, вид, задача, шлях, ланцюг)]} — джерела коду значень полів-підметів."""
    знайдені = {}
    for п in пд:
        дріт.дозволені |= {п[2]} | дріт.псевдоніми.get(п[2], set())
    for задача, шлях, ключ, бажані, підпис, мод_о in пд:
        писачі = писачі_підмета(дріт, задача, ключ, мод_о)
        if бажані is None and (контейнер_писачів(писачі) or має_поля(шлях, шляхи)):
            # контейнер її фактів (case, day) цілком не простежується: усередині — поля з власними підписами,
            # а поле паспорта з типовим коду лічить правило `типові_паспорта`
            continue
        for мод, ім, з, рядок in писачі:
            for м, ф, р, вид, ланцюг in дріт.походження((мод, ім), з, бажані, 0, 0, set(),
                                                         ("писач «%s» %s:%d" % (ключ, мод, рядок),)):
                знайдені.setdefault((м, ф), []).append((р, вид, задача, шлях, ланцюг))
    return знайдені


ВИД_СУСІДА = {"бік", "джерело", "вид", "правило", "source", "side", "kind"}


def типові_паспорта(дріт, поля):
    """[(мод, рядок, чому)]: `x.setdefault("<поле паспорта>", <значення коду>)` — код ставить у її паспорт значення,
    якого вона не дала (поле читають як її факт). Не місце: порожнє (`[]`, `{}`, `""`) і копія змінної."""
    вих = []
    for мод in дріт.а.м.values():
        for в in ast.walk(мод.дерево):
            if not (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "setdefault"
                    and len(в.args) == 2):
                continue
            к, з = _рядок(в.args[0]), в.args[1]
            if к not in поля or not re.search(r"[а-яіїєґ]", к):
                continue
            if not _значення_коду(з):
                continue
            вих.append((мод.ім, в.lineno, "типове коду в полі паспорта «%s»: %s" % (к, ast.unparse(з)[:60])))
    return вих


def певність_літералом(дріт, модулі):
    """[(мод, рядок, чому)]: `впевненість=<число>` літералом у записі без виду (бік, джерело, правило): певність
    судження моделі чи виміру, яку поставив код (рішення менеджера 31.10, 11935)."""
    вих = []
    for ім in модулі:
        мод = дріт.а.м.get(ім)
        if not мод:
            continue
        for в in ast.walk(мод.дерево):
            пари = []
            if isinstance(в, ast.Dict):
                пари = [(_рядок(к), з) for к, з in zip(в.keys, в.values) if к is not None]
            elif isinstance(в, ast.Call) and _ім(в.func) in ("dict", "update"):
                пари = [(к.arg, к.value) for к in в.keywords if к.arg]
            ключі = {к for к, _ in пари}
            for к, з in пари:
                if к == "впевненість" and isinstance(з, ast.Constant) and _значуща_стала(з) \
                        and not isinstance(з.value, str) and з.value > 0 and not (ключі & ВИД_СУСІДА):
                    вих.append((ім, з.lineno, "певність %s літералом коду в записі без виду" % з.value))
    return вих


ФУНКЦІЇ_ВИДУ = {"на_її_словах", "рукою", "типовий", "_звідки_поля"}
ЗНАКИ_ВИДУ = {"джерело_полів", "типові_поля"}


def _батьки(ф):
    б = {}
    for в in ast.walk(ф):
        for д in ast.iter_child_nodes(в):
            б[id(д)] = в
    return б


def зріз(дріт, к, вирази, глибина=0, бачені=None):
    """(мод, функція, рядок) першого читання виду (`джерело_полів`, `типові_поля`, суд виду факту) у зворотному
    зрізі виразів усередині функції `к`: самі вирази, присвоєння й записи змінних, які вони читають, умови `if` і
    фільтри включень над ними, повернення функцій продукту, які вони кличуть (до двох рівнів). Вид, прочитаний в
    умові через виклик, — місце на рядку виклику: відбирає ця функція; у значенні — там, де його читає викликана."""
    бачені = бачені if бачені is not None else set()
    ф = дріт.функція_вузла.get(к)
    if ф is None:
        return None
    батьки = _батьки(ф)
    черга = [(в, False) for в in вирази]
    while черга:
        в, умова = черга.pop()
        if (id(в), умова) in бачені:
            continue
        бачені.add((id(в), умова))
        б = батьки.get(id(в))
        while б is not None and б is not ф:
            if isinstance(б, (ast.If, ast.IfExp, ast.While)):
                черга.append((б.test, True))
            elif isinstance(б, ast.comprehension):
                черга += [(у, True) for у in б.ifs] + [(б.iter, умова)]
            б = батьки.get(id(б))
        for вв in ast.walk(в):
            if isinstance(вв, ast.Constant) and вв.value in ЗНАКИ_ВИДУ:
                return к + (вв.lineno,)
            if isinstance(вв, ast.comprehension):
                черга += [(у, True) for у in вв.ifs] + [(вв.iter, умова)]
            if isinstance(вв, ast.Call):
                if _ім(вв.func).rsplit(".", 1)[-1] in ФУНКЦІЇ_ВИДУ:
                    return к + (вв.lineno,)
                ц = дріт.ціль(дріт.а.м[к[0]], вв)
                if ц and глибина < 2 and ц in дріт.функція_вузла and ("ф", умова) + ц not in бачені:
                    бачені.add(("ф", умова) + ц)
                    р = зріз(дріт, ц, [п.value for п in дріт.повернення(дріт.функція_вузла[ц])], глибина + 1, бачені)
                    if р:
                        return к + (вв.lineno,) if умова else р
            if isinstance(вв, ast.Name) and isinstance(вв.ctx, ast.Load):
                черга += [(x, умова) for x in дріт.присвоєння.get(к, {}).get(вв.id, [])[:6]]
                for (змінна, _), зз in дріт.сховища.get(к, {}).items():
                    if змінна == вв.id:
                        черга += [(x, умова) for x in зз[:6]]
    return None


def вид_губиться(дріт, пд, шляхи):
    """[(мод, функція, рядок, чому, задача, шлях)]: значення поля з підписом «її» код відібрав за видом (зворотний
    зріз писача читає `джерело_полів`, `типові_поля` чи судить вид факту), а дріт несе його без виду: що з
    відібраного — її, а що — тлумачення моделі чи форма, модель уже не розрізнить."""
    вих = []
    for задача, шлях, ключ, бажані, підпис, мод_о in пд:
        if бажані is not None or задача.startswith("легенда "):
            continue
        писачі = писачі_підмета(дріт, задача, ключ, мод_о)
        if контейнер_писачів(писачі) or має_поля(шлях, шляхи):
            continue
        for мод, ім, з, рядок in писачі:
            сус = дріт.сусідні.get(id(з), frozenset())
            if any(re.search(r"source|_by$|kind|джерело|вид", с) for с in сус if с.startswith(ключ)):
                continue
            р = зріз(дріт, (мод, ім), [з])
            if р:
                вих.append((р[0], р[1], р[2], "вид значення код знає (%s:%d), а дріт «%s» (%s:%d) несе його без виду"
                            % (р[0], р[2], шлях, мод, рядок), задача, шлях))
    return вих


# ── вхід для `корінь_е2_межі.py` ──
def місця_п6(джерела, Модуль, Аналіз, НЕ_ШЛЯХ, продукт):
    """[(мод, рядок, чому)] — місця п.6 «дріт без виду» в модулях `продукт`, відсортовані, без повторів рядка."""
    модулі = {}
    for ф in sorted(os.listdir(джерела)):
        if ф.endswith(".py") and not НЕ_ШЛЯХ.match(ф[:-3]) and not ф.startswith(("тест", "стенд")):
            with open(os.path.join(джерела, ф), encoding="utf-8") as фл:
                дерево = ОБСЯГ.розібрати(фл.read(), "джерела/" + ф)
            if дерево is not None:
                модулі[ф[:-3]] = дерево
    а = Аналіз.__new__(Аналіз)
    а.м = {ім: Модуль(ім, д) for ім, д in модулі.items()}
    дріт = ДрітБезВиду(а, джерела)
    пд = підмети(дріт, джерела)
    шляхи = {п[1] for п in пд} | {п.шлях for _, _, п in оголошення(джерела)}
    вих = {}

    def дод(мод, рядок, чому):
        if мод in продукт:
            з = вих.setdefault((мод, рядок), [])
            if чому not in з:
                з.append(чому)

    for (мод, ф), сп in місця(дріт, пд, шляхи).items():
        рядок = min(x[0] for x in сп)
        види = sorted({x[1] for x in сп})
        поля = sorted({"%s:%s" % (x[2], x[3]) for x in сп})
        дод(мод, рядок, "дріт без виду: `%s` дає %s → %s" % (ф, "; ".join(види[:3]), ", ".join(поля[:3])
                                                              + (" …" if len(поля) > 3 else "")))
    for мод, рядок, чому in типові_паспорта(дріт, дріт.паспорт):
        дод(мод, рядок, "дріт без виду: " + чому)
    for мод, рядок, чому in певність_літералом(дріт, sorted(продукт)):
        дод(мод, рядок, "дріт без виду: " + чому)
    for мод, ф, рядок, чому, задача, шлях in вид_губиться(дріт, пд, шляхи):
        дод(мод, рядок, "дріт без виду: `%s` — %s" % (ф, чому))
    return [(мод, рядок, "; ".join(ч)) for (мод, рядок), ч in sorted(вих.items())]


# ── самоперевірка: `python3 джерела/прилади/корінь_е2_межі_дріт.py` — правила на малому дереві джерел, без продукту ──
def _тест():
    import shutil
    import tempfile
    import textwrap
    import unittest
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import корінь_е2_межі as К

    ФАЙЛИ = {
        "збирач_промптів.py": '''
            class Поле:
                def __init__(self, шлях, що="", як="", **_):
                    self.шлях, self.що, self.як = шлях, що, як


            class Оголошення:
                def __init__(self, задача, роль="", вхід=()):
                    self.задача, self.роль, self.вхід = задача, роль, tuple(вхід)
            ''',
        "паспорт_поля.py": '''
            ПОЛЯ_ПАСПОРТА = {"намір": {}, "пора_року": {}, "настрій": {}, "@мета": {}}
            ''',
        "дт_вхід.py": '''
            import збирач_промптів as _ЗП

            ВХІД = _ЗП.Оголошення("дт", вхід=(
                _ЗП.Поле("case.intent", "her intent as she named it"),
                _ЗП.Поле("case.mood", "her words about the mood"),
                _ЗП.Поле("case.style", "her style; the code's default when she named none"),
                _ЗП.Поле("case.formality", "the level of dress she named"),
                _ЗП.Поле("count", "how many outfits to return"),
            ))
            ''',
        "дт_пакет.py": '''
            def випадок(паспорт):
                вих = {}
                вих["intent"] = паспорт.get("намір") or "conventional"
                вих["mood"] = паспорт.get("настрій")
                вих["style"] = паспорт.get("стиль") or "classic"
                if (паспорт.get("джерело_полів") or {}).get("ошатність") != "подія":
                    вих["formality"] = паспорт.get("ошатність")
                вих["count"] = 2
                return вих


            def паспорт_з(п):
                п.setdefault("пора_року", пора(п.get("місяць")))
                п.setdefault("настрій", [])
                return п


            def пора(м):
                return "зима" if м in (12, 1, 2) else "літо"


            def кеш(hex_):
                return dict(lab=hex_, впевненість=0.8, розкид=None)


            def правило(hex_):
                return dict(lab=hex_, впевненість=0.8, бік="код")
            ''',
        "дт_проба.py": '''
            def кеш_проби(hex_):
                return dict(lab=hex_, впевненість=0.8)
            ''',
    }


    class Перевірка(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.тека = tempfile.mkdtemp(prefix="е2_дріт_")
            for ім, текст in ФАЙЛИ.items():
                with open(os.path.join(cls.тека, ім), "w", encoding="utf-8") as ф:
                    ф.write(textwrap.dedent(текст))
            cls.місця = місця_п6(cls.тека, К.Модуль, К.Аналіз, К.НЕ_ШЛЯХ, {"дт_вхід", "дт_пакет"})
            cls.рядки = {(м, р) for м, р, _ in cls.місця}
            cls.текст = ФАЙЛИ["дт_пакет.py"].splitlines()

        @classmethod
        def tearDownClass(cls):
            shutil.rmtree(cls.тека, ignore_errors=True)

        def рядок(self, уривок):
            """Номер рядка `дт_пакет.py` (перший рядок файлу — порожній, як і в тексті до dedent)."""
            return next(і for і, р in enumerate(self.текст, 1) if уривок in р)

        def test_типове_or_під_підписом_її(self):
            self.assertIn(("дт_пакет", self.рядок('or "conventional"')), self.рядки)

        def test_копія_її_поля_не_місце(self):
            self.assertNotIn(("дт_пакет", self.рядок('вих["mood"]')), self.рядки)

        def test_підпис_з_міткою_коду_не_місце(self):
            self.assertNotIn(("дт_пакет", self.рядок('or "classic"')), self.рядки)

        def test_поле_без_підпису_її_не_місце(self):
            self.assertNotIn(("дт_пакет", self.рядок('вих["count"] = 2')), self.рядки)

        def test_вид_губиться(self):
            self.assertIn(("дт_пакет", self.рядок('"джерело_полів"')), self.рядки)

        def test_типове_в_полі_паспорта(self):
            self.assertIn(("дт_пакет", self.рядок('setdefault("пора_року"')), self.рядки)
            self.assertNotIn(("дт_пакет", self.рядок('setdefault("настрій", [])')), self.рядки)

        def test_певність_літералом(self):
            self.assertIn(("дт_пакет", self.рядок("розкид=None")), self.рядки)
            self.assertNotIn(("дт_пакет", self.рядок('бік="код"')), self.рядки)

        def test_лише_модулі_продукту(self):
            self.assertFalse([м for м in self.місця if м[0] == "дт_проба"])

        def test_рівно_ці_місця(self):
            self.assertEqual(len(self.місця), 4, self.місця)

    вих = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Перевірка))
    return 0 if вих.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_тест())
