# -*- coding: utf-8 -*-
"""Лічить записи кадру, кольору, наявності й ключів за класом паспорта кореня.

Одиниця — запис поля в таблицю продукту. Ключ дає кандидата ролі, а походження
значення, його присвоєння та споживач відрізняють дані крамниці від конфігурації,
тимчасового аргументу й похідного без нового входу. Атрибути, позиції кортежів,
словники й конструктори записів мають спільний суд. Схему невідомої позиції
без ознак ролі прилад не вгадує.

П.1 — кадр без власника-варіанта та без явного «невідомо». П.2 — колір/наявність
не зі своїх даних варіації або на товарі з варіаціями. Власну оферту доводить
походження з offer/variants/variations і джерела значення; самі id та наявність
на Product, як і назва змінної, доказом не є. П.3 — ключ без параметра варіації.

Читачі — поза класом. Проба/прилад у класі, коли пише таблицю продукту;
локальні константи імпортів розкриваються через AST, без запуску продукту.
Тимчасовий запис тесту не є таблицею продукту.

Непрозорі виклики лишають консервативних кандидатів; число — верхня межа,
а сумніви й перевірка вибірок — у паспорті. --вибірка друкує також відсіяні
кандидати (вони не обов'язково були місцями попередньої версії приладу).
Вивід відсортований і не містить абсолютних шляхів чи версії Python;
останній рядок stdout: «місць: N», код виходу 0.
"""
import argparse, ast, collections, gzip, hashlib, json, os, re, sys, warnings
from походження_запису import Походження, константи_імпортів, ім_виклику, власні_вузли, поля
import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

# Читачі ознаки варіацій кольору сторінки (клас паспорта «Річ-кадр-варіант», «Прилад, доповнення 14988»): гілка, що
# перезаписує колір на «невідомо», знімає місце лише за умовою з виклику такого читача, а не будь-якого виклику.
ЧИТАЧІ_ВАРІАЦІЙ_КОЛЬОРУ = frozenset({"колір_голова_списку"})

# ---- ОБСЯГ ----------------------------------------------------------------------------------------------------
ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)|.*_самотест\.py$")
ПРОДУКТ_ТЕКИ = ("джерела", "zhnyvarka")
ПОЗА_ТЕКИ = {"__pycache__", "node_modules", "фікстури", "аудит", "дані_корпусу", "дані_5191_5194", "лабораторія"}
# стадії виробництва каталогу (виконання: жнива → фід → збагачення → каталог); решта файлів — читачі, доки їхній запис на диск
# не називає файл чи модуль, який читає продукт
ВИРОБНИК = re.compile(r"^(zhnyvarka/(?!кадри_маніфест\.py$).+\.py|джерела/(фід_(?!колір\.)[^/]+|підфід|жнива_[^/]+|кадри_групи|чистка_каталогу|"
                      r"таблиця_каталогу)\.py)$")
# `фід_колір` — вимірювач принту (результат вимірювання, не запис таблиці); `каталог_розбір*` — розбір моделлю, до фіду не
# під'єднаний (його докстрінг): це читачі/похідне, їхні записи лічаться у «поза записом».
# `кадри_маніфест` — маніфест кадрів (адреса → байти, хеш, статус), кадр виміру з маніфестом — Річ-колір-вимір п.5 (рішення
# 30.10, без перетину коренів): він не пише кадр речі чи варіанта, а його читання (`читати_все`) — читач (11458; вибірка 13.11).
ЇЇ_РІЧ = re.compile(r"^джерела/річ_з_фото\.py$")      # речі користувачки: крамниці й варіацій нема, клас не діє

# ---- РОЛІ -----------------------------------------------------------------------------------------------------
ЛІЧИЛЬНИК = re.compile(r"(усього|2плюс|(^|_)без(_|$)|_класу$|лічильн|кільк|число|перевірено|_не_те$|_не_ті|_не_ті_|номер|_є$|^є_|"
                       r"_ключ$|^ключ_|_межа$|_записано|_на_офер|кеш|_n$|порядок|частка|^порогу?_|_частка|_спір$|_спір_)", re.I)
КАДР = re.compile(r"^(фото|кадр|кадри|фото_.+|кадр_.+|кадри_.+|photo|photos|image|images|picture|pictures|img|галерея|gallery|"
                  r"фото_усі)$", re.I)
КОЛІР = re.compile(r"^(колір|кольори|колір_.+|Колір|color|colour|colors|colours|color_.+|colour_.+|hex|lab|свотчі|swatch\w*|"
                   r"варіанти_кольору)$", re.I)
НАЯВНІСТЬ = re.compile(r"^(наявність.*|available|in_stock|stock\w*|розміри_в_наявності|в_наявності)$", re.I)
КЛЮЧ_ІМ = re.compile(r"(ключ|key|sig|підпис|канон|canonical|двійник|дубл|дизайн_)", re.I)


def роль(ключ):
    if not isinstance(ключ, str) or not ключ or ЛІЧИЛЬНИК.search(ключ):
        return None
    for ім, р in (("кадр", КАДР), ("колір", КОЛІР), ("наявність", НАЯВНІСТЬ)):
        if р.match(ключ):
            return ім
    return None


# ---- ОЗНАКИ ДЖЕРЕЛА Й ВИБОРУ (лексеми функції) ------------------------------------------------------------------
ДЖЕРЕЛО = (
    ("DOM", re.compile(r"beautifulsoup|\bselect_one\b|\bselect\b|find_all|\bcssselect\b|\bxpath\b|lxml|etree|\.find\b|"
                       r"htmlparser|css_?селектор|селектор")),
    ("атрибути", re.compile(r"data-|\battrs\b|\bsrc\b|srcset|\bhref\b|\balt\b|og:image|itemprop|content")),
    ("JSON-LD", re.compile(r"ld\+json|application/ld|@type|schema\.org|\bjson_?ld\b|колір_ld|\bld\b")),
    ("regex", re.compile(r"\bre\b|findall|finditer|\.search\b|\.match\b|re\.compile|регуляр|\bpattern\b|\bрег\w*")),
    ("фід", re.compile(r"\boffer|\bофер|\byml\b|<offer|\bfeed\b|\bфід\b|\bpicture\b|\bparam\b")),
    ("лістинг", re.compile(r"collection|products\.json|listing|лістинг|каталог_сторін|\bкатегор|\bсторінка_списку|\bsitemap|мапа_сайту")),
    ("галерея", re.compile(r"gallery|галере|\bimages\b|\bmedia\b|\bkpi_img|\bmedia_gallery")),
    ("API", re.compile(r"json\.loads|\.json\(|\bjson\b|wc/store|store api|/wp-json|\bapi\b")),
)
ВАРІАЦІЇ = re.compile(r"variant|variation|варіант|варіац|\bsku\b|артикул|attribute_|image_id|variant_id|featured_image|"
                      r"offer_id|group_id|options?\b|свотч|swatch|терм\b|терми|\bterms?\b")
ВЛАСНИК_ВАР = re.compile(r"variant|variation|варіант|варіац|\bsku\b|артикул|attribute_pa|image_id|featured_image")
ПОЛЕ_ВЛАСНИКА = re.compile(r"^(варіант|власник\w*|кадр_власник\w*|variant\w*|owner\w*)$", re.I)
КОЛІР_ПАРАМ = re.compile(r"колір|color|colour|variant|варіант|variation|attribute_|\bsku\b|артикул|розмір|size|param|"
                         r"опція|option|свотч")
КАДР_ТОКЕН = re.compile(r"image|photo|фото|кадр|\bsrc\b|picture|img|галер|gallery")
АКТИВНИЙ = re.compile(r"актив|active|selected|checked|current|єдин|single|\bonly\b|default|головн|featured|primary|swatch_?selected")
СЕСТРИ = re.compile(r"сестр|sibling|group_id|двійник|сусід")
СЛОВО_КОЛЬОРУ = re.compile(r"слово|назва_кольору|colour_word|color_word|колір_слов|слово_моделі|слово_крамниці")
ПІДБІР = re.compile(r"сім.?ї|сімя|вікн|\blab\b|узгоджен|співпад|збігаєть")
ЗВ_НЕВІДОМО = "невідомо"
ПЕРВИННИЙ = frozenset(("min", "max", "sorted", "next", "first", "sample", "choice"))
ІМ_ВАРІАНТА = re.compile(r"^(вар|var|варіант\w*|variant\w*|v|вар_\w+|variation\w*)$", re.I)
ВЛАСНИК_ВИКЛИК = re.compile(r"^_?власник(_кадру)?$|^власник_кадру$")

Місце = collections.namedtuple("Місце", "файл рядок пункт статус чому ключ роль")


def текст_виразу(вузол):
    """Лексеми піддерева: імена, атрибути, ключові аргументи, рядкові константи — малими літерами."""
    лекс = []
    for n in ast.walk(вузол):
        if isinstance(n, ast.Name):
            лекс.append(n.id)
        elif isinstance(n, ast.Attribute):
            лекс.append(n.attr)
        elif isinstance(n, ast.keyword) and n.arg:
            лекс.append(n.arg)
        elif isinstance(n, ast.arg):
            лекс.append(n.arg)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            лекс.append(n.name)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 160:
            лекс.append(n.value)
    return "\n".join(лекс).lower()


def розібрати(шлях):
    with open(шлях, encoding="utf-8") as ф:
        код = ф.read()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(код)


def одиниці(дерево):
    """(назва, вузол, список операторів-коренів): кожна функція верхнього рівня чи метод класу — одиниця; решта модуля — «<модуль>»."""
    од, модуль = [], []

    def пройти(тіло, клас=""):
        for н in тіло:
            if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef)):
                од.append(((клас + "." if клас else "") + н.name, н))
            elif isinstance(н, ast.ClassDef):
                пройти(н.body, н.name)
            else:
                модуль.append(н)
    пройти(дерево.body)
    return од, модуль


