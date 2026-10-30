# -*- coding: utf-8 -*-
"""Прилад кореня Річ-колір-вимір: місця коду, що порушують інваріант кольору речі (паспорт `аудит/корені/Річ-колір-вимір.md`).

КЛАС — правило паспорта, не перелік прикладів. Місце — точка коду продукту, що дає чи читає колір речі; воно порушує
інваріант, якщо хоч одне: (1) колір — точка без розкиду або без придатності виміру; (2) кадр виміру йде в колір варіанта
без жодної згадки власника кадру у функції (код, що обчислює власника, але колір не гейтить, — корінь Річ-кадр-варіант); (3) колір зі слова чи моделі записано або прочитано як вимір (читач не дивиться на вид
значення); (4) кластер виміру обирає слово; (5) вимір із кадру без збереження кадру з маніфестом.

ОБСЯГ: `джерела/*.py` продукту без фікстур і вимірників (`батарея_*`, `gate_*`, `measure_*`, `стенд_*`, `тест_*`, `audit_*`,
`pair_test`, `run_outfit`, `status_перевірки` — синтетичний каталог із ручним hex) і `джерела/показ/*.js`; `проби/`, `прилади/`, `траса/`, `лабораторія/` — не продукт. Правило — по АСТ, область свідчень — оператори, що ПЕРЕДУЮТЬ місце в його блоці й
блоках навколо, а не уся функція: у довгих функціях доказ власника чи маніфесту далеко від місця не рятує місце.

П.5: маніфест пишуть ПІСЛЯ виміру, тож доказ — уся функція, а не попередні оператори.
ДВА ШЛЯХИ. А — від записувачів: де колір речі народжується — запис ключів `lab`/`hex` зі значенням, що не пройшло типізований
читач (`колір_річ.точка_кольору`…), у блоці з вимірюванням кадру, слів(ом)/моделлю; вибір кластера; виклик вимірювача кадру.
Б — від читачів: де його беруть — ключ `lab`/`hex` чи типізований читач на записі речі або кадру галереї, коли поруч нема
виду значення (п.3) чи розкиду й придатності й власника кадру (п.1, п.2); у JS — `.вимір.hex`.
П.4 і п.5 — лише шлях А: вибір і вимір — запис, не читання. Звірка шляхів — за полями кольору: поле, яке пишуть і ніхто не
читає, чи читають і ніхто не пише в коді, названо (такі поля йдуть із даних чи в показ).

ВИВІД: `файл:рядок · п.N · чому [шлях]`, підсумки за пунктами, звірка шляхів, потім (з `--каталог`) частка варіантів каталогу
з виміру власних кадрів, останній рядок `місць: <N>`; код 0 (формат храповика, `аудит/наряди/CI-храповик-кореня.md`).
Запуск: python3 -W ignore джерела/прилади/корінь_річ_колір_вимір.py [--корінь <дерево>] [--каталог]"""
import argparse, ast, collections, glob, os, re, sys, warnings

ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)")
РОДИНА = ("колір_річ", "жнива_колір", "жнива_маски", "колір_нейтралі", "колір_принти", "словник_кольору", "фід_колір")
ТОЧКА = ("lab", "hex")
# ключі типізованого кольору й запису речі: докази, що запис — колір РЕЧІ, а не людини чи палітри
ТИПІЗОВАНІ = frozenset(("колір_тип", "колір_не_вимір", "не_вимір", "колір_джерело", "джерело_кольору", "колір_основний",
                        "колір_другий", "колір_вимір", "колір_слово", "колір_назва", "colors", "кадр_виміру",
                        "власник_кадру", "колір_невідомий", "колір_hex_фото"))
КЛЮЧІ_КАДРУ = frozenset(("файл", "url", "клас", "частка_маски"))
КЛЮЧІ_РЕЧІ = ТИПІЗОВАНІ | {"слот", "колір_назва"}
ОЗНАКИ_РЕЧІ = frozenset(("слот", "колір", "блиск", "візерунок", "фактура", "крій"))     # запис речі за іншими ознаками
# читачі типізованого кольору: код, що кличе їх, дивиться на вид значення
ВИД_ЗНАЧЕННЯ = frozenset(("тип_кольору", "точка_кольору", "hex_кольору", "не_вимір", "явний_тип_кольору", "провенанс_кольору",
                          "lab_входу", "межі_кольору", "вікно_кольору", "має_колір", "запис_кольору", "позначено_невідомим",
                          "перевірити_запис_кольору", "колір_звіту"))
