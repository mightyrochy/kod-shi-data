# -*- coding: utf-8 -*-
"""прилади/корінь_річ_запис_речі.py — прилад кореня Річ-запис-речі за класом 30.10 паспорта
`аудит/корені/Річ-запис-речі.md` («Клас місць»): місця коду на МЕЖІ ЗАПИСУ РЕЧІ, Python і JS однаково.

ОДИНИЦЯ — межа запису, а не потік наслідків: (1) запис поля в запис речі, (2) визначення переліку кодів / запис коду
поза реєстром, (3) читання текстового поля запису, (4) добування тексту з кореня документа сторінки крамниці.

ЗАПИС впізнається ЗА ШЛЯХОМ, а не за ключами, їх кількістю чи іменем змінної. Розбір (`…_розбір.py`) зводить Python
і JS до одного подання; тут — аналіз вказівників за місцем створення об'єкта (flow-insensitive, до нерухомої точки):
  • запис — об'єкт, що (а) прочитано з файлу каталогу/фіду/журналу жнив (`json.load` шляху `каталог…`, `.jsonl`,
    `brief`…) чи з відповіді мережі (`.json()`); (б) складено з тексту, добутого зі сторінки чи фіду (слова крамниці
    в полі); (в) покладено в запис-контейнер чи записано на шляху каталогу (`dump`/`write`); лежить усередині запису;
  • ПОЛЕ — будь-який ключ запису. РОЛЬ ключа береться з даних: текстове — його пишуть із тексту сторінки/фіду чи
    іншого текстового поля; кодове — його пишуть кодами реєстру (`slots.py`, схема `внутрішня_мова.schema.json`) чи
    ключ родини реєстру. Переліку ключів у приладі нема;
  • текст речі — тільки те, що має походження: текст вузла сторінки/фіду, текстове поле запису, їхні похідні.
ПУНКТИ (механічні, кожен — місце з рядком і причиною):
  1  запис поля коду/слів у запис, значення чи умова якого — результат ЧИТАЧА СЛІВ над текстом речі (регекс зі
     словом, `in`/порівняння/`startswith`/`replace` зі словом, пошук тексту в словнику слів);
  2  (а) запис у кодове поле запису літерала поза реєстром, чи самого поля нема в реєстрі; (б) власний перелік чи
     словник кодів (≥2 коди однієї родини реєстру) поза реєстром, яким порівнюють/групують/впорядковують значення
     кодового поля запису; місце — де перелік визначено. Порівняння з ОДНИМ кодом — читання, не місце;
  3  текстове поле взято із запису у читач слів (регекс, словник, `in`, порівняння) — місце саме читання поля;
  4  текст з КОРЕНЯ документа сторінки крамниці (`get_text`/`.text`/`content` без звуження селектором вузла товару;
     `body`/`html` — не звуження; JS із `document`, що виконується на сторінці, — `.evaluate`), який дійшов до запису.

Не місця: проби, прилади, тести (`джерела/проби`, `прилади`, `тест_*`) — поза класом; `document` інтерфейсу Люстерка.
СТАН (30.10, третя спроба, ще не прийнято): прицільні проби звітів #2330 — 10 з 10 (талія, одноключовий запис, `body`,
вузол товару, весь документ, `.evaluate`, JS через крапку, кеш і рамка — не запис); число на `main` 146 (п.1: 23, п.2: 103,
п.3: 22, п.4: 2), однакове на Python 3.11–3.13. Вибірка 20 місць: ~11 у класі, ~7 хибних, ~2 неясні (див. PR). Межа
підходу: аналіз вказівників без типів і без контексту викликів змішує потоки загальних допоміжних функцій — запис
визначається як «об'єкт, що несе слова крамниці чи прочитано з файлу каталогу», а далі шлях до картки через виклики
допоміжних функцій обривається (пропуски); див. паспорт, «Невдалі підходи».

Вивід: `файл:рядок · пункт · чому`, підсумки за пунктами, останній рядок `місць: <N>` (різних `файл:рядок`), код 0.
Запуск з кореня репозиторію: python3 джерела/прилади/корінь_річ_запис_речі.py [--корінь <шлях>] [--json] [--тихо]
[--пункт N] [--вибірка N --зерно S] — вивід однаковий на Python 3.11–3.13 (немає залежності від порядку множин).
"""
import ast
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from корінь_річ_запис_речі_розбір import E, розібрати_js, розібрати_py  # noqa: E402

sys.setrecursionlimit(20000)
ТЕКИ_Py = ("джерела", "zhnyvarka")
ФАЙЛИ_JS = ("джерела/worker_джерело.js",)
ТЕКИ_JS = ("джерела/показ",)
НЕ_ТЕКИ = ("проби", "прилади", "аудит", "node_modules", "розвідка", "дані_", "__pycache__", "траса", "фікстури")
НЕ_ШЛЯХ_ІМ = re.compile(r"^(тест|gate_|audit_|стенд|батарея_|measure_|pair_test|мутанти|replay|проба)")
РЕЄСТРОВІ_МОДУЛІ = frozenset(("slots", "внутрішня_мова"))

Є_СЛОВО = re.compile(r"[A-Za-zА-Яа-яЇїІіЄєҐґ]+")
ЕСКЕЙП = re.compile(r"\\[A-Za-z]|\(\?[A-Za-z:=!<P]*(<[A-Za-z_]+>)?|\[:[a-z]+:\]|\\p\{[A-Za-z]+\}")
ШЛЯХ_ЗАПИСІВ = re.compile(r"(каталог|catalog)[^/\"']*\.(xml|jsonl?)(\.gz)?$|\.jsonl|brief|/сирі|^сирі", re.I)
ВЕРХ_ДОКУМЕНТА = re.compile(r"document\s*\.\s*(body|documentElement|title|head)\b|"
                            r"querySelector(All)?\(\s*['\"`](body|html|\*|:root)['\"`]\s*\)")
ВУЗОЛ_ДОКУМЕНТА = re.compile(r"document\s*\.\s*(querySelector|querySelectorAll|getElementById|getElementsBy\w+)\b")
КОД_ЛІТЕРАЛ = re.compile(r"^[a-z][a-z0-9_]{2,40}$")

ТЕКСТ = ("TP", "TN", "TF", "TR")                        # текст кореня сторінки / вузла / фіду / текстового поля
АТРИБУТИ_ТЕКСТУ = frozenset(("text", "textContent", "innerText", "innerHTML", "outerHTML", "string", "strings",
                             "stripped_strings", "inner_html", "title"))
МЕТОДИ_ТЕКСТУ = frozenset(("get_text", "getText", "findtext", "inner_text", "text_content", "itertext", "gettext",
                           "content", "inner_html", "outer_html"))
МЕТОДИ_ВУЗЛА = frozenset(("select", "select_one", "find", "find_all", "findAll", "xpath", "querySelector",
                          "querySelectorAll", "getElementById", "getElementsByClassName", "getElementsByTagName",
                          "css", "closest", "find_parent", "find_next", "find_previous", "children", "descendants",
                          "locator", "query_selector", "query_selector_all", "findall", "iter", "iterfind",
                          "find_next_sibling", "find_all_next", "parent", "item", "get_by_role", "get_by_text"))
КОРЕНІ_СТОРІНКИ = frozenset(("BeautifulSoup", "HTML", "Selector", "document_fromstring", "fragment_fromstring"))
КОРЕНІ_ФІДУ = frozenset(("XML", "ElementTree", "iterparse", "parseString", "XMLParser", "fromstringlist"))
ШЛЯХИ_РОЗБОРУ_ФІДУ = frozenset(("ET", "etree", "ElementTree", "minidom", "defusedxml"))
КОРЕНІ_СТОРІНКИ_МОДУЛІ = frozenset(("html", "lxml", "bs4", "parsel"))
ЧИТАННЯ_JSON = frozenset(("load", "loads", "parse"))
ЗАПИС_ФАЙЛА = frozenset(("dump", "write", "write_text", "writelines", "write_bytes"))
МЕТОДИ_РЕГЕКС = frozenset(("search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split", "test",
                           "exec", "matchAll", "replace", "replaceAll"))
МЕТОДИ_РЯДКА_БУЛ = frozenset(("startswith", "endswith", "startsWith", "endsWith", "includes", "find", "rfind",
                              "index", "rindex", "count", "indexOf", "lastIndexOf", "has", "contains", "isdisjoint"))
