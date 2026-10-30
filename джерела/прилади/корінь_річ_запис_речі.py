# -*- coding: utf-8 -*-
"""прилади/корінь_річ_запис_речі.py — прилад кореня Річ-запис-речі: місця коду за класом паспорта
`аудит/корені/Річ-запис-речі.md` («Клас місць»), Python і JS однаково.

Клас — правило, а не перелік прикладів. Прилад не править коду й не бере списку місць руками: усе — з AST (Python —
`ast`, JS — acorn із самого node через `корінь_річ_запис_речі_js.js`) і з реєстру в дереві (`slots.py`, схема
`внутрішня_мова.schema.json`). Місце впізнають за ПОХОДЖЕННЯМ ДАНИХ і ВЖИТКОМ, а не за написанням літерала, його
розміром чи іменем змінної (#2314, КОЛО #2283): ім'я змінної не читається ніде, окрім ключа поля запису, з якого
дані походять або в який пишуться.

ЯК УСТРОЄНО. Обидві мови зводяться до одного проміжного подання (вирази й оператори з ланцюгами «від чого залежить»);
один граф залежностей на ввесь продукт: змінні, параметри й повернення функцій (зв'язані за викликами, між модулями
теж), операції-читачі слів, записувачі полів. Походження:
  Т  текст речі — читання з запису речі за ключем тексту (назва, опис, склад, розділ, крихти, слаг/адреса…), текст
     вузла сторінки (`get_text`, `.text`, `textContent`…); ключ КОДУ поля (слот, тип, `slot`, `item_type`…) тексту
     не дає — це читання записаного;
  С  слова — рядкові літерали зі словом і контейнери таких літералів (словник будь-якого розміру);
  К  код поля — читання ключа коду;
  Д  корінь документа сторінки — результат розбору HTML (`BeautifulSoup`, `document`…).

ОПЕРАЦІЯ-ЧИТАЧ СЛІВ — регекс зі словом над Т, `in`/порівняння/`startswith`/`replace`… зі словом над Т, пошук Т у
словнику слів. Запис поля — присвоєння/літерал/іменований аргумент з ключем поля запису (тип, слот, комплект, склад,
крій, довжина, рід, назва, опис, комір, рукав, застібка, візерунок… — за роллю; колір — корені Річ-колір-*).

ПУНКТИ КЛАСУ (паспорт; кожен — механічне правило, помилка видна в переліку `файл:рядок · пункт · чому`):
  1  операція-читач слів над Т, чий результат (даними чи умовою) доходить до запису поля — вивести код або почистити
     текст;
  2  код поля не з реєстру: (а) у запис поля коду пишуть літерал, якого нема в реєстрі; (б) власний перелік чи
     словник кодів (≥2 коди одного реєстрового переліку) поза реєстром, яким порівнюють, групують чи впорядковують
     значення, що походить з поля коду, або яким обчислюють запис поля коду. Збіг написання без такого вжитку
     (координати рамки `верх`/`низ`) і порівняння з ОДНИМ кодом — читання, не місце;
  3  поле виводять удруге: виклик функції, що виводить поле зі слів, результат якої НЕ йде в запис поля, — замість
     читати записане;
  4  джерело поля — корінь документа сторінки: добування (`get_text`, `.text`, `select`/`find`…) прямо з Д,
     не звужене до вузла товару, результат якого доходить до запису поля. Крок звуження (вибір блоку в змінну, з якої
     далі добувають) місцем не є.

ДВА ШЛЯХИ, ОДИН НАБІР МІСЦЬ (мірило (а)):
  А — від записувачів: кожен запис поля й реєстр кодів → назад по залежностях значення (із глибиною виклику до
      ГЛИБИНА_А) до операцій-читачів, джерело яких перевіряється назад до Т;
  Б — від читачів: кожна операція-читач над Т (Т — прямий прохід вперед від джерел без обмеження глибини) → вперед
      до запису поля.
  Місце, знайдене лише одним шляхом, друкується в «розбіжностях шляхів» з причиною.

ЧОГО ПРИЛАД НЕ ЛІЧИТЬ (питання менеджерові в PR): див. розділ «Прилад» PR; проби (`джерела/проби/`), прилади
(`джерела/прилади/`), тести й гейти — поза класом (паспорт), у `місць` не входять.

Вивід: перелік `файл:рядок · пункт · чому [шлях]`, підсумки за пунктами, розбіжності шляхів, останній рядок
`місць: <N>` (N — різних `файл:рядок`), код 0. Запуск з кореня репозиторію (чи `--корінь <шлях>`):
python3 джерела/прилади/корінь_річ_запис_речі.py [--json] [--тихо] [--пункт N]
"""
import ast
import json
import os
import re
import subprocess
import sys
import warnings

warnings.simplefilter("ignore", SyntaxWarning)

# ── ключі полів запису речі (за роллю) ────────────────────────────────────────────────────────────────────────────
КЛЮЧІ_КОДУ = frozenset((
    "тип", "слот", "слоти", "комплект", "рід", "довжина", "крій", "рукав", "комір", "застібка", "візерунок", "принт",
    "силует", "посадка", "каблук", "халява", "горловина", "тип_набору", "вид", "матеріал", "тканина", "набір",
    "item_type", "slot", "slots", "set_kind", "set_parts", "fabric", "material", "cut", "length", "sleeve",
    "neckline", "collar", "closure", "pattern", "gender", "silhouette", "shaft", "vamp", "alt_slots"))
КЛЮЧІ_ТЕКСТУ_ПОЛЯ = frozenset((
    "назва", "опис", "склад", "name", "description", "composition", "features", "назва_показу", "назва_суду"))
КЛЮЧІ_ЗАПИСУ = КЛЮЧІ_КОДУ | КЛЮЧІ_ТЕКСТУ_ПОЛЯ
# Ключі, з яких читається ТЕКСТ речі (джерело Т) із запису речі: українські ключі запису каталогу. Англійські ключі
# (`name`, `title`, `description`, `url`, `tags`…) — ключі JSON-документа крамниці: Т лише з кореня документа (Д).
КЛЮЧІ_Т = frozenset((
    "назва", "назва_суду", "назва_показу", "назва_ua", "опис", "склад", "крихти", "розділ", "категорія", "слаг"))
КЛЮЧІ_Т_ДОКУМЕНТА = frozenset((
    "name", "name_ua", "title", "description", "composition", "breadcrumbs", "breadcrumb", "category", "categories",
    "url", "slug", "short_description", "full_description", "body_html", "product_type", "tags", "characteristics",
    "attributes", "specs"))
АТРИБУТИ_Т = frozenset(("text", "textContent", "innerText", "innerHTML", "string", "outerHTML", "strings",
                        "stripped_strings", "inner_html"))
МЕТОДИ_Т = frozenset(("get_text", "getText", "findtext", "inner_text", "text_content", "itertext", "gettext"))
# Корені документа сторінки: розбір HTML (Д).
# Корені документа сторінки (Д): розбір HTML/XML — виклик конструктора/розбору (за модулем, не за іменем змінної).
КОРЕНІ_Д_ІМЕНА = frozenset(("BeautifulSoup", "HTMLParser", "Selector", "fromstring", "XML", "HTML", "parseFromString",
                            "DOMParser", "document_fromstring", "fragment_fromstring", "iterparse"))
КОРЕНІ_Д_МОДУЛІ = frozenset(("ElementTree", "etree", "html", "lxml", "minidom", "bs4", "parsel", "ET"))
КОРЕНІ_Д_МЕТОДИ = frozenset(("fromstring", "parse", "iterparse", "XML", "HTML", "document_fromstring",
                             "fragment_fromstring", "parseFromString"))
ЗВУЖЕННЯ_Д = frozenset(("select", "select_one", "find", "find_all", "findAll", "xpath", "querySelector",
                        "querySelectorAll", "getElementById", "getElementsByClassName", "getElementsByTagName",
                        "css", "closest", "find_parent", "find_next", "children", "descendants", "item"))
ДОБУВАННЯ_Д = frozenset(("get_text", "getText", "findtext", "text_content", "itertext", "inner_text"))
МЕТОДИ_РЕГЕКС_PY = frozenset(("search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"))
МЕТОДИ_РЯДКА = frozenset(("startswith", "endswith", "find", "rfind", "index", "rindex", "count", "replace",
                          "removeprefix", "removesuffix", "partition", "rpartition", "lstrip", "rstrip", "strip",
                          "startsWith", "endsWith", "includes", "indexOf", "lastIndexOf", "replaceAll"))
МЕТОДИ_РЕГЕКС_JS = frozenset(("test", "exec", "match", "matchAll", "search", "replace", "replaceAll", "split"))
МЕТОДИ_ПРОХОДУ = frozenset((  # результат несе текст отримувача
    "lower", "upper", "strip", "lstrip", "rstrip", "split", "rsplit", "join", "title", "capitalize", "casefold",
    "format", "splitlines", "encode", "decode", "toLowerCase", "toUpperCase", "trim", "trimStart", "trimEnd",
    "slice", "substring", "substr", "normalize", "concat", "at", "charAt", "padStart", "padEnd", "toString",
    "group", "groups", "groupdict", "span", "get", "items", "values", "keys", "copy", "pop", "popitem", "map",
    "filter", "flat", "flatMap", "sort", "sorted", "reverse", "slice", "entries", "from", "unescape", "escape",
    "translate", "expandtabs", "zfill", "ljust", "rjust", "center", "swapcase", "removeprefix", "removesuffix",
    "partition", "rpartition", "replace", "replaceAll", "sub", "subn", "findall", "finditer", "search", "match",
    "fullmatch", "exec"))
МЕТОДИ_ЗАПИСУ = frozenset(("append", "extend", "add", "update", "setdefault", "insert", "appendleft", "push",
                           "unshift", "extendleft", "assign"))
ЧИТАННЯ_ФАЙЛА = frozenset(("open", "load", "loads", "read_text", "read_bytes", "parse", "iterparse", "fromstring",
                           "fetch", "readFile", "gzip_open", "ElementTree", "jsonl"))
КАТАЛОГ_ШЛЯХ = re.compile(r"каталог|catalog|\.jsonl|brief", re.I)
ГЛИБИНА_А = 6
Є_СЛОВО = re.compile(r"[A-Za-zА-Яа-яЇїІіЄєҐґ]{2,}")
ГЛИБИНА_ПОШУКУ = 12
НЕ_ШЛЯХ_ІМ = re.compile(r"^(тест|gate_|audit_|стенд|батарея_|measure_|pair_test|мутанти|replay|проба)")
НЕ_ТЕКИ = ("проби", "прилади", "аудит", "node_modules", "розвідка", "дані_", "__pycache__", "траса")
ТЕКИ_Py = ("джерела", "zhnyvarka")
ФАЙЛИ_JS = ("джерела/worker_джерело.js",)
ТЕКИ_JS = ("джерела/показ",)


# ═══ ПРОМІЖНЕ ПОДАННЯ ═══════════════════════════════════════════════════════════════════════════════════════════
class E:
    """Вираз. k: name str const attr sub call cmp bool not cond bin fstr list dict comp lambda regex star other."""
    __slots__ = ("k", "v", "a", "line", "x")

    def __init__(s, k, v=None, a=(), line=0, x=None):
        s.k, s.v, s.a, s.line, s.x = k, v, list(a), line, x


class S:
    """Оператор: assign (targets, value) / expr / return / iter (target, iter) з ланцюгом умов ctrl."""
    __slots__ = ("k", "t", "val", "line", "ctrl")

    def __init__(s, k, t, val, line, ctrl):
        s.k, s.t, s.val, s.line, s.ctrl = k, t, val, line, tuple(ctrl)


class F:
    """Функція (або тіло модуля, `name == '<модуль>'`)."""
    __slots__ = ("fid", "name", "params", "stmts", "line", "file", "mod", "cls", "parent", "locals", "lang",
                 "defaults", "is_method")

    def __init__(s, fid, name, params, line, file, mod, cls, parent, lang):
        s.fid, s.name, s.params, s.line, s.file, s.mod, s.cls, s.parent, s.lang = fid, name, params, line, file, mod, cls, parent, lang
        s.stmts, s.locals, s.defaults, s.is_method = [], set(params), [], False