ТОЧКОВІ_ЧИТАЧІ = frozenset(("точка_кольору", "hex_кольору", "lab_входу"))
ВИМІРЮВАЧІ = frozenset(("виміряти_фото", "поверхня_фото", "виміряти_поверхню", "виміряти_колір", "поверхня_кадрів",
                        "колір_з_фото", "зразок_пікселів", "палітра_принту", "світліша_половина",
                        "виміряти_кроками", "виміряти_дотик", "фото_за_словом", "фото_за_словом_кроками"))
ОБГОРТКИ = frozenset(("виміряти", "фото_за_словом"))          # синхронні обгортки вимірювачів: самі не споживачі
МОДУЛЬ_ПОВЕРХНІ = "surface"
АЛІАСИ_МОДУЛЯ, АЛІАСИ_ФУНКЦІЇ = set(), set()     # імена модуля поверхні й функції `виміряти` у файлі: з імпортів
ПІКСЕЛІ = frozenset(("пікселі", "rgb", "bgr", "labs", "домінанта", "зразок_пікселів"))
СЛОВО = frozenset(("центр_вікна", "_центр_вікна", "ЛЕКСИКОН", "вікно_зі_слова", "вікно_слова", "lab_з_hex"))
МОДЕЛЬ = frozenset(("модель", "model_hex", "model_word", "слово_моделі", "shop_word", "назва_вікно"))
РОЗКИД = ("розкид", "spread")
ПРИДАТНІСТЬ = ("придатн", "кадри")
ВЛАСНИК = frozenset(("власник_кадру", "чужий_кадр_кольору", "чужий_кадр_речі", "чужий_кадр", "власник",
                     "кадр_належить", "спільні", "спільні_файли"))
КАДР = frozenset(("кадр", "кадри", "кадр_виміру", "файл", "url", "шлях", "фото"))
МАНІФЕСТ = frozenset(("походження_кадру", "sha256", "маніфест"))     # збереження картинки (imwrite) маніфестом не є
ОБРАННЯ = frozenset(("min", "max", "sorted", "next", "filter"))
КЛАСТЕР = re.compile(r"кластер|сегмент|поверхн|виміри|кадри|записи")
СЛОВО_ЗОВНІ = frozenset(("слово_моделі", "слова_крамниці", "слова_крамниці_", "слово_крамниці", "якір_слово", "слово_її", "крамниця",
                         "shop_word", "model_word", "сім_м"))
НЕНАДІЙНЕ = re.compile(r"ненадій|тло")
ВАЛІДАТОР = re.compile(r"справн|перевір|валід")      # перевіряє форму запису, колір не бере
JS_ВИМІР = re.compile(r"\.вимір\s*\|\|\s*\{\}\s*\)\s*\.(hex|lab)\b|\.колір_вимір\.(hex|lab)\b")
JS_РІЧ = re.compile(r"(?<![\wа-яіїєґ])(р|річ|речі)\.(hex|lab)\b")      # читач кольору на самій речі, не на виміру
JS_ВИД = re.compile(r"колір_тип|придатн")     # перевірка лише наявності `.lab ?` вид значення не дивиться

Місце = collections.namedtuple("Місце", "файл рядок пункт чому шлях")


def розібрати(шлях):
    with open(шлях, encoding="utf-8") as ф:
        текст = ф.read()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        дерево = ast.parse(текст)
    батьки = {}
    АЛІАСИ_МОДУЛЯ.clear(); АЛІАСИ_ФУНКЦІЇ.clear()
    for n in ast.walk(дерево):
        for c in ast.iter_child_nodes(n):
            батьки[c] = n
        if isinstance(n, ast.Import):
            АЛІАСИ_МОДУЛЯ.update(а.asname or а.name for а in n.names if а.name.split(".")[-1] == МОДУЛЬ_ПОВЕРХНІ)
        elif isinstance(n, ast.ImportFrom):
            for а in n.names:
                if а.name == МОДУЛЬ_ПОВЕРХНІ:
                    АЛІАСИ_МОДУЛЯ.add(а.asname or а.name)
                elif (n.module or "").split(".")[-1] == МОДУЛЬ_ПОВЕРХНІ and а.name == "виміряти":
                    АЛІАСИ_ФУНКЦІЇ.add(а.asname or а.name)
    return дерево, батьки