ЗВІТ_СУБ = re.compile(r"^(діаг\w*|лічильник\w*|звіт\w*|журнал\w*|лог|stats?|метрик\w*|підсумок|підсумки)$", re.I)


def порожнє(в):
    """Значення-заготовка: `None`, `False`, `0`, `""`, порожні `[]`, `{}`, `()`."""
    if isinstance(в, ast.Constant):
        return в.value in (None, False, 0, "")
    return isinstance(в, (ast.List, ast.Tuple, ast.Dict, ast.Set)) and not (getattr(в, "elts", None) or getattr(в, "keys", None))


class Збирач(ast.NodeVisitor):
    """Збирає записи полів ролей, записи ключів і запис на диск у одиниці; пам'ятає цикли по варіантах навколо."""

    def __init__(self, модуль=False):
        self.модуль = модуль
        self.записи = []       # (рядок, ключ, роль, у_варіанті, цикл_мітка, суб)
        self.ключі = []        # (рядок, ім'я, вузол_виразу)
        self.диск = []         # (рядок, вузол виклику)
        self.цикли = []        # стек: (вузол, чи_варіантний)
        self.виклики_власника = []
        self.читання_варіант = False
        self.варіант_цикл_кадр = False   # у циклі по варіантах є кадр-токен
        self.відображення_кадру = False
        self.власник_невідомо = False    # «невідомо» записано в поле власника/варіанта

    def _невідомо(self, ключ, значення):
        if isinstance(ключ, str) and ПОЛЕ_ВЛАСНИКА.match(ключ) and значення is not None and any(
                isinstance(x, ast.Constant) and x.value == ЗВ_НЕВІДОМО for x in ast.walk(значення)):
            self.власник_невідомо = True

    # -- контекст циклів
    def _цикл(self, вузол, ітер, тіло):
        лекс = текст_виразу(ітер)
        вар = bool(ВАРІАЦІЇ.search(лекс)) or (isinstance(вузол, ast.For) and self._ціль_варіант(вузол.target))
        self.цикли.append(вар)
        for н in ітер_вузли(тіло):
            self.visit(н)
        if вар and any(КАДР_ТОКЕН.search(текст_виразу(н)) for н in ітер_вузли(тіло)):
            self.варіант_цикл_кадр = True
        self.цикли.pop()

    @staticmethod
    def _ціль_варіант(ціль):
        return any(isinstance(n, ast.Name) and ІМ_ВАРІАНТА.match(n.id) for n in ast.walk(ціль))

    def visit_For(self, н):
        self.visit(н.iter)
        self._цикл(н, н.iter, н.body + н.orelse)

    visit_AsyncFor = visit_For

    def _comp(self, н):
        вар = False
        for г in н.generators:
            self.visit(г.iter)
            if ВАРІАЦІЇ.search(текст_виразу(г.iter)) or self._ціль_варіант(г.target):
                вар = True
        self.цикли.append(вар)
        elts = [н.elt] if not isinstance(н, ast.DictComp) else [н.key, н.value]
        for e in elts:
            self.visit(e)
        for г in н.generators:
            for і in г.ifs:
                self.visit(і)
        if вар and any(КАДР_ТОКЕН.search(текст_виразу(e)) for e in elts):
            self.варіант_цикл_кадр = True
        self.цикли.pop()

    visit_ListComp = visit_SetComp = visit_GeneratorExp = _comp

    def visit_DictComp(self, н):
        self._comp(н)
        if ВАРІАЦІЇ.search(текст_виразу(н.key)) and КАДР_ТОКЕН.search(текст_виразу(н.value)):
            self.відображення_кадру = True

    @property
    def у_варіанті(self):
        return any(self.цикли)

    # -- записи полів
    def _запис(self, вузол, ключ, суб="", значення=None):
        р = роль(ключ)
        if not р and isinstance(значення, (ast.Subscript, ast.Attribute)):
            for ч in ast.walk(значення):
                if isinstance(ч, ast.Subscript) and isinstance(ч.slice, ast.Constant):
                    р = роль(ч.slice.value)
                elif isinstance(ч, ast.Call) and isinstance(ч.func, ast.Attribute) and ч.func.attr == "get" and ч.args \
                        and isinstance(ч.args[0], ast.Constant):
                    р = роль(ч.args[0].value)
                if р:
                    break
        if р and ЗВІТ_СУБ.match(суб or ""):
            return          # діагностика й журнал прогону: не запис таблиці
        if р and порожнє(значення):
            return          # заготовка запису (`None`, `""`, `[]`, `{}`, `0`): поле ще не взято з крамниці
        if р and self.модуль and isinstance(значення, ast.Constant):
            return          # константа модуля (словник імен, таблиця коду), не запис речі
        if р:
            self.записи.append((вузол.lineno, ключ, р, self.у_варіанті, суб, вузол, значення))

    def visit_Dict(self, н):
        for к, в in zip(н.keys, н.values):
            if isinstance(к, ast.Constant) and isinstance(к.value, str):
                self._невідомо(к.value, в)
                self._запис(к, к.value, "", в)
                if ВАРІАЦІЇ.search(текст_виразу(к)) and КАДР_ТОКЕН.search(текст_виразу(в)):
                    self.відображення_кадру = True
        self.generic_visit(н)

    def visit_Subscript(self, н):
        if isinstance(н.ctx, ast.Store) and isinstance(н.slice, ast.Constant) and isinstance(н.slice.value, str):
            суб = ""

            if isinstance(н.value, ast.Name):
                суб = н.value.id
            self._запис(н, н.slice.value, суб)
        elif isinstance(н.ctx, ast.Store):
            if ВАРІАЦІЇ.search(текст_виразу(н.slice)):
                self.відображення_кадру = True
        elif isinstance(н.ctx, ast.Load) and isinstance(н.slice, ast.Constant) and н.slice.value == "варіант":
            self.читання_варіант = True
        self.generic_visit(н)

    def visit_Attribute(self, н):
        """Атрибутний запис має ту саму одиницю й суд, що запис ключем."""
        if isinstance(н.ctx, ast.Store):
            self._запис(н, н.attr, ім_виклику(н.value))
        self.generic_visit(н)

    def visit_Call(self, н):
        ф = н.func
        ім = ф.attr if isinstance(ф, ast.Attribute) else (ф.id if isinstance(ф, ast.Name) else "")
        if ім == "setdefault" and н.args and isinstance(н.args[0], ast.Constant) and isinstance(н.args[0].value, str):
            суб = ф.value.id if isinstance(ф.value, ast.Name) else ""
            self._запис(н, н.args[0].value, суб, н.args[1] if len(н.args) > 1 else None)
        elif ім in ("update", "dict", "_replace"):
            for к in н.keywords:
                if к.arg:
                    self._невідомо(к.arg, к.value)
                    self._запис(н, к.arg, "", к.value)
        elif ім == "get" and н.args and isinstance(н.args[0], ast.Constant) and н.args[0].value == "варіант":
            self.читання_варіант = True
        if ВЛАСНИК_ВИКЛИК.match(ім):
            self.виклики_власника.append(н.lineno)
        if ім in ("dump", "write_text", "write_bytes", "writerow", "writerows", "write") or (
                ім == "open" and len(н.args) > 1 and isinstance(н.args[1], ast.Constant)
                and isinstance(н.args[1].value, str) and any(c in н.args[1].value for c in "wax")):
            self.диск.append((н.lineno, н))
        elif ім == "open" and any(isinstance(к.value, ast.Constant) and isinstance(к.value.value, str) and
                                  any(c in к.value.value for c in "wax") for к in н.keywords if к.arg == "mode"):
            self.диск.append((н.lineno, н))
        elif ім == "add" and н.args and isinstance(н.args[0], (ast.Tuple, ast.JoinedStr)):
            self.ключі.append((н.lineno, "<add>", н.args[0]))
        elif ім in ("append", "writerow") and н.args and isinstance(н.args[0], (ast.Tuple, ast.List)):
            for і, знач in enumerate(н.args[0].elts):
                ключ = знач.id if isinstance(знач, ast.Name) else "<позиція %d>" % і
                self._запис(н, ключ, ім_виклику(ф.value) if isinstance(ф, ast.Attribute) else "", знач)
        self.generic_visit(н)

    def visit_Assign(self, н):
        for ц in н.targets:
            if isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant):
                self._невідомо(ц.slice.value, н.value)
            if isinstance(ц, ast.Name) and КЛЮЧ_ІМ.search(ц.id) and isinstance(н.value, (ast.Tuple, ast.JoinedStr, ast.Call,
                                                                                      ast.BinOp, ast.Subscript)):
                self.ключі.append((н.lineno, ц.id, н.value))
        self.generic_visit(н)


def ітер_вузли(тіло):
    return тіло if isinstance(тіло, list) else [тіло]


def ключ_функції(вузол):
    """Функція-ключ (ім'я з `ключ`, `канон`, `двійник`): повернені вирази."""
    if not isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    if not КЛЮЧ_ІМ.search(вузол.name):
        return []
    return [(н.lineno, вузол.name, н.value) for н in ast.walk(вузол) if isinstance(н, ast.Return) and н.value is not None
            and isinstance(н.value, (ast.Tuple, ast.JoinedStr, ast.Call, ast.BinOp, ast.Subscript, ast.Name))]


ЗАПИТ_ВІДКИНУТО = re.compile(r"urlparse|urlsplit|urldefrag|urlunparse|urlunsplit|\.path\b|_replace|\"\?\"|'\?'|split\(\"\?\"\)|"
                             r"query=|^\?$|rstrip|\.netloc")
