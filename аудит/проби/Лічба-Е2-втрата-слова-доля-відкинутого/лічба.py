# -*- coding: utf-8 -*-
"""ЛІЧБА Е2-втрата-слова: перевірки поля відповіді моделі (форма | перелік) у коді продукту і доля відкинутого.

Питання: скільки перевірок поля відповіді моделі відкидають значення за формою (тип, структура) чи за переліком
(enum, таблиця кодів) і що кожна робить із відкинутим: (а) порожнє мовчки; (б) «не записано» чи інший слід у записі;
(в) цитата чи слово стилістці; (г) інше — із назвою. Нічого не править; коду продукту не імпортує (AST).

ОБСЯГ: `джерела/*.py` і `zhnyvarka/**/*.py` без тестів, проб, приладів, стендів, батарей і воріт CI (список виключень —
ВИКЛЮЧЕНІ нижче, друкується). Python; JS (`джерела/показ`, `worker*.js`) — НЕ ВИМІРЯНО (лише вказано). JSON-схеми
(`*.schema.json`) — окремі лічильники `enum`-вузлів (декларація, перевіряє її код з таблиці).

ПОТІК ЗНАЧЕННЯ (як прилад кореня, але від відповіді моделі): корінь «відповідь моделі» — (1) параметри з іменами
КОРЕНІ_ПАРАМЕТРІВ; (2) ключі `відповідь_моделі`/`відповідь`/… у `.get`/`[ ]`; (3) результат викликів розбору тексту
моделі (РОЗБІР: `json.loads`, `розбір`, `розібрати_json`, …). Далі — присвоєння, цикли, розпакування, `.get/.items/…`,
`dict/list/str/…`, виклики функцій продукту (параметри й повернення, неподільний зв'язок крізь `from … import`).
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
Запуск з кореня: `python3 аудит/проби/Лічба-Е2-втрата-слова-доля-відкинутого/лічба.py [--таблиця ФАЙЛ] [--звірка]
[--два-значення]`; останній рядок — `перевірок: N · відкидають: M · а: … · б: … · в: … · г: … · веде далі: K`."""
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
            if м in МОДУЛІ and і in МОДУЛІ[м].функції:
                return МОДУЛІ[м].функції[і]
    elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in мод.імпорти:
        м, і = мод.імпорти[f.value.id]
        цілий = і or м
        if цілий in МОДУЛІ and f.attr in МОДУЛІ[цілий].функції:
            return МОДУЛІ[цілий].функції[f.attr]
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
                res.append((н, н.args[0], 'форма', полярність(н)))
        elif isinstance(н, ast.Compare):
            if len(н.ops) == 1 and isinstance(н.ops[0], (ast.In, ast.NotIn)):
                л, ц = н.left, н.comparators[0]
                if isinstance(л, ast.Constant):
                    continue
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


def читає_значення(вузли, імʼя):
    if not імʼя:
        return False

    def ход(х):
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
            if імена and СЛІД.search(імена):
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


def без_слідових(гілка):
    """Гілка без стейтментів-слідів (`…не_взято.append(…)`, `незнайомі += …`): вони значення не ведуть далі."""
    res = []
    for х in гілка:
        if isinstance(х, ast.Expr) and isinstance(х.value, ast.Call) and isinstance(х.value.func, ast.Attribute) \
                and х.value.func.attr in ('append', 'extend', 'add', 'update', 'setdefault') \
                and СЛІД.search(ast.unparse(х.value.func.value)):
            continue
        if isinstance(х, ast.AugAssign) and СЛІД.search(ast.unparse(х.target)):
            continue
        if isinstance(х, ast.Assign) and any(СЛІД.search(ast.unparse(ц)) for ц in х.targets):
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