МЕТОДИ_РЯДКА_ТЕКСТ = frozenset(("replace", "replaceAll", "removeprefix", "removesuffix", "partition", "rpartition",
                                "lstrip", "rstrip", "strip", "split", "rsplit", "trim"))
ПЕРЕДАЮТЬ = frozenset(("lower", "upper", "title", "capitalize", "casefold", "strip", "lstrip", "rstrip", "split",
                       "rsplit", "join", "format", "splitlines", "encode", "decode", "toLowerCase", "toUpperCase",
                       "trim", "trimStart", "trimEnd", "slice", "substring", "substr", "normalize", "concat", "at",
                       "charAt", "padStart", "padEnd", "toString", "group", "groups", "groupdict", "read", "open",
                       "strip", "readline", "readlines", "copy", "deepcopy", "get_text", "sorted", "list", "tuple",
                       "set", "dict", "str", "reversed", "join", "dumps", "dump", "loads_text", "Path", "join_path",
                       "resolve", "with_name", "with_suffix", "joinpath", "abspath", "dirname", "basename", "parent",
                       "unescape", "escape", "quote", "unquote", "urljoin", "format_map", "translate", "zfill",
                       "ljust", "rjust", "center", "swapcase", "expandtabs", "values", "keys", "sort", "reverse",
                       "flat", "unique", "enumerate", "zip", "filter", "next", "iter", "chain", "from_iterable",
                       "islice", "reduce", "assign", "freeze", "entries", "Object", "Array", "from", "of"))
ЗБЕРІГАЮТЬ = frozenset(("append", "add", "push", "appendleft", "unshift", "insert", "extend", "extendleft", "update",
                       "setdefault", "assign"))
ДЛЯ_ПЕРЕБОРУ = frozenset(("map", "forEach", "filter", "find", "findIndex", "some", "every", "flatMap", "reduce",
                          "sort", "sorted", "min", "max"))
НЕ_РОЗРІШУВАТИ = frozenset(("get", "set", "items", "values", "keys", "append", "extend", "add", "update", "pop",
                            "copy", "join", "split", "strip", "lower", "upper", "replace", "format", "read", "write",
                            "close", "open", "startswith", "endswith", "find", "index", "count", "sort", "remove",
                            "insert", "clear", "encode", "decode", "run", "then", "catch", "push", "map", "filter",
                            "forEach", "includes", "indexOf", "slice", "has", "delete", "setdefault", "json",
                            "text", "test", "exec", "match", "search", "sub", "toString", "isinstance", "len"))
МЕРЕЖА = frozenset(("requests", "httpx", "urllib", "aiohttp", "session", "sess", "client", "http"))
РОДИНИ_КЛЮЧІВ = (
    ("slot", ("слот", "slot", "слоти", "slots", "alt_slots", "комплект")),
    ("item_type", ("тип", "item_type", "тип_набору", "set_kind")),
    ("fabric", ("тканина", "fabric", "матеріал_коди", "погодні_матеріали", "склад_коди")),
    ("material", ("матеріал", "material")),
    ("pattern", ("візерунок", "pattern", "принт")),
    ("length", ("довжина", "length")),
    ("cut", ("крій", "cut")),
)


# ═══ РЕЄСТР ═════════════════════════════════════════════════════════════════════════════════════════════════════
class Реєстр:
    """Реєстр кодів з дерева: `slots.py` (слоти, типи), схема `внутрішня_мова.schema.json` (`x-таблиця`) і крої
    `силует_реєстр.py`. Імена полів реєстру — властивості схем (`properties`)."""
    РОДИНИ_СХЕМИ = ("slot", "item_type", "fabric", "material", "pattern", "length")

    def __init__(s, корінь):
        s.родини, s.назви_ua, s.поля = {}, {}, set()
        таб = {}
        for ім in ("внутрішня_мова.schema.json", "каталог_розбір.schema.json"):
            try:
                схема = json.load(open(os.path.join(корінь, "джерела", ім), encoding="utf8"))
            except (OSError, ValueError):
                continue
            if ім.startswith("внутрішня"):
                таб = схема.get("x-таблиця", {})
            s._властивості(схема)
        for р in s.РОДИНИ_СХЕМИ:
            ф = таб.get(р) or {}
            s.родини[р] = set(ф) if isinstance(ф, (dict, list)) else set()
            if isinstance(ф, dict):
                s.назви_ua[р] = {str(v) for v in ф.values()}
        s.родини["cut"] = set()
        try:
            дерево = ast.parse(open(os.path.join(корінь, "джерела", "slots.py"), encoding="utf8").read())
        except (OSError, SyntaxError):
            дерево = None
        for н in (дерево.body if дерево else []):
            if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
                ім = н.targets[0].id
                s.поля.add(ім)
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
        try:
            for н in ast.parse(open(os.path.join(корінь, "джерела", "силует_реєстр.py"), encoding="utf8").read()).body:
                if isinstance(н, ast.Assign) and isinstance(н.targets[0], ast.Name) and н.targets[0].id == "КРОЇ" \
                        and isinstance(н.value, ast.Dict):
                    s.родини["cut"] |= {к.value for к in н.value.keys if isinstance(к, ast.Constant) and isinstance(к.value, str)}
        except (OSError, SyntaxError):
            pass
        for р in list(s.родини):
            s.родини[р].discard("unknown")
        s.коди = frozenset().union(*s.родини.values())
        s.назви = frozenset().union(*s.назви_ua.values()) if s.назви_ua else frozenset()
        s.ключі_родин = {к: р for р, ключі in РОДИНИ_КЛЮЧІВ for к in ключі if s.родини.get(р)}
        s.поля |= set(s.ключі_родин)
        s.чужі_ключі = frozenset(("type", "kind", "причина", "чому", "ремонт", "source", "state", "стан", "role"))

    def _властивості(s, o):
        if isinstance(o, dict):
            for к, v in sorted(o.items()):
                if к == "properties" and isinstance(v, dict):
                    s.поля |= set(v)
                s._властивості(v)
        elif isinstance(o, list):
            for v in o:
                s._властивості(v)

    def дозволені(s, ключ):
        р = s.ключі_родин.get(ключ)
        база = s.родини.get(р, set()) | s.назви_ua.get(р, set()) if р else s.коди | s.назви
        return base_or(база)

    def сім_я(s, елементи):
        ел = {e for e in елементи if isinstance(e, str)}
        if len(ел) < 2:
            return None
        найкраща = None
        for р in sorted(s.родини):
            n = len(ел & s.родини[р])
            if n >= 2 and n * 2 >= len(ел) and (найкраща is None or n > найкраща[1]):
                найкраща = (р, n)
        return найкраща[0] if найкраща else None


def base_or(множина):
    return set(множина) | {"", "unknown", "невідомо", "none", "None"}


def слово_в_літералі(т):
    return isinstance(т, str) and bool(Є_СЛОВО.search(т))


def слово_в_регексі(т):
    return isinstance(т, str) and bool(Є_СЛОВО.search(ЕСКЕЙП.sub("", т)))


# ═══ ОБ'ЄКТИ ═══════════════════════════════════════════════════════════════════════════════════════════════════
class О:
    """Абстрактний об'єкт — за місцем створення. вид: dict list tuple pairs rec feed page node rx file."""
    __slots__ = ("id", "вид", "файл", "рядок", "пол", "рек", "родина", "шаблон_слів")

    def __init__(s, id_, вид, файл, рядок):
        s.id, s.вид, s.файл, s.рядок = id_, вид, файл, рядок
        s.пол, s.рек, s.родина, s.шаблон_слів = {}, вид == "rec", None, False


def об(v):
    return isinstance(v, О)


# ═══ АНАЛІЗ ═════════════════════════════════════════════════════════════════════════════════════════════════════
МЕЖІ_ВИДУ = {"obj": 24, "L": 12}
МЕЖА_ІНШОГО = 16
МЕЖА_НАБОРУ = 12
МЕЖА_ВИКЛИКІВ = 12
МЕЖА_ТЕГІВ = 5
ЗАГАЛЬНІ_СЛОВА = frozenset(("none", "source", "high", "medium", "other", "mixed", "solid", "unknown", "hex"))


def ключ_порядку(v):
    return (0, v.id, "") if isinstance(v, О) else (1, 0, v[0] + "\0" + str(v[1:]))


