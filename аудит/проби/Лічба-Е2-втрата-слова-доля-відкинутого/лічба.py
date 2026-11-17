# -*- coding: utf-8 -*-
"""ЛІЧБА Е2-втрата-слова: перевірки поля відповіді моделі (форма | перелік) у коді продукту і доля відкинутого.

Питання: скільки перевірок поля відповіді моделі відкидають значення за формою (тип, структура) чи за переліком
(enum, таблиця кодів) і що кожна робить із відкинутим: (а) порожнє мовчки; (б) «не записано» чи інший слід у записі;
(в) цитата чи слово стилістці; (г) інше — із назвою. Нічого не править; коду продукту не імпортує (AST).

ОБСЯГ: `джерела/*.py` і `zhnyvarka/**/*.py` без тестів, проб, приладів, стендів, батарей і воріт CI (список виключень —
ВИКЛЮЧЕНІ нижче, друкується). Python; JS (`джерела/показ`, `worker*.js`) — НЕ ВИМІРЯНО (лише вказано). JSON-схеми
(`*.schema.json`) — окремі лічильники `enum`-вузлів (декларація, перевіряє її код з таблиці).

ПОТІК ВІД ВІДПОВІДІ МОДЕЛІ (крок 16239, 17.11): корінь — лише значення, що походить з відповіді моделі, визначене
будовою, а не іменем. ДЖЕРЕЛА (`--джерела` друкує місця): ендпойнти мосту (`bridge.виклик`, `виклик_а`), чий вхід —
ЗАПИТ; у ньому поля відповіді моделі КЛЮЧІ_A (сира відповідь) і КЛЮЧІ_B (повернене показом з попереднього виклику),
вкладені ВКЛАДЕНІ_ДЖЕРЕЛА, і тіло відповіді сервера `choices→message→content`; решта полів запиту — запис коду.
Абстрактне значення — (М: A|B, запит, форма полів); функції — за контекстом аргументів (понад 6 — розширення, межа
росту); середовище — за порядком тексту (присвоєння імені замінює, гілки зливаються, цикл — до нерухомої точки), і
перевірка бере значення виразу в своєму місці. М несе рух даних, а не обчислення: виклик поза продуктом — запис коду
(перенос — регулярні, перетворення листка, `злам` → третій аргумент); методи класів продукту — за єдиним іменем;
`схема.виконати_розбір/перевірити` — реєстр `схеми_розбору.РОЗБІР`; ключі — й сталі модулів; поле, назване у формі, —
без М верху злиття; рекурсивні обходи будови (`без_ід_глибоко`) — тотожність. Корінь за іменем (лічба до 16239: імена
параметрів, `json_.loads(вхід)`) лишився лише окремим рядком «запис коду» — те, що він брав, а потік — ні.
ПЕРЕВІРКА (на зараженому значенні E):
  форма   — `isinstance(E, …)`, `type(E) is/==`, `re.match/fullmatch(…, E)`, `E.isdigit()`-подібні, `int(E)`/`float(E)`
            у `try` з `except ValueError/TypeError`;
  перелік — `E in C` / `E not in C`, де C — стала модуля (таблиця/множина/кортеж), імпортована стала, літерал із ≥2
            елементів чи `…["enum"|"значення"|…]`.
ГІЛКА ВІДКИНУТОГО — за положенням перевірки в умові (`if`/`IfExp`/умова генератора/`try`): позитивна перевірка → `else`
чи проходження далі; негативна (`not`, `not in`) → тіло. Перевірка, чия відкинута гілка веде значення далі (те саме
коріння читається нижче чи в гілці), — НЕ ВІДКИДАЄ («веде далі»), у підсумок за долями не йде.
ДОЛЯ (за текстом відкинутої гілки; все — локально, слід деінде видно лише очима):
  а  порожнє мовчки — `continue/pass/break`, `return` порожнього (None, False, "", [], {}, ()), присвоєння порожнього,
     відсів у генераторі/умові без гілки;
  б  слід у записі — гілка кладе в змінну/ключ/виклик з іменем про «не_взято/не_записано/невідомо/незнайомі/помилка/
     причина/заглушки/відкинуто/зняте…» чи повертає такий запис;
  в  цитата чи слово стилістці — гілка пише в `quote/уривок/цитата/слова_ходу/her_*`;
  г  інше (названо): `raise` (причина повтору/помилки), предикат (`return isinstance…` — доля у викликача), підміна
     значення, виклик іншої функції.
КЛАСИ ПРАВИЛ, виправлені за вадами перевірки 16221–16224 (16.11 23:06 UTC, PR #4129), кожен — правило класу, не перелік:
  16221  «читає значення» ≠ «описує його»: корінь у `type(…)`, `isinstance(…)`, `_як_звати(…)`, у повідомленні
         (`"…%s" % …`) і в `raise` — це текст про відкинуте; заперечна перевірка з `return [помилка]`/`raise` під нею — (г);
  16222  охоронений `if` без `else` (позитивна перевірка): відкинуте мовчки не йде далі — (а); долею лічиться лише те,
         що стоїть одразу після нього (слід, вихід), а не решта блоку чи звичайний `return` результату;
  16223  запасне значення умовного виразу — останнє `else` ланцюга `[v] if str else v if list else []` — (а); відсів значення
         в умові, чий корінь далі не читається (перепризначення імені циклом, генератором, лямбдою — інше значення), — (а);
  16224  (в) — лише коли гілка кладе саме відкинуте значення в канал цитати; гілка з іншого джерела — не (в).
Додано з двох вибірок очима: відкинуте — за ПОЛЯРНІСТЮ перевірки (тіло позитивної перевірки з роботою — прийняте);
корінь поля `об.get("k")` — лише той самий доступ чи ціла `об`; відсів у генераторі з коренем із зовнішньої області
читається далі; присвоєння-предикат, що вживається в умовному виразі.
`--самоперевірка` — фікстура на кожен клас (код виходу 1 при розбіжності).
Запуск з кореня: `python3 аудит/проби/Лічба-Е2-втрата-слова-доля-відкинутого/лічба.py [--таблиця ФАЙЛ]
[--два-значення] [--самоперевірка] [--джерела] [--вибірка SEED N]` (вибірка — без звірених раніше,
`звірені_раніше.json`); останній рядок — `перевірок: N · відкидають: M · а: … · б: … · в: … · г: … · веде далі: K`."""
import ast, collections, glob, json, os, re, sys, warnings
warnings.simplefilter('ignore')
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(КОРІНЬ)

ВИКЛЮЧЕНІ = re.compile(r'^(тест_|test_|проба|стенд|батарея|audit|measure|gate|verify|status|звірка|pair_test|покроковик|'
                       r'прилади|мутанти|поломки|run_outfit|build_|тема-)')
КОРЕНІ_ПАРАМЕТРІВ = {'відповідь', 'відповідь_моделі', 'відп', 'вих', 'вихід', 'слово_моделі', 'оновлення', 'внутрішня', 'об', 'знач',
                      'вердикт', 'суд_', 'образи', 'попередній_вердикт'}
КОРЕНІ_КЛЮЧІВ = {'відповідь_моделі', 'відповідь', 'відп', 'answer', 'вихід', 'відповіді_шару', 'json_моделі'}
РОЗБІР = {'loads', 'розбір', 'розібрати_json', 'розбір_за_схемою', '_обʼєкт', 'obj_from_text'}
ЗА_ІМЕНЕМ = re.compile(r'відповід|відп\b|вих\b|json_моделі|текст_моделі|сирий|слово_моделі|raw', re.I)
ПЕРЕНОС_МЕТОДИ = {'get', 'items', 'values', 'keys', 'copy', 'strip', 'lower', 'upper', 'split', 'lstrip', 'rstrip',
                  'casefold', 'pop', 'setdefault', 'splitlines', 'title', 'capitalize', 'replace'}
ПЕРЕНОС_ВБУДОВАНІ = {'dict', 'list', 'str', 'tuple', 'set', 'frozenset', 'sorted', 'reversed', 'enumerate', 'zip', 'next',
                     'iter', 'filter', 'map', 'max', 'min', 'int', 'float', 'deepcopy', 'copy', 'sum', 'any_'}
СЛІД = re.compile(r'(не_взято|не_записано|невідом|незнайом|помил|причин|errors?|format_error|заглуш|відкинут|знят|невірн|'
                  r'пропущ|rejected|dropped|skipped|вад[аиі]?\b|попередж|warn|unknown|not_taken|not_recorded|звіт|'
                  r'нотатк|слід|reason|extra|зайв)', re.I)
ЦИТАТА = re.compile(r'(her_other|слова_ходу|цитат|quote|уривок|her_words|слов[ао]_стил)', re.I)
ПОРОЖНІ = (None, False, '', 0)
ТАБЛИЧНІ_КЛЮЧІ = {'enum', 'значення', 'перелік', 'allowed', 'допустимі'}


def файли():
    res = []
    for ф in sorted(glob.glob('джерела/*.py') + glob.glob('zhnyvarka/**/*.py', recursive=True)):
        if ВИКЛЮЧЕНІ.match(os.path.basename(ф)):
            continue
        res.append(ф)
    return res


def джерело_шляху(вузол):
    return ast.unparse(вузол)


class Модуль:
    def __init__(с, шлях):
        с.шлях = шлях
        с.імʼя = os.path.splitext(os.path.basename(шлях))[0]
        с.текст = open(шлях, encoding='utf-8').read()
        с.дерево = ast.parse(с.текст)
        с.рядки = с.текст.split('\n')
        с.імпорти = {}                # локальне імʼя → (модуль, імʼя | None)
        с.сталі = set()               # імена сталих рівня модуля (присвоєння)
        с.рядкові = {}                # стала рівня модуля → рядок чи число (`ВЕРДИКТ_ОБРАЗІВ = "вердикт"`)
        с.функції = {}                # імʼя → Fn
        for н in с.дерево.body:
            if isinstance(н, ast.Import):
                for а in н.names:
                    с.імпорти[а.asname or а.name.split('.')[0]] = (а.name.split('.')[-1], None)
            elif isinstance(н, ast.ImportFrom):
                for а in н.names:
                    с.імпорти[а.asname or а.name] = (н.module.split('.')[-1] if н.module else '', а.name)
            elif isinstance(н, (ast.Assign, ast.AnnAssign)):
                цілі = н.targets if isinstance(н, ast.Assign) else [н.target]
                знач = н.value
                if isinstance(знач, ast.Constant) and isinstance(знач.value, (str, int)) and not isinstance(знач.value, bool):
                    for ц in цілі:
                        if isinstance(ц, ast.Name):
                            с.рядкові[ц.id] = знач.value
                if isinstance(знач, (ast.Dict, ast.Set, ast.List, ast.Tuple, ast.Call, ast.Constant, ast.SetComp,
                                      ast.DictComp, ast.ListComp, ast.GeneratorExp, ast.BinOp, ast.Attribute)):
                    for ц in цілі:
                        for х in ast.walk(ц):
                            if isinstance(х, ast.Name):
                                с.сталі.add(х.id)
        # функції на будь-якій глибині (імʼя → перша), включно з методами й вкладеними
        for н in ast.walk(с.дерево):
            if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef)):
                с.функції.setdefault(н.name, Fn(с, н))


class Fn:
    def __init__(с, мод, вузол):
        с.мод, с.вузол, с.імʼя = мод, вузол, вузол.name
        a = вузол.args
        с.параметри = [х.arg for х in a.posonlyargs + a.args + a.kwonlyargs]
        с.ядро = мод.імʼя in МОДУЛЬ_ЧИЯ
        с.заражені = {і for і, п in enumerate(с.параметри) if п in КОРЕНІ_ПАРАМЕТРІВ and с.ядро}
        с.повертає = False
        с.табл_парам = set()          # імена параметрів, яким виклики дають таблицю коду (перелік)
        с.табл_виклики = set()        # локальні лямбди, що повертають таблицю (`перелік = lambda п: …["enum"]`)
        с.табл_локалі = set()         # локальні імена, зібрані з таблиці (`коди = [… for к in с["enum"]]`)
        с.батьки = {}


МОДУЛІ = {}


def вирішити(мод, виклик):
    """Виклик → Fn продукту чи None."""
    f = виклик.func
    if isinstance(f, ast.Name):
        if f.id in мод.функції:
            return мод.функції[f.id]
        if f.id in мод.імпорти:
            м, і = мод.імпорти[f.id]
            if м in МОДУЛІ and і:
                return функція_модуля(МОДУЛІ[м], і)
    elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in мод.імпорти:
        м, і = мод.імпорти[f.value.id]
        цілий = і or м
        if цілий in МОДУЛІ:
            return функція_модуля(МОДУЛІ[цілий], f.attr)
    return None


def стала(мод, е, глибина_=0):
    """Ключ-стала: літерал, стала рівня модуля (`КЛЮЧ`) чи модуля імпорту (`_ПР.ВЕРДИКТ_ОБРАЗІВ`) → значення; інакше
    None. Ключ-стала без цього читався «невідомим ключем» і зливав усі поля словника (`перемішати_дріт`, вердикт на
    дроті — клас похибки вибірки 1712)."""
    if isinstance(е, ast.Constant):
        return е.value if isinstance(е.value, (str, int)) and not isinstance(е.value, bool) else None
    if глибина_ > 4:
        return None
    if isinstance(е, ast.Name):
        if е.id in мод.рядкові:
            return мод.рядкові[е.id]
        if е.id in мод.імпорти:
            м, і = мод.імпорти[е.id]
            if м in МОДУЛІ and і:
                return стала(МОДУЛІ[м], ast.Name(і), глибина_ + 1)
        return None
    if isinstance(е, ast.Attribute) and isinstance(е.value, ast.Name) and е.value.id in мод.імпорти:
        м, і = мод.імпорти[е.value.id]
        if і is None and м in МОДУЛІ:
            return стала(МОДУЛІ[м], ast.Name(е.attr), глибина_ + 1)
    return None


def функція_модуля(мод, імʼя, глибина_=0):
    """Функція `імʼя` модуля, і крізь `from x import імʼя` (`pipeline` віддає функції інших модулів далі)."""
    if імʼя in мод.функції:
        return мод.функції[імʼя]
    if глибина_ < 4 and імʼя in мод.імпорти:
        м, і = мод.імпорти[імʼя]
        if м in МОДУЛІ and і:
            return функція_модуля(МОДУЛІ[м], і, глибина_ + 1)
    return None


def ім_виклику(в):
    f = в.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ''