def класифікувати(fn, пер, E, вид, поз):
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
    if isinstance(р, ast.If) and (х is р.test):
        def природа(гілка):
            """accept — гілка читає значення (веде далі); reject — не читає й лише скидає/пише слід/кидає виняток."""
            if not гілка:
                return 'порожня'
            if читає_значення(без_слідових(гілка), корінь):
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
            шлях = відкинуте_проходження(б, р)
            if шлях and not читає_значення(без_слідових(шлях), корінь):
                д, пояс = доля(шлях, корінь)
                if д == 'г' and пояс.startswith('інше') and isinstance(шлях[-1], ast.Return):
                    # звичайний результат функції після охоронюваного блоку: значення туди не потрапило (16222)
                    return 'а', 'проходить до загального результату: ' + пояс[6:50], діапазон_гілки(шлях)
                return д, 'проходить далі: ' + пояс, діапазон_гілки(шлях)
            після = стейтменти_після(б, р)
            if читає_значення(після, корінь):
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
        if читає_значення([вираз], корінь):
            return 'далі', 'підміна читає той самий корінь', None
        if isinstance(вираз, ast.Constant) and isinstance(вираз.value, str) and re.fullmatch(r'[a-z][a-z_:()=, %s]{5,}', вираз.value):
            return 'б', 'підміна кодом причини «%s»' % вираз.value[:40], (вираз.lineno, getattr(вираз, 'end_lineno', вираз.lineno))
        д, пояс = доля([ast.Expr(value=вираз)] if порожнє_значення(вираз) is False else [ast.Return(value=вираз)], корінь)
        діап = (вираз.lineno, getattr(вираз, 'end_lineno', вираз.lineno))
        return д, 'підміна: ' + пояс, діап
    if isinstance(р, ast.comprehension):
        if not поз:
            return 'далі', 'умова в генераторі виключає протилежне (негативна перевірка)', None
        if корінь in {н.id for н in ast.walk(р.target) if isinstance(н, ast.Name)}:
            return 'а', 'відсів у генераторі (елемент зникає)', None
        # корінь із зовнішньої області (`next((x[к] for к in … if isinstance(x, dict)), None)`): значення не зникає,
        # якщо його читає наступний код (інша форма того самого значення)
        ст = р
        while ст in б and not isinstance(ст, ast.stmt):
            ст = б[ст]
        локальні = set(fn.параметри) | {н.id for у in ast.walk(fn.вузол) if isinstance(у, (ast.Assign, ast.For, ast.AnnAssign))
                                        for н in ast.walk(у.targets[0] if isinstance(у, ast.Assign) else у.target)
                                        if isinstance(н, ast.Name)}
        if корінь in локальні and читає_значення(стейтменти_після(б, ст), корінь):
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
        if для:
            ф = min(для, key=lambda x: x.lineno)
            заперечено = isinstance(ф.test, ast.UnaryOp) and isinstance(ф.test.op, ast.Not)
            # поз: істина = прийняте; умова `if N` (не заперечена): тіло — прийняте при поз
            гілка = ф.orelse if (поз and not заперечено) or (not поз and заперечено) else ф.body
            if not гілка:
                після = стейтменти_після(б, ф)
                if читає_значення(після, корінь):
                    return 'далі', 'результат перевірки в «%s», далі значення читається' % N, None
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
    міжфункційно()
    рядки = []
    for мод in МОДУЛІ.values():
        if мод.імʼя not in МОДУЛЬ_ЧИЯ:
            continue
        for fn in sorted(set(мод.функції.values()), key=lambda f: f.вузол.lineno):
            п = Потік(fn)
            п.прогін(fn.вузол)
            for пер, E, вид, поз in знайти_перевірки(fn, п):
                д, пояс, діап = класифікувати(fn, пер, E, вид, поз)
                if вид == 'перелік·пошук' and д == 'г' and пояс.startswith(('предикат', 'контекст', 'вираз', 'assert')):
                    continue      # пошук у таблиці як переклад значення, не як перевірка в умові
                рядки.append(dict(файл=мод.шлях, рядок=пер.lineno, функція=fn.імʼя, поле=поле_з(E), чия=чия(мод.імʼя),
                                  вид=вид, E=джерело_шляху(E), доля=д, пояснення=пояс, діапазон=діап, вираз=джерело_шляху(пер)[:70].replace('\n', ' '),
                                  вузол=пер, fn=fn))
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
            print('  %s:%d · %s · %s · доля(стат.) %s · відкинуту гілку виконано: %s\n      E=%s → %s' % (
                x['файл'], x['рядок'], x['вид'], x['вираз'][:60], x['доля'], відкинуто, x['E'][:50], знач))
    return


# ───────────────────────── самоперевірка: фікстура на кожен клас хибної назви ─────────────────────────
# Кожна фікстура — функція в модулі з ядра (`мовний_шар`), де значення йде від відповіді моделі (`об`); очікування —
# доля, яку названо ПРАВИЛЬНО очима. Старі правила (main до цього кроку) називали: 16221 — «веде далі», 16222 — «г»,
# 16223 — «веде далі», 16224 — «в». `--самоперевірка` друкує кожну фікстуру й виходить з кодом 1 при розбіжності.
ФІКСТУРИ_ТЕКСТ = '''
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
'''
# (функція, перевірка) → очікувана доля; `далі` — «веде далі»
ФІКСТУРИ = [
    ('16221', 'ф_16221_тип', 'isinstance(об, dict)', 'г'),
    ('16221', 'ф_16221_перелік', 'об not in ПЕРЕЛІК_Ф', 'г'),
    ('16222', 'ф_16222_охоронений_if', 'isinstance(т, dict)', 'а'),
    ('16223', 'ф_16223_запасне_значення', 'isinstance(про, str)', 'а'),
    ('16223', 'ф_16223_відсів_нижче', 'isinstance(фото, str)', 'а'),
    ('16223', 'ф_16223_змінна_циклу', 'isinstance(ц, str)', 'а'),
    ('16224', 'ф_16224_інше_джерело', 'isinstance(об, dict)', 'г'),
    ('16224', 'ф_16224_чужий_запис', 'isinstance(ош, (list, tuple))', 'а'),
]