def влити(ціль, вал):
    """Об'єднує вал у ціль; у кожному виді лишає не більше K перших за порядком (top-K асоціативне: результат не
    залежить від порядку внесків, тож загальні допоміжні функції не змішують весь продукт в одну множину й
    розрахунок сходиться). Повертає, чи змінилась множина."""
    нове = вал - ціль if not isinstance(вал, frozenset) else вал.difference(ціль)
    if not нове:
        return False
    if len(ціль) + len(нове) <= МЕЖА_НАБОРУ:
        ціль |= нове
        return True
    старе = frozenset(ціль)
    ціль |= нове
    лічба = {}
    for v in ціль:
        вид = "obj" if isinstance(v, О) else v[0]
        лічба[вид] = лічба.get(вид, 0) + 1
    if any(н > МЕЖІ_ВИДУ.get(вид, МЕЖА_ІНШОГО) for вид, н in лічба.items()):
        групи = {}
        for v in sorted(ціль, key=ключ_порядку):
            вид = "obj" if isinstance(v, О) else v[0]
            групи.setdefault(вид, []).append(v)
        ціль.clear()
        for вид in sorted(групи):
            ціль.update(групи[вид][:МЕЖІ_ВИДУ.get(вид, МЕЖА_ІНШОГО)])
    return ціль != старе