class Потік:
    """Потік зараження в одній функції; збирає виклики для міжфункційного кроку."""
    def __init__(с, fn):
        с.fn, с.env = fn, {fn.параметри[і] for і in fn.заражені}
        с.ядро = fn.ядро
        с.виклики = []

    def т(с, е):
        if е is None:
            return False
        if isinstance(е, ast.Name):
            return е.id in с.env and е.id not in с.fn.табл_парам and е.id not in с.fn.табл_локалі
        if isinstance(е, (ast.Subscript, ast.Attribute, ast.Starred)):
            if isinstance(е, ast.Subscript):
                k = е.slice
                if isinstance(k, ast.Constant) and k.value in КОРЕНІ_КЛЮЧІВ and с.ядро:
                    return True
            return с.т(е.value)
        if isinstance(е, ast.Call):
            ім = ім_виклику(е)
            арги = list(е.args) + [к.value for к in е.keywords]
            if ім in РОЗБІР and с.ядро:
                if ім != 'loads':
                    return True
                if арги and (с.т(арги[0]) or ЗА_ІМЕНЕМ.search(джерело_шляху(арги[0]))):
                    return True
            f = е.func
            if isinstance(f, ast.Attribute) and f.attr in ПЕРЕНОС_МЕТОДИ:
                if f.attr == 'get' and с.ядро and е.args and isinstance(е.args[0], ast.Constant) and е.args[0].value in КОРЕНІ_КЛЮЧІВ:
                    return True
                if с.т(f.value):
                    return True
            if isinstance(f, ast.Name) and ім in ПЕРЕНОС_ВБУДОВАНІ and any(с.т(а) for а in арги):
                return True
            g = вирішити(с.fn.мод, е)
            if g is not None and g.ядро:
                с.виклики.append((g, е))
                if g.повертає and (any(с.т(а) for а in арги) or g.корінь_повернення):
                    return True
            return False
        if isinstance(е, ast.BoolOp):
            return any(с.т(х) for х in е.values)
        if isinstance(е, ast.IfExp):
            return с.т(е.body) or с.т(е.orelse)
        if isinstance(е, (ast.Tuple, ast.List, ast.Set)):
            return any(с.т(х) for х in е.elts)
        if isinstance(е, ast.Dict):
            return any(с.т(х) for х in е.values if х is not None)
        if isinstance(е, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return с.комп(е, е.elt)
        if isinstance(е, ast.DictComp):
            return с.комп(е, е.value)
        if isinstance(е, ast.BinOp):
            return с.т(е.left) or с.т(е.right)
        if isinstance(е, ast.NamedExpr):
            з = с.т(е.value)
            if з and isinstance(е.target, ast.Name):
                с.env.add(е.target.id)
            return з
        return False

    def комп(с, е, елем):
        було = set(с.env)
        for г in е.generators:
            с.ціль(г.target, с.т(г.iter))
        р = с.т(елем)
        с.env = було | (с.env & було)
        return р

    def ціль(с, ц, з, знач=None):
        if isinstance(ц, (ast.Tuple, ast.List)) and isinstance(знач, (ast.Tuple, ast.List)) \
                and len(ц.elts) == len(знач.elts) and not any(isinstance(x, ast.Starred) for x in ц.elts + знач.elts):
            for ці, зн in zip(ц.elts, знач.elts):       # поелементне розпакування: не заражає сусідів
                с.ціль(ці, с.т(зн), зн)
            return
        if not з:
            return
        for х in ast.walk(ц):
            if isinstance(х, ast.Name):
                с.env.add(х.id)

    def прогін(с, вузол):
        for _ in range(2):
            for н in ast.walk(вузол):
                if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and н is not вузол:
                    continue
                if isinstance(н, ast.Assign):
                    [с.ціль(ц, с.т(н.value), н.value) for ц in н.targets]
                elif isinstance(н, (ast.AnnAssign, ast.AugAssign)) and getattr(н, 'value', None) is not None:
                    с.ціль(н.target, с.т(н.value))
                elif isinstance(н, ast.For):
                    с.ціль(н.target, с.т(н.iter))
                elif isinstance(н, ast.NamedExpr):
                    с.т(н)
                elif isinstance(н, ast.Return) and н.value is not None:
                    if с.т(н.value):
                        с.fn.повертає = True


def міжфункційно():
    for _ in range(10):
        змін = False
        for мод in МОДУЛІ.values():
            for fn in set(мод.функції.values()):
                п = Потік(fn)
                п.прогін(fn.вузол)
                for g, в in п.виклики:
                    for і, а in enumerate(в.args):
                        if п.т(а) and і < len(g.параметри) and і not in g.заражені and not (isinstance(в.func, ast.Name) and False):
                            g.заражені.add(і); змін = True
                    for к in в.keywords:
                        if к.arg in g.параметри and п.т(к.value):
                            j = g.параметри.index(к.arg)
                            if j not in g.заражені:
                                g.заражені.add(j); змін = True
                if fn.повертає and not getattr(fn, '_p', False):
                    fn._p = True
        if not змін:
            break


Fn.корінь_повернення = False


# ───────────────────────── ПОТІК ВІД ВІДПОВІДІ МОДЕЛІ (крок 16239) ─────────────────────────
# Джерела — будовою, а не іменами параметрів. Значення «відповідь моделі» (М) народжується лише там, де продукт
# одержує текст моделі:
#   (1) запит мосту — параметр `вхід` ендпойнтів `bridge.виклик`/`виклик_а` (словник ім → функція): сам запит — запис
#       коду (ЗАПИТ), його поля — теж, крім ключів нижче, куди показ кладе сиру відповідь моделі (A) чи повертає
#       розбір її відповіді, який раніше віддав міст (B; місця JS — у звіті `потік.md`);
#   (2) відповідь сервера моделі форми OpenAI: `…["choices"][0]["message"]["content"]` (жнива, прогін каталогу).
# Далі потік іде присвоєннями, циклами, викликами функцій продукту (контекстно: аргументи → параметри → повернення)
# з точністю до поля: запис, який склав код (`dict(причина=…, що=знач)`, `не_взято.append(…)`), — форма, де М лише
# в тих полях, куди його поклали; перевірка поля коду (`запис["причина"]`) — не перевірка відповіді моделі.
# Повідомлення (`"…%s" % знач`, f-рядок, `.format`), `len/type/isinstance` і порівняння — опис коду, не М.
КЛЮЧІ_A = {'відповідь_моделі', 'перша_відповідь', 'json_моделі', 'текст_моделі', 'тексти_моделі', 'перелік_речей'}
КЛЮЧІ_B = {'паспорт_з', 'коментар_з', 'власні', 'частини', 'попередня', 'сценарій_плитки', 'вибір_стилістки',
           'попередній_вердикт', 'вибір_над'}
Ø = frozenset()
ЧИСТЕ = (Ø, False, None)
ЗАПИТ = (Ø, True, None)
М_A = (frozenset('A'), False, None)
М_B = (frozenset('B'), False, None)
ГЛИБИНА, ШИРИНА = 6, 40


def М_(м):
    return (м, False, None) if м else ЧИСТЕ


@__import__('functools').lru_cache(maxsize=None)
@__import__('functools').lru_cache(maxsize=None)
def глибина(в):
    return 0 if в[2] is None else 1 + max((глибина(х) for _, х in в[2]), default=0)


@__import__('functools').lru_cache(maxsize=None)
def усе_м(в):
    м = в[0]
    for _, х in (в[2] or ()):
        м = м | усе_м(х)
    return м


def зрізати(в, н):
    """Форма до глибини `н`: глибші рівні — одним полем `*` із М свого піддерева, а сам вузол лишається своїм (верхні
    поля лишаються полями). Доти глибше згортання ставило М піддерева на сам вузол, і запис коду з полем моделі десь
    усередині (`виконання` вердикту з ід речей) читався відповіддю моделі (клас похибки вибірки 1712)."""
    if в[2] is None:
        return в
    if н == 0:
        у = frozenset().union(*(усе_м(х) for _, х in в[2]))
        р = any(х[1] for _, х in в[2])
        return (в[0], в[1], frozenset({('*', (у, р, None))})) if (у or р) else ((в[0], в[1], None) if (в[0] or в[1]) else ЧИСТЕ)
    пари = frozenset((к, х) for к, х in ((к, зрізати(х, н - 1)) for к, х in в[2]) if х != ЧИСТЕ)
    return (в[0], в[1], пари or None) if (пари or в[0] or в[1]) else ЧИСТЕ


@__import__('functools').lru_cache(maxsize=None)
def обріз(в):
    """Межа форми: рівень ширший за ШИРИНА — його поля зливаються в `*` (лише цей рівень); глибше ГЛИБИНА — нижні
    рівні листком. Доти вся форма згорталась в один `*` з М усього піддерева, і запис коду з одним полем моделі
    читався моделлю в кожному полі (клас похибки вибірки 1712)."""
    if в[2] is None:
        return в
    if len(в[2]) > ШИРИНА:
        в = (в[0], в[1], frozenset({('*', Jвсі(х for _, х in в[2]))}))
    if глибина(в) > ГЛИБИНА + 1:
        в = зрізати(в, ГЛИБИНА)
    return в


def Ш(д):
    пари = frozenset((к, в) for к, в in д.items() if в != ЧИСТЕ)
    return обріз((Ø, False, пари)) if пари else ЧИСТЕ


@__import__('functools').lru_cache(maxsize=None)
def J(а, б):
    if а == ЧИСТЕ or а == б:
        return б
    if б == ЧИСТЕ:
        return а
    м, р = а[0] | б[0], а[1] or б[1]
    if а[2] is None or б[2] is None:
        return (м, р, а[2] if б[2] is None else б[2])
    д = dict(а[2])
    for к, в in б[2]:
        д[к] = J(д[к], в) if к in д else в
    return обріз((м, р, frozenset(д.items())))


def Jвсі(вв):
    р = ЧИСТЕ
    for в in вв:
        р = J(р, в)
    return р


ВКЛАДЕНІ_ДЖЕРЕЛА = {      # ключ запиту → форма, де сира відповідь лежить глибше (місця JS — у звіті)
    'відповіді_шару': Ш({'*': ЗАПИТ}),                  # кожен елемент — запит шару з тими самими ключами
    'вибір_речей': Ш({'відповіді': Ш({'*': Ш({'текст': М_A})})}),
    'вибір_повноти': Ш({'текст': М_A, 'вердикт': М_B}),
}


РОЗШИРЕНЬ = collections.Counter()
НЕВІДОМІ = collections.Counter()               # виклик поза продуктом, що віддав М (для звіту)
ХТО_КЛИКАВ = collections.defaultdict(set)       # функція → {(викликач, файл, рядок, параметри з М)} — для `--звідки`
ДЖЕРЕЛА_МІСЦЯ = collections.defaultdict(set)     # (файл, рядок) → ключі: місця, де значення стає М (для звіту)


def джерельний(а, к):
    return а[1] and isinstance(к, str) and (к in КЛЮЧІ_A or к in КЛЮЧІ_B or к in ВКЛАДЕНІ_ДЖЕРЕЛА)


def читати(а, к):
    """Поле `к` (рядок, число чи None — невідомий ключ) значення `а`. Поле, назване у формі, — саме це поле, без М
    верху: верх із М і формою — злиття гілок (запис коду ⊔ текст моделі, `в` у `від_моделі` після розбору прози рук),
    і поле `вітрина` з такого злиття — поле запису коду, а не відповідь моделі (клас похибки вибірки 1712)."""
    if а[2] is not None and isinstance(к, (str, int)):
        явне = dict(а[2]).get(к)
        if явне is not None and явне != ЧИСТЕ:
            return J(явне, (М_A if к in КЛЮЧІ_A else М_B if к in КЛЮЧІ_B else ВКЛАДЕНІ_ДЖЕРЕЛА.get(к, ЧИСТЕ))
                     if а[1] and isinstance(к, str) else ЧИСТЕ)
    р = М_(а[0])
    if а[1] and isinstance(к, str):
        р = J(р, М_A if к in КЛЮЧІ_A else М_B if к in КЛЮЧІ_B else ВКЛАДЕНІ_ДЖЕРЕЛА.get(к, ЧИСТЕ))
    if а[2] is not None:
        д = dict(а[2])
        if к is None:
            р = J(р, Jвсі(д.values()))
        else:
            р = J(р, J(д.get(к, ЧИСТЕ), д.get('*', ЧИСТЕ)))
    return р


def ітерувати(а):
    """Елемент при обході: М — М; список/кортеж — елементи (`*`, номери); словник коду — ключі (код). Елементи, названі
    у формі, — лише вони, без М верху (те саме злиття гілок, що в `читати`)."""
    ел = Jвсі(в for к, в in (а[2] or ()) if к == '*' or isinstance(к, int))
    if ел != ЧИСТЕ:
        return ел
    return М_(а[0])


def значення_(а):
    return J(М_(а[0]), Jвсі(в for _, в in (а[2] or ())))


def з_choices(е):
    """`…["choices"][0]["message"]` — тіло відповіді сервера моделі форми OpenAI."""
    кл = {х.value for х in ast.walk(е) if isinstance(х, ast.Constant) and isinstance(х.value, str)}
    return 'choices' in кл and 'message' in кл


ОПИСОВІ_ВБУДОВАНІ = {'len', 'type', 'isinstance', 'issubclass', 'repr', 'id', 'callable', 'bool', 'hasattr', 'hash',
                     'any', 'all', 'print', 'range', 'open', 'vars', 'dir', 'locals', 'globals', 'object', 'super'}
РЯДКОВІ_МЕТОДИ = {'strip', 'lstrip', 'rstrip', 'lower', 'upper', 'casefold', 'title', 'capitalize', 'replace', 'split',
                  'rsplit', 'splitlines', 'partition', 'rpartition', 'group', 'groups', 'groupdict', 'encode', 'decode',
                  'removeprefix', 'removesuffix', 'translate', 'expandtabs', 'zfill', 'ljust', 'rjust', 'center'}
БУЛЕВІ_МЕТОДИ = {'startswith', 'endswith', 'isdigit', 'isnumeric', 'isalpha', 'isalnum', 'isidentifier', 'isdecimal',
                 'isspace', 'islower', 'isupper', 'istitle', 'count', 'index', 'find', 'rfind', 'format', 'format_map',
                 'issubset', 'issuperset', 'isdisjoint', '__contains__'}
МУТАТОРИ = {'append', 'add', 'insert', 'extend', 'update', 'appendleft', 'extendleft'}
РЕГУЛЯРНІ_МЕТОДИ = {'match', 'search', 'fullmatch', 'finditer', 'findall', 'sub', 'subn', 'split', 'group', 'groups',
                    'groupdict', 'expand', 'normalize', 'casefold'}
ПЕРЕНОС_АРГУМЕНТУ = {'злам': 2}          # `поломки_ядро.злам(код, точка, справне, …)` поза обсягом віддає `справне`
ВБУДОВАНІ_МЕТОДИ = {'get', 'pop', 'setdefault', 'items', 'values', 'keys', 'copy', 'join', 'format', 'sort', 'index',
                    'count', 'append', 'add', 'insert', 'extend', 'update', 'remove', 'discard', 'clear', 'strip',
                    'split', 'replace', 'lower', 'upper', 'startswith', 'endswith', 'match', 'search', 'sub', 'group'}
МЕТОДИ = {}                              # імʼя методу класу продукту → Fn, коли імʼя єдине


def ключ_(мод, е):
    к = стала(мод, е) if мод is not None else (е.value if isinstance(е, ast.Constant) else None)
    return к if isinstance(к, (str, int)) else '*'


def шлях_приймача(е, мод=None):
    """`x["a"].setdefault("b", [])` → ('x', ['a', 'b']); інше (атрибути, виклики) → None."""
    ключі = []
    while True:
        if isinstance(е, ast.Name):
            return е.id, ключі[::-1]
        if isinstance(е, ast.Subscript):
            с_ = е.slice
            ключі.append(ключ_(мод, с_))
            е = е.value
        elif isinstance(е, ast.Call) and isinstance(е.func, ast.Attribute) and е.func.attr in ('setdefault', 'get') and е.args:
            а = е.args[0]
            ключі.append(ключ_(мод, а))
            е = е.func.value
        else:
            return None


МЕМО, В_РОБОТІ, ШИРОКИЙ, КОНТЕКСТИ, АНАЛІЗИ = {}, {}, {}, collections.defaultdict(set), []
СТЕК = []


def аналіз(g, кт):
    """Повернення функції `g` за абстрактних аргументів `кт` (контекстно; понад 8 контекстів — один широкий)."""
    if any(в != ЧИСТЕ for в in кт) and len(КОНТЕКСТИ[g]) >= 6 and кт not in КОНТЕКСТИ[g]:
        ш = ШИРОКИЙ.get(g, tuple(ЧИСТЕ for _ in кт))
        кт = tuple(J(а, б) for а, б in zip(ш, кт))
        if кт != ш:
            РОЗШИРЕНЬ[g] += 1
            if РОЗШИРЕНЬ[g] > int(os.environ.get("LICHBA_CAP", "3")):           # межа росту: далі форма параметра — лише верхні поля
                кт = tuple(зрізати(в, 1) for в in кт)
        ШИРОКИЙ[g] = кт
    ключ = (g, кт)
    if ключ in МЕМО:
        return МЕМО[ключ]
    if ключ in В_РОБОТІ or len(СТЕК) > 40:
        return В_РОБОТІ.get(ключ, ЧИСТЕ)
    КОНТЕКСТИ[g].add(кт)
    if os.environ.get('LICHBA_PROGRESS') and len(МЕМО) % 2000 == 0:
        print('аналізів %d · %s' % (len(МЕМО), g.імʼя), file=sys.stderr, flush=True)
    В_РОБОТІ[ключ] = ЧИСТЕ
    СТЕК.append(ключ)
    а = Аналіз(g, кт)
    try:
        а.прогін()
    finally:
        СТЕК.pop()
        del В_РОБОТІ[ключ]
    МЕМО[ключ] = а.ret
    if а.є_м:
        АНАЛІЗИ.append(а)
    return а.ret


СТРУКТУРНІ = {}
РЕЄСТР_РОЗБОРУ = {}         # назва схеми відповіді → {'розбір'|'сторож': Fn} (`схеми_розбору.РОЗБІР`)


def fn_з_виразу(мод, е):
    if isinstance(е, ast.Name):
        return функція_модуля(мод, е.id)
    if isinstance(е, ast.Attribute) and isinstance(е.value, ast.Name) and е.value.id in мод.імпорти:
        м, і = мод.імпорти[е.value.id]
        if і is None and м in МОДУЛІ:
            return функція_модуля(МОДУЛІ[м], е.attr)
    return None


def зібрати_реєстр_розбору():
    """`схеми_розбору.РОЗБІР` — реєстр розбору відповіді моделі: `схема.виконати_розбір(текст)` викликає
    `self.розбір`, і без реєстру потік від відповіді моделі не заходив у самі розбори (і вертав вхід як є)."""
    РЕЄСТР_РОЗБОРУ.clear()
    мод = МОДУЛІ.get('схеми_розбору')
    if мод is None:
        return
    for н in мод.дерево.body:
        if isinstance(н, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == 'РОЗБІР' for ц in н.targets) \
                and isinstance(н.value, ast.Dict):
            for к, в in zip(н.value.keys, н.value.values):
                if isinstance(к, ast.Constant) and isinstance(в, ast.Call):
                    РЕЄСТР_РОЗБОРУ[к.value] = {кв.arg: fn_з_виразу(мод, кв.value) for кв in в.keywords
                                               if fn_з_виразу(мод, кв.value) is not None}


def структурна(fn):
    """Рекурсивний обхід значення по полях, що вертає ту саму будову (`без_ід_глибоко(x)`, `_без_правила(x)`:
    `x` | `{k: f(v) for k, v in x.items()}` | `[f(v) for v in x]` | перетворення листка `g(x)`) → імʼя параметра;
    інакше None. Його повернення — сам аргумент: контексти рекурсії зливали вердикт коду з його листками, і кожне
    поле вердикта на дроті читалось відповіддю моделі (клас похибки вибірки 1712)."""
    if fn in СТРУКТУРНІ:
        return СТРУКТУРНІ[fn]
    СТРУКТУРНІ[fn] = None
    if not fn.параметри or fn.параметри[0] == 'self':
        return None
    п = fn.параметри[0]
    сам = fn.імʼя
    повернення = [н.value for н in ast.walk(fn.вузол) if isinstance(н, ast.Return) and н.value is not None]
    if not повернення:
        return None
    викликає_себе = any(isinstance(н, ast.Call) and isinstance(н.func, ast.Name) and н.func.id == сам
                        for н in ast.walk(fn.вузол))
    if not викликає_себе:
        return None

    def лист(е, ім):
        if isinstance(е, ast.Name):
            return е.id == ім
        if isinstance(е, ast.IfExp):
            return лист(е.body, ім) and лист(е.orelse, ім)
        if isinstance(е, ast.Call):
            арги = е.args + [к.value for к in е.keywords]
            return bool(арги) and лист(арги[0], ім) and all(not isinstance(а, ast.Name) or а.id != ім for а in арги[1:])
        return False

    def будова(е):
        if лист(е, п):
            return True
        if isinstance(е, ast.IfExp):
            return будова(е.body) and будова(е.orelse)
        if isinstance(е, (ast.DictComp, ast.ListComp, ast.GeneratorExp, ast.SetComp)) and len(е.generators) == 1:
            г = е.generators[0]
            it = г.iter
            if isinstance(it, ast.Call) and isinstance(it.func, ast.Attribute) and it.func.attr in ('items', 'values'):
                it = it.func.value
            if not (isinstance(it, ast.Name) and it.id == п):
                return False
            ел = г.target.elts[-1] if isinstance(г.target, ast.Tuple) else г.target
            if not isinstance(ел, ast.Name):
                return False
            тіло = е.value if isinstance(е, ast.DictComp) else е.elt
            return лист(тіло, ел.id) or (isinstance(тіло, ast.IfExp) and all(
                лист(х, ел.id) or isinstance(х, ast.Name) and х.id == ел.id for х in (тіло.body, тіло.orelse)))
        if isinstance(е, ast.Call) and isinstance(е.func, ast.Name) and е.func.id in ('list', 'tuple', 'dict') and е.args:
            return будова(е.args[0])
        return False
    if all(будова(е) for е in повернення):
        СТРУКТУРНІ[fn] = п
    return СТРУКТУРНІ[fn]


def злити(а, б):
    """Середовище після злиття двох гілок; None — гілка не доходить (return, raise)."""
    if а is None:
        return б
    if б is None:
        return а
    return {к: J(а.get(к, ЧИСТЕ), б.get(к, ЧИСТЕ)) for к in а.keys() | б.keys()}


class Аналіз:
    """Одна функція за одного контексту: середовище імен за порядком тексту (присвоєння імені замінює значення,
    гілки зливаються, цикл — до нерухомої точки), значення кожного виразу в місці, де його обчислено, повернення.
    Крок 16239: середовище без порядку зливало в одне імʼя все, що йому присвоювали у великій функції (`об`, `в`,
    `р` у `від_моделі` — і відповідь моделі, і запис коду), тож корінь брав запис коду."""
    def __init__(с, fn, кт):
        с.fn, с.кт = fn, кт
        с.env = {}
        с.бачено = {}
        с.схеми = {}             # імʼя → назва схеми відповіді (None — невідома) після `схема_за_назвою(…)`
        for п, в in zip(fn.параметри, кт):
            if в != ЧИСТЕ:
                с.env[п] = в
        с.ret = ЧИСТЕ
        с.є_м = any(в != ЧИСТЕ for в in кт)

    def прогін(с):
        с.викон(с.fn.вузол.body)
        с.є_м = с.є_м or any(усе_м(в) or в[1] for в in с.бачено.values())

    def т(с, е):
        """Чи E — значення з відповіді моделі в тому місці, де його перевіряють (для `знайти_перевірки`)."""
        return bool(с.бачено.get(е, ЧИСТЕ)[0])

    def джерело(с, е):
        return ''.join(sorted(с.бачено.get(е, ЧИСТЕ)[0]))

    # ── присвоєння ──
    def до(с, імʼя, в):
        if в == ЧИСТЕ:
            с.env.pop(імʼя, None)
        else:
            с.env[імʼя] = в

    def зберегти(с, приймач, в):
        """Запис у поле контейнера не замінює контейнер, а додає до нього."""
        шл = шлях_приймача(приймач, с.fn.мод)
        if шл is None or в == ЧИСТЕ:
            return
        корінь, ключі = шл
        for к in reversed(ключі):
            в = Ш({к: в})
        с.env[корінь] = J(с.env.get(корінь, ЧИСТЕ), в)

    def присвоїти(с, ц, в):
        if isinstance(ц, ast.Name):
            с.до(ц.id, в)
        elif isinstance(ц, (ast.Tuple, ast.List)):
            for і, ці in enumerate(ц.elts):
                if isinstance(ці, ast.Starred):
                    с.присвоїти(ці.value, Ш({'*': ітерувати(в)}))
                else:
                    с.присвоїти(ці, читати(в, і))
        elif isinstance(ц, ast.Subscript):
            с.ev(ц.slice)
            к = ключ_(с.fn.мод, ц.slice)
            с.зберегти(ц.value, Ш({к: в}))
        elif isinstance(ц, ast.Starred):
            с.присвоїти(ц.value, в)

    # ── стейтменти ──
    def гілка(с, тіло, env):
        с.env = dict(env) if env is not None else None
        с.викон(тіло)
        return с.env

    def петля(с, до_, тіло, ціль=None, iter_=None):
        """Тіло циклу до нерухомої точки середовища на вході; після — злиття входу (нуль обертів) і виходу."""
        вхід = dict(до_)
        вихід = None
        for _ in range(4):
            с.env = dict(вхід)
            if ціль is not None:
                с.присвоїти(ціль, ітерувати(с.ev(iter_)))
            с.викон(тіло)
            вихід = с.env
            нове = злити(вхід, вихід)
            if нове == вхід:
                break
            вхід = нове
        return злити(вхід, вихід)

    def викон(с, тіло):
        for s in тіло:
            if с.env is None:
                return
            t = type(s)
            if t in (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef):
                continue
            if t is ast.Assign:
                в = с.ev(s.value)
                for ц in s.targets:
                    с.присвоїти(ц, в)
                    if isinstance(ц, ast.Name):
                        сх = с.назва_схеми(s.value)
                        if сх is not False:
                            с.схеми[ц.id] = сх
                        else:
                            с.схеми.pop(ц.id, None)
            elif t is ast.AnnAssign:
                if s.value is not None:
                    с.присвоїти(s.target, с.ev(s.value))
            elif t is ast.AugAssign:
                в = с.ev(s.value)
                с.присвоїти(s.target, J(с.env.get(s.target.id, ЧИСТЕ), в) if isinstance(s.target, ast.Name) else в)
            elif t in (ast.For, ast.AsyncFor):
                с.env = с.петля(с.env, s.body, s.target, s.iter)
                с.викон(s.orelse)
            elif t is ast.While:
                с.ev(s.test)
                с.env = с.петля(с.env, [ast.Expr(s.test)] + s.body)
                с.викон(s.orelse)
            elif t is ast.If:
                с.ev(s.test)
                до_ = с.env
                с.env = злити(с.гілка(s.body, до_), с.гілка(s.orelse, до_))
            elif t in (ast.With, ast.AsyncWith):
                for і in s.items:
                    в = с.ev(і.context_expr)
                    if і.optional_vars is not None:
                        с.присвоїти(і.optional_vars, в)
                с.викон(s.body)
            elif t.__name__ in ('Try', 'TryStar'):
                до_ = с.env
                після = с.гілка(s.body, до_)
                будь_де = злити(до_, після)      # виняток — з будь-якого місця тіла
                після = с.гілка(s.orelse, після)
                for h in s.handlers:
                    після = злити(після, с.гілка(h.body, будь_де))
                с.env = після if після is not None else None
                if s.finalbody:
                    с.env = с.гілка(s.finalbody, злити(після, будь_де) if після is None else після)
                    if після is None:
                        с.env = None
            elif t is ast.Return:
                if s.value is not None:
                    с.ret = J(с.ret, с.ev(s.value))
                с.env = None
            elif t is ast.Expr:
                с.ev(s.value)
            elif t is ast.Raise:
                if s.exc is not None:
                    с.ev(s.exc)
                с.env = None
            elif t is ast.Assert:
                с.ev(s.test)
            elif t.__name__ == 'Match':
                с.ev(s.subject)
                до_ = с.env
                після = до_
                for кейс in s.cases:
                    після = злити(після, с.гілка(кейс.body, до_))
                с.env = після

    # ── вирази ──
    def ev(с, е):
        р = с.ev_(е)
        if р != ЧИСТЕ:
            с.бачено[е] = J(с.бачено.get(е, ЧИСТЕ), р)
        return р

    def ev_(с, е):
        t = type(е)
        if t is ast.Name:
            return с.env.get(е.id, ЧИСТЕ)
        if t is ast.Constant:
            return ЧИСТЕ
        if t is ast.Attribute:
            return М_(с.ev(е.value)[0])
        if t is ast.Subscript:
            б = с.ev(е.value)
            сл = е.slice
            if isinstance(сл, ast.Slice):
                return б
            кс = стала(с.fn.мод, сл)
            if кс is not None:
                if кс == 'content' and з_choices(е.value):
                    ДЖЕРЕЛА_МІСЦЯ[(с.fn.мод.шлях, е.lineno)].add('choices→message→content')
                    return М_A
                if джерельний(б, кс):
                    ДЖЕРЕЛА_МІСЦЯ[(с.fn.мод.шлях, е.lineno)].add(кс)
                return читати(б, кс)
            с.ev(сл)
            return читати(б, None)
        if t is ast.Call:
            return с.виклик(е)
        if t is ast.BoolOp:
            return Jвсі(с.ev(х) for х in е.values)
        if t is ast.IfExp:
            с.ev(е.test)
            return J(с.ev(е.body), с.ev(е.orelse))
        if t is ast.Compare:
            с.ev(е.left)
            for х in е.comparators:
                с.ev(х)
            return ЧИСТЕ
        if t is ast.UnaryOp:
            в = с.ev(е.operand)
            return ЧИСТЕ if isinstance(е.op, ast.Not) else в
        if t is ast.BinOp:
            л, п = с.ev(е.left), с.ev(е.right)
            if isinstance(е.op, ast.Mod) and isinstance(е.left, ast.Constant) and isinstance(е.left.value, str):
                return ЧИСТЕ
            return J(л, п)
        if t is ast.JoinedStr:
            for х in е.values:
                if isinstance(х, ast.FormattedValue):
                    с.ev(х.value)
            return ЧИСТЕ
        if t is ast.Dict:
            д = {}
            for к, в in zip(е.keys, е.values):
                вв = с.ev(в)
                if к is None:
                    д = {'**': J(д.get('**', ЧИСТЕ), вв)} | д
                    continue
                кк = ключ_(с.fn.мод, к)
                if кк == '*':
                    с.ev(к)
                д[кк] = J(д.get(кк, ЧИСТЕ), вв)
            розгорнуте = д.pop('**', ЧИСТЕ)
            return J(розгорнуте, Ш(д))
        if t in (ast.List, ast.Set):
            return Ш({'*': Jвсі(ітерувати(с.ev(х.value)) if isinstance(х, ast.Starred) else с.ev(х) for х in е.elts)})
        if t is ast.Tuple:
            if any(isinstance(х, ast.Starred) for х in е.elts):
                return Ш({'*': Jвсі(ітерувати(с.ev(х.value)) if isinstance(х, ast.Starred) else с.ev(х) for х in е.elts)})
            return Ш({і: с.ev(х) for і, х in enumerate(е.elts)})
        if t in (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp):
            зовні = dict(с.env)                  # імена генератора — своя область
            try:
                return с.генератор(е, t)
            finally:
                с.env = зовні
        return с.ev_інше(е, t)

    def генератор(с, е, t):
        if True:
            for г in е.generators:
                с.присвоїти(г.target, ітерувати(с.ev(г.iter)))
                for у in г.ifs:
                    с.ev(у)
            if t is ast.DictComp:
                # копія словника з відсівом ключів (`{к: в for к, в in X.items() if …}`) — той самий X: поле лишається
                # своїм полем (і запит — запитом), а не зливається в «будь-який ключ» (клас похибки вибірки 1712)
                г = е.generators[0]
                if (len(е.generators) == 1 and isinstance(г.iter, ast.Call) and isinstance(г.iter.func, ast.Attribute)
                        and г.iter.func.attr == 'items' and isinstance(г.target, ast.Tuple) and len(г.target.elts) == 2
                        and all(isinstance(х, ast.Name) for х in г.target.elts) and isinstance(е.key, ast.Name)
                        and е.key.id == г.target.elts[0].id):
                    джерело_ = с.ev(г.iter.func.value)
                    if isinstance(е.value, ast.Name) and е.value.id == г.target.elts[1].id:
                        return джерело_
                    if джерело_[1]:
                        return J((Ø, True, None), Ш({'*': с.ev(е.value)}))
                return Ш({'*': J(с.ev(е.key), с.ev(е.value))})
            return Ш({'*': с.ev(е.elt)})

    def ev_інше(с, е, t):
        if t is ast.NamedExpr:
            в = с.ev(е.value)
            с.присвоїти(е.target, в)
            return в
        if t in (ast.Await, ast.Starred, ast.YieldFrom, ast.FormattedValue):
            return с.ev(е.value)
        if t is ast.Yield:
            в = с.ev(е.value) if е.value is not None else ЧИСТЕ
            с.ret = J(с.ret, Ш({'*': в}))
            return ЧИСТЕ
        return ЧИСТЕ

    def виклик(с, е):
        ав = [ітерувати(с.ev(а.value)) if isinstance(а, ast.Starred) else с.ev(а) for а in е.args]
        кв = {к.arg: с.ev(к.value) for к in е.keywords}
        g = вирішити(с.fn.мод, е)
        f = е.func
        if g is not None:
            return с.до_функції(g, ав, кв, е)
        if isinstance(f, ast.Attribute):
            модульний = isinstance(f.value, ast.Name) and f.value.id in с.fn.мод.імпорти and f.value.id not in (с.env or {})
            if модульний:
                return с.вбудована(f.attr, ав, кв)
            if f.attr in ('виконати_розбір', 'перевірити'):
                сх = с.назва_схеми(f.value)
                if сх is not False:
                    с.ev(f.value)
                    return с.розбір_схеми(сх, f.attr, ав, кв, е)
            п = с.ev(f.value)
            мт = МЕТОДИ.get(f.attr)
            if мт is not None and f.attr not in ВБУДОВАНІ_МЕТОДИ | РЯДКОВІ_МЕТОДИ | РЕГУЛЯРНІ_МЕТОДИ | МУТАТОРИ:
                # метод класу продукту (за єдиним іменем): `схема.прочитати(відповідь)` — self — приймач
                return с.до_функції(мт, [п] + ав, кв, е, зсув=True)
            return с.метод(f.attr, п, ав, кв, е)
        if isinstance(f, ast.Name):
            return с.вбудована(f.id, ав, кв)
        с.ev(f)
        return с.невідомий('(вираз)', ав + list(кв.values()))

    def назва_схеми(с, е):
        """Вираз схеми відповіді → її назва (None — невідома: `визначити_схему(d)`); не схема — False."""
        if isinstance(е, ast.Name):
            return с.схеми.get(е.id, False)
        if isinstance(е, ast.Call) and ім_виклику(е) in ('схема_за_назвою', 'визначити_схему'):
            if ім_виклику(е) == 'схема_за_назвою' and е.args:
                к = стала(с.fn.мод, е.args[0])
                return к if isinstance(к, str) else None
            return None
        if isinstance(е, ast.Subscript) and isinstance(е.value, ast.Name) and е.value.id == 'СХЕМИ_ВІДПОВІДІ':
            к = стала(с.fn.мод, е.slice)
            return к if isinstance(к, str) else None
        return False

    def розбір_схеми(с, сх, метод, ав, кв, е):
        роль = 'розбір' if метод == 'виконати_розбір' else 'сторож'
        записи = [РЕЄСТР_РОЗБОРУ[сх]] if сх in РЕЄСТР_РОЗБОРУ else ([] if сх is not None else list(РЕЄСТР_РОЗБОРУ.values()))
        р = ЧИСТЕ
        for зап in записи:
            g = зап.get(роль)
            if g is not None:
                р = J(р, с.до_функції(g, ав, кв, е))
        if роль == 'розбір' and (сх is None or роль not in РЕЄСТР_РОЗБОРУ.get(сх, {})):
            р = J(р, ав[0] if ав else ЧИСТЕ)      # схема без розбору вертає вхід як є
        return р

    def до_функції(с, g, ав, кв, е, зсув=False):
        стр = структурна(g)
        if стр is not None and g is с.fn:
            # обхід самого себе по полях — та сама будова: поле лишається полем, листок — листком
            return ав[0] if ав else ЧИСТЕ
        кт = [ЧИСТЕ] * len(g.параметри)
        if not any(isinstance(а, ast.Starred) for а in е.args):
            for і, в in enumerate(ав[:len(кт)]):
                кт[і] = в
        for к, в in кв.items():
            if к in g.параметри:
                кт[g.параметри.index(к)] = в
        if any(усе_м(в) for в in кт):
            ХТО_КЛИКАВ[g].add((с.fn.імʼя, с.fn.мод.шлях, е.lineno, tuple(п for п, в in zip(g.параметри, кт) if усе_м(в))))
        р = аналіз(g, tuple(кт))
        return кт[0] if стр is not None else р

    def невідомий(с, ім, усі):
        """Виклик поза продуктом і поза переліком переносу: новий запис коду, а не те саме значення (крок 16239: М
        несе рух даних, а не обчислення). Обірване М лічиться для звіту."""
        if any(в[0] or усе_м(в) for в in усі):
            НЕВІДОМІ[ім] += 1
        return ЧИСТЕ

    def вбудована(с, ім, ав, кв):
        усі = ав + list(кв.values())
        м = frozenset().union(*(в[0] for в in усі)) if усі else Ø
        if ім in ОПИСОВІ_ВБУДОВАНІ:
            return ЧИСТЕ
        if ім == 'dict':
            return J(ав[0] if ав else ЧИСТЕ, J(кв.pop(None, ЧИСТЕ), Ш({к: в for к, в in кв.items() if к})))
        if ім in ('list', 'tuple', 'set', 'frozenset', 'sorted', 'reversed', 'deque', 'OrderedDict', 'Counter'):
            return J(М_(ав[0][0]), Ш({'*': ітерувати(ав[0])})) if ав else ЧИСТЕ
        if ім == 'dumps':          # рядок JSON несе ту саму будову, що й значення: `loads(dumps(x))` — це x, а не М скрізь
            return ав[0] if ав else ЧИСТЕ
        if ім in ('str', 'int', 'float', 'abs', 'round', 'Decimal', 'Fraction', 'normalize', 'unescape', 'escape',
                  'sub', 'match', 'fullmatch', 'search', 'findall', 'finditer', 'split', 'quote', 'unquote'):
            return М_(м)
        if ім == 'enumerate':
            return Ш({'*': Ш({0: ЧИСТЕ, 1: ітерувати(ав[0])})}) if ав else ЧИСТЕ
        if ім == 'zip':
            return Ш({'*': Ш({і: ітерувати(а) for і, а in enumerate(ав)})})
        if ім == 'next':
            return J(ітерувати(ав[0]) if ав else ЧИСТЕ, ав[1] if len(ав) > 1 else ЧИСТЕ)
        if ім == 'iter':
            return ав[0] if ав else ЧИСТЕ
        if ім == 'filter':
            return Ш({'*': ітерувати(ав[1])}) if len(ав) > 1 else ЧИСТЕ
        if ім == 'map':
            return Ш({'*': М_(ітерувати(ав[-1])[0])}) if ав else ЧИСТЕ
        if ім in ('min', 'max'):
            return J(ітерувати(ав[0]) if len(ав) == 1 else Jвсі(ав), кв.get('default', ЧИСТЕ))
        if ім == 'sum':
            return М_(ітерувати(ав[0])[0]) if ав else ЧИСТЕ
        if ім in ('deepcopy', 'copy'):
            return ав[0] if ав else ЧИСТЕ
        if ім in ('loads', 'literal_eval'):
            return ав[0] if ав else ЧИСТЕ
        if ім in ('getattr',):
            return М_(ав[0][0]) if ав else ЧИСТЕ
        if ім in ПЕРЕНОС_АРГУМЕНТУ:
            і = ПЕРЕНОС_АРГУМЕНТУ[ім]
            return ав[і] if len(ав) > і else кв.get('справне', ЧИСТЕ)
        if ім == 'fromkeys':
            return Ш({'*': ітерувати(ав[0])}) if ав else ЧИСТЕ
        return с.невідомий(ім, усі)

    def метод(с, ім, п, ав, кв, е):
        f = е.func
        if ім in ('get', 'pop'):
            к = стала(с.fn.мод, е.args[0]) if е.args else None
            if к == 'content' and з_choices(f.value):
                ДЖЕРЕЛА_МІСЦЯ[(с.fn.мод.шлях, е.lineno)].add('choices→message→content')
                return М_A
            if джерельний(п, к):
                ДЖЕРЕЛА_МІСЦЯ[(с.fn.мод.шлях, е.lineno)].add(к)
            return J(читати(п, к), ав[1] if len(ав) > 1 else ЧИСТЕ)
        if ім == 'setdefault':
            к = ключ_(с.fn.мод, е.args[0]) if е.args else '*'
            if len(ав) > 1:
                с.зберегти(f.value, Ш({к: ав[1]}))
            return J(читати(п, к if к != '*' else None), ав[1] if len(ав) > 1 else ЧИСТЕ)
        if ім == 'items':
            return J(М_(п[0]), Ш({'*': Ш({0: ЧИСТЕ, 1: значення_(п)})}))
        if ім == 'values':
            return J(М_(п[0]), Ш({'*': значення_(п)}))
        if ім == 'keys':
            return М_(п[0])
        if ім in ('copy', '__copy__'):
            return п
        if ім in МУТАТОРИ:
            if ім in ('append', 'add', 'appendleft') and ав:
                с.зберегти(f.value, Ш({'*': ав[0]}))
            elif ім == 'insert' and len(ав) > 1:
                с.зберегти(f.value, Ш({'*': ав[1]}))
            elif ім in ('extend', 'extendleft') and ав:
                с.зберегти(f.value, Ш({'*': ітерувати(ав[0])}))
            elif ім == 'update':
                с.зберегти(f.value, J(ав[0] if ав else ЧИСТЕ, Ш({к: в for к, в in кв.items() if к})))
            return ЧИСТЕ
        if ім in РЯДКОВІ_МЕТОДИ:
            return М_(п[0])
        if ім == 'join':
            return М_(ітерувати(ав[0])[0]) if ав else ЧИСТЕ
        if ім in БУЛЕВІ_МЕТОДИ:
            return ЧИСТЕ
        if ім in РЕГУЛЯРНІ_МЕТОДИ:        # шматок того самого тексту: `_RE.match(текст)`, `м.group(1)`
            return М_(frozenset().union(п[0], *(в[0] for в in ав)))
        if ім == 'fromkeys':
            return Ш({'*': ітерувати(ав[0])}) if ав else ЧИСТЕ
        return с.невідомий('.' + ім, [п] + ав + list(кв.values()))


def ендпойнти():
    """Функції, які кличе показ: значення словника `bridge.виклик` і виклики з `вхід` у `bridge.виклик_а`."""
    б = МОДУЛІ.get('bridge')
    res = []
    if б is None:
        return res
    for ім in ('виклик', 'виклик_а'):
        fn = б.функції.get(ім)
        if fn is None:
            continue
        for х in ast.walk(fn.вузол):
            імена = []
            if isinstance(х, ast.Dict):
                імена = [в.id for в in х.values if isinstance(в, ast.Name)]
            elif isinstance(х, ast.Call) and isinstance(х.func, ast.Name) and any(
                    isinstance(а, ast.Name) and а.id == 'вхід' for а in х.args) and х.func.id not in ('виклик',):
                імена = [х.func.id]
            for і in імена:
                g = вирішити(б, ast.Call(func=ast.Name(id=і, ctx=ast.Load()), args=[], keywords=[]))
                if g is not None and g not in res:
                    res.append(g)
    return res


def потік_від_моделі():
    """Аналіз: ендпойнти з ЗАПИТ у першому параметрі, потім кожна функція продукту з чистими аргументами (джерело (2)
    і повернення М із глибини). → [Аналіз] із М у середовищі."""
    for таб in (МЕМО, В_РОБОТІ, ШИРОКИЙ, КОНТЕКСТИ, ДЖЕРЕЛА_МІСЦЯ, ХТО_КЛИКАВ, РОЗШИРЕНЬ, НЕВІДОМІ):
        таб.clear()
    del АНАЛІЗИ[:]
    sys.setrecursionlimit(20000)
    for g in ендпойнти():
        аналіз(g, (ЗАПИТ,) + tuple(ЧИСТЕ for _ in g.параметри[1:]))
    for мод in МОДУЛІ.values():
        for fn in sorted(set(мод.функції.values()), key=lambda f: f.вузол.lineno):
            аналіз(fn, tuple(ЧИСТЕ for _ in fn.параметри))
    return АНАЛІЗИ


# ───────────────────────── перевірки ─────────────────────────
_ВГЛИБ = set()


def табличний(fn, c):
    """Чи C — перелік/таблиця коду (а не динамічна колекція відповіді): стала модуля, імпортована, літерал із ≥2
    рядків/чисел, `…["enum"]`, параметр, якому виклики дають таблицю, локальне імʼя, зібране з таблиці."""
    мод = fn.мод
    if isinstance(c, ast.Name):
        if c.id in мод.імпорти:
            м, і = мод.імпорти[c.id]
            return і is not None and м in МОДУЛІ and і in МОДУЛІ[м].сталі
        return c.id in мод.сталі or c.id in fn.табл_парам or c.id in fn.табл_локалі
    if isinstance(c, ast.Attribute):
        if isinstance(c.value, ast.Name) and c.value.id in мод.імпорти:
            м, і = мод.імпорти[c.value.id]
            ц = і or м
            return ц in МОДУЛІ and c.attr in МОДУЛІ[ц].сталі
        return isinstance(c.value, ast.Name) and c.value.id in мод.сталі
    if isinstance(c, (ast.Tuple, ast.List, ast.Set)):
        return len(c.elts) >= 2 and all(isinstance(х, ast.Constant) for х in c.elts)
    if isinstance(c, ast.BinOp):
        return табличний(fn, c.left) or табличний(fn, c.right)
    if isinstance(c, ast.BoolOp):
        return any(табличний(fn, x) for x in c.values)
    if isinstance(c, ast.IfExp):
        return табличний(fn, c.body) or табличний(fn, c.orelse)
    if isinstance(c, ast.Subscript):
        k = c.slice
        return (isinstance(k, ast.Constant) and k.value in ТАБЛИЧНІ_КЛЮЧІ) or \
            (isinstance(c.value, ast.Name) and c.value.id in мод.сталі)
    if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in fn.табл_виклики:
        return True
    if isinstance(c, ast.Call):
        g = вирішити(мод, c)
        if g is not None and g not in _ВГЛИБ:
            повернення = [x.value for x in ast.walk(g.вузол) if isinstance(x, ast.Return) and x.value is not None]
            _ВГЛИБ.add(g)
            try:
                if повернення and all(табличний(g, x) for x in повернення):
                    return True
            finally:
                _ВГЛИБ.discard(g)
    if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == 'get':
        if c.args and isinstance(c.args[0], ast.Constant) and c.args[0].value in ТАБЛИЧНІ_КЛЮЧІ:
            return True
        return табличний(fn, c.func.value) and isinstance(c.func.value, (ast.Name, ast.Attribute, ast.Call))
    if isinstance(c, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return any(табличний(fn, г.iter) for г in c.generators)
    return False


def табличні_локалі(fn):
    for _ in range(2):
        for н in ast.walk(fn.вузол):
            if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
                if isinstance(н.value, ast.Lambda) and табличний(fn, н.value.body):
                    fn.табл_виклики.add(н.targets[0].id)
                elif табличний(fn, н.value):
                    fn.табл_локалі.add(н.targets[0].id)


def табличні_параметри():
    """Параметр — таблиця коду, коли КОЖЕН виклик у продукті дає йому таблицю (стала, `…["enum"]`, зібране з таблиці)."""
    for _ in range(4):
        усього, табл = collections.Counter(), collections.Counter()
        for мод in МОДУЛІ.values():
            for fn in set(мод.функції.values()):
                табличні_локалі(fn)
                for в in ast.walk(fn.вузол):
                    if isinstance(в, ast.Call):
                        g = вирішити(мод, в)
                        if g is None:
                            continue
                        пари = [(g.параметри[і], а) for і, а in enumerate(в.args) if і < len(g.параметри)]
                        пари += [(к.arg, к.value) for к in в.keywords if к.arg in g.параметри]
                        for імʼя, а in пари:
                            усього[(id(g), імʼя)] += 1
                            if табличний(fn, а):
                                табл[(id(g), імʼя)] += 1
        змін = False
        for мод in МОДУЛІ.values():
            for g in set(мод.функції.values()):
                for п in g.параметри:
                    є = усього[(id(g), п)] > 0 and усього[(id(g), п)] == табл[(id(g), п)]
                    if є and п not in g.табл_парам:
                        g.табл_парам.add(п); змін = True
        if not змін:
            break


def знайти_перевірки(fn, п):
    """→ [(вузол_перевірки, E, вид, позитивна)] на зараженому E; позитивна — істина = значення прийняте."""
    мод = fn.мод
    res = []
    батьки = {}
    for н in ast.walk(fn.вузол):
        for д in ast.iter_child_nodes(н):
            батьки[д] = н
    fn.батьки = батьки

    def полярність(н):
        поз = True
        х = н
        while х in батьки:
            р = батьки[х]
            if isinstance(р, ast.UnaryOp) and isinstance(р.op, ast.Not):
                поз = not поз
            if isinstance(р, (ast.stmt, ast.IfExp, ast.comprehension)):
                break
            х = р
        return поз

    for н in ast.walk(fn.вузол):
        if isinstance(н, ast.Call) and isinstance(н.func, ast.Name) and н.func.id == 'isinstance' and len(н.args) == 2:
            if п.т(н.args[0]):
                # `isinstance(E, bool)` — виняток типу (bool ⊂ int): істина = відкинуто, полярність обернена (16233)
                виняток = isinstance(н.args[1], ast.Name) and н.args[1].id == 'bool'
                res.append((н, н.args[0], 'форма', полярність(н) != виняток))
        elif isinstance(н, ast.Compare):
            if len(н.ops) == 1 and isinstance(н.ops[0], (ast.In, ast.NotIn)):
                л, ц = н.left, н.comparators[0]
                if isinstance(л, ast.Constant):
                    continue
                if isinstance(ц, (ast.Tuple, ast.List, ast.Set)) and ц.elts and all(порожнє_значення(х) for х in ц.elts):
                    continue      # `E not in (None, "")` — непорожність, не перевірка значення (16233)
                if п.т(л) and not п.т(ц) and табличний(fn, ц):
                    поз = полярність(н) == isinstance(н.ops[0], ast.In)
                    res.append((н, л, 'перелік', поз))
            elif isinstance(н.left, ast.Call) and ім_виклику(н.left) == 'type' and н.left.args and п.т(н.left.args[0]):
                поз = isinstance(н.ops[0], (ast.Is, ast.Eq))
                res.append((н, н.left.args[0], 'форма', полярність(н) == поз))
        elif isinstance(н, ast.Call):
            ім = ім_виклику(н)
            if ім == 'get' and isinstance(н.func, ast.Attribute) and н.args and п.т(н.args[0]) and not п.т(н.func.value) \
                    and табличний(fn, н.func.value) and isinstance(н.func.value, (ast.Name, ast.Attribute, ast.Call)):
                res.append((н, н.args[0], 'перелік·пошук', полярність(н)))
            if ім in ('fullmatch', 'match') and isinstance(н.func, ast.Attribute) and len(н.args) >= 2 and п.т(н.args[1]):
                res.append((н, н.args[1], 'форма', полярність(н)))
            elif ім in ('fullmatch', 'match') and isinstance(н.func, ast.Attribute) and len(н.args) == 1 and п.т(н.args[0]):
                res.append((н, н.args[0], 'форма', полярність(н)))
            elif isinstance(н.func, ast.Attribute) and н.func.attr in ('isdigit', 'isnumeric', 'isalpha', 'isalnum',
                                                                       'isidentifier', 'isdecimal') and п.т(н.func.value):
                res.append((н, н.func.value, 'форма', полярність(н)))
        elif isinstance(н, ast.Try):
            ловить = [джерело_шляху(о.type) if о.type else '' for о in н.handlers]
            if any(('ValueError' in л or 'TypeError' in л) for л in ловить):
                for м in ast.walk(ast.Module(body=н.body, type_ignores=[])):
                    if isinstance(м, ast.Call) and ім_виклику(м) in ('int', 'float') and м.args and п.т(м.args[0]):
                        res.append((н, м.args[0], 'форма', True))
                        break
    return res


def ім_кореня(е):
    """Основа ланцюга читання (`x.get(к)[0]` → x), а не перше імʼя в обході вширину (там був би аргумент `к`)."""
    х = е
    while True:
        if isinstance(х, (ast.Subscript, ast.Attribute, ast.Starred)):
            х = х.value
        elif isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute):
            х = х.func.value
        elif isinstance(х, ast.Call) and isinstance(х.func, ast.Name) and х.args:
            х = х.args[0]
        elif isinstance(х, ast.BoolOp):
            х = х.values[0]
        elif isinstance(х, ast.IfExp):
            х = х.body
        else:
            break
    if isinstance(х, ast.Name):
        return х.id
    for х in ast.walk(е):
        if isinstance(х, ast.Name):
            return х.id
    return None


def поле_з(е):
    """Імʼя поля відповіді: останній рядковий ключ у ланцюгу читання E, інакше імʼя змінної."""
    кл = []
    х = е
    while True:
        if isinstance(х, ast.Subscript):
            if isinstance(х.slice, ast.Constant) and isinstance(х.slice.value, str):
                кл.append(х.slice.value)
            х = х.value
        elif isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr in ПЕРЕНОС_МЕТОДИ:
            if х.func.attr == 'get' and х.args and isinstance(х.args[0], ast.Constant) and isinstance(х.args[0].value, str):
                кл.append(х.args[0].value)
            х = х.func.value
        elif isinstance(х, ast.Attribute):
            х = х.value
        else:
            break
    if кл:
        return кл[0]
    return ім_кореня(е) or джерело_шляху(е)[:20]


def читає_імʼя(вузли, імʼя):
    for в in вузли:
        for х in ast.walk(в):
            if isinstance(х, ast.Name) and х.id == імʼя and isinstance(х.ctx, ast.Load):
                return True
    return False


# Читання значення ≠ опис значення: корінь у `type(…)`, `isinstance(…)`, `_як_звати(…)`, у повідомленні (`"…%s" % …`,
# f-рядок, `.format`) і в `raise` — це текст про відкинуте, а не його ведення далі (клас 16221); у генераторі й лямбді,
# що перепризначають те саме імʼя, читається вже інше значення (клас 16223, `ц` у `1524`).
ОПИСОВІ_ВИКЛИКИ = {'type', 'isinstance', 'repr', 'len', 'id', 'callable', '_як_звати', '_тип_en'}


def ключ_доступу(е, імʼя):
    """Перевірка поля `об.get("k")`/`об["k"]` → текст ключа: далі значення «читає» лише той самий доступ до поля чи ціла
    `об` (передана, повернена, переписана), а не будь-яке інше поле (`об.get("інше")`)."""
    х, ключ = е, None
    while True:
        if isinstance(х, ast.Subscript):
            if isinstance(х.value, ast.Name) and х.value.id == імʼя:
                ключ = ast.unparse(х.slice)
            х = х.value
        elif isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr == 'get' and х.args:
            if isinstance(х.func.value, ast.Name) and х.func.value.id == імʼя:
                ключ = ast.unparse(х.args[0])
            х = х.func.value
        elif isinstance(х, (ast.Attribute, ast.Starred)):
            х = х.value
        else:
            return ключ


def читає_значення(вузли, імʼя, ключ=None):
    if not імʼя:
        return False

    def ход(х):
        if ключ is not None:
            if isinstance(х, ast.Subscript) and isinstance(х.value, ast.Name) and х.value.id == імʼя:
                return ast.unparse(х.slice) == ключ or ход(х.slice)
            if isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr == 'get' and х.args \
                    and isinstance(х.func.value, ast.Name) and х.func.value.id == імʼя:
                return ast.unparse(х.args[0]) == ключ or any(ход(а) for а in х.args)
        if isinstance(х, ast.Name):
            return х.id == імʼя and isinstance(х.ctx, ast.Load)
        if isinstance(х, (ast.Raise, ast.JoinedStr)):
            return False
        if isinstance(х, ast.Call):
            if ім_виклику(х) in ОПИСОВІ_ВИКЛИКИ:
                return False
            if isinstance(х.func, ast.Attribute) and х.func.attr == 'format' and isinstance(х.func.value, ast.Constant):
                return False
        if isinstance(х, ast.BinOp) and isinstance(х.op, ast.Mod) and isinstance(х.left, ast.Constant) \
                and isinstance(х.left.value, str):
            return False
        if isinstance(х, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            звʼязані = {н.id for г in х.generators for н in ast.walk(г.target) if isinstance(н, ast.Name)}
            if імʼя in звʼязані:
                return ход(х.generators[0].iter)
        if isinstance(х, (ast.For, ast.AsyncFor)) and імʼя in {н.id for н in ast.walk(х.target) if isinstance(н, ast.Name)}:
            return ход(х.iter)      # цикл перепризначає імʼя: його тіло читає вже інше значення
        if isinstance(х, ast.Lambda):
            a = х.args
            if імʼя in {н.arg for н in a.posonlyargs + a.args + a.kwonlyargs}:
                return False
        return any(ход(д) for д in ast.iter_child_nodes(х))
    return any(ход(в) for в in вузли)


def текст_вузлів(вузли):
    return '\n'.join(ast.unparse(в) for в in вузли)


def порожнє_значення(в):
    if в is None:
        return True
    if isinstance(в, ast.Constant):
        return в.value in ПОРОЖНІ or isinstance(в.value, str) and not в.value
    if isinstance(в, ast.Tuple) and в.elts:
        return all(порожнє_значення(х) for х in в.elts)
    if isinstance(в, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
        return not (getattr(в, 'elts', None) or getattr(в, 'keys', None))
    if isinstance(в, ast.Call) and not в.args and not в.keywords and ім_виклику(в) in ('dict', 'list', 'set', 'tuple', 'str'):
        return True
    return False


def доля(гілка, корінь=None):
    """Відкинута гілка (список вузлів-стейтментів) чи вираз → (доля, пояснення). (в) — лише коли гілка несе саме
    відкинуте значення (читає корінь) у канал цитати: гілка, що бере уривок з іншого джерела, — не (в) (клас 16224)."""
    вузли = [гілка] if isinstance(гілка, ast.AST) else list(гілка)
    if not вузли:
        return 'а', 'гілки нема'
    for в in вузли:
        for х in ast.walk(в):
            if isinstance(х, ast.Raise):
                return 'г', 'raise ' + (джерело_шляху(х.exc)[:50] if х.exc else '')
    цілий = текст_вузлів(вузли)
    for в in вузли:
        for х in ast.walk(в):
            імена = ''
            if isinstance(х, ast.Name):
                імена = х.id
            elif isinstance(х, ast.Attribute):
                імена = х.attr
            elif isinstance(х, ast.Constant) and isinstance(х.value, str):
                імена = х.value if len(х.value) < 40 else ''
            if імена and ЦИТАТА.search(імена) and (корінь is None or читає_значення(вузли, корінь)):
                return 'в', 'пише в ' + імена
    for в in вузли:
        for х in ast.walk(в):
            імена = ''
            if isinstance(х, ast.Name):
                імена = х.id
            elif isinstance(х, ast.Attribute):
                імена = х.attr
            elif isinstance(х, ast.Constant) and isinstance(х.value, str) and len(х.value) < 60:
                імена = х.value
            elif isinstance(х, ast.keyword) and х.arg:        # `dict(…, причина="…")` — слід названий ключем
                імена = х.arg
            if імена and (СЛІД.search(імена) or імена in СЛІД_КОДУ):
                return 'б', 'слід: ' + імена[:40]
    # порожня
    усі_порожні = True
    for в in вузли:
        if isinstance(в, (ast.Continue, ast.Pass, ast.Break)):
            continue
        if isinstance(в, ast.Return) and порожнє_значення(в.value):
            continue
        if isinstance(в, ast.Assign) and порожнє_значення(в.value):
            continue
        if isinstance(в, ast.Expr) and isinstance(в.value, ast.Constant):
            continue
        if isinstance(в, ast.Delete):
            continue
        усі_порожні = False
    if усі_порожні:
        return 'а', 'порожнє мовчки: ' + цілий[:40].replace('\n', ' ')
    return 'г', 'інше: ' + цілий[:60].replace('\n', ' ')


# Імена сліду З КОДУ (16237): приймачі й ключі, куди продукт кладе код причини (`сторож.append(dict(чому="code_outside_list"))`,
# `причина="not_json_object: …"`), — доповнюють СЛІД, щоб гілка, яка пише в такий запис, лічилася (б), а не (а).
СЛІД_КОДУ = set()
КОД_ПРИЧИНИ = re.compile(r'^[a-z][a-z0-9]*(_[a-z0-9]+)+([:;( =].*)?$', re.S)


def код_причини(в):
    return isinstance(в, ast.Constant) and isinstance(в.value, str) and len(в.value) < 90 and bool(КОД_ПРИЧИНИ.match(в.value))


def зібрати_сліди():
    СЛІД_КОДУ.clear()
    for мод in МОДУЛІ.values():
        if мод.імʼя not in МОДУЛЬ_ЧИЯ:
            continue
        for н in ast.walk(мод.дерево):
            if isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr in МУТАТОРИ \
                    and any(код_причини(х) for а in н.args for х in ast.walk(а)):
                шл = шлях_приймача(н.func.value)
                if шл:
                    СЛІД_КОДУ.add(str(шл[1][-1]) if шл[1] else шл[0])
            elif isinstance(н, ast.keyword) and н.arg and (код_причини(н.value) or isinstance(н.value, ast.BinOp)
                                                             and код_причини(н.value.left)):
                СЛІД_КОДУ.add(н.arg)
            elif isinstance(н, ast.Dict):
                for к, в in zip(н.keys, н.values):
                    if isinstance(к, ast.Constant) and isinstance(к.value, str) and (код_причини(в) or isinstance(в, ast.BinOp) and код_причини(в.left)):
                        СЛІД_КОДУ.add(к.value)
    СЛІД_КОДУ.discard('*')


def слідове(текст):
    return bool(СЛІД.search(текст)) or any(т in СЛІД_КОДУ for т in re.findall(r'\w+', текст))


def без_слідових(гілка):
    """Гілка без стейтментів-слідів (`…не_взято.append(…)`, `незнайомі += …`): вони значення не ведуть далі."""
    res = []
    for х in гілка:
        if isinstance(х, ast.Expr) and isinstance(х.value, ast.Call) and isinstance(х.value.func, ast.Attribute) \
                and х.value.func.attr in ('append', 'extend', 'add', 'update', 'setdefault') \
                and слідове(ast.unparse(х.value.func.value)):
            continue
        if isinstance(х, ast.AugAssign) and слідове(ast.unparse(х.target)):
            continue
        if isinstance(х, ast.Assign) and any(слідове(ast.unparse(ц)) for ц in х.targets):
            continue            # `причина = "…"`, `р["помилки"] = …` — слід, не ведення значення
        res.append(х)
    return res


def шлях_проходження(батьки, вузол):
    """Стейтменти після `вузла` в його блоці до першого виходу (return/raise/continue/break) включно."""
    р = батьки.get(вузол)
    for поле in ('body', 'orelse', 'finalbody'):
        бл = getattr(р, поле, None)
        if isinstance(бл, list) and вузол in бл:
            res = []
            for х in бл[бл.index(вузол) + 1:]:
                res.append(х)
                if isinstance(х, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                    break
            return res
    return []


def стейтменти_після(батьки, вузол):
    """Стейтменти, що йдуть після вузла-стейтмента в його блоці (і в обʼємних блоках до кінця функції)."""
    після = []
    х = вузол
    while х in батьки:
        р = батьки[х]
        for поле in ('body', 'orelse', 'finalbody'):
            бл = getattr(р, поле, None)
            if isinstance(бл, list) and х in бл:
                після += бл[бл.index(х) + 1:]
        if isinstance(р, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
        х = р
    return після


def діапазон_гілки(гілка):
    return (гілка[0].lineno, max(getattr(s_, 'end_lineno', s_.lineno) for s_ in гілка)) if гілка else None


def лише_відмова(гілка):
    """Гілка — сама відмова: вихід, порожнє значення, слід чи виняток; жодної роботи над значенням."""
    for в in гілка:
        if isinstance(в, (ast.Continue, ast.Pass, ast.Break, ast.Return, ast.Raise, ast.Delete)):
            continue
        if isinstance(в, ast.Assign) and порожнє_значення(в.value):
            continue
        if isinstance(в, ast.Expr) and (isinstance(в.value, ast.Constant) or not без_слідових([в])):
            continue
        return False
    return True


def відкинуте_проходження(б, вузол):
    """Доля значення, що пройшло повз охоронений `if` без `else`: лише ТЕ, що стоїть одразу після нього (слідові
    стейтменти й вихід `return/raise/continue/break`); решта блоку — чужа робота, значення в ній не бере участі
    (клас 16222: `if isinstance(т, dict) and т: …` без `else` — не-dict мовчки губиться, це (а))."""
    res = []
    for s_ in шлях_проходження(б, вузол):
        if not без_слідових([s_]):
            res.append(s_)
            continue
        if isinstance(s_, (ast.Return, ast.Raise, ast.Continue, ast.Break)):
            res.append(s_)
        break
    # присвоєння `причина = …` без виходу — не доля, а ініціалізація далі по коду (`речі = [речі]` і т. п.)
    if res and not isinstance(res[-1], (ast.Return, ast.Raise, ast.Continue, ast.Break)) \
            and all(isinstance(x, ast.Assign) for x in res):
        return []
    return res


def імена_цілі(ц):
    return {н.id for н in ast.walk(ц) if isinstance(н, ast.Name)} if ц is not None else set()


def пошук_першого(б, р, корінь):
    """16238: `for о in …: if <перевірка о>: return о / break` — пошук першого придатного, невідповідне не відкинуто."""
    цикл = б.get(р)
    if isinstance(цикл, (ast.For, ast.AsyncFor)) and р in цикл.body and корінь in імена_цілі(цикл.target):
        return any(isinstance(х, (ast.Return, ast.Break)) for s_ in р.body for х in ast.walk(s_))
    return False


def цілим(fn, вузли, імʼя):
    """Чи `імʼя` читається цілим (передано, повернено, розкладено), а не лише інше поле `імʼя["k"]`/`.get("k")`,
    опис (`len`, `isinstance`) чи належність (`x in імʼя`)."""
    б = fn.батьки
    for в in вузли:
        for х in ast.walk(в):
            if not (isinstance(х, ast.Name) and х.id == імʼя and isinstance(х.ctx, ast.Load)):
                continue
            р = б.get(х)
            if isinstance(р, ast.Subscript) and р.value is х and isinstance(р.slice, ast.Constant):
                continue
            if isinstance(р, ast.Attribute) and р.value is х:
                ррр = б.get(р)
                if isinstance(ррр, ast.Call) and р.attr in ('get', 'items', 'keys', 'values', 'pop') and ррр.args[:1] \
                        and isinstance(ррр.args[0], ast.Constant):
                    continue
                if р.attr in БУЛЕВІ_МЕТОДИ or р.attr in МУТАТОРИ:
                    continue
            if isinstance(р, ast.Call) and ім_виклику(р) in ОПИСОВІ_ВБУДОВАНІ and х in р.args:
                continue
            if isinstance(р, ast.Compare) and any(isinstance(о, (ast.In, ast.NotIn)) for о in р.ops):
                continue
            return True
    return False


def контейнер_далі(fn, ст, корінь, після=None):
    """16238: відкинуте лишається в контейнері, що йде далі — корінь узято з C (`for корінь in …C…` чи
    `корінь = …C…`), і C після перевірки читається цілим. → імʼя C чи None."""
    б = fn.батьки
    while ст in б and not isinstance(ст, ast.stmt):
        ст = б[ст]
    джерела = []
    х = ст
    while х in б:
        х = б[х]
        if isinstance(х, (ast.For, ast.AsyncFor)) and корінь in імена_цілі(х.target):
            джерела.append(х.iter)
            break
    for н in ast.walk(fn.вузол):
        if isinstance(н, ast.Assign) and н.lineno <= ст.lineno and any(корінь in імена_цілі(ц) for ц in н.targets):
            джерела.append(н.value)
    локальні = set(fn.параметри) | {н.id for у in ast.walk(fn.вузол) if isinstance(у, (ast.Assign, ast.For, ast.AnnAssign))
                                    for н in ast.walk(у.targets[0] if isinstance(у, ast.Assign) else у.target)
                                    if isinstance(н, ast.Name)}
    кандидати = {н.id for д in джерела for н in ast.walk(д) if isinstance(н, ast.Name) and н.id in локальні and н.id != корінь}
    після = стейтменти_після(б, ст) if після is None else після
    for к in sorted(кандидати):
        if цілим(fn, після, к):
            return к
    return None


def носії_відмови(fn, пер, діап):
    """Імена, які гілка відкинутого пише (присвоєння, `+=`, `.append`), і ціль присвоєння, в якому стоїть перевірка
    (`вердикт = … if <перевірка> else None`)."""
    б = fn.батьки
    н_ = set()
    ст = пер
    while ст in б and not isinstance(ст, ast.stmt):
        ст = б[ст]
    if isinstance(ст, ast.Assign):
        for ц in ст.targets:
            н_ |= імена_цілі(ц)
    if діап:
        for х in ast.walk(fn.вузол):
            if not (діап[0] <= getattr(х, 'lineno', 0) <= діап[1]):
                continue
            if isinstance(х, ast.Assign):
                for ц in х.targets:
                    шл = шлях_приймача(ц) if not isinstance(ц, ast.Name) else (ц.id, [])
                    if шл:
                        н_.add(шл[0])
            elif isinstance(х, ast.AugAssign) and isinstance(х.target, ast.Name):
                н_.add(х.target.id)
            elif isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr in МУТАТОРИ:
                шл = шлях_приймача(х.func.value)
                if шл:
                    н_.add(шл[0])
    return н_, ст


def слід_нижче(fn, пер, діап):
    """16237: доля в усій функції — нижче за тією самою умовою (той самий текст перевірки) чи змінною, яку пише гілка
    відкинутого: гілка нижче пише слід (СЛІД, імена сліду з коду) чи повертає запис із цією змінною. → (рядок, що)."""
    носії, ст = носії_відмови(fn, пер, діап)
    текст = ast.unparse(пер)
    for s_ in стейтменти_після(fn.батьки, ст):
        for х in ast.walk(s_):
            if not isinstance(х, (ast.If, ast.While, ast.IfExp)):
                continue
            тест = х.test
            та_сама = any(ast.unparse(у) == текст for у in ast.walk(тест) if isinstance(у, type(пер)))
            через = sorted({у.id for у in ast.walk(тест) if isinstance(у, ast.Name) and у.id in носії})
            if not (та_сама or через):
                continue
            гілки = [s_] if isinstance(х, ast.IfExp) else [х.body, х.orelse]
            for г in гілки:
                г = г if isinstance(г, list) else [г]
                if г and доля(г)[0] == 'б':
                    return х.lineno, 'та сама умова' if та_сама else 'через «%s»' % через[0]
                for у in г:
                    for z in ast.walk(у):
                        if isinstance(z, ast.Return) and isinstance(z.value, (ast.Dict, ast.Call)) and через \
                                and читає_імʼя([z.value], через[0]):
                            return х.lineno, 'запис відмови з «%s»' % через[0]
    return None


def класифікувати(fn, пер, E, вид, поз):
    д, пояс, діап = класифікувати_місцево(fn, пер, E, вид, поз)
    if д in ('а', 'г') and not пояс.startswith(('raise', 'except: raise', 'предикат', 'assert')):
        н = слід_нижче(fn, пер, діап)
        if н:
            return 'б', 'слід нижче (рядок %d, %s); місцево: %s' % (н[0], н[1], пояс[:50]), діап
    return д, пояс, діап


def класифікувати_місцево(fn, пер, E, вид, поз):
    """→ (доля, пояснення, діапазон рядків відкинутої гілки | None).
    Відкинута гілка — за ПОЛЯРНІСТЮ перевірки: позитивна → `else` (чи проходження далі), негативна → тіло; «веде далі» —
    лише коли ця гілка читає саме значення (а не описує його типом чи повідомленням, див. `читає_значення`)."""
    б = fn.батьки
    # шукаємо найближчий контекст: If/While/IfExp/comprehension/Assert/Return/Assign
    х = пер
    while х in б and not isinstance(б[х], (ast.stmt, ast.IfExp, ast.comprehension)):
        х = б[х]
    р = б.get(х)
    if isinstance(пер, ast.Try):
        р = пер
    if isinstance(р, ast.Try) and пер is р:
        обр = [s for o in р.handlers for s in o.body]
        д, пояс = доля(обр)
        діап = (обр[0].lineno, max(getattr(s, 'end_lineno', s.lineno) for s in обр)) if обр else None
        return д, 'except: ' + пояс, діап
    if р is None:
        return 'г', 'контекст не розпізнано', None
    корінь = ім_кореня(E)
    ключ = ключ_доступу(E, корінь)
    чит = lambda вузли: читає_значення(вузли, корінь, ключ)
    if isinstance(р, ast.If) and (х is р.test):
        def природа(гілка):
            """accept — гілка читає значення (веде далі); reject — не читає й лише скидає/пише слід/кидає виняток."""
            if not гілка:
                return 'порожня'
            if чит(без_слідових(гілка)):
                return 'accept'
            return 'reject'
        тіло, інакше = р.body, р.orelse
        # позитивна перевірка (істина = прийняте): тіло — відкинуте лише коли воно сама відмова (вихід, порожнє, слід);
        # тіло з роботою (`вердикти = …`) — прийняте, а відкинуте тоді в `else` чи в проходженні далі (5004)
        тіло_відмова = природа(тіло) == 'reject' and (not поз or лише_відмова(тіло))
        if тіло_відмова:
            гілка = тіло
        elif інакше and природа(інакше) == 'reject':
            гілка = інакше
        elif інакше:
            return 'далі', 'обидві гілки читають значення (корінь «%s»)' % корінь, None
        else:
            гілка = []
        діап = діапазон_гілки(гілка)
        if not гілка:
            # 16238: без гілки відкинутого — (а) лише коли умова — відмова, а не пошук першого придатного, і відкинуте не
            # лишається в контейнері, що йде далі
            if поз and пошук_першого(б, р, корінь):
                return 'далі', 'пошук першого придатного: невідповідне — не відмова', None
            с_ = контейнер_далі(fn, р, корінь)
            if с_:
                return 'далі', 'відкинуте лишається в «%s», що йде далі' % с_, None
            шлях = відкинуте_проходження(б, р)
            if шлях and not чит(без_слідових(шлях)):
                д, пояс = доля(шлях, корінь)
                if д == 'г' and пояс.startswith('інше') and isinstance(шлях[-1], ast.Return):
                    # звичайний результат функції після охоронюваного блоку: значення туди не потрапило (16222);
                    # (а) — лише коли цей результат порожній, інакше — підміна непорожнім (16238)
                    if порожнє_значення(шлях[-1].value):
                        return 'а', 'проходить до загального результату: ' + пояс[6:50], діапазон_гілки(шлях)
                    return 'г', 'проходить до непорожнього загального результату: ' + пояс[6:50], діапазон_гілки(шлях)
                return д, 'проходить далі: ' + пояс, діапазон_гілки(шлях)
            після = стейтменти_після(б, р)
            if чит(після):
                return 'далі', 'проходить нижче без гілки (корінь «%s» читається далі)' % корінь, None
            return 'а', 'відсів без гілки (корінь «%s» далі не читається)' % корінь, None
        д, пояс = доля(гілка, корінь)
        return д, пояс, діап
    if isinstance(р, ast.IfExp) and (х is р.test):
        вираз = р.orelse if поз else р.body
        # запасне значення ланцюга `[v] if str else v if list else []` — останнє `else`, а не наступна перевірка (16223)
        while isinstance(вираз, ast.IfExp) and читає_імʼя([вираз.test], корінь):
            заперечено = isinstance(вираз.test, ast.UnaryOp) and isinstance(вираз.test.op, ast.Not)
            вираз = вираз.body if заперечено else вираз.orelse
        if чит([вираз]):
            return 'далі', 'підміна читає той самий корінь', None
        с_ = контейнер_далі(fn, р, корінь, [вираз])
        if с_:
            return 'далі', 'підміна несе контейнер «%s» з відкинутим далі' % с_, None
        if isinstance(вираз, ast.Constant) and isinstance(вираз.value, str) and re.fullmatch(r'[a-z][a-z_:()=, %s]{5,}', вираз.value):
            return 'б', 'підміна кодом причини «%s»' % вираз.value[:40], (вираз.lineno, getattr(вираз, 'end_lineno', вираз.lineno))
        д, пояс = доля([ast.Expr(value=вираз)] if порожнє_значення(вираз) is False else [ast.Return(value=вираз)], корінь)
        діап = (вираз.lineno, getattr(вираз, 'end_lineno', вираз.lineno))
        return д, 'підміна: ' + пояс, діап
    if isinstance(р, ast.comprehension):
        if not поз:
            # негативна перевірка у фільтрі (16233): істина перевірки — відкинуте, і саме воно проходить фільтр, тобто
            # генератор збирає відкинуті; доля — куди йде результат генератора
            ст = р
            while ст in б and not isinstance(ст, ast.stmt):
                ст = б[ст]
            цілі = [ast.unparse(ц) for ц in getattr(ст, 'targets', [getattr(ст, 'target', None)]) if ц is not None]
            if isinstance(ст, ast.Expr) and isinstance(ст.value, ast.Call) and isinstance(ст.value.func, ast.Attribute):
                цілі.append(ast.unparse(ст.value.func.value))
            if any(слідове(ц) for ц in цілі):
                return 'б', 'відкинуті зібрано генератором у слід «%s»' % цілі[0][:30], None
            return 'далі', 'відкинуті проходять фільтр (негативна перевірка): генератор їх лишає', None
        if корінь in {н.id for н in ast.walk(р.target) if isinstance(н, ast.Name)}:
            return 'а', 'відсів у генераторі (елемент зникає)', None
        # корінь із зовнішньої області (`next((x[к] for к in … if isinstance(x, dict)), None)`): значення не зникає,
        # якщо його читає наступний код (інша форма того самого значення)
        ст = р
        while ст in б and not isinstance(ст, ast.stmt):
            ст = б[ст]
        if isinstance(ст, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == корінь for ц in ст.targets):
            return 'а', 'відсів у генераторі, результат замінює «%s» (відкинуте не читається далі)' % корінь, None
        локальні = set(fn.параметри) | {н.id for у in ast.walk(fn.вузол) if isinstance(у, (ast.Assign, ast.For, ast.AnnAssign))
                                        for н in ast.walk(у.targets[0] if isinstance(у, ast.Assign) else у.target)
                                        if isinstance(н, ast.Name)}
        if корінь in локальні and чит(стейтменти_після(б, ст)):
            return 'далі', 'відсів у генераторі, але значення читається далі (корінь «%s»)' % корінь, None
        return 'а', 'відсів у генераторі (корінь «%s» далі не читається)' % корінь, None
    if isinstance(р, ast.While):
        return 'далі', 'цикл', None
    if isinstance(р, ast.Return):
        return 'г', 'предикат (return): доля — у викликача', None
    if isinstance(р, ast.Assert):
        return 'г', 'assert', None
    if isinstance(р, ast.Assign) and len(р.targets) == 1 and isinstance(р.targets[0], ast.Name) and р.value is not None:
        N = р.targets[0].id
        для = [x for x in ast.walk(fn.вузол) if isinstance(x, ast.If) and x.lineno > р.lineno
               and any(isinstance(y, ast.Name) and y.id == N for y in ast.walk(x.test))]
        вирази = [x for x in ast.walk(fn.вузол) if вид != 'перелік·пошук' and isinstance(x, ast.IfExp) and x.lineno >= р.lineno
                  and any(isinstance(y, ast.Name) and y.id == N for y in ast.walk(x.test))]
        if вирази and (not для or min(x.lineno for x in вирази) <= min(x.lineno for x in для)):          # `якщо_рядок = isinstance(с, str)` → `"" if якщо_рядок else …`: умовний вираз, не `if`
            в_ = min(вирази, key=lambda x: x.lineno)
            заперечено = isinstance(в_.test, ast.UnaryOp) and isinstance(в_.test.op, ast.Not)
            вираз = в_.body if (поз and заперечено) or (not поз and not заперечено) else в_.orelse
            if чит([вираз]):
                return 'далі', 'результат перевірки в «%s», умовний вираз читає значення' % N, None
            д, пояс = доля([ast.Return(value=вираз)], корінь)
            return д, 'через «%s» (умовний вираз): %s' % (N, пояс), None
        if для:
            ф = min(для, key=lambda x: x.lineno)
            заперечено = isinstance(ф.test, ast.UnaryOp) and isinstance(ф.test.op, ast.Not)
            # поз: істина = прийняте; умова `if N` (не заперечена): тіло — прийняте при поз
            гілка = ф.orelse if (поз and not заперечено) or (not поз and заперечено) else ф.body
            if not гілка:
                після = стейтменти_після(б, ф)
                if чит(після):
                    return 'далі', 'результат перевірки в «%s», далі значення читається' % N, None
                if пошук_першого(б, ф, корінь):
                    return 'далі', 'пошук першого придатного (через «%s»): невідповідне — не відмова' % N, None
                с_ = контейнер_далі(fn, ф, корінь)
                if с_:
                    return 'далі', 'відкинуте лишається в «%s», що йде далі' % с_, None
                return 'а', 'відсів без гілки (результат у «%s»)' % N, None
            д, пояс = доля(гілка, корінь)
            return д, 'через «%s»: %s' % (N, пояс), діапазон_гілки(гілка)
        return 'г', 'предикат у присвоєнні «%s»: наступної умови не знайдено' % N, None
    if isinstance(р, (ast.Assign, ast.AnnAssign)):
        return 'г', 'предикат у присвоєнні: доля — у місці використання', None
    if isinstance(р, ast.Expr):
        return 'г', 'вираз-стейтмент', None
    return 'г', 'контекст ' + type(р).__name__, None


# ЯДРО — модулі, де код приймає відповідь моделі (шви). Потік зараження ходить лише в них: після шва значення — запис
# кодом (паспорт, сценарій, бриф), а не відповідь моделі, і його перевірки (`паспорт_нагоди`, `сценарій`, `brief`, …) —
# поза обсягом цієї лічби (клас «значення від неї» кореня — інший вимір).
ЯДРО = {
    'розмовна модель': ['мовний_шар', 'внутрішня_мова', 'conversation_tools', 'міст_вхід'],
    'стилістка (складання, ремонт, повнота, помічниця)': [
        'розбір_відповідей', 'міст_відповіді', 'схеми_розбору', 'протокол', 'схема_відповіді', 'дріт_моделі',
        'повнота_образу', 'пакет_моделі', 'вибір_палітри', 'руки_без_коду', 'міст_стилістка', 'міст_пакет',
        'міст_помічниця', 'міст_запити', 'міст_основи', 'міст_річ', 'міст_опис'],
    'судді й оцінка': ['вердикт_моделі', 'суд_від_моделі', 'оцінка_образу', 'перевірка_образу', 'міст_оцінка'],
    'опис фото, каталог, жниварка': ['каталог_розбір', 'каталог_розбір_прогін', 'річ_з_фото', 'фід_власник_кадру',
                                     'language_contract', 'заміна_речі', 'пошук_речі', 'приміряння', 'жнива_розбір',
                                     'жнива_промпти', 'жнива_збагачення', 'жнива_маски', 'знання_дріт'],
}
МОДУЛЬ_ЧИЯ = {м: к for к, мм in ЯДРО.items() for м in мм}


def чия(імʼя_модуля):
    return МОДУЛЬ_ЧИЯ.get(імʼя_модуля, 'поза ядром')


def зібрати():
    for ф in файли():
        try:
            МОДУЛІ[os.path.splitext(os.path.basename(ф))[0]] = Модуль(ф)
        except SyntaxError:
            print('пропущено (синтаксис):', ф, file=sys.stderr)
    табличні_параметри()
    зібрати_сліди()
    зібрати_реєстр_розбору()
    МЕТОДИ.clear()
    усі_методи = collections.defaultdict(list)
    for мод in МОДУЛІ.values():
        for кл in ast.walk(мод.дерево):
            if isinstance(кл, ast.ClassDef):
                for н in кл.body:
                    if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fn = мод.функції.get(н.name)
                        усі_методи[н.name].append(fn if fn is not None and fn.вузол is н else Fn(мод, н))
    МЕТОДИ.update({ім: фф[0] for ім, фф in усі_методи.items() if len(фф) == 1 and фф[0].параметри[:1] == ['self']})
    # (1) потік від відповіді моделі (16239): перевірки на значенні з джерел будовою, у кожному контексті
    сирі = collections.OrderedDict()
    for а in потік_від_моделі():
        for пер, E, вид, поз in знайти_перевірки(а.fn, а):
            к = (а.fn.мод.шлях, пер.lineno, вид, джерело_шляху(пер)[:70].replace('\n', ' '))
            було = сирі.get(к)
            сирі[к] = (а.fn, пер, E, вид, поз, (було[5] if було else '') + а.джерело(E))
    # (2) корінь за іменем (лічба до кроку 16239) — лише щоб назвати окремим рядком «запис коду» те, що вона брала
    міжфункційно()
    за_іменем = collections.OrderedDict()
    for мод in МОДУЛІ.values():
        if мод.імʼя not in МОДУЛЬ_ЧИЯ:
            continue
        for fn in sorted(set(мод.функції.values()), key=lambda f: f.вузол.lineno):
            п = Потік(fn)
            п.прогін(fn.вузол)
            for пер, E, вид, поз in знайти_перевірки(fn, п):
                к = (мод.шлях, пер.lineno, вид, джерело_шляху(пер)[:70].replace('\n', ' '))
                if к not in сирі and к not in за_іменем:
                    за_іменем[к] = (fn, пер, E, вид, поз, '')
    рядки = []
    for корінь, набір in (('модель', сирі), ('запис коду', за_іменем)):
        for (шлях, _, _, _), (fn, пер, E, вид, поз, дж) in набір.items():
            fn.батьки = {д: н for н in ast.walk(fn.вузол) for д in ast.iter_child_nodes(н)}
            д, пояс, діап = класифікувати(fn, пер, E, вид, поз)
            if вид == 'перелік·пошук' and д == 'г' and пояс.startswith(('предикат', 'контекст', 'вираз', 'assert')):
                continue      # пошук у таблиці як переклад значення, не як перевірка в умові
            рядки.append(dict(файл=шлях, рядок=пер.lineno, функція=fn.імʼя, поле=поле_з(E), чия=чия(fn.мод.імʼя),
                              вид=вид, E=джерело_шляху(E), доля=д, пояснення=пояс, діапазон=діап,
                              вираз=джерело_шляху(пер)[:70].replace('\n', ' '), вузол=пер, fn=fn, корінь=корінь,
                              джерело='A' if 'A' in дж else 'B' if 'B' in дж else ''))
    # слід у викликача: (а) із `return <порожнє>` у функції — дивимось, чи біля кожного виклику (8 рядків униз, без
    # коментарів) стоїть слід (СЛІД); це лише ознака для звірки очима, у долю (а) не вноситься
    виклики = collections.defaultdict(list)
    for мод in МОДУЛІ.values():
        if мод.імʼя not in МОДУЛЬ_ЧИЯ:
            continue
        for fn in set(мод.функції.values()):
            for в in ast.walk(fn.вузол):
                if isinstance(в, ast.Call):
                    g = вирішити(мод, в)
                    if g is not None:
                        виклики[id(g)].append((мод, в))
    for р in рядки:
        р['слід_у_викликача'] = None
        if р['доля'] == 'а' and 'return' in р['пояснення']:
            сайти = виклики.get(id(р['fn']), [])
            ок = 0
            for мод, в in сайти:
                вікно = '\n'.join(re.sub(r'#.*', '', x) for x in мод.рядки[в.lineno - 1: в.lineno + 8])
                ок += bool(СЛІД.search(вікно))
            р['слід_у_викликача'] = (ок, len(сайти))
    # унікальні за файл:рядок:вид:поле (вузли в вкладених функціях дублюються при ast.walk)
    унік, бачено = [], set()
    for р in рядки:
        к = (р['файл'], р['рядок'], р['вид'], р['вираз'])
        if к in бачено:
            continue
        бачено.add(к)
        унік.append(р)
    return унік


def схеми():
    res = []
    for ф in sorted(glob.glob('джерела/**/*.schema.json', recursive=True)):
        if '/проби/' in ф or '/прилади/' in ф:
            continue
        д = json.load(open(ф, encoding='utf-8'))
        n = dict(enum=0, тип=0)
        def ход(в):
            if isinstance(в, dict):
                if 'enum' in в:
                    n['enum'] += 1
                if 'type' in в:
                    n['тип'] += 1
                for x in в.values():
                    ход(x)
            elif isinstance(в, list):
                for x in в:
                    ход(x)
        ход(д)
        res.append((ф, n['enum'], n['тип']))
    return res


def підсумок(р):
    відкидають = [x for x in р if x['доля'] in 'абвг' and x['доля'] != 'далі']
    відкидають = [x for x in р if x['доля'] in ('а', 'б', 'в', 'г')]
    далі = [x for x in р if x['доля'] == 'далі']
    ч = collections.Counter(x['доля'] for x in відкидають)
    return відкидають, далі, ч


ДВА = [  # (id рядка дошки, сцена, записаний хід, маркери значення в зрізі)
    ('16184', 'ж4_робота_срібні_сережки', ['earrings', 'silvery']),
    ('16168', 'ж1_213_золоте_намисто', ['festive_dinner']),
]


def два_значення(р):
    """Повтор записаної відповіді першого ходу сцени через `мовний_шар.мова` (два виклики, як `міст`: прочитати відповідь,
    скласти паспорт) під `sys.settrace`: у кожному місці перевірки, знайденому лічбою, рахуємо значення з маркером у E."""
    sys.path.insert(0, os.path.join(КОРІНЬ, 'джерела', 'прилади'))
    import корінь_е2_втрата_слова_вхід as П
    джерела = os.path.join(КОРІНЬ, 'джерела')
    sys.path.insert(0, джерела)
    os.chdir(джерела)
    import мовний_шар as М
    індекс = collections.defaultdict(list)
    for x in р:
        індекс[(os.path.abspath(os.path.join(КОРІНЬ, x['файл'])), x['рядок'])].append(x)
    for ід, сцена, маркери in ДВА:
        ф = os.path.join(П.НІЧНИЙ, сцена, 'VIDPOVIDI', 'seed3_01_мовний_шар_хід_розмови.txt')
        т = П._текст(ф)
        п, _, в = т.partition('── ВІДПОВІДЬ')
        її = П.перша_репліка(п)
        відп = в.split('──', 1)[1] if '──' in в else в
        виконано, влучання = [], []

        def трейс(кадр, подія, арг):
            шлях = кадр.f_code.co_filename
            if not шлях.startswith(джерела) or '/прилади/' in шлях or '/проби/' in шлях:
                return None
            if подія == 'line':
                к = (шлях, кадр.f_lineno)
                виконано.append(к)
                for x in індекс.get(к, ()):
                    try:
                        знач = repr(eval(x['E'], кадр.f_globals, кадр.f_locals))
                    except Exception:
                        continue
                    if any(м in знач for м in маркери):
                        влучання.append((len(виконано), x, знач[:90]))
            return трейс
        sys.settrace(трейс)
        try:
            р1 = json.loads(М.мова({'розмова': {'нове': її, 'історія': []}, 'відповідь_моделі': відп, 'сценарій': {}}))
            d = {'паспорт_з': р1.get('внутрішня'), 'сценарій': {}, 'слова_розмови': [її], 'частини': р1.get('частини') or {}}
            for к in ('не_взято', 'не_записано'):
                if р1.get(к):
                    d[к] = р1[к]
            р2 = json.loads(М.мова(d))
        finally:
            sys.settrace(None)
        print('\n=== %s · %s · маркери %s' % (ід, сцена, маркери))
        print('її репліка: «%s»' % її[:120])
        print('внутрішня після 1-го виклику: %s' % json.dumps(р1.get('внутрішня'), ensure_ascii=False)[:600])
        print('незнайомі: %s · не_взято: %s' % (р1.get('незнайомі'), р1.get('не_взято')))
        п2 = р2.get('паспорт') or {}
        print('паспорт після 2-го виклику: occasion=%r jewelry=%r place=%r не_взято_кодом=%s' % (
            п2.get('occasion'), п2.get('jewelry'), п2.get('place'), п2.get('не_взято_кодом')))
        бачено = set()
        for порядок, x, знач in влучання:
            к = (x['файл'], x['рядок'], x['вираз'])
            if к in бачено:
                continue
            бачено.add(к)
            діап = x.get('діапазон')
            відкинуто = 'n/a'
            if діап:
                відкинуто = 'так' if any(os.path.abspath(os.path.join(КОРІНЬ, x['файл'])) == ш and діап[0] <= л <= діап[1]
                                          for ш, л in виконано[порядок:]) else 'ні'
            print('  %s:%d · %s · %s · корінь %s · доля(стат.) %s · відкинуту гілку виконано: %s\n      E=%s → %s' % (
                x['файл'], x['рядок'], x['вид'], x['вираз'][:60], x.get('корінь', ''), x['доля'], відкинуто, x['E'][:50], знач))
    return


# ───────────────────────── самоперевірка: фікстура на кожен клас хибної назви ─────────────────────────
# Кожна фікстура — функція в модулі з ядра (`мовний_шар`), де значення йде від відповіді моделі (`об`); очікування —
# доля, яку названо ПРАВИЛЬНО очима. Старі правила (main до цього кроку) називали: 16221 — «веде далі», 16222 — «г»,
# 16223 — «веде далі», 16224 — «в». `--самоперевірка` друкує кожну фікстуру й виходить з кодом 1 при розбіжності.
ФІКСТУРИ_ТЕКСТ = '''
import json as json_


def ф_16221_тип(об, шлях):
    if not isinstance(об, dict):
        return [("wrong_type(got=%s)" % type(об).__name__)]
    return []


ПЕРЕЛІК_Ф = ("a", "b")


def ф_16221_перелік(об):
    if об not in ПЕРЕЛІК_Ф:
        raise ValueError("не з переліку: %s" % об)
    return об


def ф_16222_охоронений_if(об):
    вих = {}
    т = об.get("тіло")
    if isinstance(т, dict) and т:
        вих["body"] = dict(т)
    вих["done"] = 1
    return вих


def ф_16223_запасне_значення(об):
    про = об.get("about")
    про = [про] if isinstance(про, str) else про if isinstance(про, list) else []
    return про


def ф_16223_відсів_нижче(об):
    фото = об.get("photo")
    if isinstance(фото, str):
        if фото != "ok":
            return {"відмова": фото}
    вих = {"шкіра": об.get("skin")}
    вих["тип"] = "рядок" if isinstance(фото, (str, bytes)) else "інше"
    return вих


def ф_16223_змінна_циклу(об):
    за = {}
    for ц in об.get("цитати") or []:
        if isinstance(ц, str) and ц.strip():
            за.setdefault("к", []).append(ц.strip())
    return [dict(не_взято=ц) for ц in за]


def ф_16224_інше_джерело(об, внутрішня, подія):
    уривок = об.get("quote") if isinstance(об, dict) else (внутрішня.get("quotes") or {}).get(подія)
    return уривок


def ф_16224_чужий_запис(об):
    вих = {}
    ош = об.get("ошатність")
    if isinstance(ош, (list, tuple)) and len(ош) == 2:
        вих["formality"] = ош[0]
    уривок = об.get("quote")
    вих["quote"] = уривок
    return вих


ВЕРДИКТИ_Ф = ("так", "ні")
СХЕМИ_Ф = {"а": 1, "типова": 2}


def ф_16237_слід_нижче(об):
    сторож = []
    вердикт = об.get("verdict") if об.get("verdict") in ВЕРДИКТИ_Ф else None
    if об.get("verdict") not in (None, "") and вердикт is None:
        сторож.append(dict(де="verdict", чому="code_outside_list", що=об.get("verdict")))
    return dict(вердикт=вердикт, сторож=сторож)


def ф_16237_та_сама_умова(об):
    т = об.get("text") if isinstance(об, dict) else None
    if т:
        return dict(текст=т)
    return dict(текст="", причина="no_text" if т == "" else "not_json_object")


def ф_16238_контейнер(вердикт):
    for о in вердикт["образи"]:
        if isinstance(о.get("структура"), dict):
            о["структура"] = dict(о["структура"], ок=1)
    return вердикт


def ф_16238_пошук(вердикт, ід):
    for о in (вердикт.get("образи") or []):
        if isinstance(о, dict) and о.get("ід") == ід:
            return о
    return None


def ф_16238_непорожній(відповідь):
    if відповідь in СХЕМИ_Ф:
        return СХЕМИ_Ф[відповідь]
    return СХЕМИ_Ф["типова"]


def ф_16233_збирає_вади(виклик):
    вади = ["tool.%s: not a key" % к for к in виклик if к not in ("name", "args")]
    return вади


def ф_16233_непорожні(об):
    return {к: в for к, в in об.items() if в not in (None, "")}


def ф_16239_запис_коду(вердикт):
    for о in вердикт.get("образи") or []:
        if not isinstance(о, dict):
            continue
    return вердикт


def ф_16239_поле_запиту(відповідь):
    d = json_.loads(відповідь)
    тексти = d.get("тексти")
    if not isinstance(тексти, dict):
        return None
    return тексти


def ф_16239_поле_моделі_в_записі(об):
    запис = dict(причина="value_not_string", що=об.get("k"))
    if запис["причина"] in ("value_not_string", "x"):
        return None
    return запис


def вхід_ф(вхід):
    d = json_.loads(вхід)
    об = json_.loads(d["відповідь_моделі"])
    ф_16221_тип(об, "")
    ф_16221_перелік(об)
    ф_16222_охоронений_if(об)
    ф_16223_запасне_значення(об)
    ф_16223_відсів_нижче(об)
    ф_16223_змінна_циклу(об)
    ф_16224_інше_джерело(об, об, "подія")
    ф_16224_чужий_запис(об)
    ф_16237_слід_нижче(об)
    ф_16237_та_сама_умова(об)
    ф_16238_контейнер(об)
    ф_16238_пошук(об, d.get("ід"))
    ф_16238_непорожній(об.get("схема"))
    ф_16233_збирає_вади(об)
    ф_16233_непорожні(об)
    ф_16239_запис_коду(dict(образи=[dict(ід=1)], тексти=d.get("тексти")))
    ф_16239_поле_запиту(вхід)
    return ф_16239_поле_моделі_в_записі(об)
'''
ФІКСТУРИ_МІСТ = '''
from мовний_шар import вхід_ф


def виклик(ім, вхід):
    return {"ф": вхід_ф}[ім](вхід)
'''
# (функція, перевірка) → очікувана доля; `далі` — «веде далі», `код` — рядок «запис коду» (корінь не з відповіді
# моделі), `нема` — не перевірка значення
ФІКСТУРИ = [
    ('16221', 'ф_16221_тип', 'isinstance(об, dict)', 'г'),
    ('16221', 'ф_16221_перелік', 'об not in ПЕРЕЛІК_Ф', 'г'),
    ('16222', 'ф_16222_охоронений_if', 'isinstance(т, dict)', 'а'),
    ('16223', 'ф_16223_запасне_значення', 'isinstance(про, str)', 'а'),
    ('16223', 'ф_16223_відсів_нижче', 'isinstance(фото, str)', 'а'),
    ('16223', 'ф_16223_змінна_циклу', 'isinstance(ц, str)', 'а'),
    ('16224', 'ф_16224_інше_джерело', 'isinstance(об, dict)', 'г'),
    ('16224', 'ф_16224_чужий_запис', 'isinstance(ош, (list, tuple))', 'а'),
    ('16237', 'ф_16237_слід_нижче', "об.get('verdict') in ВЕРДИКТИ_Ф", 'б'),
    ('16237', 'ф_16237_та_сама_умова', 'isinstance(об, dict)', 'б'),
    ('16238', 'ф_16238_контейнер', "isinstance(о.get('структура'), dict)", 'далі'),
    ('16238', 'ф_16238_пошук', 'isinstance(о, dict)', 'далі'),
    ('16238', 'ф_16238_непорожній', 'відповідь in СХЕМИ_Ф', 'г'),
    ('16233', 'ф_16233_збирає_вади', "к not in ('name', 'args')", 'б'),
    ('16233', 'ф_16233_непорожні', "в not in (None, '')", 'нема'),
    ('16239', 'ф_16239_запис_коду', 'isinstance(о, dict)', 'код'),
    ('16239', 'ф_16239_поле_запиту', 'isinstance(тексти, dict)', 'код'),
    ('16239', 'ф_16239_поле_моделі_в_записі', "запис['причина'] in ('value_not_string', 'x')", 'код'),
]


def самоперевірка(мод=None):
    """Фікстури → класифікація; `мод` — модуль лічби (для порівняння зі старою версією: фікстури й місток — звідси).
    → число розбіжностей."""
    import tempfile
    мод = мод or sys.modules[__name__]
    з = tempfile.mkdtemp()
    шлях, міст = os.path.join(з, 'мовний_шар.py'), os.path.join(з, 'bridge.py')
    open(шлях, 'w', encoding='utf-8').write(ФІКСТУРИ_ТЕКСТ)
    open(міст, 'w', encoding='utf-8').write(ФІКСТУРИ_МІСТ)
    мод.файли = lambda: [міст, шлях]
    мод.МОДУЛІ.clear()
    рядки = мод.зібрати()
    за = {(x['функція'], x['вираз']): ('код' if x.get('корінь') == 'запис коду' else x['доля']) for x in рядки}
    поганих = 0
    for клас, функція, вираз, очікується in ФІКСТУРИ:
        одержано = за.get((функція, вираз), 'нема')
        ок = одержано == очікується
        поганих += not ок
        print('фікстура %s · %s · %s · очікується %s · одержано %s · %s' % (
            клас, функція, вираз, очікується, одержано, 'ОК' if ок else 'РОЗБІЖНІСТЬ'))
    return поганих


ВІДОМІ_МІСЦЯ = ('мовний_шар.py:4695 мовний_шар.py:4843 мовний_шар.py:926 дріт_моделі.py:808 мовний_шар.py:5004 мовний_шар.py:1939 '
                'мовний_шар.py:1524 мовний_шар.py:4935 мовний_шар.py:1049 дріт_моделі.py:1747 дріт_моделі.py:1762 міст_вхід.py:662 '
                'протокол.py:240 протокол.py:252 протокол.py:262 conversation_tools.py:274 мовний_шар.py:799 мовний_шар.py:4104 '
                'мовний_шар.py:1894 дріт_моделі.py:1768 мовний_шар.py:342 мовний_шар.py:4650 мовний_шар.py:5259 '
                'розбір_відповідей.py:658 розбір_відповідей.py:1845 руки_без_коду.py:498 руки_без_коду.py:518 '
                'language_contract.py:60 схема_відповіді.py:325')


ЗВІРЕНІ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'звірені_раніше.json')


def ключ_звірки(x):
    return (os.path.basename(x['файл']), x['функція'], x['вираз'])


def вибірка(рядки, seed, n, без=()):
    """`n` місць лічби (корінь з відповіді моделі, ядро) з `seed`, без звірених раніше (ЗВІРЕНІ: 140 місць трьох
    вибірок і названі місця — за файлом, функцією й виразом, бо рядки зсунулись) і без `без`."""
    import random
    звірені = {(x['файл'], x['функція'], x['вираз']) for x in json.load(open(ЗВІРЕНІ, encoding='utf-8'))}
    пул = [x for x in рядки if ключ_звірки(x) not in звірені and ключ_звірки(x) not in без]
    random.seed(seed)
    return пул, random.sample(пул, n)


def друк_рядків(назва, рр):
    ч = collections.Counter(x['доля'] for x in рр)
    print('%s: перевірок %d · відкидають %d · а: %d · б: %d · в: %d · г: %d · веде далі: %d' % (
        назва, len(рр), sum(ч[к] for к in 'абвг'), ч['а'], ч['б'], ч['в'], ч['г'], ч['далі']))


def головна():
    арги = sys.argv[1:]
    if '--самоперевірка' in арги:
        sys.exit(1 if самоперевірка() else 0)
    усі = зібрати()
    р = [x for x in усі if x['корінь'] == 'модель' and x['чия'] != 'поза ядром']      # лічба: корінь з моделі, ядро
    код = [x for x in усі if x['корінь'] == 'запис коду']
    поза = [x for x in усі if x['корінь'] == 'модель' and x['чия'] == 'поза ядром']
    відкидають, далі, ч = підсумок(р)
    if '--таблиця' in арги:
        шлях = арги[арги.index('--таблиця') + 1]
        with open(шлях, 'w', encoding='utf-8') as ф:
            ф.write('| файл:рядок | поле | корінь | чия відповідь | вид | доля | що робить гілка відкинутого | перевірка |\n'
                    '|---|---|---|---|---|---|---|---|\n')
            for x in sorted(усі, key=lambda x: (x['файл'], x['рядок'])):
                ф.write('| `%s:%d` | %s | %s | %s | %s | %s | %s%s | `%s` |\n' % (
                    x['файл'].replace('джерела/', ''), x['рядок'], x['поле'],
                    {'модель': 'модель·' + (x['джерело'] or '?')}.get(x['корінь'], x['корінь']), x['чия'], x['вид'],
                    {'далі': 'веде далі'}.get(x['доля'], x['доля']), x['пояснення'].replace('|', '/'),
                    (' · слід у викликачі: %d з %d' % x['слід_у_викликача']) if x.get('слід_у_викликача') else '',
                    x['вираз'].replace('|', '/').replace('`', "'")))
    if '--два-значення' in арги:
        два_значення(усі)
        return
    if '--джерела' in арги:
        print('ендпойнти (bridge.виклик, bridge.виклик_а; перший параметр — ЗАПИТ показу):')
        for g in ендпойнти():
            print('  %s:%d %s' % (g.мод.шлях, g.вузол.lineno, g.імʼя))
        print('місця, де значення стає відповіддю моделі (поле запиту з КЛЮЧІ_A/КЛЮЧІ_B/ВКЛАДЕНІ_ДЖЕРЕЛА чи '
              'choices→message→content):')
        for (ф, л), кк in sorted(ДЖЕРЕЛА_МІСЦЯ.items()):
            print('  %s:%d %s' % (ф, л, ', '.join(sorted(кк))))
        return
    if '--звідки' in арги:
        # ланцюг викликів, яким М доходить у функцію: кожен рівень — викликачі з параметрами, що несуть М
        ціль, бачено = арги[арги.index('--звідки') + 1], set()
        черга = [(g, 0) for g in ХТО_КЛИКАВ if g.імʼя == ціль]
        while черга:
            g, р_ = черга.pop(0)
            if g in бачено or р_ > 6:
                continue
            бачено.add(g)
            for ім, ф, л, пп in sorted(ХТО_КЛИКАВ[g])[:8]:
                print('%s%s ← %s:%d %s (М у: %s)' % ('  ' * р_, g.імʼя, ф, л, ім, ', '.join(пп)))
                черга += [(h, р_ + 1) for h in ХТО_КЛИКАВ if h.імʼя == ім]
        for (ф, л), кк in sorted(ДЖЕРЕЛА_МІСЦЯ.items()):
            if any(fn.імʼя == ціль for fn in set(МОДУЛІ[os.path.basename(ф)[:-3]].функції.values())
                   if fn.вузол.lineno <= л <= fn.вузол.end_lineno) if os.path.basename(ф)[:-3] in МОДУЛІ else False:
                print('джерело в самій функції: %s:%d %s' % (ф, л, ', '.join(кк)))
        return
    if '--вибірка' in арги:
        і = арги.index('--вибірка')
        seed, n = int(арги[і + 1]), int(арги[і + 2])
        без = set()
        if '--без' in арги:
            for с_ in арги[арги.index('--без') + 1].split(','):
                без |= {ключ_звірки(x) for x in вибірка(р, int(с_.split(':')[0]), int(с_.split(':')[1]))[1]}
        пул, вв = вибірка(р, seed, n, без)
        print('пул %d (лічба %d без звірених раніше%s)' % (len(пул), len(р), ' і без ' + арги[арги.index('--без') + 1] if без else ''))
        for k, x in enumerate(вв, 1):
            рядки = open(x['файл'], encoding='utf-8').read().split('\n')
            print('#%d %s:%d · %s · %s · E=%s · джерело %s · ДОЛЯ=%s · %s' % (
                k, x['файл'].replace('джерела/', ''), x['рядок'], x['функція'], x['вираз'][:90], x['E'][:40],
                x['джерело'], x['доля'], x['пояснення'][:150]))
            for к in range(max(1, x['рядок'] - 3), min(len(рядки), x['рядок'] + 9)):
                print('    %d%s %s' % (к, '>' if к == x['рядок'] else ' ', рядки[к - 1][:180]))
        return
    print('модулів у обсязі: %d · функцій: %d' % (len(МОДУЛІ), sum(len(set(м.функції.values())) for м in МОДУЛІ.values())))
    for ф, e, t in схеми():
        print('схема %s: enum-вузлів %d, type-вузлів %d (декларація; перевіряє код з таблиці)' % (ф, e, t))
    print('ендпойнтів показу: %d · місць джерела: %d (`--джерела`)' % (len(ендпойнти()), len(ДЖЕРЕЛА_МІСЦЯ)))
    for вид in ('форма', 'перелік', 'перелік·пошук'):
        print('вид %s: перевірок %d · відкидають %d' % (вид, sum(1 for x in р if x['вид'] == вид),
                                                      sum(1 for x in відкидають if x['вид'] == вид)))
    for чиє in sorted(set(x['чия'] for x in р)):
        print('чия %s: перевірок %d · відкидають %d' % (чиє, sum(1 for x in р if x['чия'] == чиє),
                                                      sum(1 for x in відкидають if x['чия'] == чиє)))
    for дж, назва in (('A', 'сира відповідь моделі (поле запиту чи choices)'), ('B', 'повернене показом з попереднього виклику')):
        print('джерело %s — %s: перевірок %d · відкидають %d' % (дж, назва, sum(1 for x in р if x['джерело'] == дж),
                                                                 sum(1 for x in відкидають if x['джерело'] == дж)))
    г_ = collections.Counter(('raise' if x['пояснення'].startswith('raise') else 'предикат/присвоєння/assert' if x['пояснення'].startswith(('предикат', 'assert', 'вираз')) else 'інше (названо у таблиці)') for x in відкидають if x['доля'] == 'г')
    print('г за підкласом: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(г_.items())))
    print('б через слід нижче (16237): %d' % sum(1 for x in відкидають if x['доля'] == 'б' and x['пояснення'].startswith('слід нижче')))
    аз = [x for x in відкидають if x['доля'] == 'а']
    ар = [x for x in аз if x.get('слід_у_викликача')]
    print('а з `return <порожнє>`: %d; з них поруч з викликом є слід у ≥1 виклику: %d, у жодному: %d, викликів не знайдено: %d' % (
        sum(1 for x in аз if x.get('слід_у_викликача') is not None), sum(1 for x in ар if x['слід_у_викликача'][0] > 0),
        sum(1 for x in аз if x.get('слід_у_викликача') is not None and x['слід_у_викликача'][1] > 0 and x['слід_у_викликача'][0] == 0),
        sum(1 for x in аз if x.get('слід_у_викликача') is not None and x['слід_у_викликача'][1] == 0)))
    друк_рядків('поза ядром (корінь з відповіді моделі; поза лічбою)', поза)
    друк_рядків('запис коду (корінь лічби до 16239 за іменем, не з відповіді моделі; поза лічбою)', код)
    print('перевірок: %d · відкидають: %d · а: %d · б: %d · в: %d · г: %d · веде далі: %d' % (
        len(р), len(відкидають), ч['а'], ч['б'], ч['в'], ч['г'], len(далі)))


if __name__ == '__main__':
    головна()