ІД_ЛИШЕ = re.compile(r"^[\wа-яіїєґ_.]*(\bid\b|\bід\b|_id|\bідентифікатор)[\wа-яіїєґ_.]*$")
ПРОДУКТ_ЧАСТИНА = re.compile(r"url|адрес|назва|name|group|model|бренд|фасон|дизайн|href|link|stem|стем|слаг|slug|канон")


def частин_ключа(в):
    if isinstance(в, ast.Tuple):
        return len(в.elts)
    if isinstance(в, ast.JoinedStr):
        return sum(1 for x in в.values if isinstance(x, ast.FormattedValue))
    if isinstance(в, ast.Call):
        ф = в.func
        if isinstance(ф, ast.Attribute) and ф.attr == "join" and в.args:
            а = в.args[0]
            return len(а.elts) if isinstance(а, (ast.Tuple, ast.List)) else 2
        return max(1, len(в.args))
    return 1


def адреса_як_є(вираз):
    """Частина складеного ключа — адреса, прочитана без перетворення (`з.get("url")`, `з["url"]`, `url`): запит із
    параметром варіації в ній лишається. Адреса через виклик (`норм_адреса(url)`) доказом не є — він міг зрізати запит."""
    частини = вираз.elts if isinstance(вираз, ast.Tuple) else [ч.value for ч in вираз.values
                                                               if isinstance(ч, ast.FormattedValue)] if isinstance(вираз, ast.JoinedStr) else []
    for ч in частини:
        if isinstance(ч, ast.Call) and isinstance(ч.func, ast.Attribute) and ч.func.attr == "get" and ч.args \
                and isinstance(ч.args[0], ast.Constant):
            назва = ч.args[0].value
        elif isinstance(ч, ast.Subscript) and isinstance(ч.slice, ast.Constant):
            назва = ч.slice.value
        elif isinstance(ч, ast.Name):
            назва = ч.id
        else:
            continue
        if isinstance(назва, str) and re.fullmatch(r"url|адреса|href|link", назва.lower()):
            return True
    return False


def суд_ключа(рядок, ім, вираз):
    """Суд п.3 для ключа: (порушує, чому) або None, якщо вираз не ключ запису речі."""
    лекс = текст_виразу(вираз)
    чи_адреса = bool(re.search(r"url|адрес|href|link", лекс))
    параметр = bool(КОЛІР_ПАРАМ.search(лекс))
    відкинуто = bool(ЗАПИТ_ВІДКИНУТО.search(лекс))
    частин = частин_ключа(вираз)
    запит_збережено = bool(re.search(r"urlencode|parse_qsl?|\.query\b|^query$", лекс, re.M))
    if чи_адреса and відкинуто and not запит_збережено and not параметр:
        return True, "ключ — адреса без запиту: параметр варіації відкинуто (`%s`)" % ім
    if частин >= 2 and ПРОДУКТ_ЧАСТИНА.search(лекс) and not відкинуто and not параметр and адреса_як_є(вираз):
        return False, "ключ несе адресу як є: запит із параметром варіації не відкинуто (`%s`)" % ім
    if частин >= 2 and ПРОДУКТ_ЧАСТИНА.search(лекс) and not параметр:
        return True, "складений ключ (%d частин) без кольору, варіанта, артикула чи параметра (`%s`)" % (частин, ім)
    if частин >= 2 and ПРОДУКТ_ЧАСТИНА.search(лекс):
        return False, "ключ несе параметр варіації (`%s`)" % ім
    return None


КЕШ = re.compile(r"кеш|cache|memo", re.I)


def ключ_кешу(ім, одиниця):
    """Ключ лише кешу похідного (`if ключ in КЕШ: return КЕШ[ключ]` … `КЕШ[ключ] = результат`), а кешоване й повернене
    функцією не має ролі кадру, кольору чи наявності: такий ключ не ключ двійника чи запису за п.3 — сестри з тим самим
    ключем ділять лише похідне без ролі (вид речі за назвою), а не поле варіанта. Кеш, що тримає роль, — далі суд п.3."""
    if ім.startswith("<") or одиниця is None:
        return False

    def кеш(в):
        return isinstance(в, (ast.Name, ast.Attribute)) and bool(КЕШ.search(ім_виклику(в) or ""))

    вжитків, кешоване = 0, []
    for н in ast.walk(одиниця):
        if isinstance(н, ast.Name) and н.id == ім and isinstance(н.ctx, ast.Load):
            вжитків += 1
    кешових = 0
    for н in ast.walk(одиниця):
        if isinstance(н, ast.Compare) and isinstance(н.left, ast.Name) and н.left.id == ім and len(н.ops) == 1 \
                and isinstance(н.ops[0], (ast.In, ast.NotIn)) and кеш(н.comparators[0]):
            кешових += 1
        elif isinstance(н, ast.Subscript) and isinstance(н.slice, ast.Name) and н.slice.id == ім and кеш(н.value):
            кешових += 1
            if isinstance(н.ctx, ast.Store):
                кешоване.append(батько_присвоєння(одиниця, н))
        elif isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr == "get" and кеш(н.func.value) \
                and н.args and isinstance(н.args[0], ast.Name) and н.args[0].id == ім:
            кешових += 1
    if not вжитків or кешових != вжитків or not кешоване or None in кешоване:
        return False
    присвоєння = {}
    for н in ast.walk(одиниця):
        if isinstance(н, ast.Assign):
            for ц in н.targets:
                for в in ast.walk(ц):
                    if isinstance(в, ast.Name):
                        присвоєння.setdefault(в.id, []).append(н.value)
    повернене = [н.value for н in ast.walk(одиниця) if isinstance(н, ast.Return) and н.value is not None]
    черга, бачено = list(кешоване) + повернене, set()
    while черга:
        в = черга.pop()
        for н in ast.walk(в):
            if isinstance(н, ast.Name) and н.id not in бачено:
                бачено.add(н.id)
                черга.extend(присвоєння.get(н.id, []))
            elif isinstance(н, ast.Constant) and isinstance(н.value, str) and роль(н.value):
                return False
            elif isinstance(н, ast.keyword) and роль(н.arg):
                return False
    return not any(роль(і) for і in бачено if і != ім)


def батько_присвоєння(одиниця, ціль):
    """Значення присвоєння, чия ціль — `ціль`; None, якщо ціль не в простому присвоєнні."""
    for н in ast.walk(одиниця):
        if isinstance(н, ast.Assign) and any(ц is ціль for ц in н.targets):
            return н.value
    return None


def ознаки(лекс):
    дж = [н for н, р in ДЖЕРЕЛО if р.search(лекс)]
    return дж


def вибір(вузли_одиниці, лекс):
    """Ознаки вибору в одиниці: голова списку, активний/єдиний, перший кадр, кадр за кольором слова, дані сестер."""
    в = []
    голова = False
    for вуз in ast.walk(вузли_одиниці):
        if isinstance(вуз, ast.Subscript) and isinstance(вуз.ctx, ast.Load):
            с = вуз.slice
            if isinstance(с, ast.Constant) and с.value in (0, -1) and not isinstance(с.value, bool):
                голова = True
            elif isinstance(с, ast.Slice) and isinstance(с.upper, ast.Constant) and isinstance(с.upper.value, int) \
                    and с.lower is None and с.upper.value <= 3:
                голова = True
        elif isinstance(вуз, ast.Call):
            ф = вуз.func
            ім = ф.attr if isinstance(ф, ast.Attribute) else (ф.id if isinstance(ф, ast.Name) else "")
            if ім in ПЕРВИННИЙ:
                голова = True
            if ім == "pop" and вуз.args and isinstance(вуз.args[0], ast.Constant) and вуз.args[0].value == 0:
                голова = True
    if голова:
        в.append("голова списку")
    if АКТИВНИЙ.search(лекс):
        в.append("активний чи єдиний")
    if СЛОВО_КОЛЬОРУ.search(лекс) and КАДР_ТОКЕН.search(лекс) and ПІДБІР.search(лекс):
        в.append("кадр за кольором слова")
    if СЕСТРИ.search(лекс):
        в.append("дані сестер")
    return в


# ---- ДОКАЗ ВЛАСНИКА КАДРУ (уточнення класу 13.11, паспорт «Рішення») ----------------------------------------------
# Колір, виміряний із кадру, чий власник-варіант доведено даними крамниці, — не місце за п.2, коли запис несе цього
# власника, а кадр виміру збережено з маніфестом; той самий запис кольору без доведеного власника — місце. Запис самого
# доказу власності (власник із даних крамниці або «невідомо») — не місце за п.1. Доказ — значення виклику `доказ…`
# (`фід_власник_кадру.доказ_варіанта`, `жнива_запис.доказ_кадру`) і все, що з нього присвоєно; назва поля чи змінної
# доказом не є.
ДОКАЗ_ВИКЛИК = re.compile(r"^_?доказ\w*$")
КАДР_ВИМІРУ = re.compile(r"^кадр_виміру$")
МАНІФЕСТ = frozenset(("sha256",))


def заперечення(тест):
    """Чи гілка `if тест` — гілка БЕЗ доказу: `not д`, `д is None`, `д == "невідомо"`."""
    if isinstance(тест, ast.UnaryOp) and isinstance(тест.op, ast.Not):
        return True
    if isinstance(тест, ast.Compare) and len(тест.ops) == 1 and isinstance(тест.comparators[0], ast.Constant) \
            and тест.comparators[0].value in (None, ЗВ_НЕВІДОМО):
        return isinstance(тест.ops[0], (ast.Is, ast.Eq))
    return False


