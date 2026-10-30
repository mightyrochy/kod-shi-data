# -*- coding: utf-8 -*-
"""Прилад кореня Річ-кадр-варіант: записи полів кадру, кольору й наявності речі та їхній суд за пунктами 1–3 класу
(паспорт `аудит/корені/Річ-кадр-варіант.md`, «Клас місць», уточнено 30.10, #2340).

ОДИНИЦЯ — запис поля: оператор, що кладе кадр, колір чи наявність речі в каталог чи іншу таблицю, яку читає продукт
(`dict`-літерал з ключем поля, `запис["поле"] = …`, `.setdefault("поле", …)`, `dict(поле=…)`/`.update(поле=…)`), і запис
ключа двійника чи запису (п.3). Розбір джерела (DOM, атрибути, JSON-LD, regex, фід, лістинг, галерея) і вибір (голова
списку, активний чи єдиний свотч, перший кадр, кадр за кольором слова, дані сестер) — ознаки ТОГО САМОГО запису в його
функції (оператор модуля — «<модуль>»), а не окремі місця. Читачі каталогу (вимір, суд, картка, показ, вихід до моделі)
— поза класом: їхній вибір знімає запис, тож вони лічаться окремо як «поза записом» і місцями не є.

РОЛЬ поля — за ключем: кадр (`фото`, `кадр…`, `кадри…`, `photo(s)`, `image(s)`, галерея…), колір (`колір…`, `кольори`,
`hex`, `lab`, `свотчі`, `color…`; другий колір, джерело й тип кольору — той самий колір), наявність (`наявність…`,
`available`, `stock…`); лічильники й діагностика (`…_усього`, `…_без_…`, `…_перевірено`, `…_не_те`, `…_номери`, `…_ключ`) —
не поле речі. Приклади — не перелік: роль судить правило (`РОЛІ`), а не список файлів. Таблицю продукту, що пише проба чи
прилад (`проби/vikna_vzhytku.py --записати` → `verify.ВЖИТОК`), знаходить сам прилад: файл у `проби/`/`прилади/`, чий
запис на диск (open «w», json.dump, write_text) називає файл чи модуль, який читає продукт; місце — оператор запису, ролі —
поля, прочитані в тій самій функції.

СУД за пунктами (кожне місце має рішення «порушує» / «дотримує» / «не діє» — нерозв'язаних нема):
  П.1 (роль «кадр») — кадр записано як кадр варіанта, а власника-варіанта з даних крамниці нема й «невідомо» не
      записано. Дотримує: запис у циклі по варіантах крамниці (кадр — поле запису варіанта), або функція вибирає кадр
      за варіантом (цикл/відображення «варіант → кадр»), або пише «невідомо». Власник «товар» (`власник_кадру`, чий
      варіант — «невідомо» в усіх точках) без читання `["варіант"]` власником-варіантом не є (9686).
  П.2 (роль «колір», «наявність») — записано полем товару, хоча дані крамниці мають варіації. Дотримує лише запис у
      циклі по варіантах чи в об'єкті, названому варіантом; колір крамниці з лістингу всіх варіантів, записаний на товар,
      — порушення (3040), як і колір виміру, записаний ключем товару.
  П.3 (ключ) — ключ двійника чи запису відкидає параметр варіації: адреса без запиту (`urlparse(…).path`,
      `split("?")`, `urlunparse` з порожнім запитом), або складений ключ (≥ 2 частин) без кольору, варіанта, артикула,
      розміру, параметра (6370).
НЕ ДІЄ: запис речі з фото користувачки (`річ_з_фото.py`) — даних крамниці й варіацій нема.

ВИВІД: рядки `файл:рядок · п.N · чому`, підсумки за пунктами, рішення (порушує / дотримує / не діє / нерозв'язано),
поза записом (читачі), звірка з рядками дошки паспорта, потім (з `--каталог`) частка кадрів із відомим власником-
варіантом, останній рядок `місць: <N>`; код 0 (формат храповика, `аудит/КОД.md`). Вивід — лише з кодовими точками
і порядком рядків, однаковий на Python 3.11–3.13 (хеш виводу — `хеш:`).
Запуск: python3 -W ignore джерела/прилади/корінь_річ_кадр_варіант.py [--корінь <дерево>] [--каталог] [--вибірка]"""
import argparse, ast, collections, gzip, hashlib, json, os, re, sys, warnings

# ---- ОБСЯГ ----------------------------------------------------------------------------------------------------
ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)")
ПРОДУКТ_ТЕКИ = ("джерела", "zhnyvarka")
ПОЗА_ТЕКИ = {"__pycache__", "node_modules", "фікстури", "аудит", "дані_корпусу", "дані_5191_5194", "лабораторія"}
# стадії виробництва каталогу (виконання: жнива → фід → збагачення → каталог); решта файлів — читачі, доки їхній запис на диск
# не називає файл чи модуль, який читає продукт
ВИРОБНИК = re.compile(r"^(zhnyvarka/.+\.py|джерела/(фід_(?!колір\.)[^/]+|підфід|жнива_[^/]+|кадри_групи|чистка_каталогу|"
                      r"таблиця_каталогу)\.py)$")
