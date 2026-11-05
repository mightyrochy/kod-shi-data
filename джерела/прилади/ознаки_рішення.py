"""Вивід ваги шкали й арифметичний вхід пари для приладу ознак обличчя."""
import ast, copy
from collections import defaultdict


def прозовий(в):
    """Речення, а не слово-клас: сталий рядок з трьох і більше слів ніколи не є значенням класу."""
    return isinstance(в, ast.Constant) and isinstance(в.value, str) and len(в.value.split()) >= 3


def форматований_текст(в):
    """Впізнає форматування чи злиття рядків, відрізняючи його від простого класу-слова."""
    рядок = lambda н: isinstance(н, ast.Constant) and isinstance(н.value, str)
    def рядковий_операнд(н):
        """Розпізнає обидві текстові гілки всередині злиття, не називаючи сам клас форматуванням."""
        return рядок(н) or форматований_текст(н) or isinstance(н, ast.IfExp) \
            and рядковий_операнд(н.body) and рядковий_операнд(н.orelse)
    return isinstance(в, ast.JoinedStr) or прозовий(в) or isinstance(в, ast.BinOp) and (
        isinstance(в.op, ast.Mod) and рядок(в.left) or isinstance(в.op, ast.Add)
        and any(рядковий_операнд(н) for н in (в.left, в.right))) or \
        isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in ('format', 'join') \
        and рядок(в.func.value)


def поля_підписів(дерева):
    """Знаходить поля, які всі писачі форматують, а читачі лише зливають у текст чи копіюють.

    Клас-слово та поле, що бере участь у рішенні, не стають підписом через один текстовий читач.
    """
    записи, читачі = defaultdict(list), defaultdict(list)

    def ключ(в):
        """Читає сталий ключ індексу або get."""
        н = в.slice if isinstance(в, ast.Subscript) else в.args[0] if isinstance(в, ast.Call) \
            and isinstance(в.func, ast.Attribute) and в.func.attr == 'get' and в.args else None
        return н.value if isinstance(н, ast.Constant) and isinstance(н.value, str) else None

    def текстове_тіло(тіло):
        """Перевіряє, що охорона наявності підпису лише дописує форматований текст."""
        return bool(тіло) and all(isinstance(і, ast.Assign) and форматований_текст(і.value) for і in тіло)

    for дерево in дерева:
        батьки = {id(д): в for в in ast.walk(дерево) for д in ast.iter_child_nodes(в)}
        for в in ast.walk(дерево):
            if isinstance(в, ast.Assign):
                for ц in в.targets:
                    if isinstance(ц, ast.Subscript) and (к := ключ(ц)) is not None:
                        записи[к].append(в.value)
            elif isinstance(в, (ast.AnnAssign, ast.AugAssign)) and isinstance(в.target, ast.Subscript):
                if (к := ключ(в.target)) is not None:
                    записи[к].append(в.value if isinstance(в, ast.AnnAssign) else ast.Constant(0))
            elif isinstance(в, ast.Dict):
                for к, з in zip(в.keys, в.values):
                    if isinstance(к, ast.Constant) and isinstance(к.value, str):
                        записи[к.value].append(з)
            elif isinstance(в, ast.Call):
                for к in в.keywords:
                    if к.arg:
                        записи[к.arg].append(к.value)
            к = ключ(в)
            if к is not None and (isinstance(в, ast.Call) or isinstance(в.ctx, ast.Load)):
                читачі[к].append((в, батьки))
    кандидати = {к for к, значення in записи.items() if any(форматований_текст(з) for з in значення)
                 and all(форматований_текст(з) or ключ(з) == к or isinstance(з, ast.Constant)
                         and з.value is None for з in значення)}
    вихід = set()
    for к in кандидати:
        лише_текст, є_підпис = True, False
        for читач, батьки in читачі[к]:
            н, дозволено = читач, False
            while (б := батьки.get(id(н))) is not None:
                if форматований_текст(б):
                    дозволено, є_підпис = True, True
                    break
                власник = батьки.get(id(б))
                if isinstance(б, ast.keyword) and б.arg == к and isinstance(власник, ast.Call) \
                        and isinstance(власник.func, ast.Name) and власник.func.id == 'dict':
                    дозволено = True
                    break
                if isinstance(б, ast.Dict) and any(з is н and isinstance(ім, ast.Constant) and ім.value == к
                                                  for ім, з in zip(б.keys, б.values)):
                    дозволено = True
                    break
                if isinstance(б, ast.If) and б.test is н and not б.orelse and текстове_тіло(б.body):
                    дозволено = True
                    break
                if isinstance(б, (ast.Compare, ast.Call, ast.stmt)):
                    break
                н = б
            лише_текст &= дозволено
        if лише_текст and є_підпис:
            вихід.add(к)
    return вихід