def нейтральне(вираз):
    """Значення без кольору: None чи «невідомо» (гілка без доказу так не пише колір варіанта)."""
    return вираз is None or (isinstance(вираз, ast.Constant) and вираз.value in (None, ЗВ_НЕВІДОМО)) or (
        isinstance(вираз, (ast.Dict, ast.Call)) and any(isinstance(з, ast.Constant) and з.value == ЗВ_НЕВІДОМО
                                                       for з in поля(вираз).values()))


class Доказ:
    """Змінні й поля одиниці, що несуть доказ власника-варіанта кадру з даних крамниці."""

    def __init__(self, охоплення, функції):
        self.вузли = list(власні_вузли(охоплення))
        self.функції = функції or {}
        self.імена, self.ключі = set(), set()
        змінилось = True
        while змінилось:
            змінилось = False
            for н in self.вузли:
                if isinstance(н, ast.Assign):
                    цілі, значення = н.targets, н.value
                elif isinstance(н, (ast.AnnAssign, ast.AugAssign)) and н.value is not None:
                    цілі, значення = [н.target], н.value
                elif isinstance(н, (ast.comprehension, ast.For, ast.AsyncFor)):
                    цілі, значення = [н.target], н.iter
                else:
                    continue
                if not self.є_доказом(значення):
                    continue
                for ц in цілі:
                    for е in (ц.elts if isinstance(ц, (ast.Tuple, ast.List)) else [ц]):
                        if isinstance(е, ast.Name) and е.id not in self.імена:
                            self.імена.add(е.id)
                            змінилось = True
                        elif isinstance(е, ast.Subscript) and isinstance(е.value, ast.Name) \
                                and isinstance(е.slice, ast.Constant) and (е.value.id, е.slice.value) not in self.ключі:
                            self.ключі.add((е.value.id, е.slice.value))
                            змінилось = True

    def є_доказом(self, вираз):
        """Значення — сам доказ чи його проєкція (`д["варіант"]`, `д if д else "невідомо"`, `[доказ(…)]`), а не запис,
        у якому доказ — одне з багатьох полів: інакше доказом ставав би кожен запис поруч."""
        if isinstance(вираз, ast.Call):
            if ДОКАЗ_ВИКЛИК.match(ім_виклику(вираз.func).rsplit(".", 1)[-1] or ""):
                return True
            return isinstance(вираз.func, ast.Attribute) and вираз.func.attr == "get" and self.є_доказом(вираз.func.value)
        if isinstance(вираз, ast.Name):
            return вираз.id in self.імена
        if isinstance(вираз, ast.Subscript):
            if isinstance(вираз.value, ast.Name) and isinstance(вираз.slice, ast.Constant) \
                    and (вираз.value.id, вираз.slice.value) in self.ключі:
                return True
            return self.є_доказом(вираз.value)
        if isinstance(вираз, ast.Attribute):
            return self.є_доказом(вираз.value)
        if isinstance(вираз, ast.IfExp):
            гілки = [вираз.body, вираз.orelse]
            return any(self.є_доказом(г) for г in гілки) and all(self.є_доказом(г) or нейтральне(г) for г in гілки)
        if isinstance(вираз, ast.BoolOp):
            return any(self.є_доказом(з) for з in вираз.values) and all(
                self.є_доказом(з) or нейтральне(з) for з in вираз.values)
        if isinstance(вираз, (ast.List, ast.Tuple)) and вираз.elts:
            return all(self.є_доказом(е) for е in вираз.elts)
        return False

    def несе(self, вираз):
        """Умова читає доказ: виклик `доказ…`, змінну з доказом чи поле, записане з доказу."""
        if вираз is None:
            return False
        for н in ast.walk(вираз):
            if isinstance(н, ast.Call) and ДОКАЗ_ВИКЛИК.match(ім_виклику(н.func).rsplit(".", 1)[-1] or ""):
                return True
            if isinstance(н, ast.Name) and isinstance(н.ctx, ast.Load) and н.id in self.імена:
                return True
            if isinstance(н, ast.Subscript) and isinstance(н.value, ast.Name) and isinstance(н.slice, ast.Constant) \
                    and (н.value.id, н.slice.value) in self.ключі:
                return True
        return False

    def поля_запису(self, вузол):
        """Поля запису: літерал чи конструктор — його ключі; `база["поле"] = …` — усі такі присвоєння бази в одиниці."""
        if isinstance(вузол, (ast.Dict, ast.Call)):
            return поля(вузол)
        if isinstance(вузол, ast.Subscript) and isinstance(вузол.value, ast.Name):
            база, п = вузол.value.id, {}
            for н in self.вузли:
                if isinstance(н, ast.Assign):
                    for ц in н.targets:
                        for е in (ц.elts if isinstance(ц, (ast.Tuple, ast.List)) else [ц]):
                            if isinstance(е, ast.Subscript) and isinstance(е.value, ast.Name) and е.value.id == база \
                                    and isinstance(е.slice, ast.Constant) and isinstance(е.slice.value, str):
                                п.setdefault(е.slice.value, н.value)
            return п
        return {}

    def маніфест(self, значення, граф, шлях=frozenset()):
        """Кадр виміру з маніфестом: значення походить із запису з `sha256` (байти кадру виміру), а не лише з адреси."""
        if значення is None:
            return False
        for н in ast.walk(значення):
            if isinstance(н, (ast.Dict, ast.Call)) and МАНІФЕСТ & set(поля(н)):
                return True
            if isinstance(н, ast.Call) and isinstance(н.func, ast.Name) and н.func.id in self.функції \
                    and any(isinstance(х, ast.Constant) and х.value in МАНІФЕСТ or isinstance(х, ast.keyword) and х.arg in МАНІФЕСТ
                            for х in ast.walk(self.функції[н.func.id])):
                return True
            if isinstance(н, ast.Name) and н.id not in шлях:
                if any(self.маніфест(з, граф, шлях | {н.id}) for з in граф.визначення(н.id, getattr(н, "lineno", 10 ** 9))):
                    return True
        return False

    def під_доказом(self, вузол, значення, батьки, межа):
        """Колір пишеться лише з доказом: гілка `if <доказ>` чи `… if <доказ> else None/«невідомо»`."""
        if isinstance(значення, ast.IfExp) and self.несе(значення.test):
            return нейтральне(значення.body if заперечення(значення.test) else значення.orelse)
        cur = вузол
        while cur in батьки and cur is not межа:
            р = батьки[cur]
            if isinstance(р, (ast.If, ast.IfExp)) and cur is not р.test and self.несе(р.test):
                у_тілі = any(х is cur for х in р.body) if isinstance(р, ast.If) else cur is р.body
                return у_тілі != заперечення(р.test) or нейтральне(значення)
            cur = р
        return False

    def власник_у_записі(self, п):
        """Запис несе власника з доказу: поле власника з доказу чи кадр виміру, у якого поле власника записано з доказу."""
        if any(ПОЛЕ_ВЛАСНИКА.match(к) and self.є_доказом(з) for к, з in п.items() if isinstance(к, str)):
            return True
        return any(isinstance(з, ast.Name) and any(б == з.id and ПОЛЕ_ВЛАСНИКА.match(к) for б, к in self.ключі)
                   for к, з in п.items() if isinstance(к, str) and КАДР_ВИМІРУ.match(к))

    def колір_доведеного(self, вузол, значення, батьки, межа, граф):
        """(дотримує, чому): колір кадру з доведеним власником; None — запис без власника й кадру виміру з маніфестом."""
        п = self.поля_запису(вузол)
        кадр = [з for к, з in п.items() if isinstance(к, str) and КАДР_ВИМІРУ.match(к)]
        if not (self.власник_у_записі(п) and кадр and any(self.маніфест(з, граф) for з in кадр)):
            return None
        if self.під_доказом(вузол, значення, батьки, межа):
            return True, "колір кадру з доведеним власником-варіантом: запис несе власника, кадр виміру з маніфестом"
        return False, ("запис несе власника й кадр виміру з маніфестом, але колір пишеться й без доказу власника "
                       "(гілка «невідомо» дає колір варіанта)")

    def колір_знято_гілкою(self, значення, батьки):
        """Колір пишеться змінною, яку гілка `if <змінна> and <виклик(…)>:` перезаписує на None разом із причиною-словом
        «невідомо…» (`колір, акценти, джерело = None, [], "невідомо: …"`), а умова — виклик читача ознаки варіацій кольору
        (`ЧИТАЧІ_ВАРІАЦІЙ_КОЛЬОРУ`, клас паспорта; 14988: «будь-який виклик» знімав і вигадану умову): у гілці запис
        несе «невідомо» з причиною, а не колір (рішення 13.11, кв2). Що читач і справді знаходить такі сторінки, кажуть
        дані крамниці, а не код (у PR — гіпотезою)."""
        if not isinstance(значення, ast.Name):
            return False
        ім = значення.id
        for н in self.вузли:
            if not isinstance(н, ast.Assign) or not isinstance(н.value, (ast.Tuple, ast.List)) \
                    or not isinstance(н.targets[0], (ast.Tuple, ast.List)):
                continue
            цілі, зн = н.targets[0].elts, н.value.elts
            if len(цілі) != len(зн):
                continue
            пара = [(ц, з) for ц, з in zip(цілі, зн) if isinstance(ц, ast.Name) and ц.id == ім]
            причина = any(isinstance(з, ast.Constant) and isinstance(з.value, str) and з.value.startswith(ЗВ_НЕВІДОМО)
                          for з in зн)
            if not (пара and причина and all(isinstance(з, ast.Constant) and з.value is None for _, з in пара)):
                continue
            cur = н
            while cur in батьки:
                р = батьки[cur]
                if isinstance(р, ast.If) and any(х is cur for х in р.body) \
                        and any(isinstance(х, ast.Name) and х.id == ім for х in ast.walk(р.test)) \
                        and any(isinstance(х, ast.Call) and (ім_виклику(х.func) or "").rsplit(".", 1)[-1] in ЧИТАЧІ_ВАРІАЦІЙ_КОЛЬОРУ
                                for х in ast.walk(р.test)):
                    return True
                cur = р
        return False

    def позиційний_доказ(self, вузол, значення):
        """Позиційний запис (список чи кортеж): одна з позицій — виклик читача доказу варіанта (`доказ…`) із запасним
        словом «невідомо» (`доказ(…) or "невідомо"`): власник записано, а коли доказу нема — «невідомо»."""
        л = значення if isinstance(значення, (ast.List, ast.Tuple)) else вузол if isinstance(вузол, (ast.List, ast.Tuple)) else None
        if л is None:
            return False
        for е in л.elts:
            if isinstance(е, ast.BoolOp) and isinstance(е.op, ast.Or) and len(е.values) >= 2 \
                    and isinstance(е.values[-1], ast.Constant) and е.values[-1].value == ЗВ_НЕВІДОМО \
                    and any(isinstance(з, ast.Call) and ДОКАЗ_ВИКЛИК.match(ім_виклику(з.func).rsplit(".", 1)[-1] or "")
                            for з in е.values[:-1]):
                return True
        return False

    def запис_доказу(self, вузол, значення, граф):
        """Запис самого доказу власності: у записі кадру поле власника з даних крамниці, а кадр — ключ звірки з прив'язкою
        платформи (`прив'язка.get(кадр)` у перевірці перед записом)."""
        if self.позиційний_доказ(вузол, значення):
            return True
        п = self.поля_запису(вузол)
        власник = [з for к, з in п.items() if isinstance(к, str) and ПОЛЕ_ВЛАСНИКА.match(к)
                   and not isinstance(з, ast.Constant)]
        if not власник or not any("вхід" in граф.теги(з) for з in власник):
            return False
        імена = {н.id for н in ast.walk(значення) if isinstance(н, ast.Name)} if значення is not None else set()
        пошук = set()
        for н in self.вузли:
            if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
                в = н.value
                ключ = (в.args[0] if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get"
                        and в.args else в.slice if isinstance(в, ast.Subscript) else None)
                if isinstance(ключ, ast.Name) and ключ.id in імена:
                    пошук.add(н.targets[0].id)
        if not пошук:
            return False
        return any(isinstance(н, ast.If) and any(isinstance(х, ast.Name) and х.id in пошук for х in ast.walk(н.test))
                   for н in self.вузли)