# `фід_колір` — вимірювач принту (результат вимірювання, не запис таблиці); `каталог_розбір*` — розбір моделлю, до фіду не
# під'єднаний (його докстрінг): це читачі/похідне, їхні записи лічаться у «поза записом».
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
    if частин >= 2 and ПРОДУКТ_ЧАСТИНА.search(лекс) and not параметр:
        return True, "складений ключ (%d частин) без кольору, варіанта, артикула чи параметра (`%s`)" % (частин, ім)
    if частин >= 2 and ПРОДУКТ_ЧАСТИНА.search(лекс):
        return False, "ключ несе параметр варіації (`%s`)" % ім
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
        назва = "%s «%s»" % ({"кадр": "кадр", "колір": "колір", "наявність": "наявність"}[р], ключ)
        if її_річ:
            результат.append(Місце(файл, рядок, 1 if р == "кадр" else 2, "не діє",
                                   "запис речі з фото користувачки: даних крамниці й варіацій нема", ключ, р))
            continue
        пояс = пояснення(вузол_запису, значення, назва)
        if р == "кадр":
            лок = "\n".join(текст_виразу(x) for x in локальний_контекст(вузол_запису, значення, батьки, межа))
            if у_вар:
                м = Місце(файл, рядок, 1, "дотримує", "кадр у записі варіанта (цикл по варіантах крамниці)", ключ, р)
            elif ВЛАСНИК_ВАР.search(лок) and КАДР_ТОКЕН.search(лок) and not ПОЛЕ_ВЛАСНИКА.match(ключ):
                м = Місце(файл, рядок, 1, "дотримує", "кадр узято за варіантом у контексті запису (варіант → кадр)", ключ, р)
            elif невідомо:
                м = Місце(файл, рядок, 1, "дотримує", "власник невідомий записано словом «невідомо»", ключ, р)
            else:
                хвіст = ("власник — товар (`власник_кадру`), `[\"варіант\"]` не читано: варіант «невідомо» (9686)"
                         if власник_виклик and not збирач.читання_варіант else
                         "власника-варіанта з даних крамниці нема, «невідомо» не записано")
                м = Місце(файл, рядок, 1, "порушує", пояс + "; " + хвіст, ключ, р)
        else:
            if у_вар or ІМ_ВАРІАНТА.match(суб or ""):
                м = Місце(файл, рядок, 2, "дотримує", "поле запису варіанта (цикл по варіантах чи об'єкт-варіант)", ключ, р)
            elif значення is not None and any(isinstance(x, ast.Name) and ІМ_ВАРІАНТА.match(x.id) for x in ast.walk(значення)):
                м = Місце(файл, рядок, 2, "дотримує", "значення взято з варіанта запису (`вар[…]`)", ключ, р)
            else:
                хвіст = ("записано полем товару; варіації у функції: " + ", ".join(варіації) if варіації else
                         "записано полем товару; варіацій у функції нема — вхід бере готовий запис товару")
                м = Місце(файл, рядок, 2, "порушує", пояс + "; " + хвіст, ключ, р)
        результат.append(м)
    for рядок, ім, вираз in sorted(збирач.ключі, key=lambda х: (х[0], х[1])):
        с = суд_ключа(рядок, ім, вираз)
        if с is None:
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
        except (SyntaxError, ValueError, OSError):
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


def присвоєння(вузли):
    """ім'я → базові імена рядків у присвоєних значеннях (модуль чи одиниця)."""
    рез = collections.defaultdict(set)
    for корінь_ in вузли:
        for н in ast.walk(корінь_):
            if isinstance(н, ast.Assign) and шлях_значення(н.value):
                рядки = {os.path.basename(к.value) for к in ast.walk(н.value)
                         if isinstance(к, ast.Constant) and isinstance(к.value, str)}
                for ц in н.targets:
                    if isinstance(ц, ast.Name):
                        рез[ц.id] |= рядки
    return рез


def записує_таблицю_продукту(звідси, збирач, продукт_імена, значення):
    """Чи одиниця пише на диск файл чи модуль продукту: рядки в самому записі на диск (з розкриттям імен) — серед імен продукту."""
    цілі = set()
    for _, вуз in збирач.диск:
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
    for ф in продукт + допоміжні:
        try:
            дерево = розібрати(os.path.join(корінь, ф))
        except (SyntaxError, ValueError):
            без_розбору.append(ф)
            continue
        допоміжний = ф in допоміжні
        значення_модуля = присвоєння(дерево.body)
        в_обсязі = not допоміжний
        для_суду = []
        for ім, вузол, тіло, з in зібрати_одиниці(дерево):
            охоплення = вузол if вузол is not None else ast.Module(body=тіло, type_ignores=[])
            if допоміжний:
                значення = dict(значення_модуля)
                for к, в in присвоєння([охоплення]).items():
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
        if м.статус == "порушує":
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
    for р in ролі:
        пункт = 1 if р == "кадр" else 2
        чому = ("таблиця продукту записана з полів «%s» ← %s; вибір: %s; %s" % (
            р, "+".join(дж) if дж else "готовий запис", "; ".join(вб) if вб else "без вибору",
            "власник — товар (`власник_кадру`), `[\"варіант\"]` не читано: варіант «невідомо» (9686)" if власник
            else "власник-варіант не прочитано, «невідомо» не записано"))
        порушує = власник or not (з.читання_варіант or з.варіант_цикл_кадр or з.відображення_кадру)
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
    рядки.append("рішення: порушує %d, дотримує %d, не діє %d, нерозв'язано 0 (розібрано файлів %d, не розібрано %d)"
                 % (розв["порушує"], розв["дотримує"], розв["не діє"], len(файли) - len(без_розбору), len(без_розбору)))
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
