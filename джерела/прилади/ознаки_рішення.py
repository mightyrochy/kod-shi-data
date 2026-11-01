"""Вивід ваги шкали й арифметичний вхід пари для приладу ознак обличчя."""
import ast
from collections import defaultdict


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
        return set().union(*(залежності.get(н.id, set()) for н in ast.walk(в) if isinstance(н, ast.Name)))

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