def межі_сортування(ф):
    """Знаходить тотожну нижню межу: ключ елемента черги не нижчий за ключ її відсортованого початку."""
    вузли = list(вузли_тіла(ф))
    присвоєння = []
    for в in вузли:
        if isinstance(в, ast.Assign):
            for ц in в.targets:
                if isinstance(ц, ast.Tuple) and isinstance(в.value, ast.Tuple) and len(ц.elts) == len(в.value.elts):
                    присвоєння.extend(zip(ц.elts, в.value.elts))
                else:
                    присвоєння.append((ц, в.value))
    вихід = set()
    лямбди = {ц.id: з for ц, з in присвоєння if isinstance(ц, ast.Name) and isinstance(з, ast.Lambda)}
    for ц, з in присвоєння:
        if not (isinstance(ц, ast.Name) and isinstance(з, ast.Call) and isinstance(з.func, ast.Name)
                and з.func.id == 'sorted' and з.args):
            continue
        q = ц.id
        к = next((к.value for к in з.keywords if к.arg == 'key'), None)
        if not (isinstance(к, ast.Lambda) and len(к.args.args) == 1) or any(
                к.arg == 'reverse' and not (isinstance(к.value, ast.Constant) and к.value.value is False) for к in з.keywords):
            continue
        вираз = к.body.elts[0] if isinstance(к.body, ast.Tuple) and к.body.elts else к.body
        if not (isinstance(вираз, ast.Call) and isinstance(вираз.func, ast.Name) and len(вираз.args) == 1
                and isinstance(вираз.args[0], ast.Name) and вираз.args[0].id == к.args.args[0].arg
                and вираз.func.id in лямбди):
            continue
        f = вираз.func.id
        л = лямбди[f]
        if any(isinstance(н, ast.Call) for н in ast.walk(л.body)):
            continue
        замикання = {н.id for н in ast.walk(л.body) if isinstance(н, ast.Name)} - {а.arg for а in л.args.args}
        стабільна = all(інша is з or isinstance(інша, ast.ListComp) and isinstance(інша.elt, ast.Name)
                       and len(інша.generators) == 1 and isinstance(інша.generators[0].iter, ast.Name)
                       and інша.generators[0].iter.id == q and isinstance(інша.generators[0].target, ast.Name)
                       and інша.elt.id == інша.generators[0].target.id
                       for тар, інша in присвоєння if isinstance(тар, ast.Name) and тар.id == q)
        if not стабільна or any(isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute)
                               and isinstance(н.func.value, ast.Name) and н.func.value.id == q for н in вузли):
            continue
        for цикл in (н for н in вузли if isinstance(н, ast.While) and isinstance(н.test, ast.Name) and н.test.id == q):
            всередині = list(ast.walk(цикл))
            псевдоніми = set(замикання)
            while True:
                нові = {ц.id for н in всередині if isinstance(н, ast.Assign) and isinstance(н.value, ast.Name)
                        and н.value.id in псевдоніми for ц in н.targets if isinstance(ц, ast.Name)} - псевдоніми
                if not нові:
                    break
                псевдоніми |= нові
            змінені = set()
            for н in всередині:
                if isinstance(н, ast.Name) and isinstance(н.ctx, ast.Store):
                    змінені.add(н.id)
                if isinstance(н, (ast.Subscript, ast.Attribute)) and isinstance(н.ctx, ast.Store):
                    корінь = н.value
                    while isinstance(корінь, (ast.Subscript, ast.Attribute)):
                        корінь = корінь.value
                    if isinstance(корінь, ast.Name):
                        змінені.add(корінь.id)
                if isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and isinstance(н.func.value, ast.Name) \
                        and н.func.attr in ('append', 'extend', 'pop', 'clear', 'update', 'sort', 'reverse', 'remove'):
                    змінені.add(н.func.value.id)
            if з in всередині or змінені & (псевдоніми | {f}):
                continue
            межі = set()
            for і in цикл.body:
                if isinstance(і, ast.Assign) and len(і.targets) == 1 and isinstance(і.targets[0], ast.Name) \
                        and isinstance(і.value, ast.Call) and isinstance(і.value.func, ast.Name) and і.value.func.id == f \
                        and len(і.value.args) == 1 and isinstance(і.value.args[0], ast.Subscript):
                    а = і.value.args[0]
                    if isinstance(а.value, ast.Name) and а.value.id == q and isinstance(а.slice, ast.Constant) and а.slice.value == 0:
                        межі.add(і.targets[0].id)
            межі = {м for м in межі if sum(isinstance(н, ast.Name) and isinstance(н.ctx, ast.Store)
                                         and н.id == м for н in всередині) == 1}
            for в in всередині:
                if not (isinstance(в, ast.ListComp) and len(в.generators) == 1
                        and isinstance(в.generators[0].iter, ast.Name) and в.generators[0].iter.id == q
                        and isinstance(в.generators[0].target, ast.Name)):
                    continue
                for т in (н for у in в.generators[0].ifs for н in ast.walk(у) if isinstance(н, ast.Compare)):
                    if len(т.ops) == 1 and isinstance(т.ops[0], ast.GtE) and isinstance(т.comparators[0], ast.Name) \
                            and т.comparators[0].id in межі and isinstance(т.left, ast.Call) \
                            and isinstance(т.left.func, ast.Name) and т.left.func.id == f and len(т.left.args) == 1 \
                            and isinstance(т.left.args[0], ast.Name) and т.left.args[0].id == в.generators[0].target.id:
                        вихід.add(id(т))
    return вихід