def виміряти_поверхні(n):
    """Виклик `surface.виміряти`: модуль чи функція названі за імпортом файла, а не за писанням псевдоніма."""
    ім, мод = ім_виклику(n)
    return (ім == "виміряти" and мод in АЛІАСИ_МОДУЛЯ) or (мод is None and ім in АЛІАСИ_ФУНКЦІЇ)


def власні_вузли(вузол):
    """Вузли функції без вкладених функцій."""
    стек = list(ast.iter_child_nodes(вузол))
    while стек:
        n = стек.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            стек.extend(ast.iter_child_nodes(n))


def ім_виклику(n):
    if isinstance(n.func, ast.Name):
        return n.func.id, None
    if isinstance(n.func, ast.Attribute):
        return n.func.attr, (n.func.value.id if isinstance(n.func.value, ast.Name) else None)
    return None, None


def свідчення(вузли):
    """(імена й атрибути, рядкові константи й імена аргументів, імена викликів) у піддеревах."""
    імена, конст, виклики = set(), set(), set()
    for корінь in вузли:
        доки = {id(т.body[0].value) for т in ast.walk(корінь)
                if isinstance(т, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)) and т.body
                and isinstance(т.body[0], ast.Expr) and isinstance(т.body[0].value, ast.Constant)}     # докстрінг — не свідчення
        for n in ast.walk(корінь):
            if id(n) in доки:
                continue
            if isinstance(n, ast.Name):
                імена.add(n.id)
            elif isinstance(n, ast.Attribute):
                імена.add(n.attr)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                конст.add(n.value)
            elif isinstance(n, ast.keyword) and n.arg:
                конст.add(n.arg)
            if isinstance(n, ast.Call):
                ім, мод = ім_виклику(n)
                if ім:
                    виклики.add(ім)
                    if виміряти_поверхні(n):
                        виклики.add("surface.виміряти")
    return імена, конст, виклики


def блок(вузол, батьки):
    """Область свідчень: оператори, що передують місцю в його блоці й у всіх блоках, що його обгортають, до тіла функції
    (разом з оператором місця). Доказ далі від місця чи після нього — не свідчення про місце."""
    вузли, n = [], вузол
    while n in батьки:
        п = батьки[n]
        for поле in ("body", "orelse", "finalbody", "handlers"):
            спис = getattr(п, поле, None)
            if isinstance(спис, list) and n in спис:
                вузли.extend(спис[:спис.index(n) + 1])
        if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            break
        n = п
    return вузли or [вузол]


def функція_вузла(вузол, батьки):
    n = вузол
    while n in батьки:
        n = батьки[n]
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return n
    return None


def охорона(вузол, батьки):
    """Свідчення з умов, що обгортають вузол (`if`, умова розуміння, ліві операнди `and`/`or`) і його оператора."""
    вузли, n = [], вузол
    while n in батьки:
        п = батьки[n]
        if isinstance(п, (ast.If, ast.While, ast.IfExp)) and n is not п.test:
            вузли.append(п.test)
        elif isinstance(п, ast.comprehension) and n is not п.iter:
            вузли.extend(п.ifs)
            вузли.append(п.iter)
        elif isinstance(п, ast.BoolOp):
            вузли.extend(п.values)
        elif isinstance(п, ast.stmt) and not isinstance(п, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef)):
            вузли.append(п)
        if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
        n = п
    return вузли


def у_ненадійному(вузол, батьки):
    """Запис лежить у полі, що саме каже «не вимір» (`ненадійний=dict(hex=…)`, колір тла): це не колір речі."""
    n = вузол
    while n in батьки:
        п = батьки[n]
        if isinstance(п, ast.keyword) and п.arg and НЕНАДІЙНЕ.search(п.arg):
            return True
        if isinstance(п, ast.Dict):
            for к, з in zip(п.keys, п.values):
                if з is n and isinstance(к, ast.Constant) and isinstance(к.value, str) and НЕНАДІЙНЕ.search(к.value):
                    return True
        if isinstance(п, ast.stmt):
            return False
        n = п
    return False


