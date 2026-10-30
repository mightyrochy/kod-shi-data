# -*- coding: utf-8 -*-
"""Статично збирає сталий текст виклику: функції, join, підстановки та реєстри.

Код продукту не виконується. Невідомі дані мають порожній текст; невідомі умови
дають окремі варіанти. Незрозумілі операції та обмеження обходу повертаються
діагностикою, щоб неповний вимір не виглядав повним.
"""
import ast
import collections
import copy
import json
import os
import re
import sys


class Невідоме:
    """Змінні дані виклику, які не належать сталій частині промпту."""


НЕВІДОМЕ = Невідоме()


def текст(значення):
    """Рядок сталої частини; невідомий вхід символів не додає."""
    return "" if isinstance(значення, Невідоме) else str(значення)


class Вибір(Exception):
    """Невідома умова, яку треба виміряти обома гілками."""

    def __init__(я, ключ, варіанти=(False, True)):
        я.ключ = ключ
        я.варіанти = варіанти


class Відкладене:
    """Присвоєння, яке потрібне лише якщо його значення дійде до виходу."""

    def __init__(я, вузол, середовище):
        я.вузол, я.середовище = вузол, середовище.copy()


class Повернення(Exception):
    """Повернене значення інтерпретованої функції."""

    def __init__(я, значення):
        я.значення = значення