def вузли_тіла(ф):
    """Обходить власне тіло функції без вкладених функцій і класів."""
    вузол = ф if isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) else ф.вузол
    стек = list(вузол.body) if isinstance(вузол.body, list) else [вузол.body]
    while стек:
        в = стек.pop()
        yield в
        if not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            стек.extend(ast.iter_child_nodes(в))


def кутові_пари(ф):
    """Впізнає різницю кутів, яку згортають за повним обертом 360°."""
    return {id(н) for в in вузли_тіла(ф) if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Mod)
            and isinstance(в.right, ast.Constant) and в.right.value == 360
            for н in ast.walk(в.left) if isinstance(н, ast.BinOp) and isinstance(н.op, ast.Sub)}


def числові_цикли(ф):
    """Розрізняє прогресію кандидатів та предикат звуження числового інтервалу."""
    вузли = list(вузли_тіла(ф))
    прогресії, формули, межі = set(), set(), set()
    повернені = {в.value.id for в in вузли if isinstance(в, ast.Return) and isinstance(в.value, ast.Name)}
    for в in вузли:
        if isinstance(в, ast.While):
            for к in ast.walk(в):
                if isinstance(к, ast.Call) and isinstance(к.func, ast.Attribute) and к.func.attr == 'append' \
                        and isinstance(к.func.value, ast.Name) and len(к.args) == 1 \
                        and isinstance(к.args[0], ast.BinOp) and isinstance(к.args[0].op, ast.Add):
                    ім = к.func.value.id
                    if any(isinstance(н, ast.Subscript) and isinstance(н.value, ast.Name) and н.value.id == ім
                           for н in ast.walk(к.args[0])) and any(isinstance(н, ast.Name) and н.id == ім for н in ast.walk(в.test)):
                        прогресії.add(ім)
        if not isinstance(в, (ast.For, ast.While)):
            continue
        for с in в.body:
            if not (isinstance(с, ast.Assign) and len(с.targets) == 1 and isinstance(с.targets[0], ast.Name)
                    and isinstance(с.value, ast.BinOp) and isinstance(с.value.op, ast.Div)
                    and isinstance(с.value.right, ast.Constant) and с.value.right.value == 2
                    and isinstance(с.value.left, ast.BinOp) and isinstance(с.value.left.op, ast.Add)
                    and isinstance(с.value.left.left, ast.Name) and isinstance(с.value.left.right, ast.Name)):
                continue
            середина = с.targets[0].id
            кінці = {с.value.left.left.id, с.value.left.right.id}
            for г in в.body:
                if not (isinstance(г, ast.If) and len(г.body) == len(г.orelse) == 1):
                    continue
                присвоєння = г.body + г.orelse
                if all(isinstance(а, ast.Assign) and len(а.targets) == 1 and isinstance(а.targets[0], ast.Name)
                       and isinstance(а.value, ast.Name) and а.value.id == середина for а in присвоєння) \
                        and {а.targets[0].id for а in присвоєння} == кінці:
                    формули.update(id(т) for т in ast.walk(г.test) if isinstance(т, ast.Compare))
                    межі.update(кінці)
    початки = {id(в) for в in вузли if isinstance(в, ast.Assign) and isinstance(в.value, ast.List)
               and any(isinstance(ц, ast.Name) and ц.id in прогресії for ц in в.targets)}
    return початки, формули, bool(межі & повернені), bool(прогресії & повернені)