def діагностика(вузол, батьки):
    """Літерал чи конструктор запису, присвоєний змінній діагностики (`діаг = dict(…)`): журнал прогону, не таблиця
    (те саме правило, що `діаг["поле"] = …` у `Збирач._запис`)."""
    б = батьки.get(вузол)
    return isinstance(вузол, (ast.Dict, ast.Call)) and isinstance(б, ast.Assign) and б.value is вузол and any(
        isinstance(ц, ast.Name) and ЗВІТ_СУБ.match(ц.id) for ц in б.targets)


def єдиний_збіг(ф):
    """Функція модуля, що падає на кількох збігах: `if len(…) > 1: raise`."""
    for н in ast.walk(ф):
        if isinstance(н, ast.If) and any(isinstance(х, ast.Raise) for х in н.body) and isinstance(н.test, ast.Compare) \
                and isinstance(н.test.left, ast.Call) and ім_виклику(н.test.left.func) == "len" \
                and isinstance(н.test.ops[0], ast.Gt) and isinstance(н.test.comparators[0], ast.Constant) \
                and н.test.comparators[0].value == 1:
            return True
    return False


def сторінка_варіації(значення, одиниця, функції):
    """Колір чи наявність зі сторінки однієї варіації (уточнення 13.11, кв3): активний свотч чи кнопка на власній
    сторінці варіації — дані її варіанта, коли запис — ця сторінка (одиниця падає, якщо канонічна адреса сторінки не
    адреса запису), а поле — єдиний збіг (помічник падає на кількох). Значення складено лише з таких збігів, локальних
    імен і сталих: наявність оферти, приписана всім розмірам (список усіх кнопок), — не єдиний збіг, лишається місцем.
    Що активний елемент і є ця сторінка, кажуть дані крамниці, а не код: прилад цього не бачить (у PR — гіпотезою)."""
    if значення is None or одиниця is None:
        return False
    канонічна = any(isinstance(н, ast.If) and any(isinstance(х, ast.Raise) for х in н.body)
                    and any(isinstance(к, ast.Constant) and isinstance(к.value, str) and "canonical" in к.value
                            for к in ast.walk(н.test)) for н in ast.walk(одиниця))
    if not канонічна:
        return False
    присвоєно = {}
    for н in ast.walk(одиниця):
        if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
            присвоєно.setdefault(н.targets[0].id, []).append(н.value)
    збігів, черга, бачено = 0, [значення], set()
    while черга:
        в = черга.pop()
        if isinstance(в, ast.Call):
            if isinstance(в.func, ast.Name) and в.func.id in функції and єдиний_збіг(функції[в.func.id]):
                збігів += 1
                continue
            if isinstance(в.func, ast.Attribute) and в.func.attr == "get" and isinstance(в.func.value, ast.Name) \
                    and в.func.value.id.isupper():
                черга.extend(в.args)
                continue
            return False
        if isinstance(в, ast.Name):
            if в.id in бачено:
                continue
            бачено.add(в.id)
            if в.id not in присвоєно:
                return False
            черга.extend(присвоєно[в.id])
        elif isinstance(в, ast.IfExp):
            черга.extend((в.test, в.body, в.orelse))
        elif isinstance(в, ast.Compare):
            черга.extend([в.left] + в.comparators)
        elif not isinstance(в, ast.Constant):
            return False
    return збігів > 0


ЧИТАЧ_ТАБЛИЦІ = re.compile(r"^_?(читати|прочитати|read)_\w+$")


def таблиця_цілою(значення, одиниця, функції):
    """Значення — ім'я, кожне присвоєння якого — виклик функції модуля-читача (`читати_кадри()`), що відкриває файл:
    поле несе всю таблицю каталогу як контекст читача, а не кадр, колір чи наявність однієї речі (клас: читачі каталогу —
    не місця)."""
    if not isinstance(значення, ast.Name) or одиниця is None:
        return False
    присвоєно = [н.value for н in ast.walk(одиниця) if isinstance(н, ast.Assign)
                 and any(isinstance(ц, ast.Name) and ц.id == значення.id for ц in н.targets)]
    if not присвоєно:
        return False
    for в in присвоєно:
        if not (isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and ЧИТАЧ_ТАБЛИЦІ.match(в.func.id)
                and в.func.id in функції):
            return False
        if not any(isinstance(н, ast.Call) and ім_виклику(н.func) in ("open", "load")
                   for н in ast.walk(функції[в.func.id])):
            return False
    return True


def копія_запису(вузол, значення, батьки, граф, доказ, рядок, ключ):
    """Похідне без нового входу: значення читає лише сам запис, у який пишеться, а це поле вже записано в ньому вище
    (`r["colors"] = [dict(lab=точка_кольору(r))]` після `r["lab"] = …`)."""
    cur = вузол
    while cur in батьки and not isinstance(cur, ast.stmt):
        cur = батьки[cur]
    ціль = cur.targets[0] if isinstance(cur, ast.Assign) and len(cur.targets) == 1 else None
    while isinstance(ціль, (ast.Subscript, ast.Attribute)):
        ціль = ціль.value
    if not isinstance(ціль, ast.Name) or значення is None:
        return False
    корені = граф.корені(значення)
    if not корені or not корені <= {ціль.id}:
        return False
    for н in доказ.вузли:
        if isinstance(н, ast.Assign) and н.lineno < рядок:
            for ц in н.targets:
                for е in (ц.elts if isinstance(ц, (ast.Tuple, ast.List)) else [ц]):
                    if isinstance(е, ast.Subscript) and isinstance(е.value, ast.Name) and е.value.id == ціль.id \
                            and isinstance(е.slice, ast.Constant) and е.slice.value == ключ:
                        return True
    return False


ПОПЕРЕДНІХ = 8       # оператори блоку перед місцем, що ще вважаються його контекстом


def локальний_контекст(вузол, значення, батьки, межа):
    """Вузли контексту запису: значення, умови навколишніх `if`/`while`/`for` і до 8 операторів перед місцем у кожному блоці."""
    вузли = [значення] if значення is not None else []
    cur = вузол
    while cur in батьки and cur is not межа:
        р = батьки[cur]
        if isinstance(р, ast.Assign) and cur is not р.value and значення is None:
            вузли.append(р.value)
        for поле in ("body", "orelse", "finalbody"):
            блок = getattr(р, поле, None)
            if isinstance(блок, list) and any(x is cur for x in блок):
                індекс = [i for i, x in enumerate(блок) if x is cur][0]
                вузли.extend(блок[max(0, індекс - ПОПЕРЕДНІХ):індекс])
        if isinstance(р, (ast.If, ast.While)):
            вузли.append(р.test)
        elif isinstance(р, (ast.For, ast.AsyncFor)):
            вузли.append(р.iter)
        cur = р
    return вузли


