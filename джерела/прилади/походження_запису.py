# -*- coding: utf-8 -*-
"""Статичне походження значення запису: новий вхід, готове поле чи конфігурація.

Не виконує код продукту. Імена полів — підказки ролі; рішення потребує значення,
його присвоєнь і місця використання. Непрозорий виклик не вважається доказом.
"""
import ast
import re


ДОБУВАННЯ = frozenset(("select", "select_one", "find_all", "findtext", "findall", "finditer",
                       "itertext", "xpath", "cssselect", "get_text", "search", "match", "fullmatch"))
ВХІД = re.compile(r"beautifulsoup|htmlparser|fromstring|json\.loads|\.json$|\.read$|\.read_text$|"
                  r"\.parse$|urlopen|requests\.|httpx\.|поверхня_фото|виміряти_фото|_запит$", re.I)
СИРІ_ПОЛЯ = frozenset(("variants", "variations", "hasVariant", "offers", "@type", "productGroupID",
                       "inProductGroupWithID", "option1", "featured_image", "variant_ids"))
ІД = frozenset(("id", "ід", "offer_id", "variant_id"))
ДОСТУП = frozenset(("available", "availability", "наявність", "in_stock"))
ВАРІАНТИ = frozenset(("variants", "variations", "hasVariant", "offer"))
АГРЕГАТ = frozenset(("any", "all", "sum", "min", "max", "len", "Counter"))
НЕ_КАДР = re.compile(r"(^[.#\[]|\[.*(?:itemprop|class|src)|::| > |^shopify:|^json-ld$|^og:image$)")


def ім_виклику(вузол):
    """Повертає кваліфіковане ім'я виклику без виконання виразу."""
    if isinstance(вузол, ast.Name):
        return вузол.id
    if isinstance(вузол, ast.Attribute):
        return ім_виклику(вузол.value) + "." + вузол.attr
    return ""


def поле(вузол):
    """Читає сталий ключ доступу, не ототожнюючи назву змінної з роллю."""
    if isinstance(вузол, ast.Subscript) and isinstance(вузол.slice, ast.Constant):
        return вузол.slice.value
    if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr == "get" \
            and вузол.args and isinstance(вузол.args[0], ast.Constant):
        return вузол.args[0].value
    return None


def поля(вузол):
    """Повертає поля словника чи конструктора запису."""
    if isinstance(вузол, ast.Dict):
        return {к.value: з for к, з in zip(вузол.keys, вузол.values) if isinstance(к, ast.Constant)}
    if isinstance(вузол, ast.Call):
        return {к.arg: к.value for к in вузол.keywords if к.arg}
    return {}