def множини_функції(ф):
    """Виводить локальні імена множин із побудови й псевдонімів, включно із замиканням."""
    визначення = defaultdict(list)
    for в in вузли_тіла(ф):
        if isinstance(в, ast.Assign):
            for ц in в.targets:
                if isinstance(ц, ast.Name):
                    визначення[ц.id].append(в.value)
    затінені = set(визначення) | set(ф.позиційні + ф.іменні)
    вихід = set(getattr(ф.батько, 'множини', ())) - затінені

    def множина(в):
        """Розрізняє множину та число без виконання виразу."""
        return isinstance(в, (ast.Set, ast.SetComp)) or isinstance(в, ast.Name) and в.id in вихід \
            or isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ('set', 'frozenset') \
            or isinstance(в, ast.IfExp) and множина(в.body) and множина(в.orelse) \
            or isinstance(в, ast.BinOp) and isinstance(в.op, (ast.BitOr, ast.BitAnd, ast.BitXor, ast.Sub)) \
            and множина(в.left) and множина(в.right)
    for _ in range(len(визначення) + 1):
        нові = {ім for ім, вирази in визначення.items() if all(множина(в) for в in вирази)} - вихід
        вихід.update(нові)
        if not нові:
            break
    return frozenset(вихід)


def вільні_свідки_пари(ф):
    """Впізнає спільну опорну точку двох вільних областей у пошуку найближчої пари.

    Одне вільне обмеження бере точку другого; коли вільні обидва, однакова опора
    є свідком нульової відстані. Пошук min над декартовим добутком відрізняє
    геометричний свідок від підстановки значень двох фізичних ознак.
    """
    вузли = list(вузли_тіла(ф))
    інші = {}
    def відсутній(т):
        """Повертає параметр у перевірці `параметр is None`."""
        return т.left.id if isinstance(т, ast.Compare) and isinstance(т.left, ast.Name) \
            and т.left.id in ф.позиційні + ф.іменні and len(т.ops) == 1 and isinstance(т.ops[0], ast.Is) \
            and isinstance(т.comparators[0], ast.Constant) and т.comparators[0].value is None else None
    for в in вузли:
        if isinstance(в, ast.If) and відсутній(в.test) and len(в.body) == 1 and isinstance(в.body[0], ast.Return):
            р = в.body[0].value
            if isinstance(р, ast.Tuple) and len(р.elts) == 2 and ast.dump(р.elts[0]) == ast.dump(р.elts[1]) \
                    and isinstance(р.elts[0], ast.Subscript) and isinstance(р.elts[0].value, ast.Name):
                інші[відсутній(в.test)] = р.elts[0].value.id
    добутки = [в for в in вузли if isinstance(в, ast.Call) and isinstance(в.func, ast.Name)
               and в.func.id == 'min' and в.args and isinstance(в.args[0], ast.GeneratorExp)
               and len(в.args[0].generators) == 2]
    вихід = set()
    for в in вузли:
        if not (isinstance(в, ast.If) and isinstance(в.test, ast.BoolOp) and isinstance(в.test.op, ast.And)
                and len(в.test.values) == 2 and len(в.body) == 1 and isinstance(в.body[0], ast.Return)):
            continue
        а, б = (відсутній(т) for т in в.test.values)
        р = в.body[0].value
        if а and б and інші.get(а) == б and інші.get(б) == а and isinstance(р, ast.Tuple) and len(р.elts) == 2 \
                and ast.dump(р.elts[0]) == ast.dump(р.elts[1]) and isinstance(р.elts[0], ast.Constant) \
                and isinstance(р.elts[0].value, (int, float)) and any(
                    {г.iter.id for г in д.args[0].generators if isinstance(г.iter, ast.Name)} == {а, б} for д in добутки):
            вихід.add(id(в.test))
    return вихід