def наявність(вузол, батьки):
    """Читання лише для перевірки наявності (`if x.get("lab")`, `and`, `not`, `bool`): значення не використано."""
    n = вузол
    while n in батьки:
        п = батьки[n]
        if isinstance(п, (ast.If, ast.While, ast.IfExp, ast.Assert)) and n is п.test:
            return True
        if isinstance(п, ast.comprehension) and n in п.ifs:
            return True
        if isinstance(п, ast.UnaryOp) and isinstance(п.op, ast.Not):
            return True
        if isinstance(п, ast.Call) and isinstance(п.func, ast.Name) and п.func.id == "bool":
            return True
        if isinstance(п, ast.Compare) and any(isinstance(c, ast.Constant) and c.value is None for c in п.comparators):
            return True
        if isinstance(п, ast.stmt) or isinstance(п, (ast.Tuple, ast.List, ast.Dict, ast.Call, ast.Subscript, ast.keyword)):
            return False
        n = п
    return False


def типізоване_значення(вираз, функція):
    """Значення пройшло типізований читач (або змінну, усі присвоєння якої з нього чи з таких змінних): це
    перевираження виду значення, а не народження точки."""
    if вираз is None:
        return False
    присвоєння = collections.defaultdict(list)    # ім'я → [(імена й виклики правої частини)]
    for n in власні_вузли(функція):
        if isinstance(n, ast.Assign):
            імена, _, виклики = свідчення([n.value])
            for ц in n.targets:
                for t in ast.walk(ц):
                    if isinstance(t, ast.Name):
                        присвоєння[t.id].append((імена, виклики))
    типізовані = set()
    змінилось = True
    while змінилось:
        змінилось = False
        for ім, спис in присвоєння.items():
            # присвоєння, що згадує саму змінну (`x = f(x)`), лише уточнює її; вирішують решта присвоєнь
            решта = [(і, в) for і, в in спис if ім not in і]
            if ім not in типізовані and решта and all(в & ВИД_ЗНАЧЕННЯ or (і & типізовані) for і, в in решта):
                типізовані.add(ім)
                змінилось = True
    імена, _, виклики = свідчення([вираз])
    return bool(виклики & ВИД_ЗНАЧЕННЯ or імена & типізовані)


def зріз_значення(вираз, функція):
    """Свідчення про походження значення: імена, рядки й виклики виразу та правих частин усіх присвоєнь змінним, від яких воно
    залежить (транзитивно, у межах функції)."""
    присвоєння = collections.defaultdict(list)
    for n in власні_вузли(функція):
        if isinstance(n, ast.Assign):
            for ц in n.targets:
                for t in ast.walk(ц):
                    if isinstance(t, ast.Name):
                        присвоєння[t.id].append(n.value)
    імена, конст, виклики = свідчення([вираз])
    оброблені = set()
    черга = list(імена)
    while черга:
        ім = черга.pop()
        if ім in оброблені:
            continue
        оброблені.add(ім)
        for права in присвоєння.get(ім, ()):
            і, к, в = свідчення([права])
            імена |= і; конст |= к; виклики |= в
            черга.extend(і)
    return імена, конст, виклики


def крок_значення(вираз, функція):
    """Імена й рядки виразу та правих частин присвоєнь змінним, що в ньому стоять, — один крок, без транзитивності."""
    імена, конст, виклики = свідчення([вираз])
    for n in власні_вузли(функція):
        if isinstance(n, ast.Assign) and {t.id for ц in n.targets for t in ast.walk(ц) if isinstance(t, ast.Name)} & імена:
            і, к, в = свідчення([n.value])
            імена |= і; конст |= к; виклики |= в
    return імена, конст, виклики


