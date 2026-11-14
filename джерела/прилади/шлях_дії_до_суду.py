# -*- coding: utf-8 -*-
"""Консервативний доказ суду результату дії після повернення з допоміжних функцій.

Реєстр маршруту задає вхід продукту, а не дозвіл пропускати файл: виклик дії,
перенесення її поля й суд на всіх продовженнях перевіряються в AST щоразу.
Невідома форма керування лишає місце в числі. Продукт не імпортується.
"""
import ast
import re


СУД = re.compile(r'^(?:суд|judge|evaluate|ваги_образу|перевірити_від_моделі)$')


class ШляхДії:
    """Простежує значення зміненого складу до повного суду на тому самому шляху."""

    def __init__(self, аналіз):
        """Приймає індекс модулів приладу без виконання коду продукту."""
        self.аналіз = аналіз
        self.кеш = {}
        self.докази = set()
        self.модуль = ''

    def ціль(self, м, вузол):
        """Розв'язує локальні посилання й ланцюжки реекспорту фасадів."""
        м, ім = self.аналіз.визначення(м, вузол)
        бачені = set()
        while м is not None and (м.шлях, ім) not in бачені:
            бачені.add((м.шлях, ім))
            if ім in м.функції:
                return м, м.функції[ім]
            if ім not in м.імпорти:
                break
            модуль, ім = м.імпорти[ім]
            м = self.аналіз.за_імям.get(модуль)
        return None, None

    def цілі(self, м, в):
        """Розпізнає також виклик розбору через реєстр схем із явною назвою в гілці."""
        ціль = self.ціль(м, в.func)
        if ціль[0] is not None:
            return [ціль]
        if not (isinstance(в.func, ast.Attribute) and в.func.attr == 'виконати_розбір'
                and isinstance(в.func.value, ast.Call)):
            return []
        пошук = в.func.value
        реєстр, функція = self.ціль(м, пошук.func)
        if реєстр is None or функція.name != 'схема_за_назвою' or not пошук.args:
            return []
        назва = пошук.args[0]
        if isinstance(назва, ast.Name):
            п = м.батьки.get(в)
            while п is not None:
                if (isinstance(п, ast.If) and isinstance(п.test, ast.Compare)
                        and ast.unparse(п.test.left) == назва.id and len(п.test.ops) == 1
                        and isinstance(п.test.ops[0], ast.Eq) and п.body
                        and п.body[0].lineno <= в.lineno <= п.body[-1].end_lineno):
                    назва = п.test.comparators[0]
                    break
                п = м.батьки.get(п)
        if not isinstance(назва, ast.Constant):
            return []
        # Перевіряємо обидва шви реєстру: dc.replace(..., **РОЗБІР.get(...)) і
        # метод, що викликає self.розбір лише за його наявності.
        повернення = [н for н in ast.walk(функція) if isinstance(н, ast.Return)]
        if not any(isinstance(н.value, ast.Subscript)
                   and ast.unparse(н.value.value) == 'СХЕМИ_ВІДПОВІДІ' for н in повернення):
            return []
        заміни = [н for н in ast.walk(реєстр.дерево) if isinstance(н, ast.Call)
                  and isinstance(н.func, ast.Attribute) and н.func.attr == 'replace'
                  and self.аналіз.визначення(реєстр, н.func)[0] is None
                  and реєстр.імпорти.get(ast.unparse(н.func.value)) == ('dataclasses', '')
                  and any(к.arg is None and isinstance(к.value, ast.Call)
                          and ast.unparse(к.value.func) == 'РОЗБІР.get' for к in н.keywords)]
        if not заміни:
            return []
        методи = [сам.функції.get('виконати_розбір') for сам in self.аналіз.модулі]
        if not any(ф is not None and any(
                isinstance(н, ast.If) and ast.unparse(н.test) == 'self.розбір is not None'
                and len(н.body) == 1 and isinstance(н.body[0], ast.Return)
                and isinstance(н.body[0].value, ast.Call)
                and ast.unparse(н.body[0].value.func) == 'self.розбір' for н in ast.walk(ф))
                for ф in методи):
            return []
        for словник in реєстр.присвоєння.get((None, 'РОЗБІР'), []):
            if not isinstance(словник, ast.Dict):
                continue
            for к, з in zip(словник.keys, словник.values):
                if isinstance(к, ast.Constant) and к.value == назва.value and isinstance(з, ast.Call):
                    return [self.ціль(реєстр, п.value) for п in з.keywords if п.arg == 'розбір'
                            and self.ціль(реєстр, п.value)[0] is not None]
        return []

    def досягає(self, м, ф, дія):
        """Простежує повернений результат дії, а не будь-яку згадку допоміжного виклику."""
        if дія not in self.кеш:
            зворотні = {}
            модуль_дії = next(сам for сам in self.аналіз.модулі if сам.шлях == дія[0])
            функція_дії = модуль_дії.функції[дія[1]]
            параметри = [а.arg for а in функція_дії.args.args]
            керування = set()
            for в in ast.walk(функція_дії):
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) \
                        and в.func.attr in {'remove', 'pop', 'discard'}:
                    п = модуль_дії.батьки.get(в)
                    while п is not None and п is not функція_дії:
                        if isinstance(п, ast.For):
                            керування |= {н.id for н in ast.walk(п.iter) if isinstance(н, ast.Name)} & set(параметри)
                        п = модуль_дії.батьки.get(п)
            for сам in self.аналіз.модулі:
                for функція in сам.функції.values():
                    for в in ast.walk(функція):
                        if not isinstance(в, ast.Call) or сам.охопна(в) is not функція:
                            continue
                        for інший, інша in self.цілі(сам, в):
                            if (інший.шлях, інша.name) == дія:
                                аргументи = dict(zip(параметри, в.args))
                                аргументи.update({к.arg: к.value for к in в.keywords})
                                if керування and not any(ім in аргументи and not (
                                        isinstance(аргументи[ім], (ast.List, ast.Tuple)) and not аргументи[ім].elts)
                                        for ім in керування):
                                    continue
                            elif not self.несе_поле(сам, в):
                                continue
                            зворотні.setdefault((інший.шлях, інша.name), set()).add((сам.шлях, функція.name))
            досяжні, черга = {дія}, [дія]
            while черга:
                for ключ in зворотні.get(черга.pop(), set()) - досяжні:
                    досяжні.add(ключ)
                    черга.append(ключ)
            self.кеш[дія] = досяжні
        return (м.шлях, ф.name) in self.кеш[дія]

    def несе_поле(self, м, виклик):
        """Відсікає лише доведене читання інших полів результату, без передавання складу."""
        п = м.батьки.get(виклик)
        if not isinstance(п, ast.Assign) or len(п.targets) != 1 or not isinstance(п.targets[0], ast.Name):
            return True
        ім = п.targets[0].id
        for в in ast.walk(м.охопна(виклик)):
            if not isinstance(в, ast.Name) or в.id != ім or not isinstance(в.ctx, ast.Load):
                continue
            б = м.батьки.get(в)
            if isinstance(б, ast.Subscript) and isinstance(б.slice, ast.Constant) and б.slice.value != 'ід':
                continue
            д = м.батьки.get(б)
            if (isinstance(б, ast.Attribute) and б.attr == 'get' and isinstance(д, ast.Call)
                    and д.args and isinstance(д.args[0], ast.Constant) and д.args[0].value != 'ід'):
                continue
            return True
        return False

    def значення(self, в, стан, джерело=None, поле='ід'):
        """Несе походження окремих полів крізь копії, dict, get і вибір виразу."""
        if в is джерело:
            return {(поле,)}
        if isinstance(в, ast.Name):
            return стан.get(в.id, set())
        if isinstance(в, ast.Subscript):
            return self.поле(self.значення(в.value, стан, джерело, поле), в.slice)
        if isinstance(в, ast.Call):
            if isinstance(в.func, ast.Attribute) and в.func.attr == 'get' and в.args:
                return self.поле(self.значення(в.func.value, стан, джерело, поле), в.args[0])
            if isinstance(в.func, ast.Name) and в.func.id == 'dict':
                вих = set().union(*(self.значення(а, стан, джерело, поле) for а in в.args))
                for к in в.keywords:
                    з = self.значення(к.value, стан, джерело, поле)
                    вих = {п for п in вих if not п or п[0] != к.arg}
                    вих |= {(к.arg,) + п for п in з} if к.arg else з
                return вих
            if isinstance(в.func, ast.Name) and в.func.id in {'list', 'tuple', 'set'} and в.args:
                return self.значення(в.args[0], стан, джерело, поле)
            return set()
        if isinstance(в, ast.Dict):
            return set().union(*(self.значення(з, стан, джерело, поле) if к is None else
                                 {(к.value,) + п for п in self.значення(з, стан, джерело, поле)}
                                 if isinstance(к, ast.Constant) else set()
                                 for к, з in zip(в.keys, в.values)))
        if isinstance(в, ast.IfExp):
            # Нормалізація форми списку зберігає цілий останній склад.
            # Голий числовий індекс вибирає річ і такого доказу не дає.
            інакше = в.orelse
            if (isinstance(інакше, ast.Call) and ast.unparse(інакше.func) == 'list'
                    and len(інакше.args) == 1 and isinstance(інакше.args[0], ast.Name)):
                ім = інакше.args[0].id
                еталон = ast.parse(f'list({ім}[-1]) if {ім} and isinstance({ім}[0], (list, tuple)) '
                                   f'else list({ім})', mode='eval').body
                if ast.dump(в) == ast.dump(еталон):
                    return self.значення(інакше.args[0], стан, джерело, поле)
            return self.значення(в.body, стан, джерело, поле) & self.значення(в.orelse, стан, джерело, поле)
        if isinstance(в, ast.BoolOp):
            варіанти = [self.значення(з, стан, джерело, поле) for з in в.values
                        if not isinstance(з, (ast.List, ast.Tuple)) or з.elts]
            return set.intersection(*варіанти) if варіанти else set()
        return set()

    @staticmethod
    def поле(походження, ключ):
        """Читання іншого поля не успадковує склад; невідомий ключ не доводить його."""
        if not isinstance(ключ, ast.Constant) or not isinstance(ключ.value, str):
            return set()
        return {п[1:] if п else () for п in походження if not п or п[0] == ключ.value}

    def судить(self, в, стан):
        """Суд має отримати змінений склад; умовний виклик не є безумовним."""
        if isinstance(в, ast.Call):
            ім = в.func.id if isinstance(в.func, ast.Name) else getattr(в.func, 'attr', '')
            return bool(СУД.fullmatch(ім) and в.args and () in self.значення(в.args[0], стан))
        if isinstance(в, ast.IfExp):
            return self.судить(в.body, стан) and self.судить(в.orelse, стан)
        return False

    def блок(self, тіло, стан, джерело=None):
        """Дає несуджені продовження; None — вихід без суду чи невідома конструкція."""
        стани = [стан]
        for в in тіло:
            далі = []
            for с in стани:
                с = dict(с)
                if self.судить(getattr(в, 'value', None), с):
                    self.докази.add(f'{self.модуль}:{в.lineno}')
                    continue
                if isinstance(в, ast.Raise):
                    continue
                if isinstance(в, ast.Return):
                    return None
                if isinstance(в, ast.If):
                    for гілка in (в.body, в.orelse):
                        р = self.блок(гілка, с)
                        if р is None:
                            return None
                        далі.extend(р)
                    continue
                if isinstance(в, (ast.Assign, ast.AnnAssign)):
                    з = self.значення(в.value, с, джерело)
                    for ц in в.targets if isinstance(в, ast.Assign) else [в.target]:
                        if isinstance(ц, ast.Name):
                            с[ц.id] = з
                        elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name):
                            ключ = ц.slice.value if isinstance(ц.slice, ast.Constant) else None
                            с[ц.value.id] = {п for п in с.get(ц.value.id, set()) if п and п[0] != ключ}
                            с[ц.value.id] |= {(ключ,) + п for п in з}
                        else:
                            return None
                elif isinstance(в, ast.Expr) and isinstance(в.value, ast.Call):
                    дія = в.value.func
                    if isinstance(дія, ast.Attribute) and isinstance(дія.value, ast.Name):
                        # Невідомий метод може змінити копію складу перед судом.
                        с.pop(дія.value.id, None)
                elif not isinstance(в, (ast.Expr, ast.Pass, ast.FunctionDef, ast.AsyncFunctionDef)):
                    return None
                далі.append(с)
            стани = далі
            if not стани:
                break
        return стани

    def після(self, м, вузол, стан, джерело=None):
        """Перевіряє продовження саме виконаної гілки до суду або виходу функції."""
        дитина = вузол
        while дитина in м.батьки:
            п = м.батьки[дитина]
            списки = [з for _, з in ast.iter_fields(п) if isinstance(з, list) and дитина in з]
            if списки:
                хвіст = списки[0][списки[0].index(дитина) + (0 if джерело else 1):]
                стани = self.блок(хвіст, стан, джерело)
                if стани is None:
                    return False
                if not стани:
                    return True
                # Розгалуження з різним походженням не зливаємо у хибний доказ.
                решта = стани
                return all(self.продовжити(м, п, с) for с in решта)
            дитина = п
        return False

    def продовжити(self, м, вузол, стан):
        """Переходить за кінець гілки; складні виходи з циклу не вгадує."""
        if isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        if isinstance(вузол, (ast.For, ast.While)):
            if any(isinstance(н, (ast.Return, ast.Break, ast.Continue)) for н in ast.walk(вузол)):
                return False
        elif not isinstance(вузол, ast.If):
            return False
        return self.після(м, вузол, стан)

    def довести(self, м, ф, продовження=None):
        """Доводить суд кожного зняття локально або в зареєстрованому вході продукту."""
        дії = [в for в in ast.walk(ф) if isinstance(в, ast.Call) and м.охопна(в) is ф
               and isinstance(в.func, ast.Attribute) and в.func.attr in {'remove', 'pop', 'discard'}]
        if not дії:
            return True
        self.модуль = м.шлях
        if all(isinstance(в.func.value, ast.Name)
               and self.після(м, в, {в.func.value.id: {()}}) for в in дії):
            return True
        if продовження is None:
            return False
        сам = self.аналіз.за_імям.get(продовження[0])
        вхід = сам.функції.get(продовження[1]) if сам else None
        if вхід is None:
            return False
        self.модуль = сам.шлях
        джерела = [в for в in ast.walk(вхід) if isinstance(в, ast.Call) and сам.охопна(в) is вхід
                   and all(інша is not вхід for _, інша in self.цілі(сам, в))
                   and any(self.досягає(інший, інша, (м.шлях, ф.name))
                           for інший, інша in self.цілі(сам, в))]
        return bool(джерела) and all(self.після(сам, в, {}, в) for в in джерела)