def шкали_ваги(аналіз):
    """Знаходить функції, чий числовий вихід безпосередньо пишуть у вагу протоколу.

    Зворотний потік проходить локальні псевдоніми, розпаковку й позицію кортежу. Він
    зупиняється на функції шкали: її аргументи ще є вимірами, а вихід уже є вагою.
    """
    вихід = defaultdict(set)
    визначення_функцій, виклики, черга = {}, defaultdict(list), []
    поля = аналіз.ваги
    for модуль in аналіз.модулі.values():
        for ф in модуль.функції.values():
            вузли = list(вузли_тіла(ф))
            визначення = defaultdict(list)
            витоки = []

            def вага(ціль):
                """Впізнає запис у числове поле знахідки з протоколу."""
                return isinstance(ціль, ast.Subscript) and isinstance(ціль.slice, ast.Constant) \
                    and ціль.slice.value in поля

            def запис(ціль, значення, позиція=None):
                """Зберігає визначення псевдоніма або витік ваги разом із позицією."""
                if isinstance(ціль, ast.Name):
                    визначення[ціль.id].append((значення, позиція))
                elif isinstance(ціль, (ast.Tuple, ast.List)):
                    for і, е in enumerate(ціль.elts):
                        запис(е, значення, і)
                elif вага(ціль):
                    витоки.append((значення, позиція))

            for в in вузли:
                if isinstance(в, ast.Assign):
                    for ціль in в.targets:
                        запис(ціль, в.value)
                elif isinstance(в, ast.AnnAssign) and в.value is not None:
                    запис(в.target, в.value)
                elif isinstance(в, ast.Dict):
                    витоки.extend((з, None) for к, з in zip(в.keys, в.values)
                                  if isinstance(к, ast.Constant) and к.value in поля)
                    if any(isinstance(к, ast.Constant) and к.value == 'правило' for к in в.keys):
                        витоки.extend((з, None) for к, з in zip(в.keys, в.values)
                                      if isinstance(к, ast.Constant) and к.value == 'сила')
                elif isinstance(в, ast.Call):
                    витоки.extend((к.value, None) for к in в.keywords if к.arg in поля)
                    if any(к.arg == 'правило' for к in в.keywords):
                        витоки.extend((к.value, None) for к in в.keywords if к.arg == 'сила')
                    for ціль in аналіз.викликані(модуль, в.func, ф):
                        виклики[ціль.повне].append((ф, в))
            визначення_функцій[ф.повне] = визначення
            черга.extend((ф, в, п) for в, п in витоки)

    бачені = set()
    while черга:
        ф, в, позиція = черга.pop()
        ключ = (ф.повне, id(в), позиція)
        if ключ in бачені:
            continue
        бачені.add(ключ)
        if isinstance(в, ast.Name):
            визначення = визначення_функцій[ф.повне]
            черга.extend((ф, з, п if п is not None else позиція) for з, п in визначення[в.id])
            if в.id in ф.позиційні + ф.іменні:
                for батько, виклик in виклики[ф.повне]:
                    іменні = {к.arg: к.value for к in виклик.keywords}
                    аргумент = іменні.get(в.id)
                    if аргумент is None and в.id in ф.позиційні:
                        індекс = ф.позиційні.index(в.id)
                        if індекс < len(виклик.args) and not any(isinstance(а, ast.Starred) for а in виклик.args):
                            аргумент = виклик.args[індекс]
                    if аргумент is not None:
                        черга.append((батько, аргумент, позиція))
        elif isinstance(в, (ast.Tuple, ast.List)) and позиція is not None and -len(в.elts) <= позиція < len(в.elts):
            черга.append((ф, в.elts[позиція], None))
        elif isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and type(в.slice.value) is int:
            черга.append((ф, в.value, в.slice.value))
        elif isinstance(в, ast.IfExp):
            черга.extend(((ф, в.body, позиція), (ф, в.orelse, позиція)))
        elif isinstance(в, ast.Call):
            цілі = аналіз.викликані(ф.модуль, в.func, ф)
            for ціль in цілі:
                вихід[ціль.повне].add(позиція)
            if not цілі and isinstance(в.func, ast.Name) and в.func.id in ('round', 'float', 'min', 'max'):
                черга.extend((ф, а, позиція) for а in в.args)
    return dict(вихід)