def записи_точки(функція):
    """Записи ключів `lab`/`hex`: (ключ, вузол, значення, ключі запису). Запис — словник, `dict(...)`, `.update(...)`, `x[k] = v`."""
    групи = collections.defaultdict(list)    # ключ групи → [(ключ, вузол, значення)]
    for n in власні_вузли(функція):
        if isinstance(n, ast.Dict):
            for к, з in zip(n.keys, n.values):
                if isinstance(к, ast.Constant) and isinstance(к.value, str):
                    групи[("словник", id(n))].append((к.value, к, з))
        elif isinstance(n, ast.Call):
            ім, _ = ім_виклику(n)
            if ім == "dict" and isinstance(n.func, ast.Name):
                for kw in n.keywords:
                    if kw.arg:
                        групи[("dict", id(n))].append((kw.arg, kw.value, kw.value))
            elif ім == "update" and isinstance(n.func, ast.Attribute):
                for kw in n.keywords:
                    if kw.arg:
                        групи[("оновлення", ast.unparse(n.func.value))].append((kw.arg, kw.value, kw.value))
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Subscript):
            ц = n.targets[0]
            if isinstance(ц.slice, ast.Constant) and isinstance(ц.slice.value, str):
                групи[("оновлення", ast.unparse(ц.value))].append((ц.slice.value, n, n.value))
        elif isinstance(n, ast.Return) and n.value is not None:     # колір, повернений значенням чи кортежем
            for т in ast.walk(n.value):
                if isinstance(т, ast.Subscript) and isinstance(т.slice, ast.Constant) and т.slice.value in ТОЧКА \
                        and isinstance(т.ctx, ast.Load):
                    групи[("повернення", id(n), т.slice.value)].append((т.slice.value, n, т))
    вихід = []
    for елем in групи.values():
        ключі = {к for к, _, з in елем if not (isinstance(з, ast.Constant) and з.value is None and к in ("розкид", "spread"))}
        впевненість_число = any(к == "впевненість" and isinstance(з, ast.Constant) and isinstance(з.value, (int, float)) for к, _, з in елем)
        тип = next((з for к, _, з in елем if к == "колір_тип"), None)
        запис_конст = свідчення([з for _, _, з in елем if з is not None])[1]
        оголошує_вимір = тип is not None and "вимір" in свідчення([тип])[1]
        for к, вузол, зн in елем:
            if к in ТОЧКА and not (isinstance(зн, ast.Constant) and (зн.value is None or isinstance(зн.value, (int, float)))):
                вихід.append((к, вузол, зн, ключі, оголошує_вимір, впевненість_число, запис_конст))
    return вихід