class Модуль:
    def __init__(s, файл, мова):
        s.файл, s.мова = файл, мова
        s.ім_я = os.path.splitext(os.path.basename(файл))[0]
        s.функції = []                  # усі F файла, у т.ч. вкладені й <модуль>
        s.тіло = None
        s.псевдоніми = {}               # ім'я → ('mod', модуль) | ('name', модуль, ім'я)


def лінія(n):
    return getattr(n, "lineno", 0) or 0


# ── Python → подання ───────────────────────────────────────────────────────────────────────────────────────────────
class Py:
    def __init__(s, мод):
        s.мод = мод

    def вираз(s, n):
        if n is None:
            return E("const")
        t = type(n)
        L = лінія(n)
        if t is ast.Name:
            return E("name", n.id, line=L)
        if t is ast.Constant:
            return E("str", n.value, line=L) if isinstance(n.value, str) else E("const", n.value, line=L)
        if t is ast.JoinedStr:
            return E("fstr", None, [s.вираз(v.value) if isinstance(v, ast.FormattedValue) else s.вираз(v)
                                    for v in n.values], L)
        if t is ast.Attribute:
            return E("attr", n.attr, [s.вираз(n.value)], L)
        if t is ast.Subscript:
            return E("sub", None, [s.вираз(n.value), s.вираз(n.slice)], L)
        if t is ast.Slice:
            return E("other", None, [s.вираз(x) for x in (n.lower, n.upper, n.step) if x is not None], L)
        if t is ast.Call:
            арги = [E("star", None, [s.вираз(a.value)], лінія(a)) if isinstance(a, ast.Starred) else s.вираз(a)
                    for a in n.args]
            імена = [k.arg for k in n.keywords]
            знач = [s.вираз(k.value) for k in n.keywords]
            return E("call", {"n": len(арги), "kw": імена}, [s.вираз(n.func)] + арги + знач, L)
        if t is ast.Compare:
            частини, лів = [], s.вираз(n.left)
            for оп, пр in zip(n.ops, n.comparators):
                прав = s.вираз(пр)
                частини.append(E("cmp", type(оп).__name__, [лів, прав], L))
                лів = прав
            return частини[0] if len(частини) == 1 else E("bool", "and", частини, L)
        if t is ast.BoolOp:
            return E("bool", type(n.op).__name__, [s.вираз(v) for v in n.values], L)
        if t is ast.UnaryOp:
            return E("not", None, [s.вираз(n.operand)], L) if isinstance(n.op, ast.Not) else E("other", None, [s.вираз(n.operand)], L)
        if t is ast.BinOp:
            return E("bin", type(n.op).__name__, [s.вираз(n.left), s.вираз(n.right)], L)
        if t is ast.IfExp:
            return E("cond", None, [s.вираз(n.test), s.вираз(n.body), s.вираз(n.orelse)], L)
        if t in (ast.List, ast.Tuple, ast.Set):
            return E("list", t.__name__, [s.вираз(x) for x in n.elts], L)
        if t is ast.Dict:
            a = []
            for k, v in zip(n.keys, n.values):
                a.append(s.вираз(k) if k is not None else E("star", None, [], L))
                a.append(s.вираз(v))
            return E("dict", None, a, L)
        if t in (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp):
            ген = []
            for g in n.generators:
                ген.append((s.ціль(g.target), s.вираз(g.iter), [s.вираз(i) for i in g.ifs]))
            елт = [s.вираз(n.key), s.вираз(n.value)] if t is ast.DictComp else [s.вираз(n.elt)]
            return E("comp", ген, елт, L)
        if t is ast.Lambda:
            return E("lambda", [a.arg for a in n.args.args], [s.вираз(n.body)], L)
        if t is ast.NamedExpr:
            return E("walrus", n.target.id if isinstance(n.target, ast.Name) else "", [s.вираз(n.value)], L)
        if t is ast.Starred:
            return E("star", None, [s.вираз(n.value)], L)
        if t in (ast.Await, ast.Yield, ast.YieldFrom):
            return s.вираз(n.value) if n.value is not None else E("const")
        return E("other", None, [s.вираз(c) for c in ast.iter_child_nodes(n) if isinstance(c, ast.expr)], L)

    def ціль(s, n):
        return s.вираз(n)

    def блок(s, інструкції, ф, ctrl, out):
        неявні = []
        for n in інструкції:
            t = type(n)
            ц = tuple(ctrl) + tuple(неявні)
            L = лінія(n)
            if t is ast.Assign:
                out.append(S("assign", [s.ціль(x) for x in n.targets], s.вираз(n.value), L, ц))
            elif t is ast.AnnAssign:
                if n.value is not None:
                    out.append(S("assign", [s.ціль(n.target)], s.вираз(n.value), L, ц))
            elif t is ast.AugAssign:
                ц2 = s.ціль(n.target)
                out.append(S("assign", [ц2], E("bin", "Aug", [ц2, s.вираз(n.value)], L), L, ц))
            elif t in (ast.For, ast.AsyncFor):
                out.append(S("iter", s.ціль(n.target), s.вираз(n.iter), L, ц))
                s.блок(n.body, ф, ц, out)
                s.блок(n.orelse, ф, ц, out)
            elif t is ast.While:
                тест = s.вираз(n.test)
                out.append(S("expr", None, тест, L, ц))
                s.блок(n.body, ф, ц + (тест,), out)
            elif t is ast.If:
                тест = s.вираз(n.test)
                out.append(S("expr", None, тест, L, ц))
                s.блок(n.body, ф, ц + (тест,), out)
                s.блок(n.orelse, ф, ц + (тест,), out)
                if n.body and isinstance(n.body[-1], ast.Return) and not n.orelse:
                    неявні.append(тест)       # рання повернення значення: далі — залежить від умови
            elif t in (ast.With, ast.AsyncWith):
                for it in n.items:
                    if it.optional_vars is not None:
                        out.append(S("assign", [s.ціль(it.optional_vars)], s.вираз(it.context_expr), L, ц))
                    else:
                        out.append(S("expr", None, s.вираз(it.context_expr), L, ц))
                s.блок(n.body, ф, ц, out)
            elif t is ast.Try or (hasattr(ast, "TryStar") and t is getattr(ast, "TryStar")):
                s.блок(n.body, ф, ц, out)
                for h in n.handlers:
                    s.блок(h.body, ф, ц, out)
                s.блок(n.orelse, ф, ц, out)
                s.блок(n.finalbody, ф, ц, out)
            elif t is ast.Return:
                out.append(S("return", None, s.вираз(n.value) if n.value is not None else E("const"), L, ц))
            elif t is ast.Expr:
                if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    continue
                out.append(S("expr", None, s.вираз(n.value), L, ц))
            elif t in (ast.FunctionDef, ast.AsyncFunctionDef):
                s.функція(n, ф, ф.cls)
            elif t is ast.ClassDef:
                for ч in n.body:
                    if isinstance(ч, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        s.функція(ч, ф, n.name)
                    elif isinstance(ч, (ast.Assign, ast.AnnAssign)):
                        s.блок([ч], ф, ц, out)
            elif t in (ast.Import, ast.ImportFrom):
                s.імпорт(n)
            elif t is ast.Global:
                ф.locals.difference_update(n.names)
            elif t is ast.Delete or t is ast.Pass or t is ast.Break or t is ast.Continue or t is ast.Nonlocal:
                pass
            elif t is ast.Raise or t is ast.Assert:
                for c in ast.iter_child_nodes(n):
                    if isinstance(c, ast.expr):
                        out.append(S("expr", None, s.вираз(c), L, ц))
            elif hasattr(ast, "Match") and t is ast.Match:
                тема = s.вираз(n.subject)
                for ке in n.cases:
                    s.блок(ке.body, ф, ц + (тема,), out)

    def імпорт(s, n):
        м = s.мод
        if isinstance(n, ast.Import):
            for а in n.names:
                м.псевдоніми[а.asname or а.name.split(".")[0]] = ("mod", а.name.split(".")[-1] if а.asname else а.name.split(".")[0])
        else:
            for а in n.names:
                м.псевдоніми[а.asname or а.name] = ("name", (n.module or "").split(".")[-1], а.name)

    def функція(s, n, батько, клас):
        м = s.мод
        арг = n.args
        параметри = [a.arg for a in arg_all(арг)]
        fid = "%s:%d:%s" % (м.файл, лінія(n), n.name)
        ф = F(fid, n.name, параметри, лінія(n), м.файл, м.ім_я, клас, батько, "py")
        ф.is_method = bool(клас) and bool(параметри) and параметри[0] in ("self", "cls")
        ф.defaults = [s.вираз(d) for d in арг.defaults + [d for d in арг.kw_defaults if d is not None]]
        м.функції.append(ф)
        s.блок(n.body, ф, (), ф.stmts)
        # декоратори/значення за замовчуванням — у батьківському тілі
        return ф


def arg_all(a):
    return list(getattr(a, "posonlyargs", [])) + list(a.args) + ([a.vararg] if a.vararg else []) + \
        list(a.kwonlyargs) + ([a.kwarg] if a.kwarg else [])


def розібрати_py(файл, текст):
    м = Модуль(файл, "py")
    try:
        дерево = ast.parse(текст)
    except (SyntaxError, ValueError):
        return м
    тіло = F("%s:0:<модуль>" % файл, "<модуль>", [], 0, файл, м.ім_я, None, None, "py")
    м.тіло = тіло
    м.функції.append(тіло)
    п = Py(м)
    п.блок(дерево.body, тіло, (), тіло.stmts)
    return м


# ── JS → подання ───────────────────────────────────────────────────────────────────────────────────────────────────
class Js:
    def __init__(s, мод, зсув=0):
        s.мод, s.зсув = мод, зсув

    def L(s, n):
        return (n.get("line", 0) if isinstance(n, dict) else 0) + s.зсув

    def вираз(s, n):
        if not isinstance(n, dict):
            return E("const")
        t, L = n.get("type"), s.L(n)
        if t == "Identifier":
            return E("name", n["name"], line=L)
        if t == "Literal":
            if "regex" in n:
                return E("regex", n["regex"]["pattern"], line=L)
            v = n.get("value")
            return E("str", v, line=L) if isinstance(v, str) else E("const", v, line=L)
        if t == "TemplateLiteral":
            return E("fstr", None, [s.вираз(x) for x in n.get("expressions", [])] +
                     [E("str", q.get("value", {}).get("cooked") or "", line=L) for q in n.get("quasis", [])], L)
        if t == "MemberExpression":
            if n.get("computed"):
                return E("sub", None, [s.вираз(n["object"]), s.вираз(n["property"])], L)
            return E("attr", n["property"].get("name", ""), [s.вираз(n["object"])], L)
        if t == "ChainExpression":
            return s.вираз(n["expression"])
        if t in ("CallExpression", "NewExpression"):
            арги = [E("star", None, [s.вираз(a["argument"])], L) if a.get("type") == "SpreadElement" else s.вираз(a)
                    for a in n.get("arguments", [])]
            return E("call", {"n": len(арги), "kw": [], "new": t == "NewExpression"}, [s.вираз(n["callee"])] + арги, L)
        if t in ("BinaryExpression", "LogicalExpression"):
            оп = n["operator"]
            a = [s.вираз(n["left"]), s.вираз(n["right"])]
            if оп in ("===", "==", "!==", "!=", "in", "instanceof", "<", ">", "<=", ">="):
                return E("cmp", {"===": "Eq", "==": "Eq", "!==": "NotEq", "!=": "NotEq", "in": "In"}.get(оп, оп), a, L)
            if оп in ("&&", "||", "??"):
                return E("bool", оп, a, L)
            return E("bin", оп, a, L)
        if t == "UnaryExpression":
            return E("not", None, [s.вираз(n["argument"])], L) if n["operator"] == "!" else E("other", None, [s.вираз(n["argument"])], L)
        if t == "ConditionalExpression":
            return E("cond", None, [s.вираз(n["test"]), s.вираз(n["consequent"]), s.вираз(n["alternate"])], L)
        if t == "ArrayExpression":
            return E("list", "Array", [s.вираз(x) for x in n.get("elements", []) if x], L)
        if t == "ObjectExpression":
            a = []
            for p in n.get("properties", []):
                if p.get("type") == "SpreadElement":
                    a += [E("star", None, [], L), s.вираз(p["argument"])]
                    continue
                к = p["key"]
                ключ = E("str", к["name"] if к.get("type") == "Identifier" and not p.get("computed") else к.get("value", ""), line=L) \
                    if к.get("type") in ("Identifier", "Literal") and not p.get("computed") else s.вираз(к)
                a += [ключ, s.значення_властивості(p, L)]
            return E("dict", None, a, L)
        if t in ("FunctionExpression", "ArrowFunctionExpression"):
            ф = s.функція(n, None, None, "<лямбда>")
            return E("lambda", ф.fid, [], L, x=ф)
        if t == "AssignmentExpression":
            ц = s.вираз(n["left"])
            пр = s.вираз(n["right"])
            return E("assignx", None, [ц, пр], L)
        if t == "SequenceExpression":
            return E("other", None, [s.вираз(x) for x in n["expressions"]], L)
        if t == "SpreadElement":
            return E("star", None, [s.вираз(n["argument"])], L)
        if t in ("AwaitExpression", "YieldExpression"):
            return s.вираз(n.get("argument"))
        if t == "ThisExpression":
            return E("name", "this", line=L)
        if t == "TaggedTemplateExpression":
            return E("other", None, [s.вираз(n["tag"]), s.вираз(n["quasi"])], L)
        return E("other", None, [], L)

    def значення_властивості(s, p, L):
        # {a() {...}} / {a: function(){}} / {a: v}
        зн = p.get("value")
        return s.вираз(зн)

    def функція(s, n, батько, клас, ім_я=None):
        м = s.мод
        імя = ім_я or ((n.get("id") or {}).get("name")) or "<лямбда>"
        параметри = []
        for p in n.get("params", []):
            параметри += s.імена_шаблону(p)
        fid = "%s:%d:%s#%d" % (м.файл, s.L(n), імя, len(м.функції))
        ф = F(fid, імя, параметри, s.L(n), м.файл, м.ім_я, клас, батько, "js")
        м.функції.append(ф)
        тіло = n.get("body")
        if isinstance(тіло, dict) and тіло.get("type") == "BlockStatement":
            s.блок(тіло.get("body", []), ф, (), ф.stmts)
        elif isinstance(тіло, dict):
            ф.stmts.append(S("return", None, s.вираз(тіло), s.L(n), ()))
        for p in n.get("params", []):
            if p.get("type") == "AssignmentPattern":
                ф.defaults.append(s.вираз(p.get("right")))
        return ф

    def імена_шаблону(s, p):
        t = p.get("type") if isinstance(p, dict) else None
        if t == "Identifier":
            return [p["name"]]
        if t == "AssignmentPattern":
            return s.імена_шаблону(p["left"])
        if t == "RestElement":
            return s.імена_шаблону(p["argument"])
        if t == "ArrayPattern":
            return [x for e in p.get("elements", []) if e for x in s.імена_шаблону(e)]
        if t == "ObjectPattern":
            return [x for pr in p.get("properties", []) for x in s.імена_шаблону(pr.get("value") or pr.get("argument") or {})]
        return []

    def ціль(s, p):
        """Шаблон (деструктурування) → вираз-ціль: для об'єкта — ключі як `sub`, щоб ключ поля зберігся."""
        t = p.get("type") if isinstance(p, dict) else None
        if t == "Identifier":
            return E("name", p["name"], line=s.L(p))
        if t == "AssignmentPattern":
            return s.ціль(p["left"])
        if t == "MemberExpression":
            return s.вираз(p)
        return E("list", "Pat", [E("name", n, line=s.L(p)) for n in s.імена_шаблону(p)], s.L(p))

    def блок(s, інструкції, ф, ctrl, out):
        неявні = []
        for n in інструкції:
            if not isinstance(n, dict):
                continue
            t, L = n.get("type"), s.L(n)
            ц = tuple(ctrl) + tuple(неявні)
            if t == "VariableDeclaration":
                for d in n.get("declarations", []):
                    ініт = d.get("init")
                    пат = d.get("id")
                    if ініт is None:
                        for ім in s.імена_шаблону(пат):
                            ф.locals.add(ім)
                        continue
                    if ініт.get("type") in ("FunctionExpression", "ArrowFunctionExpression") and пат.get("type") == "Identifier":
                        ф2 = s.функція(ініт, ф, None, пат["name"])
                        ф.locals.add(пат["name"])
                        out.append(S("assign", [E("name", пат["name"], line=L)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
                        continue
                    if пат.get("type") == "ObjectPattern":
                        знач = s.вираз(ініт)
                        for пр in пат.get("properties", []):
                            if пр.get("type") == "Property" and not пр.get("computed"):
                                ключ = пр["key"].get("name", пр["key"].get("value", ""))
                                for ім in s.імена_шаблону(пр.get("value") or {}):
                                    out.append(S("assign", [E("name", ім, line=L)],
                                                 E("sub", None, [знач, E("str", ключ, line=L)], L), L, ц))
                            elif пр.get("type") == "RestElement":
                                for ім in s.імена_шаблону(пр):
                                    out.append(S("assign", [E("name", ім, line=L)], знач, L, ц))
                        continue
                    out.append(S("assign", [s.ціль(пат)], s.вираз(ініт), L, ц))
                    for ім in s.імена_шаблону(пат):
                        ф.locals.add(ім)
            elif t == "FunctionDeclaration":
                ф2 = s.функція(n, ф, None)
                ф.locals.add(n["id"]["name"])
                out.append(S("assign", [E("name", n["id"]["name"], line=L)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
            elif t == "ClassDeclaration":
                for ч in n.get("body", {}).get("body", []):
                    if ч.get("type") == "MethodDefinition":
                        ф2 = s.функція(ч["value"], ф, n["id"]["name"], ч["key"].get("name", "?"))
                        ф2.is_method = True
            elif t == "ExpressionStatement":
                вир = n["expression"]
                if вир.get("type") == "AssignmentExpression":
                    s.присвоєння(вир, ф, ц, out)
                else:
                    out.append(S("expr", None, s.вираз(вир), L, ц))
            elif t == "ReturnStatement":
                out.append(S("return", None, s.вираз(n.get("argument")) if n.get("argument") else E("const"), L, ц))
            elif t == "IfStatement":
                тест = s.вираз(n["test"])
                out.append(S("expr", None, тест, L, ц))
                s.блок(s.обгорнути(n["consequent"]), ф, ц + (тест,), out)
                if n.get("alternate"):
                    s.блок(s.обгорнути(n["alternate"]), ф, ц + (тест,), out)
                кін = s.обгорнути(n["consequent"])
                if кін and isinstance(кін[-1], dict) and кін[-1].get("type") == "ReturnStatement" and not n.get("alternate"):
                    неявні.append(тест)
            elif t in ("ForStatement",):
                if n.get("init"):
                    s.блок([n["init"]] if n["init"].get("type") == "VariableDeclaration" else
                           [{"type": "ExpressionStatement", "expression": n["init"], "line": L}], ф, ц, out)
                тест = s.вираз(n["test"]) if n.get("test") else E("const")
                s.блок(s.обгорнути(n["body"]), ф, ц + (тест,), out)
            elif t in ("ForOfStatement", "ForInStatement"):
                ліве = n["left"]
                ітер = s.вираз(n["right"])
                if ліве.get("type") == "VariableDeclaration":
                    ліве = ліве["declarations"][0]["id"]
                for ім in s.імена_шаблону(ліве):
                    ф.locals.add(ім)
                out.append(S("iter", s.ціль(ліве), ітер, L, ц))
                s.блок(s.обгорнути(n["body"]), ф, ц, out)
            elif t in ("WhileStatement", "DoWhileStatement"):
                тест = s.вираз(n["test"])
                s.блок(s.обгорнути(n["body"]), ф, ц + (тест,), out)
            elif t == "BlockStatement":
                s.блок(n.get("body", []), ф, ц, out)
            elif t == "TryStatement":
                s.блок(n["block"].get("body", []), ф, ц, out)
                if n.get("handler"):
                    s.блок(n["handler"]["body"].get("body", []), ф, ц, out)
                if n.get("finalizer"):
                    s.блок(n["finalizer"].get("body", []), ф, ц, out)
            elif t == "SwitchStatement":
                диск = s.вираз(n["discriminant"])
                for ке in n.get("cases", []):
                    тест = E("cmp", "Eq", [диск, s.вираз(ке["test"])], L) if ке.get("test") else диск
                    s.блок(ке.get("consequent", []), ф, ц + (тест,), out)
            elif t in ("ThrowStatement",):
                out.append(S("expr", None, s.вираз(n.get("argument")), L, ц))
            elif t == "LabeledStatement":
                s.блок(s.обгорнути(n["body"]), ф, ц, out)

    def обгорнути(s, n):
        if isinstance(n, dict) and n.get("type") == "BlockStatement":
            return n.get("body", [])
        return [n] if isinstance(n, dict) else []

    def присвоєння(s, n, ф, ц, out):
        L = s.L(n)
        прав = n["right"]
        if прав.get("type") == "AssignmentExpression":
            s.присвоєння(прав, ф, ц, out)
            прав = прав["left"]
        ліве = n["left"]
        if n["operator"] != "=":
            ц2 = s.ціль(ліве)
            out.append(S("assign", [ц2], E("bin", "Aug", [ц2, s.вираз(прав)], L), L, ц))
            return
        if прав.get("type") in ("FunctionExpression", "ArrowFunctionExpression"):
            ім = ліве.get("name") or (ліве.get("property") or {}).get("name") or "<лямбда>"
            ф2 = s.функція(прав, ф, None, ім)
            out.append(S("assign", [s.ціль(ліве)], E("lambda", ф2.fid, [], L, x=ф2), L, ц))
            return
        out.append(S("assign", [s.ціль(ліве)], s.вираз(прав), L, ц))


def розібрати_js(файл, дерево, зсув=0):
    м = Модуль(файл, "js")
    тіло = F("%s:0:<модуль>" % файл, "<модуль>", [], 0, файл, м.ім_я, None, None, "js")
    м.тіло = тіло
    м.функції.append(тіло)
    if not isinstance(дерево, dict) or "body" not in дерево:
        return м
    Js(м, зсув).блок(дерево["body"], тіло, (), тіло.stmts)
    return м


# ═══ ГРАФ ЗАЛЕЖНОСТЕЙ ════════════════════════════════════════════════════════════════════════════════════════════
sys.setrecursionlimit(20000)
ЕСКЕЙП_РЕГЕКСУ = re.compile(r"\\[A-Za-z]|\(\?[A-Za-z:=!<P]*(<[A-Za-z_]+>)?|\[:[a-z]+:\]|\\p\{[A-Za-z]+\}")
ЧИСТІ_ВБУДОВАНІ = frozenset(("len", "int", "float", "bool", "isinstance", "hasattr", "callable", "id", "print", "range",
                            "sum", "round", "abs", "ord", "hash", "min", "max", "type", "chr", "enumerate", "any",
                            "all", "parseInt", "parseFloat", "Number", "isNaN", "Boolean", "setTimeout",
                            "startswith", "endswith", "find", "rfind", "index", "rindex", "count", "includes",
                            "indexOf", "lastIndexOf", "startsWith", "endsWith", "test", "isdigit", "isalpha",
                            "isalnum", "isupper", "islower", "isspace", "isnumeric", "has", "contains"))
ТЕКСТОВІ_ОПИ = frozenset(("sub", "subn", "replace", "replaceAll", "findall", "finditer", "search", "match",
                         "fullmatch", "split", "exec", "matchAll", "removeprefix", "removesuffix", "partition",
                         "rpartition", "lstrip", "rstrip", "strip"))
ФІЛЬТР_ЗАПИСУ = КЛЮЧІ_ЗАПИСУ


def слово_літерал(т):
    return isinstance(т, str) and "\n" not in т and bool(Є_СЛОВО.search(т))


def слово_в_регексі(т):
    return isinstance(т, str) and bool(Є_СЛОВО.search(ЕСКЕЙП_РЕГЕКСУ.sub("", т)))


class Оп:
    __slots__ = ("id", "файл", "рядок", "вид", "суб", "пар", "ім_я", "ф", "пункт")

    def __init__(s, id, файл, рядок, вид, суб, пар, ім_я, ф, пункт=1):
        s.id, s.файл, s.рядок, s.вид, s.суб, s.пар, s.ім_я, s.ф, s.пункт = id, файл, рядок, вид, суб, пар, ім_я, ф, пункт


class Запис:
    __slots__ = ("id", "файл", "рядок", "ключ", "вузол", "значення", "ф", "вираз", "контейнер")

    def __init__(s, id, файл, рядок, ключ, значення, ф, вираз=None, контейнер=None):
        s.id, s.файл, s.рядок, s.ключ, s.значення, s.ф, s.вираз = id, файл, рядок, ключ, значення, ф, вираз
        s.контейнер = контейнер if контейнер is not None else set()
        s.вузол = ("sink", id)


SEED = {n: ("seed", n) for n in ("T", "W", "F", "D", "C", "RX", "RXW")}


class Рушій:
    def __init__(s, модулі, реєстр):
        s.модулі = модулі
        s.реєстр = реєстр
        s.дані = {}        # вузол -> set(вузлів, від яких залежить за даними)
        s.усі = {}         # вузол -> set(вузлів, від яких залежить за даними й умовами)
        s.оп = []          # [Оп]
        s.записи = []      # [Запис]
        s.виклики = []     # (id, файл, рядок, caller F, [callees])
        s.контейнери = []  # (id, файл, рядок, родина, коди)
        s.пари_контейнер = []   # (оп-подібне: файл, рядок, дані_а, дані_б, вид)
        s.приймачі = set()  # вузли, які вжито як отримувач (attr) — для кроку звуження
        s.селекції = []    # (id, файл, рядок, вузол_результату, вузол_отримувача_дані)
        s.f_по_id = {}
        s.модуль_по_імені = {}
        s.функції_модуля = {}      # (мод, ім'я) -> [F] верхнього рівня
        s.методи = {}              # (мод, клас, ім'я) -> [F]
        s.методи_ім = {}           # ім'я -> [F]
        s.js_ім = {}               # ім'я -> [F]
        s.вкладені = {}            # (fid батька, ім'я) -> [F]
        s.лічильник = 0
        s.джерела_Т = []
        s.константи = {}
        for м in модулі:
            if м.тіло is not None:
                for st in м.тіло.stmts:
                    if st.k == 'assign' and st.val is not None and st.val.k == 'str':
                        for ц in st.t:
                            if ц.k == 'name':
                                s.константи.setdefault((м.ім_я, ц.v), []).append(st.val.v)
        for м in модулі:
            s.модуль_по_імені.setdefault(м.ім_я, м)
            for ф in м.функції:
                s.f_по_id[ф.fid] = ф
                if ф.name == "<модуль>":
                    continue
                if ф.lang == "js":
                    s.js_ім.setdefault(ф.name, []).append(ф)
                    continue
                if ф.parent is not None and ф.parent.name != "<модуль>":
                    s.вкладені.setdefault((ф.parent.fid, ф.name), []).append(ф)
                elif ф.cls:
                    s.методи.setdefault((м.ім_я, ф.cls, ф.name), []).append(ф)
                    s.методи_ім.setdefault(ф.name, []).append(ф)
                else:
                    s.функції_модуля.setdefault((м.ім_я, ф.name), []).append(ф)

    # ── допоміжне ──
    def нов(s):
        s.лічильник += 1
        return s.лічильник

    def дод(s, ціль, дані=(), усі=(), тільки_усі=()):
        if дані:
            s.дані.setdefault(ціль, set()).update(дані)
            s.усі.setdefault(ціль, set()).update(дані)
        if усі:
            s.усі.setdefault(ціль, set()).update(усі)
        if тільки_усі:
            s.усі.setdefault(ціль, set()).update(тільки_усі)

    def вузол(s, ф, ім):
        if ф.name == "<модуль>":
            return s.глобальний(ф, ім)
        if ім in ф.locals:
            return ("v", ф.fid, ім)
        п = ф.parent
        while п is not None:
            if п.name != "<модуль>" and ім in п.locals:
                return ("v", п.fid, ім)
            п = п.parent
        return s.глобальний(ф, ім)

    def глобальний(s, ф, ім):
        if ф.lang == "js":
            return ("g", "js", ім)
        м = s.модуль_по_імені.get(ф.mod)
        if м is not None:
            пс = м.псевдоніми.get(ім)
            if пс and пс[0] == "name":
                return ("g", пс[1], пс[2])
        return ("g", ф.mod, ім)

    def модуль_f(s, ф):
        return s.модуль_по_імені.get(ф.mod)

    # ── розв'язання викликів ──
    def розв(s, ф, функц):
        res = []
        if ф.lang == "js":
            if функц.k == "name":
                res = s.js_ім.get(функц.v, [])[:4]
            elif функц.k == "attr":
                res = s.js_ім.get(функц.v, [])[:3]
            return res
        м = s.модуль_f(ф)
        if функц.k == "name":
            п = ф
            while п is not None:
                if п.name != "<модуль>":
                    res += s.вкладені.get((п.fid, функц.v), [])
                п = п.parent
            if not res:
                res = list(s.функції_модуля.get((ф.mod, функц.v), []))
            if not res and м is not None:
                пс = м.псевдоніми.get(функц.v)
                if пс and пс[0] == "name":
                    res = list(s.функції_модуля.get((пс[1], пс[2]), []))
        elif функц.k == "attr":
            об = функц.a[0]
            if об.k == "name":
                пс = м.псевдоніми.get(об.v) if м is not None else None
                if пс and пс[0] == "mod":
                    res = list(s.функції_модуля.get((пс[1], функц.v), []))
                elif об.v in ("self", "cls") and ф.cls:
                    res = list(s.методи.get((ф.mod, ф.cls, функц.v), []))
                    if not res:
                        res = [x for x in s.методи_ім.get(функц.v, []) if x.mod == ф.mod][:2]
                else:
                    res = list(s.методи.get((ф.mod, об.v, функц.v), []))
        return res

    # ── збір локальних імен ──
    def зібрати_локальні(s, ф):
        def з_цілі(е):
            if е is None:
                return
            if е.k == "name":
                ф.locals.add(е.v)
            elif е.k in ("list", "star", "other"):
                for ч in е.a:
                    з_цілі(ч)
        def обійти(е):
            if е.k == "comp":
                for т, іт, ifs in е.v:
                    з_цілі(т)
                    обійти(іт)
                    for i in ifs:
                        обійти(i)
            elif е.k == "lambda" and ф.lang == "py":
                for p in е.v:
                    ф.locals.add(p)
            elif е.k == "walrus" and е.v:
                ф.locals.add(е.v)
            elif е.k == "assignx":
                з_цілі(е.a[0])
            for ч in е.a:
                if isinstance(ч, E):
                    обійти(ч)
        for st in ф.stmts:
            if st.k == "assign":
                for т in st.t:
                    з_цілі(т)
            elif st.k == "iter":
                з_цілі(st.t)
                обійти(st.val)
                continue
            if st.val is not None:
                обійти(st.val)

    # ── побудова ──
    def побудувати(s):
        for м in s.модулі:
            for ф in м.функції:
                s.зібрати_локальні(ф)
        # Python: усі присвоєні на рівні модуля імена — глобальні (<модуль> повертає ('g',…) сам)
        for м in s.модулі:
            for ф in м.функції:
                s.функція(ф)

    def функція(s, ф):
        for ум in ф.defaults:
            s.d(ф, ум)
        for п_ім in ф.params:
            pass
        for st in ф.stmts:
            ctrl = set()
            for т in st.ctrl:
                ctrl |= s.d(ф, т)[1]
            if st.k == "assign":
                if len(st.t) == 1 and s.розпакувати(ф, st.t[0], st.val, ctrl, st.line, False):
                    continue
                дд, уу = s.d(ф, st.val)
                for ц in st.t:
                    s.призначити(ф, ц, дд, уу, ctrl, st.line, st.val)
            elif st.k == "iter":
                if s.розпакувати(ф, st.t, st.val, ctrl, st.line, True):
                    continue
                дд, уу = s.d(ф, st.val)
                s.призначити(ф, st.t, дд, уу, ctrl, st.line)
            elif st.k == "return":
                дд, уу = s.d(ф, st.val)
                s.дод(("ret", ф.fid), дд, уу | ctrl)
            else:
                s.d(ф, st.val)

    def розпакувати(s, ф, ц, зн, ctrl, рядок, цикл):
        """Розпаковка парами: `a, b = x, y`; `for a, b in zip(x, y)`; `for i, a in enumerate(x)` — кожна ціль бере
        дані свого джерела, а не суміш усіх."""
        if ц.k != "list" or ц.v == "Pat":
            return False
        цілі = ц.a
        if not цикл and зн.k == "list" and len(зн.a) == len(цілі) and all(x.k != "star" for x in цілі + зн.a):
            for ціль, джерело in zip(цілі, зн.a):
                a, b = s.d(ф, джерело)
                s.призначити(ф, ціль, a, b, ctrl, рядок, джерело)
            return True
        if цикл and зн.k == "call" and зн.a[0].k == "name":
            ім = зн.a[0].v
            арги = зн.a[1:1 + зн.v["n"]]
            if ім == "zip" and len(арги) == len(цілі) and not зн.v["kw"]:
                for ціль, джерело in zip(цілі, арги):
                    a, b = s.d(ф, джерело)
                    s.призначити(ф, ціль, a, b, ctrl, рядок)
                return True
            if ім == "enumerate" and len(цілі) == 2 and арги:
                a, b = s.d(ф, арги[0])
                s.призначити(ф, цілі[0], set(), set(), ctrl, рядок)
                s.призначити(ф, цілі[1], a, b, ctrl, рядок)
                return True
        return False

    def корінь_цілі(s, е):
        while е is not None and е.k in ("attr", "sub"):
            е = е.a[0]
        return е

    def призначити(s, ф, ц, дд, уу, ctrl, рядок, знач=None):
        k = ц.k
        if k == "name":
            s.дод(s.вузол(ф, ц.v), дд, уу | ctrl)
        elif k == "attr":
            s.d(ф, ц.a[0])
            for вз in s.вузол_атрибута(ф, ц.v):
                s.дод(вз, дд, уу | ctrl)
            корінь = s.корінь_цілі(ц)
            if корінь is not None and корінь.k == "name":
                s.дод(s.вузол(ф, корінь.v), дд, уу | ctrl)
            if ц.v in ФІЛЬТР_ЗАПИСУ:
                s.запис(ф, рядок, ц.v, дд, уу | ctrl, знач,
                        {s.вузол(ф, корінь.v)} if корінь is not None and корінь.k == "name" else s.d(ф, ц.a[0])[0])
        elif k == "sub":
            s.d(ф, ц.a[0])
            ключ = ц.a[1]
            kd, ku = s.d(ф, ключ)
            корінь = s.корінь_цілі(ц)
            if корінь is not None and корінь.k == "name":
                s.дод(s.вузол(ф, корінь.v), дд, уу | ctrl)
            if ключ.k == "str" and ключ.v in ФІЛЬТР_ЗАПИСУ:
                s.запис(ф, рядок, ключ.v, дд, уу | ctrl, знач,
                        {s.вузол(ф, корінь.v)} if корінь is not None and корінь.k == "name" else s.d(ф, ц.a[0])[0])
        elif k in ("list", "star", "other"):
            for ч in ц.a:
                s.призначити(ф, ч, дд, уу, ctrl, рядок)

    def запис(s, ф, рядок, ключ, дд, уу, вираз=None, контейнер=None):
        з = Запис(len(s.записи), ф.file, рядок, ключ, дд, ф, вираз, контейнер)
        s.записи.append(з)
        s.дод(з.вузол, дд, уу)
        return з

    # ── вирази: (дані, усі) ──
    def d(s, ф, е):
        k = е.k
        порожньо = (set(), set())
        if k in ("const",):
            return порожньо
        if k == "name":
            н = s.вузол(ф, е.v)
            return {н}, {н}
        if k == "str":
            if слово_літерал(е.v):
                return {SEED["W"]}, {SEED["W"]}
            return порожньо
        if k == "regex":
            з = SEED["RXW"] if слово_в_регексі(е.v) else SEED["RX"]
            return {з}, {з}
        if k == "fstr" or k == "other" or k == "star":
            дд, уу = set(), set()
            for ч in е.a:
                a, b = s.d(ф, ч)
                дд |= a
                уу |= b
            return дд, уу
        if k == "attr":
            од, оу = s.d(ф, е.a[0])
            s.приймачі.update(n for n in од if n[0] == "sel")
            if е.v in АТРИБУТИ_Т:
                оп_д, оп_у = s.реєструвати_оп(ф, е, "doc", од, set(), е.v, 4)
                s.приймачі_додати(ф, е.a[0])
                тв = ("txt", s.нов())
                s.дод(тв, од, оу)
                return {тв}, {тв} | оп_у
            if е.v in КЛЮЧІ_КОДУ:
                s.приймачі_додати(ф, е.a[0])
                return {SEED["F"]}, {SEED["F"]} | оу
            s.приймачі_додати(ф, е.a[0])
            if е.v in ("length", "size"):
                return set(), оу
            вузол_ат = s.вузол_атрибута(ф, е.v)
            return од | вузол_ат, оу | вузол_ат
        if k == "sub":
            од, оу = s.d(ф, е.a[0])
            ключ = е.a[1]
            kd, ку = s.d(ф, ключ)
            s.приймачі_додати(ф, е.a[0])
            if ключ.k == "str":
                if ключ.v in КЛЮЧІ_Т or ключ.v in КЛЮЧІ_Т_ДОКУМЕНТА:
                    тв = ("txt", s.нов())
                    s.дод(тв, од, оу)
                    s.джерела_Т.append((ф.file, е.line, ключ.v))
                    return {тв}, {тв} | оу
                if ключ.v in КЛЮЧІ_КОДУ:
                    return {SEED["F"]}, {SEED["F"]} | оу
            оп_у = s.реєструвати_оп(ф, е, "dictlook", kd, од, "sub")
            s.пара_контейнер(ф, е, од, kd, "sub")
            if ключ.k == "str":      # читання за сталим ключем, що не є ключем тексту, — інше поле: тексту не несе
                return set(), оу | ку | оп_у[1]
            return од | оп_у[0], оу | ку | оп_у[1]
        if k == "cmp":
            ld, la = s.d(ф, е.a[0])
            rd, ra = s.d(ф, е.a[1])
            н = s.реєструвати_оп(ф, е, "cmp", ld, rd, е.v)
            s.пара_контейнер(ф, е, ld, rd, "cmp")
            return set(), la | ra | н[1]
        if k == "bool":
            дд, уу = set(), set()
            for ч in е.a:
                a, b = s.d(ф, ч)
                дд |= a
                уу |= b
            return дд, уу
        if k == "not":
            _, уу = s.d(ф, е.a[0])
            return set(), уу
        if k == "cond":
            td, tu = s.d(ф, е.a[0])
            ad, au = s.d(ф, е.a[1])
            bd, bu = s.d(ф, е.a[2])
            return ad | bd, au | bu | tu
        if k == "bin":
            ad, au = s.d(ф, е.a[0])
            bd, bu = s.d(ф, е.a[1])
            if е.v == "Mod" or е.v == "+" or е.v == "Aug" or е.v == "Add":
                return ad | bd, au | bu
            return ad | bd, au | bu
        if k == "list":
            дд, уу = set(), set()
            for ч in е.a:
                a, b = s.d(ф, ч)
                дд |= a
                уу |= b
            c = s.контейнер_літерал(ф, е)
            if c:
                дд |= c
                уу |= c
            return дд, уу
        if k == "dict":
            дд, уу = set(), set()
            нові_записи = []
            for i in range(0, len(е.a), 2):
                kd, ku = s.d(ф, е.a[i])
                vd, vu = s.d(ф, е.a[i + 1])
                дд |= kd | vd
                уу |= ku | vu
                кл = е.a[i]
                if кл.k == "str" and кл.v in ФІЛЬТР_ЗАПИСУ:
                    нові_записи.append(s.запис(ф, е.a[i + 1].line or е.line, кл.v, vd, vu, е.a[i + 1], дд))
            c = s.контейнер_літерал(ф, е)
            if c:
                дд |= c
                уу |= c
            return дд, уу
        if k == "comp":
            дд, уу = set(), set()
            умови = set()
            for т, іт, ifs in е.v:
                if s.розпакувати(ф, т, іт, set(), е.line, True):
                    for i in ifs:
                        умови |= s.d(ф, i)[1]
                    continue
                a, b = s.d(ф, іт)
                s.призначити(ф, т, a, b, set(), е.line)
                for i in ifs:
                    умови |= s.d(ф, i)[1]
            for ч in е.a:
                a, b = s.d(ф, ч)
                дд |= a
                уу |= b
            return дд, уу | умови
        if k == "lambda":
            if ф.lang == "py":
                дд, уу = s.d(ф, е.a[0])
                return дд, уу
            return порожньо
        if k == "walrus":
            a, b = s.d(ф, е.a[0])
            if е.v:
                s.дод(s.вузол(ф, е.v), a, b)
            return a, b
        if k == "assignx":
            a, b = s.d(ф, е.a[1])
            s.призначити(ф, е.a[0], a, b, set(), е.line)
            return a, b
        if k == "call":
            return s.виклик(ф, е)
        return порожньо

    def вузол_атрибута(s, ф, ім):
        """Сховище атрибута: у Python — на модуль (поле об'єкта), у JS атрибути не відстежуються (контейнер)."""
        return {("a", ф.mod, ім)} if ф.lang == "py" else set()

    def корінь_каталогу(s, ф, функц, ім_я, арги):
        """Читання файла каталогу (дані записів речі): відкриття/розбір, чий шлях згадує каталог."""
        if ім_я not in ЧИТАННЯ_ФАЙЛА:
            return False
        return any(КАТАЛОГ_ШЛЯХ.search(л) for a in арги for л in s.літерали_шляху(ф, a))

    def літерали_шляху(s, ф, е, глиб=0):
        вих = []
        if е is None or глиб > 4:
            return вих
        if е.k == "str":
            вих.append(е.v)
        elif е.k == "name":
            м = s.модуль_f(ф)
            if м is not None:
                вих += s.константи.get((ф.mod, е.v), [])
        for ч in е.a:
            if isinstance(ч, E):
                вих += s.літерали_шляху(ф, ч, глиб + 1)
        return вих

    def корінь_д(s, ф, функц, ім_я, арги_д=()):
        м = s.модуль_f(ф)
        if функц.k == "name":
            if ім_я in КОРЕНІ_Д_ІМЕНА:
                return True
            пс = м.псевдоніми.get(ім_я) if м is not None else None
            return bool(пс and пс[0] == "name" and пс[2] in КОРЕНІ_Д_ІМЕНА)
        # JSON-документ крамниці: відповідь HTTP (`.json()` відповіді, `json.loads` її тіла) у збирачі крамниць
        if "zhnyvarka/" in ф.file and функц.k == "attr" and ім_я == "json":
            return True
        if "zhnyvarka/" in ф.file and функц.k == "attr" and ім_я == "loads" and функц.a[0].k == "name" \
                and функц.a[0].v == "json" and арги_д:
            а0 = арги_д[0]
            return (а0.k == "sub" and а0.a[1].k == "str" and а0.a[1].v in ("тіло", "body", "text", "content")) or \
                (а0.k == "attr" and а0.v in ("text", "content"))
        if функц.k == "attr" and ім_я in КОРЕНІ_Д_МЕТОДИ:
            об = функц.a[0]
            while об.k == "attr":
                if об.v in КОРЕНІ_Д_МОДУЛІ:
                    return True
                об = об.a[0]
            if об.k == "name":
                пс = м.псевдоніми.get(об.v) if м is not None else None
                return bool(пс and ((пс[0] == "mod" and пс[1] in КОРЕНІ_Д_МОДУЛІ) or
                                    (пс[0] == "name" and пс[2] in КОРЕНІ_Д_МОДУЛІ)) or об.v in КОРЕНІ_Д_МОДУЛІ)
            return ф.lang == "js" and ім_я == "parseFromString"
        return False

    def приймачі_додати(s, ф, обє):
        if обє.k == "name":
            s.приймачі.add(s.вузол(ф, обє.v))

    # ── контейнери кодів (п.2б) ──
    def контейнер_літерал(s, ф, е):
        if ф.mod in s.реєстр.модулі_реєстру:
            return set()
        if е.k == "list":
            ел = [x.v for x in е.a if x.k == "str"]
        else:
            ел = [е.a[i].v for i in range(0, len(е.a), 2) if е.a[i].k == "str"]
            ел += [е.a[i].v for i in range(1, len(е.a), 2) if е.a[i].k == "str"]
        if len(ел) < 2:
            return set()
        родина = s.реєстр.сім_я(ел)
        if not родина:
            return set()
        id = len(s.контейнери)
        s.контейнери.append((id, ф.file, е.line, родина, tuple(sorted(set(ел)))[:6], ф.fid, е.k))
        return {("cont", id)}

    def пара_контейнер(s, ф, е, a, b, вид):
        s.пари_контейнер.append((ф.file, е.line, a, b, вид, ф.fid))

    # ── операції-читачі ──
    def реєструвати_оп(s, ф, е, вид, суб, пар, ім_я, пункт=1):
        id = len(s.оп)
        о = Оп(id, ф.file, е.line, вид, суб, пар, ім_я, ф.fid, пункт)
        s.оп.append(о)
        вуз = ("op", id)
        return {вуз} if (вид in ("regex", "strm", "dictlook") and ім_я in ТЕКСТОВІ_ОПИ) else set(), {вуз}

    def виклик(s, ф, е):
        n = е.v["n"]
        функц = е.a[0]
        арги = е.a[1:1 + n]
        кварги = dict(zip(е.v["kw"], е.a[1 + n:]))
        ім_я = функц.v if функц.k in ("attr", "name") else None
        отр = функц.a[0] if функц.k == "attr" else None
        фд, фу = s.d(ф, функц) if функц.k != "attr" else (set(), set())
        од, оу = (s.d(ф, отр) if отр is not None else (set(), set()))
        if отр is not None:
            s.приймачі_додати(ф, отр)
            s.приймачі.update(n for n in од if n[0] == "sel")
        ад, ау = [], []
        for a in арги:
            x, y = s.d(ф, a)
            ад.append(x)
            ау.append(y)
        кд = {k: s.d(ф, v) for k, v in кварги.items()}
        for k, (x, y) in кд.items():
            if k in ФІЛЬТР_ЗАПИСУ:
                s.запис(ф, е.line, k, x, y, кварги[k], set().union(*[x2 for k2, (x2, y2) in кд.items() if k2 != k], *ад))
        вс_д = set().union(*ад) if ад else set()
        вс_у = set().union(*ау) if ау else set()
        for x, y in кд.values():
            вс_д |= x
            вс_у |= y
        # ключ-доступ: x.get("назва"), x.pop("слот"), setdefault(ключ, значення)
        if ім_я in ("get", "pop", "getattr") and арги and арги[0 if ім_я != "getattr" else 1:][:1] and \
                арги[0 if ім_я != "getattr" else 1].k == "str":
            ключ = арги[0 if ім_я != "getattr" else 1].v
            if ключ in КЛЮЧІ_Т or ключ in КЛЮЧІ_Т_ДОКУМЕНТА:
                тв = ("txt", s.нов())
                s.дод(тв, од, оу)
                s.джерела_Т.append((ф.file, е.line, ключ))
                return {тв}, {тв} | оу
            if ключ in КЛЮЧІ_КОДУ:
                return {SEED["F"]}, {SEED["F"]} | оу
        if ім_я in ("get", "pop") and арги and арги[0].k == "str" and отр is not None:
            return set(), оу | вс_у
        if ім_я == "setdefault" and len(арги) >= 2 and арги[0].k == "str" and арги[0].v in ФІЛЬТР_ЗАПИСУ:
            s.запис(ф, е.line, арги[0].v, ад[1], ау[1], арги[1], set(од))
        # коріння документа (Д)
        if s.корінь_д(ф, функц, ім_я, арги):
            return {SEED["D"]} | вс_д, {SEED["D"]} | вс_у
        if s.корінь_каталогу(ф, функц, ім_я, арги):
            return {SEED["C"]} | вс_д, {SEED["C"]} | вс_у
        # регекс-об'єкт
        if ім_я in ("compile", "RegExp") and арги:
            якість = SEED["RXW"] if (SEED["W"] in ад[0] or SEED["RXW"] in ад[0] or
                                      (арги[0].k == "str" and слово_в_регексі(арги[0].v))) else SEED["RX"]
            if арги[0].k == "str" and not слово_в_регексі(арги[0].v):
                якість = SEED["RX"]
            return {якість}, {якість}
        # добування тексту/вузла з документа
        if ім_я in МЕТОДИ_Т and отр is not None:
            оп_д, оп_у = s.реєструвати_оп(ф, е, "doc", од, set(), ім_я, 4)
            тв = ("txt", s.нов())
            s.дод(тв, од, оу)
            return {тв}, {тв} | оп_у | оу | вс_у
        if ім_я in ЗВУЖЕННЯ_Д and отр is not None and ф.lang != "none":
            id = s.нов()
            вуз = ("sel", id)
            s.дод(вуз, од | вс_д, оу | вс_у)
            оп_д, оп_у = s.реєструвати_оп(ф, е, "doc", од, {вуз}, ім_я, 4)
            s.селекції.append((id, ф.file, е.line, вуз))
            return {вуз} | оп_д, {вуз} | оп_у
        # користувацькі функції
        кал = s.розв(ф, функц)
        if кал:
            id = s.нов()
            вуз = ("call", id)
            зсув = 1 if (функц.k == "attr" and кал[0].is_method) else 0
            for ц in кал:
                s.виклики_ф(ц, арги, ад, ау, кварги, кд, зсув, од, оу, функц)
                s.дод(вуз, {("ret", ц.fid)}, set())
            s.виклики.append((id, ф.file, е.line, ф, [ц.fid for ц in кал]))
            # аргументи-лямбди
            s.зв_лямбди(ф, е, арги, од, оу, ад, ау)
            return {вуз}, {вуз} | (оу if False else set())
        # операції-читачі над текстом
        результат_д, результат_у = set(), set()
        оп_визначено = False
        if ім_я in МЕТОДИ_РЕГЕКС_PY | МЕТОДИ_РЕГЕКС_JS and (отр is not None):
            якщо_re = (отр.k == "name" and s.модуль_f(ф) is not None and
                       s.модуль_f(ф).псевдоніми.get(отр.v) == ("mod", "re")) or (отр.k == "name" and отр.v == "re")
            if якщо_re and ім_я in МЕТОДИ_РЕГЕКС_PY and len(арги) >= 2:
                суб = ад[2] if (ім_я in ("sub", "subn") and len(арги) >= 3) else ад[1] if ім_я not in ("sub", "subn") else set()
                if ім_я in ("sub", "subn") and "string" in кд:
                    суб = кд["string"][0]
                d1, u1 = s.реєструвати_оп(ф, е, "regex", суб, ад[0], ім_я)
                результат_д |= d1
                результат_у |= u1 | (ау[2] if len(ау) > 2 else set()) | (ау[1] if len(ау) > 1 else set())
                оп_визначено = True
            elif SEED["RXW"] in од or SEED["RX"] in од:
                суб = ад[1] if (ім_я in ("sub", "subn") and len(арги) >= 2) else (ад[0] if арги else set())
                д1, у1 = s.реєструвати_оп(ф, е, "regex", суб, од & {SEED["RXW"]}, ім_я)
                результат_д |= д1
                результат_у |= у1 | вс_у
                оп_визначено = True
            elif ф.lang == "js" and арги and (SEED["RXW"] in ад[0] or SEED["RX"] in ад[0]):
                д1, у1 = s.реєструвати_оп(ф, е, "regex", од, ад[0] & {SEED["RXW"]}, ім_я)
                результат_д |= д1
                результат_у |= у1 | оу
                оп_визначено = True
        if not оп_визначено and ім_я in МЕТОДИ_РЯДКА and отр is not None and арги:
            д1, у1 = s.реєструвати_оп(ф, е, "strm", од, ад[0], ім_я)
            результат_д |= д1
            результат_у |= у1
            оп_визначено = True
        if not оп_визначено and ім_я == "get" and отр is not None and арги:
            д1, у1 = s.реєструвати_оп(ф, е, "dictlook", ад[0], од, "get")
            результат_д |= д1
            результат_у |= у1
            пара = (од, ад[0])
            s.пара_контейнер(ф, е, од, ад[0], "get")
        if ім_я in ("index", "count") and отр is not None and арги:
            s.пара_контейнер(ф, е, од, ад[0], "index")
        # джерела тексту та проходження
        дд = set()
        if ім_я in ЧИСТІ_ВБУДОВАНІ:
            дд = set()
        else:
            дд = вс_д | (од if отр is not None else set())
            if функц.k == "name":
                дд |= set()
        усі = результат_у | вс_у | оу | фу
        if ім_я in ЧИСТІ_ВБУДОВАНІ and ім_я not in ("enumerate", "min", "max"):
            дд = set()
        # операції, що ПИШУТЬ у отримувач
        if ім_я in МЕТОДИ_ЗАПИСУ and отр is not None:
            корінь = s.корінь_цілі(отр)
            if корінь is not None and корінь.k == "name":
                s.дод(s.вузол(ф, корінь.v), вс_д, вс_у)
                if ім_я == "setdefault" and len(арги) >= 2:
                    pass
        if ім_я in ("sorted", "list", "tuple", "set", "frozenset", "dict", "str", "sum"):
            pass
        s.зв_лямбди(ф, е, арги, од, оу, ад, ау)
        return (дд | результат_д), (усі | дд | результат_д)

    def зв_лямбди(s, ф, е, арги, од, оу, ад, ау):
        for i, a in enumerate(арги):
            if a.k == "lambda":
                if ф.lang == "py":
                    для = set(од)
                    для_у = set(оу)
                    for j in range(len(арги)):
                        if j != i:
                            для |= ад[j]
                            для_у |= ау[j]
                    for p in a.v:
                        s.дод(s.вузол(ф, p), для, для_у)
                elif isinstance(a.x, F) and a.x.params:
                    s.дод(("v", a.x.fid, a.x.params[0]), од, оу)

    def виклики_ф(s, ц, арги, ад, ау, кварги, кд, зсув, од, оу, функц):
        пар = ц.params
        for i, (д, у) in enumerate(zip(ад, ау)):
            if арги[i].k == "star":
                continue
            j = i + зсув
            if j < len(пар):
                s.дод(("v", ц.fid, пар[j]), д, у)
        for k, (д, у) in кд.items():
            if k in пар:
                s.дод(("v", ц.fid, k), д, у)
        # методи: self ← отримувач
        if зсув and пар:
            s.дод(("v", ц.fid, пар[0]), од, оу)



# ═══ РЕЄСТР ═════════════════════════════════════════════════════════════════════════════════════════════════════════
class Реєстр:
    """Реєстр кодів з дерева: `slots.py` (слоти, типи) і схема `внутрішня_мова.schema.json` (`x-таблиця`)."""
    модулі_реєстру = frozenset(("slots", "внутрішня_мова"))
    РОДИНИ_СХЕМИ = ("slot", "item_type", "fabric", "material", "pattern", "length")

    def __init__(s, корінь):
        s.родини = {}
        s.назви_ua = {}
        шлях = os.path.join(корінь, "джерела", "внутрішня_мова.schema.json")
        try:
            таб = json.load(open(шлях, encoding="utf8")).get("x-таблиця", {})
        except (OSError, ValueError):
            таб = {}
        for р in s.РОДИНИ_СХЕМИ:
            ф = таб.get(р) or {}
            s.родини[р] = set(ф) if isinstance(ф, (dict, list)) else set()
            if isinstance(ф, dict):
                s.назви_ua[р] = {str(v) for v in ф.values()}
        шлях = os.path.join(корінь, "джерела", "slots.py")
        try:
            дерево = ast.parse(open(шлях, encoding="utf8").read())
        except (OSError, SyntaxError):
            дерево = None
        if дерево:
            for н in дерево.body:
                if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
                    ім = н.targets[0].id
                    try:
                        зн = ast.literal_eval(н.value)
                    except (ValueError, SyntaxError):
                        continue
                    if ім == "КЛЮЧІ" and isinstance(зн, dict):
                        s.родини["slot"] |= set(зн) | set(зн.values())
                    elif ім == "_SLOT_TYPES" and isinstance(зн, dict):
                        s.родини["slot"] |= set(зн)
                        for ти in зн.values():
                            s.родини["item_type"] |= set(ти)
        ш2 = os.path.join(корінь, "джерела", "силует_реєстр.py")
        s.родини["cut"] = set()
        try:
            for н in ast.parse(open(ш2, encoding="utf8").read()).body:
                if isinstance(н, ast.Assign) and isinstance(н.targets[0], ast.Name) and н.targets[0].id == "КРОЇ" \
                        and isinstance(н.value, ast.Dict):
                    s.родини["cut"] |= {к.value for к in н.value.keys if isinstance(к, ast.Constant) and isinstance(к.value, str)}
        except (OSError, SyntaxError):
            pass
        for р in list(s.родини):
            s.родини[р].discard("unknown")
        s.усі_коди = set().union(*s.родини.values()) if s.родини else set()

    def родина_ключа(s, ключ):
        if ключ in ("слот", "slot", "слоти", "slots", "alt_slots", "комплект"):
            return "slot"
        if ключ in ("тип", "item_type", "type", "тип_набору", "set_kind"):
            return "item_type"
        return None

    def дозволені(s, родина):
        return s.родини.get(родина, set()) | s.назви_ua.get(родина, set()) | {"", "unknown", "невідомо"}

    def сім_я(s, елементи):
        ел = {e for e in елементи if isinstance(e, str)}
        if len(ел) < 2:
            return None
        найкраща = None
        for р, коди in s.родини.items():
            n = len(ел & коди)
            if n >= 2 and n * 2 >= len(ел) and (найкраща is None or n > найкраща[1]):
                найкраща = (р, n)
        return найкраща[0] if найкраща else None


# ═══ ПОТОКИ, РОЗВ'ЯЗАННЯ, ШЛЯХИ ═════════════════════════════════════════════════════════════════════════════════
def вперед(словник):
    р = {}
    for х, залежить in словник.items():
        for у in залежить:
            р.setdefault(у, []).append(х)
    return р


def потік(старт, вп, не_розкривати=("sel",)):
    бачено = set(старт)
    черга = list(старт)
    while черга:
        н = черга.pop()
        for х in вп.get(н, ()):
            if х in бачено:
                continue
            бачено.add(х)
            if х[0] in не_розкривати:
                бачено.discard(х)
                continue
            черга.append(х)
    return бачено


def tarjan_досяг(вузли, вп, цілі):
    """Для кожного вузла: чи досяжна якась ціль уперед (ітеративний Тарʼян із мемо за компонентами)."""
    індекс, низ, на_стеку, стек = {}, {}, set(), []
    комп = {}
    досяг_комп = {}
    лічильник = [0]
    for корінь in вузли:
        if корінь in індекс:
            continue
        робота = [(корінь, iter(вп.get(корінь, ())))]
        індекс[корінь] = низ[корінь] = лічильник[0]
        лічильник[0] += 1
        стек.append(корінь)
        на_стеку.add(корінь)
        while робота:
            н, ітер = робота[-1]
            рушили = False
            for х in ітер:
                if х not in індекс:
                    індекс[х] = низ[х] = лічильник[0]
                    лічильник[0] += 1
                    стек.append(х)
                    на_стеку.add(х)
                    робота.append((х, iter(вп.get(х, ()))))
                    рушили = True
                    break
                if х in на_стеку:
                    низ[н] = min(низ[н], індекс[х])
            if рушили:
                continue
            робота.pop()
            if робота:
                низ[робота[-1][0]] = min(низ[робота[-1][0]], низ[н])
            if низ[н] == індекс[н]:
                склад = []
                while True:
                    у = стек.pop()
                    на_стеку.discard(у)
                    склад.append(у)
                    if у == н:
                        break
                id = len(досяг_комп)
                ок = any(у in цілі for у in склад)
                if not ок:
                    for у in склад:
                        for х in вп.get(у, ()):
                            c = комп.get(х)
                            if c is not None and c != id and досяг_комп[c]:
                                ок = True
                                break
                        if ок:
                            break
                досяг_комп[id] = ок
                for у in склад:
                    комп[у] = id
    return {н: досяг_комп[комп[н]] for н in комп}


def відстані(старти, вп, не_розкривати=("sel",), вага=None):
    """0-1 BFS уперед: найменше число переходів через виклик (повернення/параметр) від джерела до вузла."""
    from collections import deque
    d = {н: 0 for н in старти}
    q = deque(старти)
    while q:
        н = q.popleft()
        dн = d[н]
        for х in вп.get(н, ()):
            if х[0] in не_розкривати:
                continue
            w = 1 if (х[0] == "ret" or х in вага) else 0
            if d.get(х, 1 << 30) > dн + w:
                d[х] = dн + w
                if w:
                    q.append(х)
                else:
                    q.appendleft(х)
    return d


class Аналіз:
    def __init__(s, р, реєстр):
        s.р = р
        s.реєстр = реєстр

    def виконати(s):
        р = s.р
        р.побудувати()
        s.вп_д = вперед(р.дані)
        s.вп_у = вперед(р.усі)
        s.DD = потік([SEED["D"], SEED["C"]], s.вп_д, не_розкривати=())
        s.T = потік([SEED["T"]] + [н for н in s.DD if н[0] == "txt"], s.вп_д)
        s.W = потік([SEED["W"], SEED["RXW"]], s.вп_д)
        s.F = потік([SEED["F"]], s.вп_д)
        s.D = потік([SEED["D"]], s.вп_д)
        # реєстр-код у Т: ключ кодів не дає тексту, але Д-текст береться після добування
        s.параметри = {("v", ф.fid, п) for ф in р.f_по_id.values() for п in ф.params}
        s.відст = {
            "T": відстані([SEED["T"]] + [н for н in s.DD if н[0] == "txt"], s.вп_д, вага=s.параметри),
            "W": відстані([SEED["W"], SEED["RXW"]], s.вп_д, вага=s.параметри),
            "RXW": відстані([SEED["RXW"]], s.вп_д, вага=s.параметри),
            "D": відстані([SEED["D"]], s.вп_д, вага=s.параметри),
            "C": відстані([SEED["C"]], s.вп_д, вага=s.параметри),
        }
        s.RR = s.DD
        s.сінки_усі = {з.вузол: з for з in р.записи}
        s.сінки = {з.вузол: з for з in р.записи if any(н in s.RR for н in з.контейнер)}
        s.вузли_усі = set(р.усі) | set(s.вп_у)
        s.досяг = tarjan_досяг(sorted(s.вузли_усі, key=repr), s.вп_у, set(s.сінки))
        s.досяг_д = tarjan_досяг(sorted(set(р.дані) | set(s.вп_д), key=repr), s.вп_д, set(s.сінки))
        s.оп_за_вузлом = {("op", о.id): о for о in р.оп}

    # ── чинність операції ──
    def чинна_Б(s, о, T=None):
        T = s.T if T is None else T
        суб, пар = о.суб, о.пар
        є = lambda множина, потік_: any(н in потік_ for н in множина)
        if о.вид == "doc":
            return є(суб, s.D), 4
        if о.вид == "regex":
            слова = є(пар, s.W)
            return (слова and є(суб, T), 1) if not (слова and є(суб, s.D) and not є(суб, T)) else (True, 4)
        if о.вид == "strm":
            вс = (є(суб, T) and є(пар, s.W)) or (є(суб, s.W) and є(пар, T) and о.ім_я in ("includes", "indexOf", "lastIndexOf", "find", "count", "index"))
            if вс:
                return True, 1
            if є(суб, s.D) and є(пар, s.W):
                return True, 4
            return False, 1
        if о.вид == "dictlook":
            if є(суб, T) and є(пар, s.W):
                return True, 1
            return False, 1
        if о.вид == "cmp":
            if о.ім_я in ("In", "NotIn", "Eq", "NotEq", "Is", "IsNot"):
                вс = (є(суб, T) and є(пар, s.W)) or (є(пар, T) and є(суб, s.W))
                if вс:
                    return True, 1
                if (є(суб, s.D) and є(пар, s.W)) or (є(пар, s.D) and є(суб, s.W)):
                    return True, 4
            return False, 1
        return False, 1

    def місце_вибору_ок(s, о):
        """Селекція на корені документа — крок звуження, коли її результат стає отримувачем."""
        if о.вид == "doc" and о.ім_я in ЗВУЖЕННЯ_Д:
            # знайти ('sel', id): це вузол, що залежить від суб Д на тому ж рядку
            return True
        return True

    def досягає(s, вузол):
        return s.досяг.get(вузол, False)

    def перший_сінк(s, вузол, максимум=200000):
        бачено = {вузол}
        черга = [вузол]
        кр = 0
        while черга and кр < максимум:
            н = черга.pop(0)
            кр += 1
            if н in s.сінки:
                return s.сінки[н]
            for х in s.вп_у.get(н, ()):
                if х not in бачено:
                    бачено.add(х)
                    черга.append(х)
        return None

    # ── шлях А: назад від записувачів ──
    def назад_від(s, вузол, глибина_макс=ГЛИБИНА_А):
        р = s.р
        найкращ = {вузол: 0}
        стек = [(вузол, 0)]
        оп_знайдені = set()
        ret_відвідані = set()
        while стек:
            н, г = стек.pop()
            if найкращ.get(н, 99) < г:
                continue
            if н[0] == "op":
                оп_знайдені.add(н[1])
            пм = г
            if н[0] == "ret":
                ret_відвідані.add(н[1])
                пм = г + 1
            elif н[0] == "v" and s.є_параметром(н):
                пм = г + 1
            if пм > глибина_макс:
                continue
            for у in р.усі.get(н, ()):
                if найкращ.get(у, 99) > пм:
                    найкращ[у] = пм
                    стек.append((у, пм))
        return оп_знайдені, ret_відвідані, найкращ

    def є_параметром(s, н):
        ф = s.р.f_по_id.get(н[1])
        return bool(ф and н[2] in ф.params)

    def походить_назад(s, вузли, мітка, глибина_макс=ГЛИБИНА_А):
        """Чи джерело `мітка` досяжне назад по даних із вузлів, не більше ніж через `ГЛИБИНА_А` переходів виклику."""
        д = s.відст[мітка]
        return any(д.get(н, 1 << 30) <= глибина_макс for н in вузли)

    def чинна_А(s, о):
        є = lambda множина, мітка: s.походить_назад(множина, мітка)
        суб, пар = о.суб, о.пар
        if о.вид == "doc":
            return є(суб, "D"), 4
        if о.вид == "regex":
            слова = є(пар, "W") or є(пар, "RXW")
            if слова and є(суб, "T"):
                return True, 1
            if слова and є(суб, "D"):
                return True, 4
            return False, 1
        if о.вид == "strm":
            if (є(суб, "T") and є(пар, "W")) or (є(суб, "W") and є(пар, "T") and о.ім_я in ("includes", "indexOf", "lastIndexOf", "find", "count", "index")):
                return True, 1
            if є(суб, "D") and є(пар, "W"):
                return True, 4
            return False, 1
        if о.вид == "dictlook":
            return (є(суб, "T") and є(пар, "W")), 1
        if о.вид == "cmp" and о.ім_я in ("In", "NotIn", "Eq", "NotEq", "Is", "IsNot"):
            if (є(суб, "T") and є(пар, "W")) or (є(пар, "T") and є(суб, "W")):
                return True, 1
            if (є(суб, "D") and є(пар, "W")) or (є(пар, "D") and є(суб, "W")):
                return True, 4
        return False, 1


# ═══ МІСЦЯ ═══════════════════════════════════════════════════════════════════════════════════════════════════════
ВИД_UA = {"regex": "регекс", "strm": "порівняння з рядком", "dictlook": "словник слів", "cmp": "порівняння/in зі словом",
          "doc": "добування з документа"}


class Місця:
    def __init__(s):
        s.м = {}     # (файл, рядок, пункт) -> {"шляхи": set, "чому": str}

    def додати(s, файл, рядок, пункт, шлях, чому):
        в = s.м.setdefault((файл, рядок, пункт), {"шляхи": set(), "чому": чому})
        в["шляхи"].add(шлях)
        if len(чому) < len(в["чому"]) or "→" in чому and "→" not in в["чому"]:
            в["чому"] = чому


def крок_звуження(a, о):
    """Селекція на корені документа, чий результат далі стає отримувачем (блок), місцем не є."""
    if о.вид == "doc" and о.ім_я in ЗВУЖЕННЯ_Д and о.пар:
        сел = next(iter(о.пар))
        потік_сел = потік([сел], a.вп_д, не_розкривати=())
        return сел in a.р.приймачі or bool(потік_сел & a.р.приймачі)
    return False


def вузол_досягу(о):
    return next(iter(о.пар)) if (о.вид == "doc" and о.ім_я in ЗВУЖЕННЯ_Д and о.пар) else ("op", о.id)


def літерали_значення(е, глиб=0):
    """Рядкові літерали, що можуть стати значенням виразу (гілки умови, `or`, елементи списку)."""
    if е is None or глиб > 6:
        return []
    if е.k == "str":
        return [(е.v, е.line)]
    if е.k in ("cond",):
        return літерали_значення(е.a[1], глиб + 1) + літерали_значення(е.a[2], глиб + 1)
    if е.k == "bool":
        return [x for ч in е.a for x in літерали_значення(ч, глиб + 1)]
    if е.k == "list":
        return [x for ч in е.a for x in літерали_значення(ч, глиб + 1)]
    return []


def обчислити(a, корінь, пункти=None):
    import time
    ч0 = time.time()
    р, реєстр = a.р, a.реєстр
    м = Місця()
    опи_Б, опи_А = {}, {}
    # ── Б: від читачів вперед ──
    for о in р.оп:
        ок, п = a.чинна_Б(о)
        if not ок:
            continue
        if крок_звуження(a, о):
            continue
        вуз = вузол_досягу(о)
        if not a.досягає(вуз):
            continue
        опи_Б[о.id] = п
    if os.environ.get("RZR_TIME"):
        print("Б: %.1f с" % (time.time() - ч0), file=sys.stderr)
    # ── А: від записувачів назад ──
    рети_А = set()
    слайси = {}
    кеш_А = set()
    for з in р.записи:
        слайси[з.id] = a.назад_від(з.вузол)
        ops, rets, _ = слайси[з.id]
        рети_А |= rets
        for id in ops:
            if id in кеш_А:
                continue
            о = р.оп[id]
            ок, п = a.чинна_А(о)
            кеш_А.add(id)
            if ок and not крок_звуження(a, о):
                опи_А[id] = (п, з)
    for id in set(опи_Б) | set(опи_А):
        о = р.оп[id]
        п = опи_Б.get(id) or опи_А[id][0]
        сінк = опи_А[id][1] if id in опи_А else a.перший_сінк(вузол_досягу(о))
        ключ = сінк.ключ if сінк else "?"
        де = "%s:%d" % (сінк.файл, сінк.рядок) if сінк else "?"
        if п == 4:
            чому = "добування з кореня документа сторінки (%s «%s») → запис «%s» (%s)" % (ВИД_UA.get(о.вид, о.вид), о.ім_я, ключ, де)
        else:
            чому = "%s «%s» над текстом речі → запис «%s» (%s)" % (ВИД_UA.get(о.вид, о.вид), о.ім_я, ключ, де)
        for шл, джерело in (("Б", опи_Б), ("А", опи_А)):
            if id in джерело:
                м.додати(о.файл, о.рядок, п, шл, чому)
    if os.environ.get("RZR_TIME"):
        print("А: %.1f с" % (time.time() - ч0), file=sys.stderr)
    # ── п.2а (А): літерал поза реєстром у записі поля коду ──
    for з in р.записи:
        родина = реєстр.родина_ключа(з.ключ)
        if not родина or з.вираз is None or з.файл.split("/")[-1].replace(".py", "") in реєстр.модулі_реєстру:
            continue
        дозв = реєстр.дозволені(родина)
        for лит, рядок in літерали_значення(з.вираз):
            if лит not in дозв and len(лит) <= 60:
                м.додати(з.файл, рядок, 2, "А", "літерал «%s» у записі «%s» — кода нема в реєстрі %s" % (лит, з.ключ, родина))
    # ── п.2б: власні переліки кодів ──
    F = a.F
    # похідні поля коду: повернення виводячих функцій (див. нижче) — додаємо після п.1
    дер_ret = set()
    досяжні_від_оп = потік([("op", i) for i in set(опи_Б) | set(опи_А)], a.вп_у, не_розкривати=())
    for н in досяжні_від_оп:
        if н[0] == "ret":
            дер_ret.add(н[1])
    F2 = потік([SEED["F"]] + [("ret", f) for f in дер_ret], a.вп_д)
    мітка_к = {}
    for (id, файл, рядок, родина, коди, fid, вид) in р.контейнери:
        for н in потік([("cont", id)], a.вп_д):
            мітка_к.setdefault(н, set()).add(id)
    вжитки = {}
    for (файл, рядок, ад, бд, вид, fid) in р.пари_контейнер:
        ід_а = set().union(*(мітка_к[н] for н in ад if н in мітка_к)) if any(н in мітка_к for н in ад) else set()
        ід_б = set().union(*(мітка_к[н] for н in бд if н in мітка_к)) if any(н in мітка_к for н in бд) else set()
        if ід_а and any(н in F2 for н in бд):
            for id in ід_а:
                вжитки.setdefault(id, (файл, рядок, вид))
        if ід_б and any(н in F2 for н in ад):
            for id in ід_б:
                вжитки.setdefault(id, (файл, рядок, вид))
    for (id, файл, рядок, родина, коди, fid, вид) in р.контейнери:
        if id in вжитки:
            ф2, р2, в2 = вжитки[id]
            м.додати(файл, рядок, 2, "Б", "перелік кодів %s %s поза реєстром порівнюють/групують значення поля коду (%s:%d)" % (родина, "/".join(коди[:3]), ф2, р2))
    for з in р.записи:
        if реєстр.родина_ключа(з.ключ) is None and з.ключ not in КЛЮЧІ_КОДУ:
            continue
        ops, rets, найкращ = слайси[з.id]
        for н in найкращ:
            if н[0] == "cont":
                (id, файл, рядок, родина, коди, fid, вид) = р.контейнери[н[1]]
                м.додати(файл, рядок, 2, "А", "перелік кодів %s %s поза реєстром обчислює запис поля «%s» (%s:%d)" % (родина, "/".join(коди[:3]), з.ключ, з.файл, з.рядок))
    if os.environ.get("RZR_TIME"):
        print("п.2: %.1f с" % (time.time() - ч0), file=sys.stderr)
    # ── п.3: повторне виведення ──
    fids_Б = set(дер_ret)
    fids_А = {fid for fid in рети_А if any(р.оп[i].ф == fid for i in опи_А)}
    for шл, множина in (("Б", fids_Б), ("А", fids_А)):
        for (id, файл, рядок, caller, кал) in р.виклики:
            if not any(k in множина for k in кал) or caller.fid in множина or caller.name == "<модуль>" and False:
                continue
            вуз = ("call", id)
            if a.досяг_д.get(вуз, False) or вуз not in a.T:
                continue
            ім = р.f_по_id[кал[0]].name
            м.додати(файл, рядок, 3, шл, "виклик «%s» виводить поле зі слів повторно: результат не йде в запис поля" % ім)
    return м


# ═══ ФАЙЛИ, ВИВІД ═══════════════════════════════════════════════════════════════════════════════════════════════
def шлях_продукту(відн):
    части = відн.split("/")
    ім = os.path.splitext(части[-1])[0]
    if any(ч in НЕ_ТЕКИ or ч.startswith("дані_") for ч in части[:-1]):
        return False
    return not НЕ_ШЛЯХ_ІМ.match(ім)


def знайти_файли(корінь):
    py, js = [], []
    for тека in ТЕКИ_Py:
        for кат, теки, файли in os.walk(os.path.join(корінь, тека)):
            теки[:] = sorted(д for д in теки if д not in НЕ_ТЕКИ and not д.startswith("дані_") and not д.startswith("."))
            for ф in sorted(файли):
                відн = os.path.relpath(os.path.join(кат, ф), корінь).replace(os.sep, "/")
                if ф.endswith(".py") and шлях_продукту(відн):
                    py.append(відн)
                elif ф.endswith(".js") and відн.startswith("джерела/показ/") and шлях_продукту(відн):
                    js.append(відн)
    for ф in ФАЙЛИ_JS:
        if os.path.exists(os.path.join(корінь, ф)):
            js.append(ф)
    return sorted(set(py)), sorted(set(js))


def вбудовані_скрипти(текст):
    """[(зсув_рядків, код)] — вбудовані `<script>` без `src` у HTML."""
    вих = []
    for м in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", текст, re.S | re.I):
        вих.append((текст.count("\n", 0, м.start(1)), м.group(1)))
    return вих


def розібрати_всі_js(корінь, файли, html_файли):
    ходи = []
    помилки = []
    shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "корінь_річ_запис_речі_js.js")
    тимч = []
    джерела = {}
    for ф in файли:
        джерела[ф] = (os.path.join(корінь, ф), 0)
    import tempfile
    теки = tempfile.mkdtemp(prefix="rzr_js_")
    for ф in html_файли:
        текст = open(os.path.join(корінь, ф), encoding="utf8").read()
        for i, (зсув, код) in enumerate(вбудовані_скрипти(текст)):
            шлях = os.path.join(теки, "%s#%d.js" % (os.path.basename(ф), i))
            open(шлях, "w", encoding="utf8").write(код)
            джерела["%s#%d" % (ф, i)] = (шлях, зсув)
    if not джерела:
        return [], помилки
    шляхи = [v[0] for v in джерела.values()]
    try:
        out = subprocess.run(["node", "--expose-internals", shim] + шляхи, capture_output=True, text=True, timeout=300)
        дані = json.loads(out.stdout or "{}")
    except (OSError, ValueError, subprocess.TimeoutExpired) as е:
        return [], ["JS не розібрано (node): %s" % е]
    if "помилка" in дані:
        return [], ["JS не розібрано: %s" % дані["помилка"]]
    for ім, (шлях, зсув) in джерела.items():
        дер = дані.get(шлях)
        if not isinstance(дер, dict) or "помилка" in дер:
            помилки.append("%s: %s" % (ім, (дер or {}).get("помилка", "нема дерева")))
            continue
        ходи.append(розібрати_js(ім.split("#")[0] if "#" in ім else ім, дер, зсув))
    import shutil
    shutil.rmtree(теки, ignore_errors=True)
    return ходи, помилки


def побудувати_модулі(корінь):
    py, js = знайти_файли(корінь)
    модулі, помилки = [], []
    for ф in py:
        try:
            текст = open(os.path.join(корінь, ф), encoding="utf8").read()
        except (OSError, UnicodeDecodeError) as е:
            помилки.append("%s: %s" % (ф, е))
            continue
        модулі.append(розібрати_py(ф, текст))
    html = [ф for ф in ("джерела/показ.html",) if os.path.exists(os.path.join(корінь, ф))]
    мJ, пJ = розібрати_всі_js(корінь, js, html)
    # унікальні імена файлів html#N → ім'я html
    модулі += мJ
    помилки += пJ
    return модулі, помилки, py, js + html


def головна(арги):
    import argparse
    ап = argparse.ArgumentParser()
    ап.add_argument("--корінь", default=".")
    ап.add_argument("--json", action="store_true")
    ап.add_argument("--тихо", action="store_true")
    ап.add_argument("--вибірка", type=int, default=0)
    ап.add_argument("--зерно", type=int, default=1)
    ап.add_argument("--пункт", type=int, default=0)
    ар = ап.parse_args(арги)
    корінь = os.path.abspath(ар.корінь)
    os.chdir(корінь)
    модулі, помилки, py, js = побудувати_модулі(корінь)
    реєстр = Реєстр(корінь)
    р = Рушій(модулі, реєстр)
    a = Аналіз(р, реєстр)
    a.виконати()
    м = обчислити(a, корінь)
    рядки = sorted(м.м.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2]))
    різні = {(ф, р_) for (ф, р_, п) in м.м}
    за_пунктами = {п: len({(ф, р_) for (ф, р_, п2) in м.м if п2 == п}) for п in (1, 2, 3, 4)}
    if ар.json:
        print(json.dumps({"місць": len(різні), "за_пунктами": за_пунктами,
                          "місця": [{"файл": ф, "рядок": р_, "пункт": п, "шляхи": sorted(в["шляхи"]), "чому": в["чому"]}
                                    for (ф, р_, п), в in рядки]}, ensure_ascii=False, indent=1))
        return 0
    if not ар.тихо:
        for (ф, р_, п), в in рядки:
            if ар.пункт and п != ар.пункт:
                continue
            print("%s:%d · пункт %d · %s [%s]" % (ф, р_, п, в["чому"], "+".join(sorted(в["шляхи"]))))
    print("")
    print("файлів: Python %d, JS %d; функцій %d; вузлів %d" % (len(py), len(js), len(р.f_по_id), len(a.вузли_усі)))
    for п_, н_ in sorted(за_пунктами.items()):
        print("пункт %d: %d" % (п_, н_))
    для_розбіжностей = [(k, v) for k, v in рядки if len(v["шляхи"]) == 1]
    print("розбіжності шляхів: %d з %d" % (len(для_розбіжностей), len(рядки)))
    if not ар.тихо:
        for (ф, р_, п), в in для_розбіжностей[:60]:
            шл = next(iter(в["шляхи"]))
            print("  %s:%d · пункт %d · знайдено лише шляхом %s" % (ф, р_, п, шл))
    for п_ in помилки[:20]:
        print("увага: " + п_)
    print("місць: %d" % len(різні))
    return 0


if __name__ == "__main__":
    sys.exit(головна(sys.argv[1:]))