def суд_місць(файл, од_ім, вузол, тіло_вузли, збирач, батьки, її_річ):
    """Усі місця одиниці з рішенням за пунктами. Джерело й вибір — з контексту запису, власник і варіації — з функції."""
    вхід = [вузол] if вузол is not None else тіло_вузли
    лекс_одиниці = "\n".join(текст_виразу(н) for н in вхід)
    межа = вузол if вузол is not None else None
    варіації = sorted(set(re.findall(ВАРІАЦІЇ, лекс_одиниці)))[:3]
    власник_виклик = bool(збирач.виклики_власника)
    невідомо = збирач.власник_невідомо
    результат = []
    охоплення = вузол if вузол is not None else ast.Module(body=тіло_вузли, type_ignores=[])
    граф = Походження(охоплення, батьки, getattr(збирач, "функції", {}))
    доказ = Доказ(охоплення, getattr(збирач, "функції", {}))

    def пояснення(вузол_запису, значення, назва):
        контекст = локальний_контекст(вузол_запису, значення, батьки, межа)
        лекс = "\n".join(текст_виразу(н) for н in контекст)
        дж = ознаки(лекс)
        вб = вибір(ast.Module(body=[x for x in контекст if isinstance(x, ast.stmt)] or
                              [ast.Expr(value=x) for x in контекст if isinstance(x, ast.expr)], type_ignores=[]), лекс)
        return "%s ← %s; вибір: %s" % (назва, "+".join(дж) if дж else "готовий запис товару",
                                       "; ".join(вб) if вб else "без вибору")

    бачено = set()
    for рядок, ключ, р, у_вар, суб, вузол_запису, значення in sorted(збирач.записи, key=lambda х: (х[0], х[1])):
        if (рядок, ключ) in бачено:
            continue
        бачено.add((рядок, ключ))
        if isinstance(вузол_запису, ast.Constant) and isinstance(батьки.get(вузол_запису), ast.Dict):
            вузол_запису = батьки[вузол_запису]
        if значення is None:
            присв = батьки.get(вузол_запису)
            if isinstance(присв, (ast.Assign, ast.AnnAssign)):
                значення = присв.value
        причина = граф.причина_виключення(вузол_запису, ключ, р, значення)
        if not причина and діагностика(вузол_запису, батьки):
            причина = "діагностика прогону, не запис таблиці"
        if not причина and таблиця_цілою(значення, охоплення, getattr(збирач, "функції", {})):
            причина = "таблиця каталогу, прочитана цілою: контекст читача, не поле запису"
        if not причина and копія_запису(вузол_запису, значення, батьки, граф, доказ, рядок, ключ):
            причина = "копія вже записаного поля того самого запису без нового входу"
        if причина and not її_річ:
            результат.append(Місце(файл, рядок, 1 if р == "кадр" else 2, "поза класом", причина, ключ, р))
            continue
        назва = "%s «%s»" % ({"кадр": "кадр", "колір": "колір", "наявність": "наявність"}[р], ключ)
        if її_річ:
            результат.append(Місце(файл, рядок, 1 if р == "кадр" else 2, "не діє",
                                   "запис речі з фото користувачки: даних крамниці й варіацій нема", ключ, р))
            continue
        пояс = пояснення(вузол_запису, значення, назва)
        if р == "кадр":
            лок = "\n".join(текст_виразу(x) for x in локальний_контекст(вузол_запису, значення, батьки, межа))
            if граф.свій_варіант(вузол_запису, значення):
                м = Місце(файл, рядок, 1, "дотримує", "кадр із даних своєї оферти/варіації", ключ, р)
            elif невідомо:
                м = Місце(файл, рядок, 1, "дотримує", "власник невідомий записано словом «невідомо»", ключ, р)
            elif доказ.запис_доказу(вузол_запису, значення, граф):
                м = Місце(файл, рядок, 1, "дотримує", "запис доказу власності: власник із даних крамниці, кадр звірено з "
                          "прив'язкою платформи (уточнення 13.11)", ключ, р)
            else:
                хвіст = ("власник — товар (`власник_кадру`), `[\"варіант\"]` не читано: варіант «невідомо» (9686)"
                         if власник_виклик and not збирач.читання_варіант else
                         "власника-варіанта з даних крамниці нема, «невідомо» не записано")
                м = Місце(файл, рядок, 1, "порушує", пояс + "; " + хвіст, ключ, р)
        else:
            доведений = доказ.колір_доведеного(вузол_запису, значення, батьки, межа, граф) if р == "колір" else None
            if граф.свій_варіант(вузол_запису, значення):
                м = Місце(файл, рядок, 2, "дотримує", "поле з даних своєї оферти/варіації (id і наявність або вхід циклу)", ключ, р)
            elif доведений and доведений[0]:
                м = Місце(файл, рядок, 2, "дотримує", доведений[1] + " (уточнення 13.11)", ключ, р)
            elif доказ.колір_знято_гілкою(значення, батьки) and р == "колір":
                м = Місце(файл, рядок, 2, "дотримує", "колір знято гілкою: сторінка з варіаціями без власного варіанта "
                          "пише «невідомо» з причиною (рішення 13.11, кв2)", ключ, р)
            elif сторінка_варіації(значення, охоплення, getattr(збирач, "функції", {})):
                м = Місце(файл, рядок, 2, "дотримує", "сторінка однієї варіації: адресу запису звірено з канонічною, "
                          "поле — єдиний збіг сторінки (уточнення 13.11, кв3)", ключ, р)
            else:
                хвіст = (доведений[1] if доведений else
                         "записано полем товару; варіації у функції: " + ", ".join(варіації) if варіації else
                         "записано полем товару; варіацій у функції нема — вхід бере готовий запис товару")
                м = Місце(файл, рядок, 2, "порушує", пояс + "; " + хвіст, ключ, р)
        if м.статус == "порушує" and "вхід" not in граф.теги(значення):
            м = м._replace(статус="нерозв'язано", чому="нерозв'язано: непрозоре походження значення; " + м.чому)
        результат.append(м)
    for рядок, ім, вираз in sorted(збирач.ключі, key=lambda х: (х[0], х[1])):
        с = суд_ключа(рядок, ім, вираз)
        if с is None:
            continue
        if ключ_кешу(ім, охоплення):
            результат.append(Місце(файл, рядок, 3, "поза класом", "ключ кешу похідного: у кешованому й поверненому "
                                   "нема поля з роллю кадру, кольору чи наявності — не ключ двійника чи запису (`%s`)"
                                   % ім, ім, "ключ"))
            continue
        результат.append(Місце(файл, рядок, 3, "порушує" if с[0] else "дотримує", с[1], ім, "ключ"))
    return результат


def норма_імені(ім):
    """`х.json`, `х.json.gz`, `х.json.tmp` — один файл даних."""
    for кінець in (".tmp", ".gz"):
        while ім.endswith(кінець):
            ім = ім[:-len(кінець)]
    return ім


def відомі_імена(корінь, файли_продукту):
    """Імена, які читає продукт: модулі продукту й файли даних, що лежать у `джерела/`/`zhnyvarka/` і названі в продукті
    (файл-стенд, якого в дереві нема, таблицею продукту не є)."""
    є = set()
    for тека in ПРОДУКТ_ТЕКИ:
        шлях = os.path.join(корінь, тека)
        for н in sorted(os.listdir(шлях)):
            if os.path.isfile(os.path.join(шлях, н)):
                є.add(н)
    названі = set()
    for ш in файли_продукту:
        названі.add(os.path.basename(ш))
        try:
            д = розібрати(ш)
        except (SyntaxError, ValueError, OSError) as е:
            ОБСЯГ.непрочитано(os.path.relpath(ш, корінь), "%s: %s" % (type(е).__name__, е))
            continue
        for н in ast.walk(д):
            if isinstance(н, ast.Constant) and isinstance(н.value, str) and 3 < len(н.value) < 120:
                названі.add(os.path.basename(н.value))
    return {норма_імені(н) for н in є if норма_імені(н) in {норма_імені(х) for х in названі} and not н.endswith(".md")}


def рядки_імен(вузол, значення):
    """Рядкові константи піддерева; імена розкриває за `значення` (ім'я → рядки з його присвоєнь у модулі й одиниці)."""
    рез = set()
    for н in ast.walk(вузол):
        if isinstance(н, ast.Constant) and isinstance(н.value, str):
            рез.add(os.path.basename(н.value))
        elif isinstance(н, ast.Name):
            рез |= значення.get(н.id, set())
        elif isinstance(н, ast.Attribute):
            рез |= значення.get(ім_виклику(н), set())
    return рез


def шлях_значення(в):
    """Значення присвоєння, що складає шлях з рядків (літерал, f-рядок, `+`, `join`/`Path`), а не читає дані."""
    if isinstance(в, (ast.Constant, ast.JoinedStr, ast.BinOp)):
        return True
    if isinstance(в, ast.Call):
        ф = в.func
        ім = ф.attr if isinstance(ф, ast.Attribute) else (ф.id if isinstance(ф, ast.Name) else "")
        return ім in ("join", "Path", "abspath", "dirname", "basename", "format", "realpath", "normpath")
    return False


def присвоєння(вузли, початкові=None):
    """ім'я → базові імена рядків у присвоєних значеннях (модуль чи одиниця)."""
    рез = collections.defaultdict(set)
    рез.update(початкові or {})
    записи = [н for к in вузли for н in ast.walk(к) if isinstance(н, ast.Assign) and шлях_значення(н.value)]
    for _ in range(len(записи) + 1):
        зміна = False
        for н in записи:
            рядки = рядки_імен(н.value, рез)
            for ц in н.targets:
                if isinstance(ц, ast.Name) and not рядки <= рез[ц.id]:
                    рез[ц.id] |= рядки
                    зміна = True
        if not зміна:
            break
    return рез


def записує_таблицю_продукту(звідси, збирач, продукт_імена, значення):
    """Чи одиниця пише на диск файл чи модуль продукту: рядки в самому записі на диск (з розкриттям імен) — серед імен продукту."""
    цілі = set()
    for _, вуз in збирач.диск:
        cur, тимчасове = вуз, False
        while cur in збирач.батьки:
            cur = збирач.батьки[cur]
            if isinstance(cur, (ast.With, ast.AsyncWith)) and any(
                    isinstance(ч, ast.Call) and ім_виклику(ч.func).endswith("TemporaryDirectory")
                    for е in cur.items for ч in ast.walk(е.context_expr)):
                тимчасове = True
        if тимчасове:
            continue
        цілі |= рядки_імен(вуз, значення)
    return bool({норма_імені(х) for х in цілі} & продукт_імена)