def пари_функції(ф):
    """Знаходить віднімання незалежних параметрів у функції числового рішення.

    Залежності локальних змінних зберігають параметри походження: розпаковані
    координати одного hex не стають двома незалежними входами. Функції, які
    збирають записи чи колекції, лишаються споживачами; вхід шукається в рахунку.
    """
    вузли = list(вузли_тіла(ф))
    повернення = [в.value for в in вузли if isinstance(в, ast.Return) and в.value is not None]
    if not повернення:
        return []
    if any(isinstance(в, (ast.Dict, ast.List, ast.ListComp, ast.DictComp)) or
           isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ('dict', 'list', 'set')
           for в in повернення):
        return []
    # Кортеж координат є перетворенням простору. Числове рішення може мати
    # другим елементом пояснення, але не другу координату того самого кольору.
    текстові = set()
    for в in вузли:
        if isinstance(в, ast.Assign) and any(isinstance(н, ast.JoinedStr) or
                isinstance(н, ast.Constant) and isinstance(н.value, str) for н in ast.walk(в.value)):
            текстові.update(н.id for ц in в.targets for н in ast.walk(ц) if isinstance(н, ast.Name))
    if any(isinstance(в, ast.Tuple) and len(в.elts) != 2 and not any(isinstance(н, ast.JoinedStr) or
           isinstance(н, ast.Name) and н.id in текстові or
           isinstance(н, ast.Constant) and isinstance(н.value, str) for н in ast.walk(в))
           for в in повернення):
        return []
    залежності = {ім: {ім} for ім in ф.позиційні + ф.іменні}

    def залежить(в):
        """Повертає параметри походження значень виразу."""
        if isinstance(в, ast.Name):
            return залежності.get(в.id, set())
        if isinstance(в, ast.Subscript):
            # Спільний селектор осі не об'єднує джерела двох записів кольору.
            return залежить(в.value)
        if isinstance(в, ast.Call):
            return set().union(*(залежить(н) for н in [*в.args, *(к.value for к in в.keywords)]))
        return set().union(*(залежить(н) for н in ast.iter_child_nodes(в)))

    присвоєння = [(в.targets, в.value) for в in вузли if isinstance(в, ast.Assign)]
    присвоєння += [([в.target], в.value) for в in вузли if isinstance(в, ast.AnnAssign) and в.value is not None]
    for _ in range(len(присвоєння) + 1):
        зміни = False
        for цілі, значення in присвоєння:
            for ціль in цілі:
                пари = zip(ціль.elts, значення.elts) if isinstance(ціль, (ast.Tuple, ast.List)) \
                    and isinstance(значення, (ast.Tuple, ast.List)) else [(ціль, значення)]
                for ц, з in пари:
                    for ім in (н.id for н in ast.walk(ц) if isinstance(н, ast.Name)):
                        нові = залежить(з) - залежності.get(ім, set())
                        if нові:
                            залежності.setdefault(ім, set()).update(нові)
                            зміни = True
        if not зміни:
            break
    вихід = []
    for в in вузли:
        if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Sub):
            ліві, праві = залежить(в.left), залежить(в.right)
            if ліві and праві and ліві.isdisjoint(праві):
                вихід.append((в, ліві, праві))
    return sorted(вихід, key=lambda п: (п[0].lineno, п[0].col_offset))


_ЧИСЛОВІ_ВБУДОВАНІ = frozenset(("abs", "min", "max", "sum", "float", "int", "round", "pow", "range", "len", "divmod"))