def шлях_А(файл, дерево, батьки):
    місця = []
    for функція in ast.walk(дерево):
        if not isinstance(функція, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # п.1, п.2, п.3 — запис точки
        вимірювач = функція.name in ВИМІРЮВАЧІ or (файл == "surface.py" and функція.name == "виміряти")
        for к, вузол, зн, ключі, оголошує_вимір, впевненість_число, запис_конст in записи_точки(функція):
            перевираження = типізоване_значення(зн, функція) and not оголошує_вимір
            if впевненість_число:
                перевираження = False
            if перевираження or у_ненадійному(вузол, батьки):
                continue
            імена, конст, виклики = зріз_значення(зн, функція)
            конст = конст | запис_конст
            народжено_виміром = оголошує_вимір or bool(виклики & ВИМІРЮВАЧІ or "surface.виміряти" in виклики or імена & ПІКСЕЛІ)
            _, конст_функції, _ = свідчення([функція])
            річ_запису = bool(конст_функції & (ТИПІЗОВАНІ | {"слот", "річ"}))
            народжено_словом = річ_запису and (впевненість_число or bool(імена & СЛОВО or конст & МОДЕЛЬ))
            рядок = getattr(вузол, "lineno", функція.lineno)
            ім = функція.name
            if народжено_виміром:
                _, власні_конст, _ = свідчення([функція]) if вимірювач else (None, ключі, None)
                бракує = []
                if not any(р in k for k in власні_конст for р in РОЗКИД):
                    бракує.append("розкиду")
                if not any(k.startswith(п) for k in власні_конст for п in ПРИДАТНІСТЬ):
                    бракує.append("придатності")
                if бракує:
                    місця.append(Місце(файл, рядок, 1, "запис «%s» у %s: точка виміру без %s" % (к, ім, " і ".join(бракує)), "А"))
                кадр_є = bool(конст_функції & КАДР or імена & КАДР)
                if not вимірювач and кадр_є and not (конст_функції | імена) & ВЛАСНИК:
                    місця.append(Місце(файл, рядок, 2, "запис «%s» у %s: кадр виміру в колір без перевірки власника кадру" % (к, ім), "А"))
            if народжено_словом and not ключі & {"колір_тип", "колір_не_вимір", "не_вимір"}:
                місця.append(Місце(файл, рядок, 3, "запис «%s» у %s: значення зі слова чи моделі без виду значення" % (к, ім), "А"))
        # п.4 — вибір кластера словом
        for n in власні_вузли(функція):
            ітер = умова = None
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ОБРАННЯ and n.args:
                ітер, умова = n.args[0], [ast.unparse(k.value) for k in n.keywords] + [ast.unparse(a) for a in n.args[1:]]
            elif isinstance(n, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
                for г in n.generators:
                    ітер, умова = г.iter, [ast.unparse(i) for i in г.ifs]
            elif isinstance(n, ast.For):
                ітер, умова = n.iter, [ast.unparse(т.test) for т in n.body if isinstance(т, ast.If)]
            if ітер is not None and КЛАСТЕР.search(ast.unparse(ітер)) and умова:
                вирази = [ast.parse(у, mode="eval").body for у in умова]
                імена_у, конст_у, _ = крок_значення(ast.Tuple(elts=вирази, ctx=ast.Load()), функція)
                if (імена_у | конст_у) & СЛОВО_ЗОВНІ:
                    місця.append(Місце(файл, n.lineno, 4, "кластер чи кадр у %s обирає слово крамниці чи моделі: %s" % (функція.name, "; ".join(умова)[:70]), "А"))
        # п.5 — вимір кадру без збереження кадру з маніфестом
        if функція.name not in ВИМІРЮВАЧІ and функція.name not in ОБГОРТКИ:
            for n in власні_вузли(функція):
                if not isinstance(n, ast.Call):
                    continue
                ім, мод = ім_виклику(n)
                if ім in ВИМІРЮВАЧІ or виміряти_поверхні(n):
                    імена_ф, конст_ф, виклики_ф = свідчення([функція])
                    if not (імена_ф | конст_ф | виклики_ф) & МАНІФЕСТ:
                        місця.append(Місце(файл, n.lineno, 5, "виклик %s у %s: кадр виміру не збережено з маніфестом" % (ім, функція.name), "А"))
    return місця


def читання_точки(функція):
    """Читання точки: (вузол, приймач, ключ|None). Ключ `lab`/`hex` чи виклик точкового читача `точка_кольору(x)`."""
    вихід = []
    for n in власні_вузли(функція):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and n.slice.value in ТОЧКА \
                and isinstance(n.ctx, ast.Load) and isinstance(n.value, ast.Name):
            вихід.append((n, n.value.id, n.slice.value))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args \
                and isinstance(n.args[0], ast.Constant) and n.args[0].value in ТОЧКА and isinstance(n.func.value, ast.Name):
            вихід.append((n, n.func.value.id, n.args[0].value))
        elif isinstance(n, ast.Call) and ім_виклику(n)[0] in ТОЧКОВІ_ЧИТАЧІ and n.args and isinstance(n.args[0], ast.Name):
            вихід.append((n, n.args[0].id, None))
    return вихід


def ключі_приймачів(функція):
    """Приймач (ім'я) → ключі, які з нього читають чи в нього пишуть у функції."""
    таблиця = collections.defaultdict(set)
    for n in власні_вузли(функція):
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str) \
                and isinstance(n.value, ast.Name):
            таблиця[n.value.id].add(n.slice.value)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("get", "pop", "setdefault") \
                and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) \
                and isinstance(n.func.value, ast.Name):
            таблиця[n.func.value.id].add(n.args[0].value)
    return таблиця