def прочитані_ролі(вузол):
    """Ролі полів, що ця одиниця ЧИТАЄ (`["колір"]`, `.get("колір")`) — для запису таблиці без ключів ролі."""
    ролі = set()
    for н in ast.walk(вузол):
        ключ = None
        if isinstance(н, ast.Subscript) and isinstance(н.slice, ast.Constant) and isinstance(н.slice.value, str):
            ключ = н.slice.value
        elif isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr == "get" and н.args \
                and isinstance(н.args[0], ast.Constant) and isinstance(н.args[0].value, str):
            ключ = н.args[0].value
        р = роль(ключ) if ключ else None
        if р:
            ролі.add(р)
    return ролі


def перелік_файлів(корінь):
    файли = []
    for тека in ПРОДУКТ_ТЕКИ:
        база = os.path.join(корінь, тека)
        for кат, теки, назви in os.walk(база):
            теки[:] = sorted(д for д in теки if д not in ПОЗА_ТЕКИ and not д.startswith("."))
            for н in sorted(назви):
                if н.endswith(".py") and not ВИКЛЮЧЕНО.match(н):
                    файли.append(os.path.relpath(os.path.join(кат, н), корінь).replace(os.sep, "/"))
    return sorted(файли)


def зібрати_одиниці(дерево):
    """[(ім'я, вузол|None, тіло, Збирач)] для кожної одиниці файлу."""
    од, модуль = одиниці(дерево)
    рез = []
    for ім, вузол, тіло in [(і, в, [в]) for і, в in од] + ([("<модуль>", None, модуль)] if модуль else []):
        з = Збирач(модуль=вузол is None)
        for н in тіло:
            з.visit(н)
        if вузол is not None:
            з.ключі.extend(ключ_функції(вузол))
        батьки = {}
        for н in тіло:
            for х in ast.walk(н):
                for ч in ast.iter_child_nodes(х):
                    батьки[ч] = х
        з.батьки = батьки
        рез.append((ім, вузол, тіло, з))
    return рез


def головна(корінь):
    файли = перелік_файлів(корінь)
    продукт = [ф for ф in файли if not re.match(r"^джерела/(проби|прилади|траса)/", ф)]
    допоміжні = [ф for ф in файли if re.match(r"^джерела/(проби|прилади)/", ф)]
    імена = відомі_імена(корінь, [os.path.join(корінь, ф) for ф in продукт])
    місця, поза, обсяг, таблиці = [], collections.Counter(), [], []
    без_розбору = []
    кеш_модулів = {}

    def читати_модуль(тека, ім):
        """Шукає локальний модуль у дереві; кожен файл розбирає лише раз."""
        ключ = (тека, ім)
        if ключ not in кеш_модулів:
            кеш_модулів[ключ] = None
            for т in (тека, os.path.join(корінь, "джерела"), os.path.join(корінь, "zhnyvarka")):
                ш = os.path.join(т, ім.replace(".", os.sep) + ".py")
                if ш not in кеш_модулів:
                    кеш_модулів[ш] = розібрати(ш) if os.path.isfile(ш) else None
                if кеш_модулів[ш] is not None:
                    кеш_модулів[ключ] = кеш_модулів[ш]
                    break
        return кеш_модулів[ключ]

    for ф in продукт + допоміжні:
        try:
            дерево = розібрати(os.path.join(корінь, ф))
        except (SyntaxError, ValueError) as е:
            без_розбору.append(ф)
            ОБСЯГ.непрочитано(ф, "%s: %s" % (type(е).__name__, е))
            continue
        допоміжний = ф in допоміжні
        імпорти = константи_імпортів(дерево, os.path.dirname(os.path.join(корінь, ф)), читати_модуль) if допоміжний else {}
        значення_модуля = присвоєння(дерево.body, імпорти) if допоміжний else {}
        в_обсязі = not допоміжний
        для_суду = []
        for ім, вузол, тіло, з in зібрати_одиниці(дерево):
            з.функції = {н.name: н for н in дерево.body if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef))}
            охоплення = вузол if вузол is not None else ast.Module(body=тіло, type_ignores=[])
            if допоміжний:
                значення = dict(значення_модуля)
                for к, в in присвоєння([охоплення], значення_модуля).items():
                    значення[к] = значення.get(к, set()) | в
                if not записує_таблицю_продукту(охоплення, з, імена, значення):
                    continue
                в_обсязі = True
            if not (з.записи or з.ключі or (допоміжний and з.диск)):
                continue
            для_суду.append((ім, вузол, охоплення, тіло, з))
        if в_обсязі:
            обсяг.append(ф)
        for ім, вузол, охоплення, тіло, з in для_суду:
            виробник = допоміжний or bool(ВИРОБНИК.match(ф) or ЇЇ_РІЧ.match(ф))
            if not виробник:
                for (_, ключ, р, _, _, _, _) in {х[:5] + (None, None) for х in з.записи}:
                    поза["%s · %s" % (родина_читача(ф), р)] += 1
                continue
            її_річ = bool(ЇЇ_РІЧ.match(ф))
            if допоміжний and not з.записи:
                ролі = sorted(прочитані_ролі(охоплення))
                if ролі:
                    таблиці.append((ф, ім, ролі, з.диск[0][0]))
                    місця.extend(суд_таблиці(ф, з, охоплення, ролі))
                continue
            місця.extend(суд_місць(ф, ім, вузол, тіло, з, з.батьки, її_річ))
    розв = collections.Counter()
    для_виводу = []
    for м in sorted(set(місця), key=lambda м: (м.файл, м.рядок, м.пункт, м.ключ)):
        розв[м.статус] += 1
        if м.статус in ("порушує", "нерозв'язано"):
            для_виводу.append(м)
    файли_з_місцями = sorted({м.файл for м in для_виводу})
    return для_виводу, розв, поза, обсяг, файли_з_місцями, без_розбору, таблиці, місця


def суд_таблиці(ф, з, охоплення, ролі):
    """Запис таблиці продукту без ключів ролі (проба/прилад): суд за полями, прочитаними в тій самій одиниці."""
    лекс = текст_виразу(охоплення)
    дж, вб = ознаки(лекс), вибір(ast.Module(body=[охоплення], type_ignores=[]), лекс)
    власник = bool(з.виклики_власника) and not з.читання_варіант
    рядок = з.диск[0][0]
    рез = []
    доказ = Доказ(охоплення, з.функції)
    складачі = [з.функції[н.func.id] for н in ast.walk(охоплення)
                if isinstance(н, ast.Call) and isinstance(н.func, ast.Name) and н.func.id in з.функції]
    позиційний = any(доказ.позиційний_доказ(н, None) for ф_ in складачі + [охоплення] for н in ast.walk(ф_)
                     if isinstance(н, (ast.List, ast.Tuple)))
    for р in ролі:
        пункт = 1 if р == "кадр" else 2
        чому = ("таблиця продукту записана з полів «%s» ← %s; вибір: %s; %s" % (
            р, "+".join(дж) if дж else "готовий запис", "; ".join(вб) if вб else "без вибору",
            "власник — товар (`власник_кадру`), `[\"варіант\"]` не читано: варіант «невідомо» (9686)" if власник
            else "власник-варіант не прочитано, «невідомо» не записано"))
        порушує = власник or not (з.читання_варіант or з.варіант_цикл_кадр or з.відображення_кадру)
        if порушує and р == "кадр" and позиційний:
            порушує, чому = False, ("позиційний запис таблиці несе доказ власника-варіанта з запасним «невідомо» "
                                    "(функція складання таблиці, уточнення 13.11)")
        рез.append(Місце(ф, рядок, пункт, "порушує" if порушує else "дотримує", чому, "<запис таблиці>", р))
    return рез


JS_КЛЮЧ = re.compile(r"(?:^|[\s,{(])['\"]?([\w\u0400-\u04ff]+)['\"]?\s*:(?!:)|\.([\w\u0400-\u04ff]+)\s*=(?!=)|\[['\"]([\w\u0400-\u04ff]+)['\"]\]\s*=(?!=)")
JS_ДИСК = re.compile(r"localStorage\.setItem|indexedDB|\.objectStore\(|writeFile|createWriteStream|\.put\(")
JS_КРАМНИЦЯ = re.compile(r"крамниц|\bshop\b|offer|варіант|variant|каталог|catalog", re.I)


def js_файли(корінь):
    рез = []
    for тека, фільтр in (("джерела", False), ("джерела/показ", True)):
        шлях = os.path.join(корінь, тека)
        if not os.path.isdir(шлях):
            continue
        for н in sorted(os.listdir(шлях)):
            if н.endswith(".js") and not ВИКЛЮЧЕНО.match(н) and os.path.isfile(os.path.join(шлях, н)):
                рез.append(тека + "/" + н)
    return sorted(рез)