class Аналіз:
    def __init__(s, модулі, реєстр):
        s.реєстр, s.модулі = реєстр, модулі
        s.функції = [ф for м in модулі for ф in м.функції]
        s.по_імені_модуля = {}
        for м in модулі:
            s.по_імені_модуля.setdefault(м.ім_я, м)
        s.у_модулі, s.методи, s.js_глобальні = {}, {}, {}
        for м in модулі:
            for ф in м.функції:
                if ф.name == "<модуль>":
                    continue
                s.у_модулі.setdefault((м.ім_я, ф.name), []).append(ф)
                if ф.cls:
                    s.методи.setdefault(ф.name, []).append(ф)
                if м.мова == "js":
                    s.js_глобальні.setdefault(ф.name, []).append(ф)
        s.призначені = {ф.fid: s.призначені_імена(ф) for ф in s.функції}
        s.виклики_за_іменем = {}
        for ф in s.функції:
            for оп in ф.stmts:
                s.порахувати_виклики(оп.val)
                for у in оп.ctrl:
                    s.порахувати_виклики(у)
        s.вкладені = {}
        for ф in s.функції:
            if ф.parent is not None:
                s.вкладені.setdefault((ф.parent.fid, ф.name), []).append(ф)
        s.env, s.ret, s.об = {}, {}, {}
        s.лічильник = 0
        s.ТЕКСТОВІ_КЛЮЧІ, s.КОДОВІ_КЛЮЧІ = set(), set(s.реєстр.ключі_родин)
        s.КОДИ_ЗАПИСІВ, s.ЧИТАНІ_З_ФАЙЛУ = {}, set()
        s.КОДОВІ_ДАНІ = set()      # ключі, що їх у запис пишуть кодами (роль з даних, не з переліку написань)
        s.записи = {}              # (id вузла, id об'єкта, ключ) → (О, ключ, значення, файл, рядок, умови D)
        s.читання3 = {}            # місце читання поля → причина (пункт 3)
        s.використання_переліків = {}   # id об'єкта-переліку → (файл, рядок використання)
        s.змін = 0
        s.рядкові_константи = {}
        s.пам = {}
        s.умови = frozenset()
        s.мф = {м.файл: м for м in модулі}

    def порахувати_виклики(s, е):
        if е is None or not hasattr(е, "k"):
            return
        if е.k == "call" and е.a:
            ім = е.a[0].v if е.a[0].k in ("name", "attr") else None
            if ім:
                s.виклики_за_іменем[ім] = s.виклики_за_іменем.get(ім, 0) + 1
        if е.k == "comp":
            for ц, i, умови in е.v:
                s.порахувати_виклики(i)
                for у in умови:
                    s.порахувати_виклики(у)
        for а in е.a:
            if hasattr(а, "k"):
                s.порахувати_виклики(а)

    # ── допоміжне ─────────────────────────────────────────────────────────────────────────────────────────────
    @staticmethod
    def призначені_імена(ф):
        вих = set(ф.params)

        def з_цілі(е):
            if е is None:
                return
            if е.k == "name":
                вих.add(е.v)
            elif е.k in ("list", "star"):
                for x in е.a:
                    з_цілі(x)
        for оп in ф.stmts:
            if оп.k == "assign":
                for т in оп.t:
                    з_цілі(т)
            elif оп.k == "iter":
                з_цілі(оп.t)
        return вих

    def новий(s, е, вид, ф):
        к = id(е)
        о = s.об.get(к)
        if о is None:
            s.лічильник += 1
            о = s.об[к] = О(s.лічильник, вид, ф.file, е.line)
        return о

    def змінна(s, ф, ім):
        g = ф
        while g is not None:
            if ім in s.призначені[g.fid]:
                return (g.fid, ім), g
            g = g.parent
        м = s.по_імені_модуля.get(ф.mod)
        return None, м

    def читати_ім(s, ф, ім):
        к, _ = s.змінна(ф, ім)
        if к is not None:
            return s.env.get(к, ())
        м = s.мф.get(ф.file)
        if м is not None:
            ал = м.псевдоніми.get(ім)
            if ал and ал[0] == "name":
                ц = s.по_імені_модуля.get(ал[1])
                if ц is not None and ц.тіло is not None:
                    return s.env.get((ц.тіло.fid, ал[2]), ())
        return ()

    def писати_ім(s, ф, ім, вал):
        к, _ = s.змінна(ф, ім)
        if к is None:
            к = (ф.fid, ім)
        старе = s.env.get(к)
        if старе is None:
            s.env[к] = set()
            старе = s.env[к]
        if влити(старе, вал):
            s.змін += 1

    def зберегти_в_об(s, о, ключ, вал):
        if not вал:
            return
        цільове = о.пол.setdefault(ключ, set())
        if влити(цільове, вал):
            s.змін += 1
        if о.рек:
            s.позначити_запис(вал)
        elif ключ == "*" and any(об(v) and v.рек for v in вал):
            s.позначити_запис({о})

    def позначити_запис(s, вал):
        """Об'єкт у записі — теж запис (з усім, що в ньому лежить). Інваріант: запис має лише записи в полях."""
        стек = [v for v in вал if об(v)]
        while стек:
            v = стек.pop()
            if v.рек or v.вид in ("rx", "file", "page", "node", "feed", "dom"):
                continue
            v.рек = True
            s.змін += 1
            for ключ in v.пол:
                стек.extend(x for x in v.пол[ключ] if об(x) and not x.рек)

    # ── вирази ────────────────────────────────────────────────────────────────────────────────────────────────
    def ev(s, е, ф):
        к = id(е)
        р = s.пам.get(к)
        if р is not None:
            return р
        s.пам[к] = frozenset()      # цикл
        р = s._ev(е, ф)
        s.пам[к] = р
        return р

    @staticmethod
    def лише(вал, *типи):
        return {v for v in вал if not об(v) and v[0] in типи}

    def місце(s, ф, е):
        return "%s:%d" % (ф.file, е.line)

    def тексти(s, вал):
        return {v for v in вал if not об(v) and v[0] in ТЕКСТ}

    def _ev(s, е, ф):
        k = е.k
        if k == "name":
            return frozenset(s.читати_ім(ф, е.v))
        if k == "str":
            if not isinstance(е.v, str) or len(е.v) > 80 or not е.v:
                return frozenset()
            return frozenset({("L", е.v)})
        if k == "const" or k == "regex":
            if k == "regex" and слово_в_регексі(е.v):
                о = s.новий(е, "rx", ф)
                о.шаблон_слів = True
                return frozenset({о})
            return frozenset()
        if k == "fstr" or k == "bin" or k == "bool" or k == "other" or k == "star":
            р = set()
            for а in е.a:
                р |= s.ev(а, ф)
            return frozenset(р)
        if k == "not":
            return frozenset(s.лише(s.ev(е.a[0], ф), "D"))
        if k == "cond":
            ум = s.лише(s.ev(е.a[0], ф), "D")
            return frozenset(s.ev(е.a[1], ф) | s.ev(е.a[2], ф) | ум)
        if k == "cmp":
            return s.порівняння(е, ф)
        if k == "attr":
            return s.атрибут(е, ф)
        if k == "sub":
            return s.підстановка(е, ф)
        if k == "call":
            return s.виклик(е, ф)
        if k == "list":
            о = s.новий(е, "tuple" if е.v in ("Tuple", "Set") else "list", ф)
            for i, а in enumerate(е.a):
                v = s.ev(а, ф)
                s.зберегти_в_об(о, "*", v)
                s.зберегти_в_об(о, str(i), v)
            s.позначити_перелік(о, [a for a in е.a if a.k == "str"], ф)
            return frozenset({о})
        if k == "dict":
            return frozenset({s.словник(е, ф)})
        if k == "comp":
            return s.включення(е, ф)
        if k == "walrus":
            v = s.ev(е.a[0], ф)
            s.писати_ім(ф, е.v, v)
            return v
        if k == "assignx":
            v = s.ev(е.a[1], ф)
            s.призначити(е.a[0], v, ф, е)
            return v
        if k == "lambda":
            return frozenset()
        return frozenset()

    def позначити_перелік(s, о, літерали, ф):
        if ф.mod in РЕЄСТРОВІ_МОДУЛІ or о.родина is not None:
            return
        ел = [a.v for a in літерали]
        р = s.реєстр.сім_я(ел) if len(ел) >= 2 else None
        if not р and len(ел) >= 2 and all(isinstance(x, str) and КОД_ЛІТЕРАЛ.match(x) for x in ел):
            р = "поза реєстром"        # перелік латинських кодів: родину дасть поле коду, яким його порівнюють
        if р:
            о.родина = р

    def словник(s, е, ф):
        о = s.новий(е, "dict", ф)
        ум = s.ум_стану(ф)
        і = 0
        while і < len(е.a):
            ключ, знач = е.a[і], е.a[і + 1]
            і += 2
            v = s.ev(знач, ф)
            if ключ.k == "str":
                s.зберегти_в_об(о, ключ.v, v)
                s.зберегти_в_об(о, "#ключі", {("L", ключ.v)})
                s.подія_запису(е, о, ключ.v, v | ум, ф, e_line=ключ.line or е.line)
            elif ключ.k == "star":
                for з in sorted((x for x in v if об(x)), key=lambda x: x.id):
                    for к2 in sorted(з.пол, key=str):
                        s.зберегти_в_об(о, к2, з.пол[к2])
                if any(x.рек for x in v if об(x)):
                    о.рек = True
            else:
                kv = s.ev(ключ, ф)
                s.зберегти_в_об(о, "#ключі", kv)
                s.зберегти_в_об(о, "*", v)
                s.подія_запису(е, о, None, v | ум, ф)
        if е.a:
            ключі = [е.a[j].v for j in range(0, len(е.a), 2) if е.a[j].k == "str"]
            if len(ключі) >= 2 and ф.mod not in РЕЄСТРОВІ_МОДУЛІ and о.родина is None:
                о.родина = s.реєстр.сім_я(ключі)
        if о.рек:
            s.позначити_запис({о})
        return о

    def ум_стану(s, ф):
        return s.умови

    def включення(s, е, ф):
        for ціль, ітер, умови in е.v:
            ел = s.елемент(s.ev(ітер, ф))
            s.призначити(ціль, ел, ф, е)
            for у in умови:
                s.ev(у, ф)
        о = s.новий(е, "dict" if len(е.a) == 2 else "list", ф)
        v = s.ev(е.a[-1], ф)
        s.зберегти_в_об(о, "*", v)
        if len(е.a) == 2:
            s.зберегти_в_об(о, "#ключі", s.ev(е.a[0], ф))
        return frozenset(v | {о}) if len(е.a) != 1 else frozenset({о} | s.лише(v, "D"))

    # ── елемент, поле ──────────────────────────────────────────────────────────────────────────────────────────
    def елемент(s, вал):
        р = set()
        for v in sorted(вал, key=lambda x: (0, x.id) if об(x) else (1, x)):
            if об(v):
                if v.вид in ("rec", "feed", "page", "node"):
                    р.add(v)
                    if v.вид == "rec":
                        р |= v.пол.get("*", set())
                elif v.вид == "dict":
                    р |= v.пол.get("#ключі", set())
                else:
                    р |= v.пол.get("*", set())
            elif v[0] in ТЕКСТ:
                р.add(v)
        return р

    def роль(s, ключ, місце):
        р = set()
        if ключ in s.ТЕКСТОВІ_КЛЮЧІ:
            р.add(("TR", місце))
        if s.код_ключ(ключ):
            р.add(("C", місце))
        return р

    def код_ключ(s, ключ):
        return ключ in s.КОДОВІ_КЛЮЧІ or (ключ in s.КОДОВІ_ДАНІ and ключ not in s.ТЕКСТОВІ_КЛЮЧІ)

    def поле(s, вал, ключ, місце):
        р = set()
        for v in sorted(вал, key=lambda x: (0, x.id) if об(x) else (1, x)):
            if not об(v):
                if v[0] in ТЕКСТ and ключ is None:
                    р.add(v)
                continue
            if ключ is None:
                р |= s.елемент({v})
                continue
            if ключ in v.пол:
                if v.рек:
                    р |= {("TR", місце) if не_об(x) and x[0] in ТЕКСТ else x for x in v.пол[ключ]}
                else:
                    р |= v.пол[ключ]
            elif v.вид == "dict" and "*" in v.пол:
                if v.рек:
                    р |= {("TR", місце) if не_об(x) and x[0] in ТЕКСТ else x for x in v.пол["*"]}
                else:
                    р |= v.пол["*"]
            if v.вид == "rec":
                s.ЧИТАНІ_З_ФАЙЛУ.add(ключ)
                ролі = s.роль(ключ, місце)
                р |= ролі
                if not s.код_ключ(ключ):
                    р.add(("TR", місце))      # зчитаний із файлу запис: поле не код — можливі слова крамниці
                    р.add(v)
            elif v.рек and v.вид in ("dict", "list") and s.код_ключ(ключ):
                р.add(("C", місце))
            elif v.вид in ("feed", "page", "node"):
                р |= {v}
        return р

    def атрибут(s, е, ф):
        ім, база = е.v, е.a[0]
        if база.k == "name":
            м = s.модуль_за_іменем(ф, база.v)
            if м is not None and м.тіло is not None:
                return frozenset(s.env.get((м.тіло.fid, ім), ()))
        bv = s.ev(база, ф)
        місце = s.місце(ф, е)
        р = set()
        if ім in АТРИБУТИ_ТЕКСТУ:
            р |= s.текст_з(bv, місце, ф, е)
        if ім in ("body", "html", "documentElement"):
            р |= {v for v in bv if об(v) and v.вид == "page"}
        elif ім in ("parent", "children", "contents", "next_sibling", "previous_sibling", "tbody", "head"):
            р |= {s.звузити(е, ф, v) for v in sorted((x for x in bv if об(x) and x.вид in ("page", "node")), key=lambda x: x.id)}
            р |= {v for v in bv if об(v) and v.вид == "feed"}
        р |= s.поле(bv, ім, місце) if ім not in АТРИБУТИ_ТЕКСТУ else set()
        return frozenset(р)

    def підстановка(s, е, ф):
        bv = s.ev(е.a[0], ф)
        iv = s.ev(е.a[1], ф)
        місце = s.місце(ф, е)
        р = set()
        ключ = е.a[1].v if е.a[1].k == "str" else None
        if ключ is not None:
            р |= s.поле(bv, ключ, місце)
            р |= s.текст_з_атрибута(bv, ключ, місце)
        else:
            р |= s.поле(bv, None, місце)
        # словник слів: D[текст]
        ум = s.тексти(iv)
        if ум:
            for о in (v for v in bv if об(v) and v.вид == "dict"):
                if s.має_слова({о}):
                    р |= {("D", місце)} | s.елемент_значень(о)
                    s.читання_слів(ум, місце, "пошук тексту в словнику слів")
        s.використання_перелік(bv, iv, е, ф)
        return frozenset(р)

    def елемент_значень(s, о):
        р = set()
        for к, v in sorted(о.пол.items(), key=lambda kv: str(kv[0])):
            if к != "#ключі":
                р |= v
        return р

    def текст_з_атрибута(s, bv, ключ, місце):
        """`вузол["href"]` / `елемент.attrib["x"]` — атрибут вузла сторінки чи фіду."""
        р = set()
        for v in bv:
            if об(v) and v.вид in ("feed", "node"):
                р.add(("TF" if v.вид == "feed" else "TN", місце))
        return р

    def текст_з(s, bv, місце, ф, е):
        р = set()
        for v in sorted((x for x in bv if об(x)), key=lambda x: x.id):
            if v.вид == "page":
                р.add(("TP", місце))
            elif v.вид == "node":
                р.add(("TN", місце))
            elif v.вид == "feed":
                р.add(("TF", місце))
        return р

    def звузити(s, е, ф, v):
        return s.новий_вузол(е, ф)

    def новий_вузол(s, е, ф):
        return s.новий(e_sub(е), "node", ф)

    def модуль_за_іменем(s, ф, ім):
        м0 = s.мф.get(ф.file)
        if м0 is None:
            return None
        ал = м0.псевдоніми.get(ім)
        if ал and ал[0] == "mod":
            return s.по_імені_модуля.get(ал[1])
        if ал and ал[0] == "name":
            return s.по_імені_модуля.get(ал[2]) if ал[2] in s.по_імені_модуля and ал[1] != ал[2] else None
        return None

    # ── порівняння та читачі слів ─────────────────────────────────────────────────────────────────────────────
    def має_слова(s, вал, глиб=0):
        for v in sorted(вал, key=lambda x: (0, x.id) if об(x) else (1, x)):
            if not об(v):
                if v[0] == "L" and слово_в_літералі(v[1]):
                    return True
            elif v.вид == "rx" and v.шаблон_слів:
                return True
            elif глиб < 3 and v.вид in ("dict", "list", "tuple", "pairs"):
                for ключ in sorted(v.пол, key=str):
                    if ключ in ("*", "#ключі") or ключ.isdigit():
                        if s.має_слова(v.пол[ключ], глиб + 1):
                            return True
        return False

    def читання_слів(s, тексти, місце, чому):
        for т in тексти:
            if т[0] == "TR":
                s.читання3.setdefault(т[1], "%s (читач слів: %s)" % ("текстове поле", чому + " " + місце))

    def порівняння(s, е, ф):
        л, п = s.ev(е.a[0], ф), s.ev(е.a[1], ф)
        місце = s.місце(ф, е)
        тл, тп = s.тексти(л), s.тексти(п)
        р = set()
        if тл and s.має_слова(п) and not тп:
            s.читання_слів(тл, місце, "порівняння/in зі словом")
            р.add(("D", місце))
        elif тп and s.має_слова(л) and not тл:
            s.читання_слів(тп, місце, "порівняння/in зі словом")
            р.add(("D", місце))
        elif тл and тп and (s.має_слова(л) or s.має_слова(п)):
            р.add(("D", місце))
        if е.v in ("In", "NotIn", "Eq", "NotEq", "Is", "IsNot", "Lt"):
            s.використання_перелік(п, л, е, ф)
            if е.v in ("Eq", "NotEq"):
                s.використання_перелік(л, п, е, ф)
        return frozenset(р)

    def використання_перелік(s, перелік, значення, е, ф):
        if not any(not об(v) and v[0] == "C" for v in значення):
            return
        for о in перелік:
            if об(о) and о.родина and ф.mod not in РЕЄСТРОВІ_МОДУЛІ:
                s.використання_переліків.setdefault(о.id, (о, "%s:%d" % (ф.file, е.line)))

    def читач_регекс(s, патерни, тексти, місце, чому, тексто_результат):
        р = {("D", місце)}
        s.читання_слів(тексти, місце, чому)
        if тексто_результат:
            р |= тексти
        return р

    # ── виклики ───────────────────────────────────────────────────────────────────────────────────────────────
    def розібрати_виклик(s, е):
        n = е.v["n"]
        return e_func(е), е.a[1:1 + n], е.a[1 + n:], е.v["kw"]

    def виклик(s, е, ф):
        fn, арги, кв, імена = s.розібрати_виклик(е)
        місце = s.місце(ф, е)
        av = [s.ev(a, ф) for a in арги]
        kv = [s.ev(a, ф) for a in кв]
        усі = set()
        for x in av + kv:
            усі |= x
        р = set()
        ім = None
        rv = frozenset()
        функція_модуля = None
        if fn.k == "name":
            ім = fn.v
        elif fn.k == "attr":
            ім = fn.v
            if fn.a[0].k == "name" and s.модуль_за_іменем(ф, fn.a[0].v) is not None:
                функція_модуля = s.модуль_за_іменем(ф, fn.a[0].v)
            rv = s.ev(fn.a[0], ф)
        # 1) користувацькі функції
        кандидати = s.кандидати(fn, ім, функція_модуля, rv, ф)
        for g in кандидати:
            s.зв_язати(g, av, kv, імена, rv if fn.k == "attr" and функція_модуля is None else None)
            р |= s.ret.get(g.fid, set())
        # 2) вбудовані значення
        р |= s.вбудований(е, fn, ім, арги, av, kv, імена, rv, усі, ф, місце, bool(кандидати))
        return frozenset(р)

    def кандидати(s, fn, ім, модуль, rv, ф):
        if ім is None:
            return []
        if модуль is not None:
            return list(s.у_модулі.get((модуль.ім_я, ім), ()))[:4]
        if fn.k == "name":
            g = ф
            while g is not None:
                вкл = s.вкладені.get((g.fid, ім))
                if вкл:
                    return вкл[:3]
                g = g.parent
            м0 = s.мф.get(ф.file)
            if м0 is not None:
                ал = м0.псевдоніми.get(ім)
                if ал and ал[0] == "name":
                    ц = s.у_модулі.get((ал[1], ал[2]))
                    if ц:
                        return list(ц)[:3]
                власні = [x for x in s.у_модулі.get((м0.ім_я, ім), ()) if x.file == м0.файл]
                if власні:
                    return власні[:3]
                if м0.мова == "js":
                    return list(s.js_глобальні.get(ім, ()))[:3]
            return []
        if ім in НЕ_РОЗРІШУВАТИ:
            return []
        ц = s.методи.get(ім, [])
        if ф.lang == "js":
            ц = ц or s.js_глобальні.get(ім, [])
        return list(ц) if len(ц) == 1 else []

    def зв_язати(s, g, av, kv, імена, отримувач):
        п = list(g.params)
        зсув = 0
        if g.is_method:
            зсув = 1
            if отримувач is not None and п:
                s.писати_ім(g, п[0], set(отримувач))
        рідко = s.виклики_за_іменем.get(g.name, 0) <= МЕЖА_ТЕГІВ
        for i, v in enumerate(av):
            if i + зсув < len(п):
                s.писати_ім(g, п[i + зсув], set(v) if рідко else {x for x in v if об(x)})
        for ім, v in zip(імена, kv):
            if ім in п:
                s.писати_ім(g, ім, set(v) if рідко else {x for x in v if об(x)})

    def вбудований(s, е, fn, ім, арги, av, kv, імена, rv, усі, ф, місце, є_користувацька):
        р = set()
        об_ = sorted((v for v in rv if об(v)), key=lambda x: x.id)
        # мережа / читання
        if ім == "json" and fn.k == "attr" and (ф.file.startswith("zhnyvarka/") or ф.lang == "js"):
            if s.шлях_запису(rv):
                return {s.новий(е, "rec", ф)}
            return {s.новий(е, "feed", ф)} if ф.file.startswith("zhnyvarka/") else set()
        if ім in ЧИТАННЯ_JSON and fn.k == "attr" and fn.a[0].k == "name" and fn.a[0].v in ("json", "JSON", "gzip", "pickle"):
            if s.шлях_запису(усі):
                return {s.новий(е, "rec", ф)}
            if any(не_об(v) and v[0] == "H" for v in усі) and ф.file.startswith("zhnyvarka/"):
                return {s.новий(е, "feed", ф)}
            return set()
        if (ім in ("urlopen", "fetch", "urlretrieve") and fn.k == "name") or (
                fn.k == "attr" and fn.a[0].k == "name" and fn.a[0].v in МЕРЕЖА and ім in ("get", "post", "request", "urlopen", "fetch")):
            return {("H", місце)} | {("U", v[1]) for v in усі if не_об(v) and v[0] == "L"}
        if ім == "new_page" or ім == "newPage":
            return {s.новий(е, "page", ф)}
        # корені документа
        if ім in КОРЕНІ_СТОРІНКИ or (fn.k == "attr" and fn.a[0].k == "name" and fn.a[0].v in КОРЕНІ_СТОРІНКИ_МОДУЛІ
                                     and ім in ("fromstring", "parse", "document_fromstring", "HTML", "Selector")):
            xml = any(не_об(v) and v[0] == "L" and v[1] in ("xml", "lxml-xml") for v in усі)
            return {s.новий(е, "feed" if xml else "page", ф)}
        if ім == "DOMParser":
            return {s.новий(е, "dom", ф)}
        if ім == "parseFromString":
            html_ = any(не_об(v) and v[0] == "L" and "html" in v[1] for v in усі)
            return {s.новий(е, "page" if html_ else "feed", ф)}
        if (ім in КОРЕНІ_ФІДУ or (ім in ("parse", "fromstring", "XML", "parseString") and fn.k == "attr"
                                  and fn.a[0].k == "name" and fn.a[0].v in ШЛЯХИ_РОЗБОРУ_ФІДУ)):
            return {s.новий(е, "feed", ф)}
        if ім in ("getroot", "getchildren", "close", "root") and any(v.вид == "feed" for v in об_):
            return {v for v in rv if об(v) and v.вид == "feed"}
        # витяг тексту та звуження
        if fn.k == "attr" and (ім in МЕТОДИ_ТЕКСТУ or ім in ("get", "attrib", "getAttribute", "text", "get_attribute")) \
                and any(v.вид in ("page", "node", "feed") for v in об_):
            if ім in ("get", "getAttribute", "get_attribute", "attrib"):
                if ім == "get" and len(арги) and арги[0].k == "str" and False:
                    pass
                р |= s.текст_з(rv, місце, ф, е)
                return р
            if ім in ("inner_text", "text_content", "inner_html", "outer_html", "content") and арги:
                sel = арги[0].v if арги[0].k == "str" else None
                if sel in ("body", "html", "*") and {v.вид for v in об_} & {"page"}:
                    return s.текст_з(rv, місце, ф, е)
                return {("TN", місце)} if any(v.вид == "page" for v in об_) else s.текст_з(rv, місце, ф, е)
            return s.текст_з(rv, місце, ф, е)
        if fn.k == "attr" and ім in МЕТОДИ_ВУЗЛА and any(v.вид in ("page", "node", "feed") for v in об_):
            рез = set()
            for v in об_:
                if v.вид == "feed":
                    рез.add(v)
                elif v.вид in ("page", "node"):
                    sel = арги[0].v if арги and арги[0].k == "str" else None
                    рез.add(v if (sel in ("body", "html", "*", ":root", "") and v.вид == "page") else s.новий_вузол(е, ф))
            return рез
        if ім in ("evaluate", "evaluate_handle", "eval", "executeScript") and арги:
            ст = s.рядок_значення(арги[0], ф)
            if ст and ВЕРХ_ДОКУМЕНТА.search(ст):
                return {("TP", місце)}
            if ст and ВУЗОЛ_ДОКУМЕНТА.search(ст):
                return {("TN", місце)}
            return set()
        # зберігання
        if fn.k == "attr" and ім in ЗБЕРІГАЮТЬ:
            if ім in ("append", "add", "push", "appendleft", "unshift", "insert", "extend", "extendleft"):
                v = усі if ім != "insert" else set(av[-1]) if av else set()
                if ім in ("extend", "extendleft"):
                    v = set(s.елемент(av[0])) | {x for x in av[0] if об(x)} if av else set()
                for о in об_:
                    s.зберегти_в_об(о, "*", set(v))
                return set()
            if ім == "update":
                for о in об_:
                    for з in av:
                        for к2 in sorted((x for x in з if об(x)), key=lambda x: x.id):
                            for ключ in sorted(к2.пол, key=str):
                                s.зберегти_в_об(о, ключ, к2.пол[ключ])
                                if ключ not in ("*", "#ключі"):
                                    s.подія_запису(е, о, ключ, к2.пол[ключ] | s.умови, ф)
                    for ім2, v in zip(імена, kv):
                        if ім2 is None:
                            continue
                        s.зберегти_в_об(о, ім2, v)
                        s.подія_запису(е, о, ім2, v | s.умови, ф)
                return set()
            if ім == "setdefault" and len(арги) >= 2:
                for о in об_:
                    ключ = арги[0].v if арги[0].k == "str" else None
                    s.зберегти_в_об(о, ключ if ключ is not None else "*", av[1])
                    s.подія_запису(е, о, ключ, av[1] | s.умови, ф)
                return set(av[1])
            if ім == "assign":
                return set(av[0]) if av else set()
        # dict(...) / list(...) / sorted(...)
        if fn.k == "name" and ім in ("dict", "Object", "list", "set", "tuple", "sorted", "reversed", "copy", "deepcopy",
                                      "Array", "frozenset", "Map", "Set"):
            о = s.новий(е, "dict" if ім in ("dict", "Object", "Map") else "list", ф)
            for v in av:
                for з in sorted((x for x in v if об(x)), key=lambda x: x.id):
                    if ім in ("dict", "Object", "Map"):
                        for ключ in sorted(з.пол, key=str):
                            s.зберегти_в_об(о, ключ, з.пол[ключ])
                    else:
                        s.зберегти_в_об(о, "*", s.елемент({з}))
                if ім in ("list", "set", "tuple", "sorted", "reversed", "Array", "frozenset", "Set") and v:
                    s.зберегти_в_об(о, "*", {x for x in v if not об(x)})
            if any(x.рек for v in av for x in v if об(x)):
                о.рек = True
            for ім2, v in zip(імена, kv):
                if ім2 is None:
                    continue
                s.зберегти_в_об(о, ім2, v)
                s.зберегти_в_об(о, "#ключі", {("L", ім2)})
                s.подія_запису(е, о, ім2, v | s.умови, ф)
            return {о} | {x for v in av for x in v if об(x) and x.вид in ("rec", "feed", "page", "node")}
        # методи словника й списку
        if fn.k == "attr" and ім in ("get", "pop", "getOrDefault") and арги and об_:
            ключ = арги[0].v if арги[0].k == "str" else None
            рез = set(s.поле(rv, ключ, місце))
            for v in av[1:]:
                рез |= v
            ум = s.тексти(av[0])
            if ключ is None and ум:
                for о in об_:
                    if о.вид == "dict" and s.має_слова({о}):
                        рез |= {("D", місце)} | s.елемент_значень(о)
                        s.читання_слів(ум, місце, "пошук тексту в словнику слів")
            s.використання_перелік(rv, av[0], е, ф)
            return рез
        if fn.k == "attr" and ім == "items" and об_:
            рез = set()
            for о in об_:
                п = s.новий(e_sub(е), "pairs", ф)
                кортеж = s.новий(e_sub(е, 1), "tuple", ф)
                s.зберегти_в_об(кортеж, "0", о.пол.get("#ключі", set()))
                s.зберегти_в_об(кортеж, "1", s.елемент_значень(о) | (о.пол.get("*", set()) if о.вид == "rec" else set()))
                s.зберегти_в_об(кортеж, "*", кортеж.пол.get("0", set()) | кортеж.пол.get("1", set()))
                s.зберегти_в_об(п, "*", {кортеж})
                if о.рек:
                    п.рек = True
                    кортеж.рек = True
                рез.add(п)
            return рез
        if fn.k == "attr" and ім == "values" and об_:
            п = s.новий(e_sub(е), "list", ф)
            for о in об_:
                s.зберегти_в_об(п, "*", s.елемент_значень(о) | ({о} if о.вид == "rec" else set()))
            return {п}
        if fn.k == "attr" and ім == "keys" and об_:
            п = s.новий(e_sub(е), "list", ф)
            for о in об_:
                s.зберегти_в_об(п, "*", о.пол.get("#ключі", set()))
            return {п}
        if fn.k == "attr" and ім in ("index", "indexOf", "get") and арги:
            s.використання_перелік(rv, av[0], е, ф)
        # читачі слів: регекс
        if fn.k == "attr" and ім in МЕТОДИ_РЕГЕКС:
            рекс = [v for v in rv if об(v) and v.вид == "rx"]
            мод_re = fn.a[0].k == "name" and fn.a[0].v in ("re", "regex")
            патерн_є = False
            тексти = set()
            if мод_re and арги:
                патерн_є = s.слово_в_патерні(арги[0], av[0])
                for x in av[1:]:
                    тексти |= s.тексти(x)
            elif рекс:
                патерн_є = any(v.шаблон_слів for v in рекс)
                for x in av:
                    тексти |= s.тексти(x)
            elif ім in ("test", "exec", "match", "matchAll", "search", "replace", "replaceAll", "split") and not мод_re:
                # JS: text.replace(/re/, …) / text.split("слово") — отримувач текст, аргумент шаблон
                тексти = s.тексти(rv)
                патерн_є = bool(арги) and (s.слово_в_патерні(арги[0], av[0]) or s.має_слова(av[0]))
            if тексти and патерн_є:
                текст_резульат = ім in ("sub", "subn", "replace", "replaceAll", "split", "findall", "finditer",
                                        "search", "match", "fullmatch", "exec", "matchAll")
                return s.читач_регекс(None, тексти, місце, "регекс зі словом", текст_резульат)
            if (тексти or s.тексти(rv)) and ім in ("search", "match", "fullmatch", "findall", "split", "sub", "exec"):
                return set(тексти | s.тексти(rv))  
        # читачі слів: методи рядка
        if fn.k == "attr" and (ім in МЕТОДИ_РЯДКА_БУЛ or ім in МЕТОДИ_РЯДКА_ТЕКСТ):
            тексти_отр = s.тексти(rv)
            if тексти_отр and арги and any(s.слово_в_патерні(a, v) or s.має_слова(v) for a, v in zip(арги, av)):
                return s.читач_регекс(None, тексти_отр, місце, "метод рядка зі словом",
                                      ім in МЕТОДИ_РЯДКА_ТЕКСТ)
            if тексти_отр and ім in МЕТОДИ_РЯДКА_ТЕКСТ:
                return set(тексти_отр)
            if not тексти_отр and ім in МЕТОДИ_РЯДКА_БУЛ:
                for x in av:
                    if s.тексти(x) and s.має_слова(rv):
                        s.читання_слів(s.тексти(x), місце, "пошук слова в тексті")
                        return {("D", місце)}
        # запис на шляху каталогу
        if ім in ЗАПИС_ФАЙЛА or ім in ("dumps",):
            шлях = any(не_об(v) and v[0] == "L" and ШЛЯХ_ЗАПИСІВ.search(v[1]) for v in усі)
            if шлях and ім in ЗАПИС_ФАЙЛА:
                s.позначити_запис({x for v in av + [rv] for x in v if об(x)})
            return {x for x in усі if об(x) or x[0] in ("L", "D") + ТЕКСТ}
        if fn.k == "attr" and ім in ("then", "catch", "finally") and арги:
            рез = set()
            for л in (a for a in арги if a.k == "lambda" and a.x is not None):
                if л.x.params:
                    s.писати_ім(л.x, л.x.params[0], set(rv))
                рез |= s.ret.get(л.x.fid, set())
            return рез or set(rv)
        # перебір з функціями (map/forEach/filter/find/…)
        if fn.k == "attr" and ім in ДЛЯ_ПЕРЕБОРУ and арги:
            лям = [a for a in арги if a.k == "lambda" and a.x is not None]
            for л in лям:
                g = л.x
                if g.params:
                    s.писати_ім(g, g.params[0], set(s.елемент(rv)))
            if ім in ("map", "flatMap"):
                п = s.новий(e_sub(е), "list", ф)
                for л in лям:
                    s.зберегти_в_об(п, "*", s.ret.get(л.x.fid, set()))
                return {п}
            if ім in ("filter", "sort", "sorted", "min", "max", "reduce"):
                return set(rv) | {x for v in av for x in v if об(x)}
            if ім in ("find",):
                return s.елемент(rv)
            return set()
        # інші методи, що повертають похідне отримувача
        if ім in ПЕРЕДАЮТЬ or ім in ("str", "int", "float", "len"):
            if ім in ("int", "float", "len"):
                return set()
            if fn.k == "attr" and ім in ("sort",):
                return set()
            рез = {x for x in (set(rv) | усі) if not об(x) or x.вид in ("rec", "feed", "page", "node", "dict", "list", "tuple", "pairs")}
            return рез
        # конструктори й невідомі функції: нічого, окрім слідів шляху й тексту
        if є_користувацька:
            return set()
        return {x for x in (set(rv) | усі) if not об(x) and x[0] in ("L", "H", "U") + ТЕКСТ + ("C",) and (x[0] != "L" or (isinstance(x[1], str) and len(x[1]) < 200))}

    @staticmethod
    def шлях_запису(вал):
        """Значення несе шлях до файлу чи адреси каталогу (`catalog.json`, `.jsonl`, `/сирі`): лише його читання дає запис."""
        return any(не_об(v) and v[0] in ("L", "U") and isinstance(v[1], str) and ШЛЯХ_ЗАПИСІВ.search(v[1]) for v in вал)

    def слово_в_патерні(s, вираз, вал):
        if вираз.k == "str":
            return слово_в_регексі(вираз.v)
        for v in sorted(вал, key=lambda x: (0, x.id) if об(x) else (1, x)):
            if об(v) and v.вид == "rx" and v.шаблон_слів:
                return True
            if not об(v) and v[0] == "L" and слово_в_регексі(v[1]):
                return True
        return False

    def рядок_значення(s, е, ф):
        if е.k == "str":
            return е.v
        if е.k == "name":
            return s.рядкові_константи.get((ф.file, е.v)) or next(
                (v for (фл, ім), v in sorted(s.рядкові_константи.items()) if ім == е.v and фл == ф.file), None)
        return None

    # ── присвоєння і події запису ─────────────────────────────────────────────────────────────────────────────
    def призначити(s, ціль, вал, ф, оп):
        к = ціль.k
        if к == "name":
            s.писати_ім(ф, ціль.v, set(вал))
        elif к == "attr":
            for о in sorted((x for x in s.ev(ціль.a[0], ф) if об(x)), key=lambda x: x.id):
                s.зберегти_в_об(о, ціль.v, set(вал))
                s.подія_запису(ціль, о, ціль.v, set(вал) | s.умови, ф)
        elif к == "sub":
            ключ = ціль.a[1].v if ціль.a[1].k == "str" else None
            for о in sorted((x for x in s.ev(ціль.a[0], ф) if об(x)), key=lambda x: x.id):
                s.зберегти_в_об(о, ключ if ключ is not None else "*", set(вал))
                if ключ is not None:
                    s.зберегти_в_об(о, "#ключі", {("L", ключ)})
                s.подія_запису(ціль, о, ключ, set(вал) | s.умови, ф)
        elif к in ("list", "star"):
            for i, а in enumerate(ціль.a):
                частина = set()
                for v in sorted(вал, key=lambda x: (0, x.id) if об(x) else (1, x)):
                    if об(v):
                        частина |= v.пол.get(str(i), set()) or v.пол.get("*", set())
                    elif v[0] in ТЕКСТ or v[0] in ("D", "L"):
                        частина.add(v)
                if а.k == "star":
                    s.призначити(а, частина, ф, оп)
                else:
                    s.призначити(а, частина, ф, оп)

    def подія_запису(s, е, о, ключ, вал, ф, e_line=None):
        s.записи[(id(е), о.id, ключ, e_line or е.line)] = (о, ключ, frozenset(вал), ф.file, e_line or е.line)
        if ключ is None:
            return
        # ролі ключа — з даних запису
        if о.рек:
            if any(не_об(v) and v[0] in ("TP", "TN", "TF") for v in вал) and ключ not in s.ТЕКСТОВІ_КЛЮЧІ:
                s.ТЕКСТОВІ_КЛЮЧІ.add(ключ)
                s.змін += 1
            коди = s.КОДИ_ЗАПИСІВ.setdefault(ключ, set())
            нові = {v[1] for v in вал if не_об(v) and v[0] == "L" and isinstance(v[1], str) and КОД_ЛІТЕРАЛ.match(v[1])} - коди
            if нові:
                коди |= нові
                s.змін += 1
            if ключ not in s.КОДОВІ_ДАНІ and коди and (о.вид == "rec" or (len(коди) >= 2 and ключ in s.ЧИТАНІ_З_ФАЙЛУ)):
                s.КОДОВІ_ДАНІ.add(ключ)
                s.змін += 1

    # ── прохід ────────────────────────────────────────────────────────────────────────────────────────────────
    def пройти(s):
        for ф in s.функції:
            s.умови = frozenset()
            for оп in ф.stmts:
                if оп.k == "assign" and оп.val.k == "str" and len(оп.t) == 1 and оп.t[0].k == "name" \
                        and len(оп.val.v) > 20 and (ф.file, оп.t[0].v) not in s.рядкові_константи:
                    s.рядкові_константи[(ф.file, оп.t[0].v)] = оп.val.v
        for _ in range(40):
            s.змін = 0
            s.пам = {}
            for ф in s.функції:
                for оп in ф.stmts:
                    s.умови = frozenset()
                    ум = set()
                    for у in оп.ctrl[-1:]:       # лише найближча умова: вкладений блок не успадковує читача зовнішнього
                        ум |= s.лише(s.ev(у, ф), "D")
                    s.умови = frozenset(ум)
                    if оп.k == "assign":
                        v = s.ev(оп.val, ф) | s.умови
                        for т in оп.t:
                            s.призначити(т, v, ф, оп)
                    elif оп.k == "expr":
                        s.ev(оп.val, ф)
                    elif оп.k == "return":
                        v = s.ev(оп.val, ф) | s.умови
                        if влити(s.ret.setdefault(ф.fid, set()), v):
                            s.змін += 1
                    elif оп.k == "iter":
                        s.призначити(оп.t, s.елемент(s.ev(оп.val, ф)), ф, оп)
            if s.змін == 0:
                break