def шлях_Б(файл, дерево, батьки):
    місця = []
    for функція in ast.walk(дерево):
        if not isinstance(функція, (ast.FunctionDef, ast.AsyncFunctionDef)) or функція.name in ВИД_ЗНАЧЕННЯ \
                or ВАЛІДАТОР.search(функція.name):
            continue
        таблиця = ключі_приймачів(функція)
        for вузол, приймач, ключ in читання_точки(функція):
            if наявність(вузол, батьки) and ключ is not None:
                continue
            ключі = таблиця.get(приймач, set())
            імена_о, конст_о, виклики_о = свідчення(охорона(вузол, батьки))
            _, конст_б, _ = свідчення(блок(вузол, батьки))
            імена_б, _, виклики_б = свідчення(блок(вузол, батьки))
            рядок = вузол.lineno
            є_вид = bool(виклики_о & ВИД_ЗНАЧЕННЯ or "колір_тип" in конст_о or "колір_тип" in ключі)
            # п.3 — запис речі з типізованими ключами: читач `lab`/`hex` напряму без виду значення
            if ключ is not None and ключі & (ТИПІЗОВАНІ | ОЗНАКИ_РЕЧІ) and not є_вид:
                місця.append(Місце(файл, рядок, 3, "читач «%s» у %s не дивиться на вид значення" % (ключ, функція.name), "Б"))
            # п.1, п.2 — кадр галереї: ключі кадру й точка без розкиду, придатності й власника
            if ключі & КЛЮЧІ_КАДРУ:
                докази = ключі | конст_б
                бракує = [н for н, ознаки in (("розкиду", РОЗКИД), ("придатності", ПРИДАТНІСТЬ))
                          if not any(о in k for k in докази for о in ознаки)]
                if бракує:
                    місця.append(Місце(файл, рядок, 1, "читач точки кадру «%s» у %s: точка без %s" % (приймач, функція.name, " і ".join(бракує)), "Б"))
                if not (свідчення([функція])[0] | свідчення([функція])[1]) & ВЛАСНИК:
                    місця.append(Місце(файл, рядок, 2, "читач кадру «%s» у %s: кадр у колір без перевірки власника кадру" % (приймач, функція.name), "Б"))
    return місця


def шлях_Б_js(js):
    місця = []
    for ш in js:
        for н, р in enumerate(open(ш, encoding="utf-8").read().split("\n"), 1):
            if (JS_ВИМІР.search(р) or JS_РІЧ.search(р)) and not JS_ВИД.search(р):
                місця.append(Місце("показ/" + os.path.basename(ш), н, 3, "читач hex/lab речі у JS не дивиться на вид значення", "Б"))
    return місця


def ключ_кольору(к):
    return к in ТОЧКА or к in ТИПІЗОВАНІ or к.startswith("колір_")


def звірка_полів(файли_py, js):
    """Поля кольору: хто пише (А), хто читає (Б)."""
    пишуть, читають = collections.defaultdict(set), collections.defaultdict(set)
    for ф, дерево, батьки in файли_py:
        for n in ast.walk(дерево):
            if isinstance(n, ast.Dict):
                for к in n.keys:
                    if isinstance(к, ast.Constant) and isinstance(к.value, str) and ключ_кольору(к.value):
                        пишуть[к.value].add(ф)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "dict":
                for kw in n.keywords:
                    if kw.arg and ключ_кольору(kw.arg):
                        пишуть[kw.arg].add(ф)
            elif isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str) \
                    and ключ_кольору(n.slice.value):
                (пишуть if isinstance(n.ctx, ast.Store) else читають)[n.slice.value].add(ф)
            elif isinstance(n, ast.Call) and ім_виклику(n)[0] in ("get", "pop") and n.args \
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) and ключ_кольору(n.args[0].value):
                читають[n.args[0].value].add(ф)
    for ш in js:
        текст = open(ш, encoding="utf-8").read()
        for к in list(пишуть):
            if re.search(r"(?<![\w])%s(?![\w])" % re.escape(к), текст):
                читають[к].add("показ/" + os.path.basename(ш))
    тільки_А = sorted(к for к in пишуть if к not in читають)
    тільки_Б = sorted(к for к in читають if к not in пишуть)
    return len(пишуть), len(читають), тільки_А, тільки_Б