def функція_формула(ф):
    """Чисте числове перетворення завдовжки від 12 кроків (див. `_чиста_функція`)."""
    повернення = _чиста_функція(ф)
    if повернення is None:
        return False
    return _кроки(ф) >= 12 and all(_число_значення(в.value) for в in повернення)


def чиста_геометрія(ф):
    """Коротка чиста функція простору кольору (`на_дузі(h, дуга)`, різниця двох входів): лише арифметика й порівняння
    своїх параметрів, без рядків, таблиць і сторонніх викликів. Поріг усередині — не вхід її значення: місце — виклик
    із її значенням (рішення менеджера 05.11)."""
    повернення = _чиста_функція(ф)
    if повернення is None or not (set(ф.позиційні) | set(ф.іменні)) or функція_формула(ф):
        return False
    def перевірка(х):
        """Повертає істину/число з порівнянь і арифметики, а не назву класу з таблиці."""
        if isinstance(х, ast.IfExp):
            return перевірка(х.body) and перевірка(х.orelse)
        if isinstance(х, ast.Tuple):
            return all(перевірка(е) for е in х.elts)
        return isinstance(х, (ast.Compare, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Call)) or (
            isinstance(х, ast.Constant) and isinstance(х.value, (int, float, bool)))
    return all(перевірка(в.value) for в in повернення)


def _кроки(ф):
    return sum(1 for в in ф.власні if isinstance(в, (ast.BinOp, ast.Call)))


def _число_значення(в):
    if isinstance(в, ast.Tuple):
        return all(_число_значення(х) for х in в.elts)
    if isinstance(в, ast.IfExp):
        return _число_значення(в.body) and _число_значення(в.orelse)
    return isinstance(в, (ast.BinOp, ast.Call, ast.Name, ast.UnaryOp)) or (
        isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool))


def _числова_стала(ф, ім):
    """Ім'я модульного рівня, що дорівнює числу чи простій арифметиці чисел (`_ЕРФ_НАСИЧЕННЯ = 6.0`)."""
    def число(в):
        return isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool) \
            or isinstance(в, ast.UnaryOp) and число(в.operand) or isinstance(в, ast.BinOp) and число(в.left) and число(в.right)
    return ім in ф.модуль.присвоєння and число(ф.модуль.присвоєння[ім])


def _чиста_функція(ф, глибина=0):
    """Чиста функція кольору — повертає її `return`-и чи None: без рядків,
    без викликів поза `math` і числовими вбудованими, без звернень до модульних таблиць і запису поза локальними, і кожне
    повернення — число чи кортеж чисел. Арифметика всередині — не вхід її значення в число рішення: місце — виклик
    із її значенням (рішення менеджера 05.11: «лічити кожну операцію після входу — лічити читачів»)."""
    вузол = ф.вузол
    if isinstance(вузол, ast.Lambda) or not ф.власні:
        return None
    повернення = [в for в in ф.власні if isinstance(в, ast.Return)]
    if not повернення or any(в.value is None for в in повернення):
        return None
    параметри = set(ф.позиційні) | set(ф.іменні)
    математика = {ім for ім, мод in ф.модуль.імпорти.items() if мод == "math"} | {"math"}
    for в in ф.власні:
        if isinstance(в, (ast.Global, ast.Nonlocal, ast.Try, ast.With, ast.Yield, ast.Raise)):
            return None
        if isinstance(в, ast.Constant) and isinstance(в.value, str):
            # лише рядок-документація: перший вираз тіла
            if not (вузол.body and isinstance(вузол.body[0], ast.Expr) and вузол.body[0].value is в):
                return None
        if isinstance(в, (ast.Subscript, ast.Dict, ast.List, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp, ast.JoinedStr)):
            return None
        if isinstance(в, ast.Call):
            f = в.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in математика:
                continue
            if isinstance(f, ast.Name) and f.id in _ЧИСЛОВІ_ВБУДОВАНІ:
                continue
            if isinstance(f, ast.Name) and глибина < 3 and f.id in ф.модуль.функції and f.id not in параметри \
                    and f.id not in ф.локальні and ф.модуль.функції[f.id] is not ф \
                    and _чиста_функція(ф.модуль.функції[f.id], глибина + 1) is not None:
                continue   # виклик іншої чистої функції цього ж модуля (`_ф` у `у_вікні`)
            return None
        if isinstance(в, ast.Attribute) and not (isinstance(в.value, ast.Name) and в.value.id in математика):
            return None
        if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Load) and в.id not in ф.локальні and в.id not in параметри \
                and в.id not in математика and not _числова_стала(ф, в.id) and в.id not in ф.модуль.функції and в.id not in ("float", "int", "abs", "min", "max", "sum", "round", "pow", "range", "len", "divmod"):
            return None
    return повернення