class Збирач:
    """Інтерпретує лише операції з даними AST, без імпортів, IO та виклику моделі."""

    def __init__(я, модулі):
        я.модулі = модулі
        я.за_іменем = {ім: м for (_, ім), м in модулі.items()}
        я.глобальні = {}
        я.стек = []
        я.умови = {}
        я.попередження = set()
        я.кроки = 0

    def умова(я, в, м, вузол):
        """Відоме значення перевіряє, невідоме розгалужує за адресою AST."""
        if not isinstance(в, Невідоме):
            return bool(в)
        ключ = (м.відн, вузол.lineno, вузол.col_offset)
        if ключ not in я.умови:
            raise Вибір(ключ)
        return я.умови[ключ]

    def імпорт(я, м, ім):
        """Знаходить модуль з того самого каталогу, потім загального індексу."""
        return я.модулі.get((os.path.dirname(м.відн), ім)) or я.за_іменем.get(ім)

    def глобальне(я, м, ім):
        """Читає оголошення чи реєстр за імпортом, з кешем і захистом від циклу."""
        ключ = (м.відн, ім)
        if ключ in я.глобальні:
            return я.глобальні[ключ]
        # Попередній збирач уже завантажує оголошення; готові дані беремо без
        # нового імпорту та без виконання функцій реєстру.
        мод = sys.modules.get(м.ім)
        готове = vars(мод).get(ім, НЕВІДОМЕ) if мод else НЕВІДОМЕ
        if isinstance(готове, (str, int, float, bool, dict, tuple, list, set)) or (
                type(готове).__name__ in ("Оголошення", "Поле")):
            я.глобальні[ключ] = copy.deepcopy(готове)
            return я.глобальні[ключ]
        if ім in м.імпорти:
            мд, назва = м.імпорти[ім]
            ін = я.імпорт(м, мд)
            if ін:
                return ("модуль", ін) if назва is None else я.глобальне(ін, назва)
            return ("зовнішнє", мд, назва)
        в = м.визначення.get(ім)
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ("функція", м, в)
        я.глобальні[ключ] = НЕВІДОМЕ
        if isinstance(в, (ast.Assign, ast.AnnAssign)):
            я.глобальні[ключ] = я.вираз(в.value, м, {})
        return я.глобальні[ключ]

    def привʼязати(я, ц, в, середовище):
        """Зв'язує ім'я або розпаковує кортеж присвоєння."""
        if isinstance(ц, ast.Name):
            середовище[ц.id] = в
        elif isinstance(ц, (ast.Tuple, ast.List)):
            значення = list(в) if isinstance(в, (tuple, list)) else [НЕВІДОМЕ] * len(ц.elts)
            for н, х in enumerate(ц.elts):
                я.привʼязати(х, значення[н] if н < len(значення) else НЕВІДОМЕ, середовище)
        elif isinstance(ц, ast.Subscript):
            об = середовище.get(getattr(ц.value, "id", ""))
            if isinstance(об, dict) and isinstance(ц.slice, ast.Constant):
                об[ц.slice.value] = в

    def функція(я, м, в, арг, іменовані):
        """Обчислює повернений сталий текст з локальних присвоєнь і гілок."""
        if any(isinstance(х, Невідоме) for х in [*арг, *іменовані.values()]):
            вузли = [х for н in в.body if not isinstance(н, ast.Expr) or not isinstance(н.value, ast.Constant)
                     for х in ast.walk(н)]
            # Обчислення значення даних (тип, слот, стан паспорта) не має
            # визначати невідомий вхід для промпту. Рядковий збирач, навпаки,
            # треба розгорнути навіть із невідомими даними.
            рядковий = any(isinstance(х, ast.JoinedStr) or isinstance(х, ast.BinOp) and isinstance(х.op, (ast.Add, ast.Mod))
                           or isinstance(х, ast.Call) and getattr(х.func, "attr", "") in ("join", "replace", "format", "зібрати")
                           or isinstance(х, ast.Constant) and isinstance(х.value, str) and len(х.value) >= 80
                           for х in вузли if not isinstance(х, ast.Expr))
            if not рядковий:
                return НЕВІДОМЕ
        ключ = (м.відн, в.name)
        if ключ in я.стек or len(я.стек) >= 12:
            я.попередження.add((м.відн, в.lineno, "цикл або глибина викликів"))
            return НЕВІДОМЕ
        сер = {}
        параметри = в.args.posonlyargs + в.args.args
        for п, д in zip(параметри[-len(в.args.defaults):], в.args.defaults):
            сер[п.arg] = я.вираз(д, м, {})
        сер.update({п.arg: з for п, з in zip(параметри, арг)})
        сер.update(іменовані)
        for п in параметри + в.args.kwonlyargs:
            сер.setdefault(п.arg, НЕВІДОМЕ)
        я.стек.append(ключ)
        try:
            я.блок(в.body, м, сер)
        except Повернення as п:
            return п.значення
        finally:
            я.стек.pop()
        return НЕВІДОМЕ

    def блок(я, вузли, м, сер):
        """Виконує дозволені оператори; зовнішні побічні дії не виконує."""
        for в in вузли:
            if isinstance(в, ast.Return):
                raise Повернення(я.вираз(в.value, м, сер))
            if isinstance(в, (ast.Assign, ast.AnnAssign)):
                з = я.вираз(в.value, м, сер)
                for ц in в.targets if isinstance(в, ast.Assign) else [в.target]:
                    я.привʼязати(ц, з, сер)
            elif isinstance(в, ast.AugAssign):
                з = я.вираз(в.target, м, сер)
                д = я.вираз(в.value, м, сер)
                я.привʼязати(в.target, я.додати(з, д), сер)
            elif isinstance(в, ast.If):
                я.блок(в.body if я.умова(я.вираз(в.test, м, сер), м, в.test) else в.orelse, м, сер)
            elif isinstance(в, ast.For):
                з = я.вираз(в.iter, м, сер)
                if isinstance(з, (dict, list, tuple, set)):
                    for х in з:
                        я.привʼязати(в.target, х, сер)
                        я.блок(в.body, м, сер)
            elif isinstance(в, ast.Expr) and not isinstance(в.value, ast.Constant):
                я.вираз(в.value, м, сер)
            elif isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                сер[в.name] = ("локальна", м, в, сер.copy())
            elif isinstance(в, ast.Try):
                я.блок(в.body, м, сер)
            elif isinstance(в, ast.Raise):
                raise Повернення(НЕВІДОМЕ)

    def додати(я, л, п):
        """Склеює сталі частини, невідомий доданок не стирає відомого."""
        if isinstance(л, Невідоме):
            return п
        if isinstance(п, Невідоме):
            return л
        try:
            return л + п
        except (TypeError, ValueError):
            return НЕВІДОМЕ

    def перебір(я, в, м, сер, н=0):
        """Обчислює генератор по відомих реєстрах, зберігаючи умови відбору."""
        if н == len(в.generators):
            yield (я.вираз(в.key, м, сер), я.вираз(в.value, м, сер)) if isinstance(в, ast.DictComp) else я.вираз(в.elt, м, сер)
            return
        г = в.generators[н]
        кол = я.вираз(г.iter, м, сер)
        if isinstance(кол, Невідоме):
            return
        if not isinstance(кол, (list, tuple, dict, set, str)):
            return
        for з in кол:
            нове = сер.copy()
            я.привʼязати(г.target, з, нове)
            if all(я.умова(я.вираз(у, м, нове), м, у) for у in г.ifs):
                yield from я.перебір(в, м, нове, н + 1)

    def вираз(я, в, м, сер):
        """Обчислює білий перелік виразів AST; довільного eval немає."""
        я.кроки += 1
        if я.кроки > 100000:
            raise RuntimeError("перевищено 100000 операцій одного варіанта")
        if в is None:
            return НЕВІДОМЕ
        if isinstance(в, ast.Constant):
            return в.value
        if isinstance(в, ast.Name):
            з = сер[в.id] if в.id in сер else я.глобальне(м, в.id)
            if isinstance(з, tuple) and з and з[0] == "гілки":
                з = з[3] if я.умова(я.вираз(з[1], м, з[2]), м, з[1]) else з[4]
            return я.вираз(з.вузол, м, з.середовище) if isinstance(з, Відкладене) else з
        if isinstance(в, ast.Attribute):
            з = я.вираз(в.value, м, сер)
            if isinstance(з, tuple) and з and з[0] == "модуль":
                return я.глобальне(з[1], в.attr)
            if type(з).__name__ in ("Оголошення", "Поле"):
                return getattr(з, в.attr, НЕВІДОМЕ)
            return НЕВІДОМЕ
        if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
            вих = []
            for х in в.elts:
                з = я.вираз(х.value if isinstance(х, ast.Starred) else х, м, сер)
                if isinstance(х, ast.Starred):
                    вих.extend(з if isinstance(з, (list, tuple)) else [])
                else:
                    вих.append(з)
            return вих
        if isinstance(в, ast.Dict):
            вих = {}
            for к, з in zip(в.keys, в.values):
                знач = я.вираз(з, м, сер)
                if к is None:
                    if isinstance(знач, dict):
                        вих.update(знач)
                else:
                    ключ = я.вираз(к, м, сер)
                    if isinstance(ключ, (str, int, float, bool, type(None))):
                        вих[ключ] = знач
            return вих
        if isinstance(в, ast.Subscript):
            з, к = я.вираз(в.value, м, сер), я.вираз(в.slice, м, сер)
            if isinstance(з, dict) and isinstance(к, Невідоме) and з:
                ключ = (м.відн, в.lineno, в.col_offset)
                if ключ not in я.умови:
                    raise Вибір(ключ, tuple(з))
                к = я.умови[ключ]
            try:
                return з[к]
            except (TypeError, KeyError, IndexError):
                return НЕВІДОМЕ
        if isinstance(в, ast.Slice):
            return slice(*(я.вираз(х, м, сер) if х is not None else None for х in (в.lower, в.upper, в.step)))
        if isinstance(в, ast.JoinedStr):
            return "".join(текст(я.вираз(х, м, сер)) for х in в.values)
        if isinstance(в, ast.FormattedValue):
            return я.вираз(в.value, м, сер)
        if isinstance(в, ast.IfExp):
            return я.вираз(в.body if я.умова(я.вираз(в.test, м, сер), м, в.test) else в.orelse, м, сер)
        if isinstance(в, ast.BoolOp):
            for х in в.values:
                з = я.вираз(х, м, сер)
                if isinstance(з, Невідоме):
                    return з
                if bool(з) == isinstance(в.op, ast.Or):
                    return з
            return з
        if isinstance(в, ast.UnaryOp):
            з = я.вираз(в.operand, м, сер)
            if isinstance(з, Невідоме):
                return з
            return not з if isinstance(в.op, ast.Not) else -з if isinstance(з, (int, float)) else НЕВІДОМЕ
        if isinstance(в, ast.Compare):
            л = я.вираз(в.left, м, сер)
            for оп, х in zip(в.ops, в.comparators):
                п = я.вираз(х, м, сер)
                if isinstance(л, Невідоме) or isinstance(п, Невідоме):
                    return НЕВІДОМЕ
                try:
                    ок = {ast.Eq: lambda: л == п, ast.NotEq: lambda: л != п,
                          ast.In: lambda: л in п, ast.NotIn: lambda: л not in п,
                          ast.Is: lambda: л is п, ast.IsNot: lambda: л is not п,
                          ast.Lt: lambda: л < п, ast.Gt: lambda: л > п,
                          ast.LtE: lambda: л <= п, ast.GtE: lambda: л >= п}[type(оп)]()
                except (TypeError, KeyError):
                    return НЕВІДОМЕ
                if not ок:
                    return False
                л = п
            return True
        if isinstance(в, ast.BinOp):
            л, п = я.вираз(в.left, м, сер), я.вираз(в.right, м, сер)
            if isinstance(в.op, ast.Add):
                return я.додати(л, п)
            if isinstance(в.op, ast.Mod) and isinstance(л, str):
                арг = tuple(текст(х) for х in п) if isinstance(п, list) else текст(п)
                try:
                    return л % арг
                except (TypeError, ValueError):
                    return НЕВІДОМЕ
            return НЕВІДОМЕ
        if isinstance(в, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
            значення = list(я.перебір(в, м, сер))
            return dict(значення) if isinstance(в, ast.DictComp) else значення
        if isinstance(в, ast.Lambda):
            return ("лямбда", м, в, сер.copy())
        if isinstance(в, ast.Call):
            return я.виклик(в, м, сер)
        return НЕВІДОМЕ

    def виклик(я, в, м, сер):
        """Виконує тільки чисті операції рядків/колекцій та інтерпретує власні функції."""
        ім = getattr(в.func, "id", None) or getattr(в.func, "attr", "")
        if ім == "зібрати" and в.args:
            о = я.вираз(в.args[0], м, сер)
            if type(о).__name__ == "Оголошення":
                return повне_оголошення(о)
        арг = [я.вираз(х, м, сер) for х in в.args]
        іменовані = {х.arg: я.вираз(х.value, м, сер) for х in в.keywords if х.arg}
        if isinstance(в.func, ast.Name):
            if ім == "str":
                return текст(арг[0]) if арг else ""
            if ім in ("list", "tuple", "set", "sorted"):
                return sorted(арг[0], key=str) if ім == "sorted" and арг and not isinstance(арг[0], Невідоме) else (
                    list(арг[0]) if арг and isinstance(арг[0], (list, tuple, set, dict, str)) else [])
            if ім == "dict":
                return dict(арг[0] if арг and isinstance(арг[0], (dict, list)) else {}, **іменовані)
            if ім == "isinstance":
                if арг and isinstance(арг[0], Невідоме):
                    return НЕВІДОМЕ
                назва = getattr(в.args[1], "id", "") if len(в.args) > 1 else ""
                типи = {"dict": dict, "str": str, "list": list, "tuple": tuple, "bool": bool, "int": int}
                return isinstance(арг[0], типи[назва]) if назва in типи else НЕВІДОМЕ
            if ім in ("len", "bool", "any", "all", "enumerate", "zip"):
                if any(isinstance(х, Невідоме) for х in арг):
                    return НЕВІДОМЕ
                return {"len": len, "bool": bool, "any": any, "all": all,
                        "enumerate": lambda *а: list(enumerate(*а)), "zip": lambda *а: list(zip(*а))}[ім](*арг)
        if isinstance(в.func, ast.Attribute):
            об = я.вираз(в.func.value, м, сер)
            if ім == "dumps":
                return json.dumps(арг[0], ensure_ascii=False, default=lambda _: "").replace("<дані>", "") if арг else ""
            if isinstance(об, dict):
                if ім == "get":
                    if арг and isinstance(арг[0], Невідоме) and об:
                        ключ = (м.відн, в.lineno, в.col_offset)
                        if ключ not in я.умови:
                            raise Вибір(ключ, tuple(об))
                        return об[я.умови[ключ]]
                    return об.get(*арг)
                if ім in ("items", "keys", "values"):
                    return list(getattr(об, ім)())
            if isinstance(об, list) and ім in ("append", "extend"):
                if арг and not isinstance(арг[0], Невідоме):
                    getattr(об, ім)(арг[0])
                return None
            if isinstance(об, str) and ім in ("join", "replace", "format", "strip", "lstrip", "rstrip", "lower", "upper",
                                               "split", "rsplit", "partition", "rpartition", "startswith", "endswith"):
                if ім == "join":
                    return об.join(текст(х) for х in арг[0]) if арг and isinstance(арг[0], (list, tuple)) else ""
                return getattr(об, ім)(*(текст(х) if isinstance(х, Невідоме) else х for х in арг), **іменовані)
        ц = я.вираз(в.func, м, сер)
        if isinstance(ц, tuple) and ц:
            if ц[0] == "функція":
                return я.функція(ц[1], ц[2], арг, іменовані)
            if ц[0] == "лямбда":
                нове = ц[3].copy()
                нове.update({п.arg: з for п, з in zip(ц[2].args.args, арг)})
                return я.вираз(ц[2].body, ц[1], нове)
        if ім not in ("get", "loads", "compile", "items", "values", "keys", "isinstance", "зібрати"):
            я.попередження.add((м.відн, в.lineno, "не розгорнуто виклик " + ім))
        return НЕВІДОМЕ


def повне_оголошення(о):
    """Збирає незмінний шаблон одного виклику з усіма оголошеними полями.

    Значення входу — порожні маркери. Структура й описи полів, роль, правила,
    реєстрові фрази та схема — справжній вихід продуктового збирача.
    """
    дані = {}
    for п in о.вхід:
        пот = дані
        шлях = п.шлях.split(".")
        for н, ключ in enumerate(шлях):
            масив = ключ.endswith("[]")
            ключ = ключ.replace("[]", "")
            if н == len(шлях) - 1:
                пот.setdefault(ключ, ["<дані>"] if масив else "<дані>")
            else:
                if масив:
                    if not isinstance(пот.get(ключ), list) or not пот[ключ] or not isinstance(пот[ключ][0], dict):
                        пот[ключ] = [{}]
                elif not isinstance(пот.get(ключ), dict):
                    пот[ключ] = {}
                пот = пот[ключ][0] if масив else пот[ключ]
    зп = sys.modules["збирач_промптів"]
    return зп.зібрати(о, дані)


def виходи_функції(в):
    """Розріз даних перед кожним return і викликом, без виконання зайвого коду."""
    вих = []
    def пройти(блок, сер):
        for н in блок:
            if not isinstance(н, (ast.If, ast.For, ast.While, ast.FunctionDef, ast.AsyncFunctionDef, ast.Try)):
                вих.extend((х, сер.copy()) for х in ast.walk(н) if isinstance(х, ast.Call))
            if isinstance(н, (ast.Assign, ast.AnnAssign)):
                цілі = н.targets if isinstance(н, ast.Assign) else [н.target]
                for ц in цілі:
                    if isinstance(ц, ast.Name):
                        сер[ц.id] = Відкладене(н.value, сер)
            elif isinstance(н, ast.AugAssign) and isinstance(н.target, ast.Name):
                вираз = ast.copy_location(ast.BinOp(left=н.target, op=н.op, right=н.value), н)
                сер[н.target.id] = Відкладене(вираз, сер)
            elif isinstance(н, ast.Return):
                вих.append((н, сер.copy()))
            elif isinstance(н, ast.If):
                л, п = сер.copy(), сер.copy()
                пройти(н.body, л)
                пройти(н.orelse, п)
                for ім in sorted(set(л) | set(п)):
                    if л.get(ім) is п.get(ім):
                        continue
                    # Дві версії присвоєння мають власне попереднє оточення.
                    сер[ім] = ("гілки", н.test, сер.copy(), л.get(ім, НЕВІДОМЕ), п.get(ім, НЕВІДОМЕ))
    пройти(в.body, {п.arg: НЕВІДОМЕ for п in в.args.posonlyargs + в.args.args + в.args.kwonlyargs})
    return вих


def текстові_параметри(м, в):
    """Індекси аргументів, що надходять у text/content повідомлення моделі."""
    if not re.search(r"chat/completions|generateContent|/v1/messages|[\"']role[\"']", м.текст):
        return set()
    присвоєння = {ц.id: н.value for н in ast.walk(в) if isinstance(н, ast.Assign)
                   for ц in н.targets if isinstance(ц, ast.Name)}
    імена = set()
    def розкрити(н, бачені):
        for х in ast.walk(н):
            if isinstance(х, ast.Name):
                імена.add(х.id)
                if х.id in присвоєння and х.id not in бачені:
                    розкрити(присвоєння[х.id], бачені | {х.id})
    for н in ast.walk(в):
        if isinstance(н, ast.Dict):
            поля = {к.value: з for к, з in zip(н.keys, н.values) if isinstance(к, ast.Constant)}
            if "role" in поля and "content" in поля:
                розкрити(поля["content"], set())
    return {і for і, п in enumerate(в.args.posonlyargs + в.args.args) if п.arg in імена}


def зібрати_функції(модулі, вимога):
    """Повертає повні сталі тексти функцій промпту та аргументів тексту транспорту.

    Оголошення, які збирач повертає словником, лишаються в окремому шляху
    оголошень. Тут доповнюються функції, що повертають рядок, і транспортні
    виклики з аргументом тексту. Імена сталих джерелом довжин не є.
    """
    з = Збирач(модулі)
    вих, діагностика, завдання, стоки = {}, [], [], {}
    for м in модулі.values():
        for ім, в in м.визначення.items():
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                індекси = текстові_параметри(м, в)
                if індекси:
                    стоки[(м.відн, ім)] = індекси
    for м in модулі.values():
        if not м.відн.startswith(("джерела/", "zhnyvarka/")) or "/прилади/" in м.відн or "/проби/" in м.відн:
            continue
        for ім, в in м.визначення.items():
            if not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            номер = 0
            for н, сер in виходи_функції(в):
                if isinstance(н, ast.Return) and re.search(r"(?:^|_)промпт(?:_|$)|prompt", ім, re.I):
                    номер += 1
                    завдання.append((м, ім + ":вихід%d" % номер, н.value, сер))
                elif isinstance(н, ast.Call):
                    if not (isinstance(н.func, ast.Name) or isinstance(н.func, ast.Attribute) and isinstance(н.func.value, ast.Name)):
                        continue
                    з.кроки = 0
                    try:
                        ц = з.вираз(н.func, м, {})
                    except (Вибір, TypeError, ValueError, AttributeError, KeyError, IndexError, RuntimeError):
                        continue
                    if isinstance(ц, tuple) and ц and ц[0] == "функція":
                        for і in sorted(стоки.get((ц[1].відн, ц[2].name), ())):
                            if і < len(н.args):
                                номер += 1
                                завдання.append((м, ім + ":виклик%d" % номер, н.args[і], сер))
    for м, ім, вираз, сер in завдання:
            черга, побачені, тексти = collections.deque([{}]), set(), set()
            while черга and len(побачені) < 256:
                умови = черга.popleft()
                ключ = tuple(sorted(умови.items()))
                if ключ in побачені:
                    continue
                побачені.add(ключ)
                з.умови, з.кроки, з.глобальні = умови, 0, {}
                try:
                    т = з.вираз(вираз, м, сер)
                    if isinstance(т, str) and (len(т) >= 120 or any(вимога(с) for с in re.split(r"\n|(?<=[.!?])\s+", т))):
                        тексти.add(т)
                except Вибір as п:
                    for знач in п.варіанти:
                        черга.append(умови | {п.ключ: знач})
                except (TypeError, ValueError, AttributeError, KeyError, IndexError, RuntimeError, RecursionError) as п:
                    діагностика.append((м.відн, вираз.lineno, type(п).__name__ + ": " + str(п)[:100]))
            if черга:
                діагностика.append((м.відн, вираз.lineno, "понад 256 станів невідомих умов"))
            for н, т in enumerate(sorted(тексти), 1):
                вих["%s:%s#%d" % (м.відн, ім, н)] = т
    return вих, sorted(set(діагностика)), sorted(з.попередження)