def не_об(v):
    return not isinstance(v, О)


def m_none(х):
    return х is None


def e_func(е):
    return е.a[0]


def e_sub(е, к=0):
    """Стабільний ідентифікатор для об'єкта, який створює той самий виклик (як 'вузол' чи 'пара')."""
    ключ = (id(е), к)
    return _ПІДВИРАЗИ.setdefault(ключ, E("other", None, [], е.line))


_ПІДВИРАЗИ = {}


# ═══ МІСЦЯ ══════════════════════════════════════════════════════════════════════════════════════════════════════
def розібрати_місце(рядок):
    ф, _, н = рядок.rpartition(":")
    return ф, int(н)


def обчислити(a):
    """{(файл, рядок, пункт): чому} за кінцевим станом аналізу."""
    м = {}

    def додати(файл, рядок, пункт, чому):
        к = (файл, рядок, пункт)
        if к not in м or чому < м[к]:
            м[к] = чому
    реєстр = a.реєстр
    for _, (о, ключ, вал, файл, рядок) in sorted(a.записи.items(), key=lambda kv: (kv[1][3], kv[1][4], str(kv[1][1]), kv[1][0].id)):
        ім = ключ if ключ is not None else "*"
        for т in sorted(v[1] for v in вал if не_об(v) and v[0] == "TP"):
            ф2, р2 = розібрати_місце(т)
            додати(ф2, р2, 4, "текст з кореня документа сторінки доходить до поля «%s» (%s:%d)" % (ім, файл, рядок))
        if not о.рек:
            continue
        d = sorted(v[1] for v in вал if не_об(v) and v[0] == "D")
        if d:
            додати(файл, рядок, 1, "запис поля «%s»: значення виведено читачем слів (%s)" % (ім, d[0]))
        if ключ is not None and a.код_ключ(ключ) and файл.rsplit("/", 1)[-1].split(".")[0] not in РЕЄСТРОВІ_МОДУЛІ:
            дозв = реєстр.дозволені(ключ)
            коди = sorted(v[1] for v in вал if не_об(v) and v[0] == "L" and
                          (КОД_ЛІТЕРАЛ.match(v[1]) or (" " not in v[1] and Є_СЛОВО.match(v[1]) and len(v[1]) <= 24)))
            поза = [c for c in коди if c not in дозв]
            if поза:
                додати(файл, рядок, 2, "кодове поле «%s» пише «%s» поза реєстром" % (ім, поза[0]))
            elif ключ not in реєстр.поля and any(c in реєстр.коди for c in коди):
                додати(файл, рядок, 2, "кодове поле «%s» пише коди реєстру, а самого поля в реєстрі нема" % ім)
    for _, (о, де) in sorted(a.використання_переліків.items()):
        додати(о.файл, о.рядок, 2, "власний перелік кодів родини «%s» порівнює поле коду (%s)" % (о.родина, де))
    for місце, чому in sorted(a.читання3.items()):
        ф2, р2 = розібрати_місце(місце)
        додати(ф2, р2, 3, "читання текстового поля запису у читач слів: " + чому.split(": ", 1)[-1].rstrip(")"))
    return м