def власні_вузли(вузол):
    """Обходить одиницю без тіл вкладених функцій і класів."""
    yield вузол
    for дитина in ast.iter_child_nodes(вузол):
        if not isinstance(дитина, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            yield from власні_вузли(дитина)


class Походження:
    """Простежує присвоєння, джерела значень і споживачів у межах функції."""

    def __init__(self, вузол, батьки, функції=None):
        self.вузол = вузол
        self.батьки = батьки
        self.функції = функції or {}
        self.вузли = list(власні_вузли(вузол))
        self.присвоєння = {}
        self.звязані = {}
        for н in self.вузли:
            if isinstance(н, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for і, г in enumerate(н.generators):
                    імена = {ц.id for ц in ast.walk(г.target) if isinstance(ц, ast.Name)}
                    вирази = [н.key, н.value] if isinstance(н, ast.DictComp) else [н.elt]
                    вирази += [в for д in н.generators for в in д.ifs] + [д.iter for д in н.generators[і + 1:]]
                    self._привязати(імена, вирази + [г.target], г.iter)
            if isinstance(н, (ast.Assign, ast.AnnAssign)) and н.value is not None:
                for ц in н.targets if isinstance(н, ast.Assign) else [н.target]:
                    self._звязати(ц, н.value)
            elif isinstance(н, (ast.For, ast.AsyncFor, ast.comprehension)):
                self._звязати(н.target, н.iter)
                if isinstance(н, (ast.For, ast.AsyncFor)):
                    імена = {ц.id for ц in ast.walk(н.target) if isinstance(ц, ast.Name)}
                    self._привязати(імена, н.body + н.orelse + [н.target], н.iter)
        self.кеш = {}
        self.кеш_коренів = {}
        self.підсумки = {}

    def _привязати(self, імена, вузли, ітер):
        """Пов'язує вживання з його циклом, не типізуючи всі однойменні змінні функції."""
        for корінь in вузли:
            for ч in власні_вузли(корінь):
                if isinstance(ч, ast.Name) and ч.id in імена:
                    self.звязані[id(ч)] = ітер

    def із_варіацій(self, вираз, шлях=frozenset()):
        """Простежує колекцію оферт/варіацій через псевдонім, or і стандартну обгортку."""
        if поле(вираз) in ВАРІАНТИ:
            return True
        if isinstance(вираз, ast.Name) and вираз.id not in шлях:
            return any(self.із_варіацій(з, шлях | {вираз.id}) for з in self.визначення(вираз.id, вираз.lineno))
        if isinstance(вираз, ast.BoolOp):
            return any(self.із_варіацій(з, шлях) for з in вираз.values)
        if isinstance(вираз, ast.Call) and вираз.args:
            if isinstance(вираз.args[0], ast.Constant) and вираз.args[0].value in ВАРІАНТИ:
                return True
            if ім_виклику(вираз.func) in ("enumerate", "sorted", "iter", "list", "tuple"):
                return self.із_варіацій(вираз.args[0], шлях)
        return False

    def _звязати(self, ціль, значення):
        """Зберігає також розпакування кортежів."""
        if isinstance(ціль, ast.Name):
            self.присвоєння.setdefault(ціль.id, []).append(значення)
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            if isinstance(значення, (ast.Tuple, ast.List)) and len(ціль.elts) == len(значення.elts):
                for ц, з in zip(ціль.elts, значення.elts):
                    self._звязати(ц, з)
            else:
                for і, ц in enumerate(ціль.elts):
                    вибір = ast.copy_location(ast.Subscript(value=значення, slice=ast.Constant(value=і), ctx=ast.Load()), значення)
                    self._звязати(ц, вибір)

    def визначення(self, ім, перед):
        """Бере досяжні попередні присвоєння; пізніші не доводять джерела."""
        return [з for з in self.присвоєння.get(ім, ()) if getattr(з, "lineno", 0) <= перед]

    def теги(self, вираз, перед=None, шлях=frozenset()):
        """Повертає множину ознак: вхід, поле, стала, невідомо."""
        if вираз is None:
            return frozenset()
        перед = перед or getattr(вираз, "lineno", 10 ** 9)
        ключ = (id(вираз), перед)
        if ключ in self.кеш:
            return self.кеш[ключ]
        рез = self._теги(вираз, перед, шлях)
        self.кеш[ключ] = рез
        return рез

    def _теги(self, в, перед, шлях):
        """Розрізняє читання готового поля й добування з зовнішнього формату."""
        if isinstance(в, ast.Constant):
            return frozenset(("стала",))
        if isinstance(в, ast.Name):
            if в.id in шлях:
                return frozenset()
            if id(в) in self.звязані:
                return self.теги(self.звязані[id(в)], шлях=шлях | {в.id})
            визначення = self.визначення(в.id, перед)
            if визначення:
                return frozenset().union(*(self.теги(з, getattr(з, "lineno", перед), шлях | {в.id}) for з in визначення))
            return frozenset(("невідомо",))
        if isinstance(в, ast.Call):
            ім = ім_виклику(в.func)
            if ім.rsplit(".", 1)[-1] in ДОБУВАННЯ:
                входи = list(в.args)
                if isinstance(в.func, ast.Attribute) and ім.rsplit(".", 1)[0] != "re":
                    входи.append(в.func.value)
                т = frozenset().union(*(self.теги(н, перед, шлях) for н in входи))
                return frozenset(("поле",)) if "поле" in т and "вхід" not in т else frozenset(("вхід",))
            if ВХІД.search(ім):
                return frozenset(("вхід",))
            if поле(в) in СИРІ_ПОЛЯ:
                return frozenset(("вхід",))
            if isinstance(в.func, ast.Name) and в.func.id in self.функції and в.func.id not in шлях:
                ф = self.функції[в.func.id]
                if в.func.id not in self.підсумки:
                    граф = Походження(ф, {})
                    повернення = [н.value for н in власні_вузли(ф) if isinstance(н, ast.Return)]
                    self.підсумки[в.func.id] = frozenset().union(*(граф.теги(з) for з in повернення))
                т = self.підсумки[в.func.id]
                if "вхід" in т:
                    аргументи = frozenset().union(*(self.теги(н, перед, шлях) for н in в.args))
                    if "поле" in аргументи and "вхід" not in аргументи:
                        return аргументи
                    return т
            if isinstance(в.func, ast.Attribute) and в.func.attr == "get":
                база = self.теги(в.func.value, перед, шлях)
                if база <= {"стала", "невідомо"}:
                    return frozenset(("поле",))
                return база if "вхід" in база else frozenset(("поле",))
            діти = list(в.args) + [к.value for к in в.keywords]
            if isinstance(в.func, ast.Attribute):
                діти.append(в.func.value)
            т = frozenset().union(*(self.теги(н, перед, шлях) for н in діти))
            return т or frozenset(("невідомо",))
        if isinstance(в, ast.Subscript):
            if isinstance(в.slice, ast.Constant) and isinstance(в.slice.value, int) and isinstance(в.value, ast.Call) \
                    and isinstance(в.value.func, ast.Name) and в.value.func.id in self.функції:
                ф = self.функції[в.value.func.id]
                граф = Походження(ф, {})
                виходи = [н.value.elts[в.slice.value] for н in власні_вузли(ф) if isinstance(н, ast.Return)
                          and isinstance(н.value, (ast.Tuple, ast.List)) and len(н.value.elts) > в.slice.value]
                if виходи:
                    return frozenset().union(*(граф.теги(з) for з in виходи))
            т = self.теги(в.value, перед, шлях)
            if поле(в) in СИРІ_ПОЛЯ:
                return frozenset(("вхід",))
            return т if "вхід" in т else frozenset(("поле",))
        if isinstance(в, ast.Attribute):
            т = self.теги(в.value, перед, шлях)
            return т if "вхід" in т else frozenset(("поле",))
        return frozenset().union(*(self.теги(н, перед, шлях) for н in ast.iter_child_nodes(в)
                                  if not isinstance(н, (ast.expr_context, ast.operator))))

    def корені(self, вираз, перед=None, шлях=frozenset()):
        """Повертає бази читань полів, розкриваючи локальні псевдоніми."""
        if вираз is None:
            return set()
        перед = перед or getattr(вираз, "lineno", 10 ** 9)
        ключ = (id(вираз), перед)
        if ключ in self.кеш_коренів:
            return self.кеш_коренів[ключ]
        рез = self._корені(вираз, перед, шлях)
        self.кеш_коренів[ключ] = рез
        return рез

    def _корені(self, вираз, перед, шлях):
        """Обчислює бази одного вузла з захистом від циклічних псевдонімів."""
        if isinstance(вираз, ast.Name):
            if вираз.id in шлях:
                return set()
            if id(вираз) in self.звязані:
                ітер = self.звязані[id(вираз)]
                if self.із_варіацій(ітер):
                    return {"вхід-елемента:%s:%d" % (вираз.id, getattr(ітер, "lineno", 0))}
                return self.корені(ітер, шлях=шлях | {вираз.id})
            if вираз.id.isupper():
                return set()
            зн = self.визначення(вираз.id, перед)
            return set().union(*(self.корені(з, getattr(з, "lineno", перед), шлях | {вираз.id}) for з in зн)) if зн else {вираз.id}
        if isinstance(вираз, ast.Call) and isinstance(вираз.func, ast.Attribute) and вираз.func.attr == "get":
            return self.корені(вираз.func.value, перед, шлях)
        if isinstance(вираз, ast.Call):
            входи = list(вираз.args) + [к.value for к in вираз.keywords]
            if isinstance(вираз.func, ast.Attribute):
                входи.append(вираз.func.value)
            return set().union(*(self.корені(н, перед, шлях) for н in входи))
        if isinstance(вираз, (ast.Subscript, ast.Attribute)):
            return self.корені(вираз.value, перед, шлях)
        return set().union(*(self.корені(н, перед, шлях) for н in ast.iter_child_nodes(вираз)
                             if isinstance(н, ast.expr)))

    def числове_зведення(self, значення, шлях=frozenset()):
        """Відрізняє словник чисел від адрес кадрів, зокрема повернений у кортежі."""
        if isinstance(значення, ast.Name) and значення.id not in шлях:
            зн = self.визначення(значення.id, getattr(значення, "lineno", 10 ** 9))
            return bool(зн) and all(self.числове_зведення(з, шлях | {значення.id}) for з in зн)
        if isinstance(значення, ast.Subscript) and isinstance(значення.value, ast.Call) \
                and isinstance(значення.value.func, ast.Name) and isinstance(значення.slice, ast.Constant) \
                and isinstance(значення.slice.value, int) and значення.value.func.id in self.функції:
            ф = self.функції[значення.value.func.id]
            граф = Походження(ф, {})
            виходи = [н.value.elts[значення.slice.value] for н in власні_вузли(ф) if isinstance(н, ast.Return)
                      and isinstance(н.value, (ast.Tuple, ast.List)) and len(н.value.elts) > значення.slice.value]
            return bool(виходи) and all(граф.числове_зведення(з) for з in виходи)
        п = поля(значення)
        return bool(п) and all(isinstance(з, ast.Constant) and (з.value is None or isinstance(з.value, (int, float)))
                              or isinstance(з, ast.Call) and ім_виклику(з.func) in АГРЕГАТ for з in п.values())

    def запис(self, вузол):
        """Знаходить об'єкт запису й зовнішній контекст конструктора."""
        cur = вузол
        if isinstance(cur, (ast.Subscript, ast.Attribute)):
            return cur.value
        if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute) and cur.func.attr in ("update", "setdefault"):
            return cur.func.value
        while cur in self.батьки:
            б = self.батьки[cur]
            if isinstance(б, (ast.Assign, ast.AnnAssign)):
                return б.targets[0] if isinstance(б, ast.Assign) else б.target
            if isinstance(б, (ast.Return, ast.Call, ast.Dict)):
                return вузол
            cur = б
        return вузол

    def причина_виключення(self, вузол, ключ, роль, значення):
        """Доводить, чому кандидат не є новим записом поля речі."""
        cur = вузол
        while cur in self.батьки:
            б = self.батьки[cur]
            if isinstance(б, ast.Call) and (cur in б.args or isinstance(cur, ast.keyword)) and ім_виклику(б.func).rsplit(".", 1)[-1] not in (
                    "append", "extend", "update", "setdefault", "dump", "dumps", "dict"):
                return "тимчасовий аргумент виклику, не запис таблиці"
            if isinstance(б, (ast.stmt, ast.Dict)):
                break
            cur = б
        контейнер = поля(вузол)
        if "помилка" in контейнер and not (ІД & контейнер.keys()):
            return "запис помилки, не запис речі"
        т = self.теги(значення)
        if роль == "кадр" and self.числове_зведення(значення):
            return "числове зведення, не кадр речі"
        if isinstance(значення, ast.Call) and ім_виклику(значення.func) in ("dict", "set", "list", "tuple") \
                and not значення.args and not значення.keywords:
            return "порожня заготовка"
        if роль == "кадр" and isinstance(значення, ast.Constant) and isinstance(значення.value, str) \
                and (НЕ_КАДР.search(значення.value) or not re.search(r"https?://|\.(?:jpg|png|webp|jpeg)(?:$|\?)", значення.value)):
            return "рядкова мітка чи селектор, не кадр"
        if т <= {"стала"} and not (ІД & контейнер.keys()):
            return "конфігурація чи стала без даних крамниці"
        if "поле" in т and "вхід" not in т:
            return "похідне з готового поля без нового входу"
        # Метадані в копії готового сегмента не створюють нового входу.
        if isinstance(вузол, ast.Call) and ім_виклику(вузол.func) == "dict" and вузол.args \
                and "вхід" not in self.теги(вузол.args[0]) and "вхід" not in т:
            return "похідне в копії готового запису без нового входу"
        if isinstance(значення, ast.Name):
            зн = self.визначення(значення.id, вузол.lineno)
            if зн and all(isinstance(з, (ast.Dict, ast.Call)) and поля(з)
                          and not any(р in поля(з) for р in ("url", "src", "image", "фото", "кадр"))
                          and all(isinstance(в, ast.Constant) or (isinstance(в, ast.Call) and
                                  ім_виклику(в.func) in АГРЕГАТ) for в in поля(з).values()) for з in зн):
                return "числове зведення, не кадр речі"
        return None

    def свій_варіант(self, вузол, значення):
        """Доводить спільне джерело id, наявності й поля оферти, а не ім'я змінної."""
        п = поля(вузол)
        if значення is not None and any(isinstance(н, ast.Call) and ім_виклику(н.func) in ("any", "all", "sum")
                                       for н in ast.walk(значення)):
            return False
        ід = [з for к, з in п.items() if к in ІД]
        наявність = [з for к, з in п.items() if к in ДОСТУП]
        if ід and наявність:
            свої = set().union(*(self.корені(з) for з in ід)) & set().union(*(self.корені(з) for з in наявність))
            дж = self.корені(значення)
            # id і наявність бувають і на Product: самі ці два поля не доводять
            # варіацію. Корінь має походити з елемента offer/variants/variations.
            if свої and дж and дж <= свої and any(к.startswith("вхід-елемента:") for к in свої):
                return True
        cur = вузол
        while cur in self.батьки:
            cur = self.батьки[cur]
            if isinstance(cur, (ast.For, ast.AsyncFor, ast.comprehension)):
                ітер = cur.iter
                є = self.із_варіацій(ітер)
                цілі = {н.id for н in ast.walk(cur.target) if isinstance(н, ast.Name)}
                # Усередині оферти значення має залежати саме від її даних.
                імена = {н.id for н in ast.walk(значення) if isinstance(н, ast.Name)} if значення else set()
                if є and (імена & цілі or self.корені(значення) & self.корені(cur.target, cur.lineno + 1)):
                    return True
        return False


def константи_імпортів(дерево, тека, читати):
    """Розкриває рядкові константи імпортованого модуля без імпорту продукту."""
    рез = {}
    for н in дерево.body:
        if isinstance(н, ast.Import):
            запити = [(а.asname or а.name, а.name, None) for а in н.names]
        elif isinstance(н, ast.ImportFrom) and н.module:
            запити = [(а.asname or а.name, н.module, а.name) for а in н.names]
        else:
            continue
        for псевдо, модуль, член in запити:
            д = читати(тека, модуль)
            if д is None:
                continue
            for з in д.body:
                if isinstance(з, ast.Assign) and isinstance(з.value, ast.Constant) and isinstance(з.value.value, str):
                    for ц in з.targets:
                        if isinstance(ц, ast.Name) and (член is None or ц.id == член):
                            рез[псевдо + "." + ц.id if член is None else псевдо] = {з.value.value}
    return рез