def самоперевірка(мод=None):
    """Фікстури → класифікація; `мод` — модуль лічби (для порівняння зі старою версією). → число розбіжностей."""
    import tempfile
    мод = мод or sys.modules[__name__]
    з = tempfile.mkdtemp()
    шлях = os.path.join(з, 'мовний_шар.py')
    open(шлях, 'w', encoding='utf-8').write(ФІКСТУРИ_ТЕКСТ)
    мод.файли = lambda: [шлях]
    мод.МОДУЛІ.clear()
    рядки = мод.зібрати()
    за = {(x['функція'], x['вираз']): x['доля'] for x in рядки}
    поганих = 0
    for клас, функція, вираз, очікується in ФІКСТУРИ:
        одержано = за.get((функція, вираз), 'нема')
        ок = одержано == очікується
        поганих += not ок
        print('фікстура %s · %s · %s · очікується %s · одержано %s · %s' % (
            клас, функція, вираз, очікується, одержано, 'ОК' if ок else 'РОЗБІЖНІСТЬ'))
    return поганих


def головна():
    арги = sys.argv[1:]
    if '--самоперевірка' in арги:
        sys.exit(1 if самоперевірка() else 0)
    р = зібрати()
    відкидають, далі, ч = підсумок(р)
    if '--таблиця' in арги:
        шлях = арги[арги.index('--таблиця') + 1]
        with open(шлях, 'w', encoding='utf-8') as ф:
            ф.write('| файл:рядок | поле | чия відповідь | вид | доля | що робить гілка відкинутого | перевірка |\n|---|---|---|---|---|---|---|\n')
            for x in sorted(р, key=lambda x: (x['файл'], x['рядок'])):
                ф.write('| `%s:%d` | %s | %s | %s | %s | %s%s | `%s` |\n' % (
                    x['файл'].replace('джерела/', ''), x['рядок'], x['поле'], x['чия'], x['вид'],
                    {'далі': 'веде далі'}.get(x['доля'], x['доля']), x['пояснення'].replace('|', '/'),
                    (' · слід у викликачі: %d з %d' % x['слід_у_викликача']) if x.get('слід_у_викликача') else '',
                    x['вираз'].replace('|', '/').replace('`', "'")))
    if '--два-значення' in арги:
        два_значення(р)
        return
    if '--звірка' in арги:
        import random
        random.seed(16207)
        for x in random.sample(р, min(40, len(р))):
            print('%s:%d · %s · %s · %s · %s · %s · %s' % (x['файл'], x['рядок'], x['функція'], x['поле'], x['вид'], x['доля'], x['пояснення'], x['вираз']))
        return
    print('модулів у обсязі: %d · функцій: %d' % (len(МОДУЛІ), sum(len(set(м.функції.values())) for м in МОДУЛІ.values())))
    for ф, e, t in схеми():
        print('схема %s: enum-вузлів %d, type-вузлів %d (декларація; перевіряє код з таблиці)' % (ф, e, t))
    for вид in ('форма', 'перелік', 'перелік·пошук'):
        print('вид %s: перевірок %d · відкидають %d' % (вид, sum(1 for x in р if x['вид'] == вид),
                                                      sum(1 for x in відкидають if x['вид'] == вид)))
    for чиє in sorted(set(x['чия'] for x in р)):
        print('чия %s: перевірок %d · відкидають %d' % (чиє, sum(1 for x in р if x['чия'] == чиє),
                                                      sum(1 for x in відкидають if x['чия'] == чиє)))
    г_ = collections.Counter(('raise' if x['пояснення'].startswith('raise') else 'предикат/присвоєння/assert' if x['пояснення'].startswith(('предикат', 'assert', 'вираз')) else 'інше (названо у таблиці)') for x in відкидають if x['доля'] == 'г')
    print('г за підкласом: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(г_.items())))
    аз = [x for x in відкидають if x['доля'] == 'а']
    ар = [x for x in аз if x.get('слід_у_викликача')]
    print('а з `return <порожнє>`: %d; з них поруч з викликом є слід у ≥1 виклику: %d, у жодному: %d, викликів не знайдено: %d' % (
        sum(1 for x in аз if x.get('слід_у_викликача') is not None), sum(1 for x in ар if x['слід_у_викликача'][0] > 0),
        sum(1 for x in аз if x.get('слід_у_викликача') is not None and x['слід_у_викликача'][1] > 0 and x['слід_у_викликача'][0] == 0),
        sum(1 for x in аз if x.get('слід_у_викликача') is not None and x['слід_у_викликача'][1] == 0)))
    print('перевірок: %d · відкидають: %d · а: %d · б: %d · в: %d · г: %d · веде далі: %d' % (
        len(р), len(відкидають), ч['а'], ч['б'], ч['в'], ч['г'], len(далі)))


if __name__ == '__main__':
    головна()