def частка_каталогу(корінь):
    """Частка варіантів каталогу з кольором з виміру власних кадрів: `прочитати_каталог` офлайн, поля запису."""
    import importlib
    дер = os.path.join(корінь, "джерела")
    sys.path.insert(0, дер)
    cwd = os.getcwd()
    os.chdir(дер)
    try:
        feed = importlib.import_module("feed")
        шлях = feed.каталог_на_диску("каталог_повний.xml")
        каталог = feed._прочитати_каталог(шлях, ліміт_фото=0)["каталог"]
    finally:
        os.chdir(cwd)
    n, л = len(каталог), collections.Counter()
    for з in каталог:
        власник = (з.get("власник_кадру") or {}).get("стан")
        вимір = з.get("колір_тип") == "вимір"
        придатний = bool((з.get("колір_вимір") or {}).get("придатний"))
        маніфест = (з.get("кадр_виміру") or {}).get("стан") not in (None, "unknown")
        л["колір_тип «вимір»"] += вимір
        л["…з придатним виміром"] += вимір and придатний
        л["…і власник кадру «свій»"] += вимір and придатний and власник == "свій"
        л["…і кадр виміру з маніфестом"] += вимір and придатний and власник == "свій" and маніфест
        л["вимір, власник «спільний»"] += вимір and власник == "спільний"
        л["вимір, власник «невідомо»"] += вимір and власник == "невідомо"
        л["вимір, власника не записано"] += вимір and власник is None
    return n, л


def головна():
    ар = argparse.ArgumentParser()
    ар.add_argument("--корінь", default=os.path.dirname(ТУТ))
    ар.add_argument("--каталог", action="store_true")
    арг = ар.parse_args()
    корінь = os.path.abspath(арг.корінь)
    дер = os.path.join(корінь, "джерела")
    py = sorted(f for f in glob.glob(os.path.join(дер, "*.py")) if not ВИКЛЮЧЕНО.match(os.path.basename(f)))
    js = sorted(glob.glob(os.path.join(дер, "показ", "*.js")))
    файли_py, місця = [], []
    for ш in py:
        ім = os.path.basename(ш)
        дерево, батьки = розібрати(ш)
        файли_py.append((ім, дерево, батьки))
        місця += шлях_А(ім, дерево, батьки) + шлях_Б(ім, дерево, батьки)
    місця += шлях_Б_js(js)
    унікальні = {}
    for м in місця:
        ключ = (м.файл, м.рядок, м.пункт)
        було = унікальні.get(ключ)
        унікальні[ключ] = м if було is None else було._replace(шлях="".join(sorted(set(було.шлях + м.шлях))))
    перелік = sorted(унікальні.values(), key=lambda м: (м.пункт, м.файл, м.рядок))
    for м in перелік:
        print("%s:%d · п.%d · %s [%s]" % (м.файл, м.рядок, м.пункт, м.чому, м.шлях))
    print("---")
    за_пунктом = collections.Counter(м.пункт for м in перелік)
    за_шляхом = collections.Counter((м.пункт, м.шлях) for м in перелік)
    for п in range(1, 6):
        print("пункт %d: %d (лише А %d, лише Б %d, обидва %d)" % (п, за_пунктом[п], за_шляхом[(п, "А")], за_шляхом[(п, "Б")], за_шляхом[(п, "АБ")]))
    print("файлів продукту %d, JS %d" % (len(py), len(js)))
    пишуть, читають, тільки_А, тільки_Б = звірка_полів(файли_py, js)
    print("звірка шляхів за полями кольору: пишуть %d, читають %d" % (пишуть, читають))
    print("  пишуть і ніхто не читає в коді (%d): %s" % (len(тільки_А), ", ".join(тільки_А) or "—"))
    print("  читають і ніхто не пише в коді (%d): %s" % (len(тільки_Б), ", ".join(тільки_Б) or "—"))
    if арг.каталог:
        n, л = частка_каталогу(корінь)
        print("каталог: варіантів %d" % n)
        for к, v in л.items():
            print("  %s: %d (%.1f%%)" % (к, v, 100.0 * v / n))
        print("частка варіантів із кольором з виміру власних кадрів: %.1f%%" % (100.0 * л["…і кадр виміру з маніфестом"] / n))
    print("місць: %d" % len(перелік))


if __name__ == "__main__":
    головна()