# ═══ ФАЙЛИ ══════════════════════════════════════════════════════════════════════════════════════════════════════
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
    вих = []
    for м in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", текст, re.S | re.I):
        вих.append((текст.count("\n", 0, м.start(1)), м.group(1)))
    return вих


def розібрати_всі_js(корінь, файли, html_файли):
    import shutil
    import tempfile
    помилки = []
    shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "корінь_річ_запис_речі_js.js")
    джерела = {ф: (os.path.join(корінь, ф), 0) for ф in файли}
    тека = tempfile.mkdtemp(prefix="rzr_js_")
    try:
        for ф in html_файли:
            with open(os.path.join(корінь, ф), encoding="utf8") as fh:
                текст = fh.read()
            for i, (зсув, код) in enumerate(вбудовані_скрипти(текст)):
                шлях = os.path.join(тека, "%s#%d.js" % (os.path.basename(ф), i))
                with open(шлях, "w", encoding="utf8") as fh:
                    fh.write(код)
                джерела["%s#%d" % (ф, i)] = (шлях, зсув)
        if not джерела:
            return [], помилки
        шляхи = [v[0] for v in джерела.values()]
        try:
            out = subprocess.run(["node", "--expose-internals", shim] + шляхи, capture_output=True,
                                 encoding="utf-8", timeout=300)
            дані = json.loads(out.stdout or "{}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as е:
            return [], ["JS не розібрано (node): %s" % е]
        if "помилка" in дані:
            return [], ["JS не розібрано: %s" % дані["помилка"]]
        вих = []
        for ім in sorted(джерела):
            шлях, зсув = джерела[ім]
            дер = дані.get(шлях)
            if not isinstance(дер, dict) or "помилка" in дер:
                помилки.append("%s: %s" % (ім, (дер or {}).get("помилка", "нема дерева")))
                continue
            вих.append(розібрати_js(ім.split("#")[0], дер, зсув))
        return вих, помилки
    finally:
        shutil.rmtree(тека, ignore_errors=True)


def побудувати_модулі(корінь):
    py, js = знайти_файли(корінь)
    модулі, помилки = [], []
    for ф in py:
        try:
            with open(os.path.join(корінь, ф), encoding="utf8") as fh:
                текст = fh.read()
        except (OSError, UnicodeDecodeError) as е:
            помилки.append("%s: %s" % (ф, е))
            continue
        модулі.append(розібрати_py(ф, текст))
    html = [ф for ф in ("джерела/показ.html",) if os.path.exists(os.path.join(корінь, ф))]
    мJ, пJ = розібрати_всі_js(корінь, js, html)
    return модулі + мJ, помилки + пJ, py, js + html


def головна(арги):
    import argparse
    ап = argparse.ArgumentParser()
    ап.add_argument("--корінь", default=".")
    ап.add_argument("--json", action="store_true")
    ап.add_argument("--тихо", action="store_true")
    ап.add_argument("--пункт", type=int, default=0)
    ап.add_argument("--вибірка", type=int, default=0)
    ап.add_argument("--зерно", type=int, default=1)
    ар = ап.parse_args(арги)
    корінь = os.path.abspath(ар.корінь)
    os.chdir(корінь)
    модулі, помилки, py, js = побудувати_модулі(корінь)
    a = Аналіз(модулі, Реєстр(корінь))
    a.пройти()
    м = обчислити(a)
    рядки = sorted(м.items())
    різні = {(ф, р) for (ф, р, п) in м}
    за = {п: len({(ф, р) for (ф, р, п2) in м if п2 == п}) for п in (1, 2, 3, 4)}
    if ар.json:
        print(json.dumps({"місць": len(різні), "за_пунктами": за,
                          "місця": [{"файл": ф, "рядок": р, "пункт": п, "чому": ч} for (ф, р, п), ч in рядки],
                          "ключі_текстові": sorted(a.ТЕКСТОВІ_КЛЮЧІ), "ключі_кодові": sorted(a.КОДОВІ_КЛЮЧІ)},
                         ensure_ascii=False, indent=1))
        return 0
    if ар.вибірка:
        import random
        for (ф, р, п), ч in sorted(random.Random(ар.зерно).sample(рядки, min(ар.вибірка, len(рядки)))):
            print("%s:%d · пункт %d · %s" % (ф, р, п, ч))
        return 0
    if not ар.тихо:
        for (ф, р, п), ч in рядки:
            if not ар.пункт or п == ар.пункт:
                print("%s:%d · пункт %d · %s" % (ф, р, п, ч))
        print("")
    print("файлів: Python %d, JS %d; функцій %d; об'єктів %d, з них записів %d" % (
        len(py), len(js), len(a.функції), len(a.об), sum(1 for о in a.об.values() if о.рек)))
    for п, н in sorted(за.items()):
        print("пункт %d: %d" % (п, н))
    for е in помилки[:20]:
        print("увага: " + е)
    print("місць: %d" % len(різні))
    return 0


if __name__ == "__main__":
    sys.exit(головна(sys.argv[1:]))