def скан_js(корінь):
    """JS шляху продукту (воркер, шаблон, показ): записи полів ролі лічаться без суду, бо JS каталог не пише: файл на диск
    чи таблицю не пише ніхто; запис у сховище браузера — її речі й профіль (крамниці й варіацій нема). Повертає
    (читачі, її_таблиці, нерозв'язані): нерозв'язане — запис ролі в рядку, де названо крамницю/каталог/оферту/варіант."""
    читачі, її, нерозв = collections.Counter(), collections.Counter(), []
    for ф in js_файли(корінь):
        with open(os.path.join(корінь, ф), encoding="utf-8") as фх:
            рядки = фх.read().split("\n")
        сховище = any(JS_ДИСК.search(р) for р in рядки)
        for i, р in enumerate(рядки, 1):
            for м in JS_КЛЮЧ.finditer(р):
                ключ = next(x for x in м.groups() if x)
                ро = роль(ключ)
                if not ро or (ключ.isupper() and len(ключ) > 2) or "\\n" in р or len(р) > 600 or \
                        re.match(r"\s*(#|var\(|rgba?\(|[a-z]+\s*[;}])", р[м.end():]) and ключ.lower() in ("color", "colour"):
                    continue          # проза промпта, вбудований HTML/CSS: не запис поля
                if JS_КРАМНИЦЯ.search(р) and ро != "наявність" and "//" not in р.split(ключ)[0]:
                    нерозв.append((ф, i, ключ, ро))
                    continue
                (її if сховище else читачі)[ро] += 1
    return читачі, її, нерозв


def родина_читача(файл):
    ім = os.path.basename(файл)
    for префікс, назва in (("міст_", "міст"), ("оцінка_", "оцінка"), ("мовний", "мовний шар"), ("дріт", "дріт моделі"),
                           ("знання", "знання"), ("паспорт", "паспорт"), ("колір_", "колір"), ("вердикт", "вердикт"),
                           ("суд_", "суд"), ("розбір_", "розбір відповідей"), ("палітр", "палітра"), ("surface", "поверхня"),
                           ("verify", "verify"), ("graph", "граф"), ("bridge", "міст")):
        if ім.startswith(префікс):
            return назва
    return "решта читачів"


ДОШКА = ((118, "знімки групуються за файлом, кадр жнив замість спільної картинки: запис кадру картки"),
         (3040, "слово крамниці в колонці кольору — колір лістингу всіх варіантів, записаний на товар"),
         (5668, "кадр, на якому міряно колір, ніде не збережено (маніфест кадру виміру)"),
         (6370, "ключ двійників відкидає `?attribute_…` — параметр варіації"),
         (8025, "maxa.ua: кадр кольору не береться з `variations[].image`"),
         (9172, "власність кадру виміру не доведена (3 061 «невідомо»)"),
         (9175, "двійники з різним кольором ділять одну галерею"),
         (9686, "довірена пара vikna_vzhytku: варіант «невідомо» в усіх точках"))


def звірка_дошки(місця):
    """Для кожного рядка дошки паспорта — які місця приладу відповідають йому (за файлом і роллю); пояснення розбіжності."""
    карта = {
        118: (lambda м: "міст_опис" in м.файл or "фід_фото" in м.файл or "жнива_запис" in м.файл, "кадр"),
        3040: (lambda м: ("жниварка" in м.файл or "виконавець" in м.файл or "фід_слот" in м.файл or "фід_каталог" in м.файл)
                         and м.пункт == 2, "колір"),
        5668: (lambda м: "кадри_маніфест" in м.файл or "жнива_запис" in м.файл or "жнива_кадри" in м.файл, "кадр"),
        6370: (lambda м: м.пункт == 3 and ("чистка_каталогу" in м.файл or "жниварка" in м.файл), "ключ"),
        8025: (lambda м: "woo_варіанти" in м.файл or "ricamare" in м.файл or "виконавець" in м.файл, "кадр"),
        9172: (lambda м: "фід_власник_кадру" in м.файл or "власник_кадру" in м.файл, "кадр"),
        9175: (lambda м: "власник_кадру" in м.файл or "фід_кадр_колір" in м.файл, "кадр"),
        9686: (lambda м: "vikna_vzhytku" in м.файл, "кадр"),
    }
    рядки = []
    for н, суть in ДОШКА:
        ф, роль_ = карта[н]
        знайдено = [м for м in місця if м.статус == "порушує" and ф(м)]
        рядки.append((н, суть, len(знайдено), sorted({м.файл for м in знайдено})[:3]))
    return рядки


def частка_каталогу(корінь):
    """Частка кадрів із відомим власником-варіантом на каталозі: `каталог_власник_кадру.json.gz` варіанта не зберігає."""
    шлях = os.path.join(корінь, "джерела", "каталог_власник_кадру.json.gz")
    if not os.path.exists(шлях):
        return "каталог: файла `каталог_власник_кадру.json.gz` нема"
    with gzip.open(шлях, "rt", encoding="utf-8") as ф:
        д = json.load(ф)
    записи = д.get("записи") or {}
    власних = sum(1 for в in записи.values() if isinstance(в, list) and len(в) >= 3 and в[2])
    поля = max((len(в) for в in записи.values() if isinstance(в, list)), default=0)
    return ("каталог: записів кадру %d, з байтами в галереї товару %d; поля запису %d (варіанта серед них нема): "
            "кадрів із відомим власником-варіантом 0 з %d (0 %%)" % (len(записи), власних, поля, len(записи)))


def вибірка(місця, всі_файли, файли_з_місцями, кількість=20):
    """Детермінована вибірка: 20 місць і 20 файлів без місць — за sha1 рядка, а не за random."""
    пул = sorted(місця, key=lambda м: hashlib.sha1(("%s:%d:%s" % (м.файл, м.рядок, м.ключ)).encode("utf-8")).hexdigest())
    без = sorted([ф for ф in всі_файли if ф not in файли_з_місцями],
                 key=lambda ф: hashlib.sha1(ф.encode("utf-8")).hexdigest())
    return пул[:кількість], без[:кількість]


def main():
    п = argparse.ArgumentParser()
    п.add_argument("--корінь", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    п.add_argument("--каталог", action="store_true")
    п.add_argument("--вибірка", action="store_true")
    п.add_argument("--тихо", action="store_true", help="лише останній рядок")
    а = п.parse_args()
    корінь = os.path.abspath(а.корінь)
    для_виводу, розв, поза, файли, файли_з_місцями, без_розбору, таблиці, всі_місця = головна(корінь)
    рядки = []
    for м in для_виводу:
        рядки.append("%s:%d · п.%d · %s" % (м.файл, м.рядок, м.пункт, м.чому))
    місць_js = len(скан_js(корінь)[2])
    за_пунктами = collections.Counter(м.пункт for м in для_виводу)
    рядки.append("")
    рядки.append("підсумки за пунктами: " + ", ".join("п.%d — %d" % (н, за_пунктами.get(н, 0)) for н in (1, 2, 3)))
    ролі = collections.Counter(м.роль for м in для_виводу)
    рядки.append("за ролями: " + ", ".join("%s — %d" % (р, ролі[р]) for р in sorted(ролі)))
    рядки.append("рішення: порушує %d, дотримує %d, не діє %d, поза класом %d, нерозв'язано %d (розібрано файлів %d, не розібрано %d)"
                 % (розв["порушує"], розв["дотримує"], розв["не діє"], розв["поза класом"], розв["нерозв'язано"],
                    len(файли) - len(без_розбору), len(без_розбору)))
    рядки.append("число для храповика — верхня межа: порушення + нерозв'язані кандидати")
    рядки.append("файлів із місцями: %d з %d" % (len(файли_з_місцями), len(файли)))
    рядки.append("поза записом (читачі, клас їх не лічить): " + (", ".join("%s — %d" % (к, в) for к, в in sorted(поза.items()))
                                                                if поза else "0"))
    читачі_js, її_js, нерозв_js = скан_js(корінь)
    рядки.append("JS продукту (%d файлів): записів ролі — читачі %d, її речі й профіль у сховищі браузера (клас не діє) %d, "
                 "біля крамниці/оферти/варіанта (нерозв'язано) %d" % (len(js_файли(корінь)), sum(читачі_js.values()),
                                                                      sum(її_js.values()), len(нерозв_js)))
    for ф, i, ключ, ро in нерозв_js:
        рядки.append("%s:%d · п.? · JS: запис «%s» (%s) біля крамниці/оферти/варіанта — рішення потрібне" % (ф, i, ключ, ро))
    рядки.append("таблиці продукту від проб і приладів: " + (", ".join("%s:%d" % (ф, л) for ф, _, _, л in sorted(таблиці)) or "0"))
    рядки.append("звірка з дошкою паспорта:")
    for н, суть, кількість, ф in звірка_дошки(всі_місця):
        рядки.append("  %d · %s · місць %d%s" % (н, суть, кількість, " · " + ", ".join(ф) if ф else " · (приладом не бачено)"))
    if а.вибірка:
        м20, ф20 = вибірка(для_виводу, файли, файли_з_місцями)
        рядки.append("вибірка місць (sha1):")
        рядки += ["  %s:%d · п.%d · %s" % (м.файл, м.рядок, м.пункт, м.ключ) for м in м20]
        рядки.append("вибірка файлів без місць (sha1):")
        рядки += ["  " + ф for ф in ф20]
        зняті = sorted((м for м in всі_місця if м.статус == "поза класом"), key=lambda м: (
            hashlib.sha1((м.файл + ":" + str(м.рядок) + ":" + м.ключ).encode("utf-8")).hexdigest(), м.файл, м.рядок, м.ключ))[:20]
        рядки.append("вибірка відсіяних кандидатів (sha1):")
        рядки += ["  %s:%d · %s · %s" % (м.файл, м.рядок, м.ключ, м.чому) for м in зняті]
    if а.каталог:
        рядки.append(частка_каталогу(корінь))
    хеш = hashlib.sha256("\n".join(рядки).encode("utf-8")).hexdigest()[:16]
    рядки.append("хеш: %s" % хеш)
    рядки.append("місць: %d" % (len(для_виводу) + місць_js))
    if а.тихо:
        print(рядки[-1])
    else:
        print("\n".join(рядки))
    return 0


if __name__ == "__main__":
    sys.exit(main())