def будує_вікно(ф):
    """Функція будує вікно кандидатів — межі інтервалу `(від, до)` з сталих і зсувів: кожне повернення — пара чисел.
    Вікно — те, де код шукає кандидатів, а не її значення (рішення менеджера 01.11 і 05.11)."""
    вузол = ф.вузол
    if isinstance(вузол, ast.Lambda):
        return False
    повернення = [в for в in ф.власні if isinstance(в, ast.Return)]
    if not повернення:
        return False
    def пара(в):
        return isinstance(в, ast.Tuple) and len(в.elts) == 2 and all(
            isinstance(х, (ast.Call, ast.Constant, ast.BinOp, ast.Name)) and not (
                isinstance(х, ast.Constant) and not isinstance(х.value, (int, float))) for х in в.elts)
    def навколо_центру(в):
        """`(центр − пів, центр + пів)`: інтервал симетричний довкола центру — вікно, збудоване з центру й пів-ширини."""
        if not (isinstance(в, ast.Tuple) and len(в.elts) == 2):
            return False
        def норма(х):
            х = copy.deepcopy(х)
            for н in ast.walk(х):
                if isinstance(н, ast.BinOp) and isinstance(н.op, ast.Sub):
                    н.op = ast.Add()
            return ast.dump(х)
        ліво, право = в.elts
        return any(isinstance(н, ast.BinOp) and isinstance(н.op, (ast.Add, ast.Sub)) for н in ast.walk(ліво)) \
            and ast.dump(ліво) != ast.dump(право) and норма(ліво) == норма(право)
    if all(в.value is not None and навколо_центру(в.value) for в in повернення):
        return True
    return all(в.value is not None and пара(в.value) for в in повернення) and any(
        isinstance(н, ast.Call) and isinstance(н.func, ast.Name) and н.func.id in ("max", "min")
        for в in повернення for н in ast.walk(в.value)) and any(
        isinstance(н, ast.Constant) and isinstance(н.value, float) for в in повернення for н in ast.walk(в.value)) or all(
        в.value is not None and isinstance(в.value, ast.Tuple) and len(в.value.elts) == 2 and all(
            isinstance(х, ast.Constant) and isinstance(х.value, (int, float)) for х in в.value.elts)
        for в in повернення)


def вікно_літерал(в):
    """`[max(2, round(база - 2*КРОК - 8)), max(8, round(база - КРОК))]`: пара меж, кожна — значення ± стала
    (з обрізанням `max`/`min`): код будує вікно кандидатів довкола її значення, а не читає її значення."""
    if not (isinstance(в, (ast.List, ast.Tuple)) and len(в.elts) == 2):
        return False
    def стала(х):
        return (isinstance(х, ast.Constant) and isinstance(х.value, (int, float)) and not isinstance(х.value, bool)) \
            or isinstance(х, ast.Name) and х.id.isupper() \
            or isinstance(х, ast.BinOp) and стала(х.left) and стала(х.right) \
            or isinstance(х, ast.UnaryOp) and стала(х.operand)
    def зсув(х):
        обрізано = False
        while isinstance(х, ast.Call) and isinstance(х.func, ast.Name) and х.func.id in ("max", "min", "round", "int", "float"):
            if х.func.id in ("max", "min"):
                обрізано = True
                решта = [а for а in х.args if not стала(а)]
                if len(решта) != 1:
                    return False, False
                х = решта[0]
            elif х.args:
                х = х.args[0]
            else:
                return False, False
        while isinstance(х, ast.BinOp) and isinstance(х.op, (ast.Add, ast.Sub)) and стала(х.right):
            х = х.left
        return not стала(х) and not isinstance(х, ast.BinOp), обрізано
    рез = [зсув(х) for х in в.elts]
    return all(р[0] for р in рез) and any(р[1] for р in рез)
