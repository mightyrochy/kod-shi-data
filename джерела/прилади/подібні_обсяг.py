# -*- coding: utf-8 -*-
"""Обсяг розвідки «Подібні до години»: перелік усіх одиниць чотирьох частин і покриття переліку вердиктами.

Наряд `аудит/наряди/Подібні-розвідка.md` (слово власника 31.10 14:26): шукати вади класу години в усьому обсязі, а не
від рядків дошки. Прилад не судить — він лічить знаменник: кожну одиницю кожної частини обсягу з детермінованим ід, щоб
перелік `аудит/корені/Подібні-перелік.md` мав вердикт на кожну, а покриття рахував скрипт, а не сесія.

Частини (ід одиниці — перша колонка):
  а  поле, яке мовна модель віддає коду: вузли схем протоколу відповідей (`протокол.ВІД_МОДЕЛІ`, `ПОЗА_ПАКЕТОМ`),
     властивості `внутрішня_мова.schema.json`, записи `паспорт_поля.ПОЛЯ_ПАСПОРТА`, властивості
     `каталог_розбір.schema.json`, і форма реєстру `схема_відповіді` без схеми протоколу — одиницею форма (полів
     статично нема: їх і лічить Е2-межі п.1);
  б  значення, яке код виводить сам: функція коду продукту, що читає поле паспорта чи сцени за ключем (назва поля
     паспорта, його англійське поле чи ключ сценарію) і в якій є виведення — порівняння з числом, арифметика,
     таблиця відповідностей, регулярка чи підрядок над рядком, типове значення (`.get(к, x)`, `or x`);
  в  правило стилю в коді й реєстрах: константа реєстру (`REGISTRY`/`РЕЄСТР`) і ід правила корпусу, що стоїть у
     коді продукту рядком (не в докстрінгу);
  г  посилання на слово власника з датою (`власник … ДД.ММ`) у правилах роботи: ядро, адаптери, файли ролей,
     додатки до ролей, `аудит/ПРОДУКТ.md`.

Код продукту — `джерела/*.py` верхнього рівня, крім приладів, проб, тестів, стендів, батарей, гейтів і аудитів.

Запуск з кореня репозиторію:
  python3 джерела/прилади/подібні_обсяг.py --частина г        одиниці частини, рядок на одиницю (ід ⇥ місце ⇥ опис)
  python3 джерела/прилади/подібні_обсяг.py --перелік аудит/корені/Подібні-перелік.md
      покриття: одиниця покрита, коли її ід стоїть першою клітинкою рядка таблиці переліку (`| ід | … |`).
"""
import argparse
import ast
import glob
import json
import os
import re
import sys

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")

НЕ_ПРОДУКТ = ("тест", "стенд", "проба", "батарея", "audit", "gate", "measure", "мутанти", "жнива", "pair_test",
              "лабораторія", "гейти", "verify", "аудит_", "поломки", "траса", "звірка", "status", "trace",
              "build_", "покроковик", "зведення", "досяжність", "відбиток", "лічба")


def _продукт():
    """Модулі коду продукту: `джерела/*.py` верхнього рівня без приладів, проб, тестів і збирання."""
    return sorted(ф for ф in glob.glob(os.path.join(ДЖ, "*.py"))
                  if not os.path.basename(ф).startswith(НЕ_ПРОДУКТ))


def _відн(шлях):
    return os.path.relpath(шлях, КОРІНЬ)


def _ast(шлях):
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(open(шлях, encoding="utf-8").read())


# ───────────────────────────── г: посилання на слово власника ─────────────────────────────
ПРАВИЛА_РОБОТИ = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "аудит/CHATGPT.md", "аудит/адаптери/CLAUDE_КЕРУВАННЯ.md",
                  "аудит/адаптери/gemini/m9v/ЩО_НАТИСНУТИ.md", "аудит/МЕНЕДЖЕР.md", "аудит/ДИСПЕТЧЕР.md",
                  "аудит/ВИКОНАВЕЦЬ.md", "аудит/ПЕРЕВІРКА.md", "аудит/НОУТБУК.md", "аудит/КОД.md", "аудит/МОДЕЛІ.md",
                  "аудит/СТАНДАРТ_КОДУ.md", "аудит/ПРОДУКТ.md", "аудит/проби/живі_порядок.md")
_ДАТА = re.compile(r"(?<![\d.])(\d{1,2}\.(?:09|10|11|12))(?![\d])")
_ВЛАСНИК = re.compile(r"власник\w*")


def частина_г():
    """Посилання — слово «власник» у будь-якій формі й дати того самого звороту: від «власник» до кінця дужок,
    речення чи 120 знаків (рядки файлів перенесено — текст склеєно); дата без «власник» — не посилання."""
    одиниці = []
    for ф in ПРАВИЛА_РОБОТИ:
        шлях = os.path.join(КОРІНЬ, ф)
        if not os.path.exists(шлях):
            continue
        текст = open(шлях, encoding="utf-8").read()
        плаский = текст.replace("\n", " ")
        на_рядку = {}
        for з in _ВЛАСНИК.finditer(плаский):
            кінець = len(плаский)
            for м in re.finditer(r"[()]|\.\s|;|:\s[«\"]|«", плаский[з.end():з.end() + 120]):
                кінець = з.end() + м.start()
                break
            else:
                кінець = min(кінець, з.end() + 120)
            дати = _ДАТА.findall(плаский[з.end():кінець])
            if not дати:
                continue
            н = текст.count("\n", 0, з.start()) + 1
            на_рядку[н] = на_рядку.get(н, 0) + 1
            одиниці.append(("г:%s:%d.%d" % (ф, н, на_рядку[н]), "%s:%d" % (ф, н),
                            "%s · %s" % (",".join(дати), плаский[max(0, з.start() - 90):кінець + 1].strip())))
    return одиниці


# ───────────────────────────── а: поля, які модель віддає коду ─────────────────────────────
def _імпорт():
    import warnings
    warnings.simplefilter("ignore")
    if ДЖ not in sys.path:
        sys.path.insert(0, ДЖ)


def _вузли_протоколу(вузол, шлях, вихід):
    """Обхід вузла схеми протоколу (`протокол.обʼєкт`, `карта`, `список`, `або_нуль`): ід — шлях полів."""
    if not isinstance(вузол, dict):
        return
    тип = вузол.get("тип")
    if тип == "обʼєкт":
        for к, в in вузол.get("поля", {}).items():
            вихід.append((шлях + "." + к, в))
            _вузли_протоколу(в, шлях + "." + к, вихід)
    elif тип == "карта":
        _вузли_протоколу(вузол.get("по_ключу"), шлях + "{}", вихід)
    elif тип == "список":
        _вузли_протоколу(вузол.get("елемент"), шлях + "[]", вихід)
    for к in ("вузол", "варіанти", "або"):
        в = вузол.get(к)
        if isinstance(в, dict):
            _вузли_протоколу(в, шлях, вихід)
        elif isinstance(в, (list, tuple)):
            for x in в:
                _вузли_протоколу(x, шлях, вихід)


def _опис_вузла(в):
    if not isinstance(в, dict):
        return type(в).__name__
    т = в.get("тип") or в.get("type") or "?"
    if в.get("значення"):
        т += " з переліку %d" % len(в["значення"])
    if в.get("enum"):
        т += " з переліку %d" % len(в["enum"])
    return str(т)


def _властивості_json(вузол, шлях, вихід, defs):
    if not isinstance(вузол, dict):
        return
    if "$ref" in вузол and вузол["$ref"].startswith("#/$defs/"):
        return  # посилання на іншу форму — її поля лічить її власний обхід
    for к, в in вузол.get("properties", {}).items():
        вихід.append((шлях + "." + к, в))
        _властивості_json(в, шлях + "." + к, вихід, defs)
    for к in ("items", "additionalProperties"):
        if isinstance(вузол.get(к), dict):
            _властивості_json(вузол[к], шлях + "[]", вихід, defs)
    for к in ("anyOf", "oneOf", "allOf"):
        for x in вузол.get(к, []):
            _властивості_json(x, шлях, вихід, defs)


def частина_а():
    _імпорт()
    import протокол
    import паспорт_поля
    import схема_відповіді
    одиниці = []
    форми = list(протокол.ВІД_МОДЕЛІ) + sorted(getattr(протокол, "ПОЗА_ПАКЕТОМ", {}))
    for ф in форми:
        схема = протокол.СХЕМИ.get(ф) or протокол.ПОЗА_ПАКЕТОМ.get(ф)
        вузли = []
        _вузли_протоколу(схема, ф, вузли)
        for шлях, в in вузли:
            одиниці.append(("а:протокол:" + шлях, "джерела/протокол.py", _опис_вузла(в)))
    мова = json.load(open(os.path.join(ДЖ, "внутрішня_мова.schema.json"), encoding="utf-8"))
    for ф, в in мова["$defs"].items():
        вузли = []
        _властивості_json(в, ф, вузли, мова["$defs"])
        for шлях, вв in вузли:
            одиниці.append(("а:мова:" + шлях, "джерела/внутрішня_мова.schema.json", _опис_вузла(вв)))
    for к, з in паспорт_поля.ПОЛЯ_ПАСПОРТА.items():
        опис = ",".join(sorted(x for x in з if not callable(з[x]))) if isinstance(з, dict) else ""
        одиниці.append(("а:паспорт:" + к, "джерела/паспорт_поля.py", "поле %s · %s" % (
            з.get("поле", "—") if isinstance(з, dict) else "—", опис)))
    кат = json.load(open(os.path.join(ДЖ, "каталог_розбір.schema.json"), encoding="utf-8"))
    вузли = []
    _властивості_json(кат["$defs"]["model_answer"], "model_answer", вузли, кат["$defs"])
    for шлях, в in вузли:
        одиниці.append(("а:каталог:" + шлях, "джерела/каталог_розбір.schema.json", _опис_вузла(в)))
    реєстр = [v for v in vars(схема_відповіді).values() if isinstance(v, dict) and v
              and all(isinstance(x, схема_відповіді.СхемаВідповіді) for x in v.values())][0]
    for ід, ф in sorted(реєстр.items()):
        if not ф.схема_протоколу:
            одиниці.append(("а:форма:" + ід, "джерела/схема_відповіді.py",
                            "форма без схеми протоколу · відповідь як %s · поля %s" % (ф.відповідь_як, ",".join(ф.поля) or "—")))
    return одиниці


# ───────────────────────────── в: правила стилю в коді й реєстрах ─────────────────────────────
БЕЗПЕЧНІ = {0, 1, 2, -1, 0.0, 1.0, 2.0, 0.5, 100, 100.0, 10, 10.0, 3, 4, 60, 360, 180}  # як `audit_anchors.БЕЗПЕЧНІ`


def _число(x):
    if isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool):
        return x.value
    if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub) and _число(x.operand) is not None:
        return -_число(x.operand)
    return None


def _числове(x):
    if _число(x) is not None:
        return True
    return isinstance(x, (ast.Tuple, ast.List)) and bool(x.elts) and all(_числове(е) for е in x.elts)


def _докстрінги(дерево):
    ід = set()
    for в in ast.walk(дерево):
        if isinstance(в, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and в.body \
                and isinstance(в.body[0], ast.Expr) and isinstance(в.body[0].value, ast.Constant) \
                and isinstance(в.body[0].value.value, str):
            ід.add(id(в.body[0].value))
    return ід


def _функції(дерево):
    """(вузол, ім'я функції) для кожного вузла: найглибша охопна функція; рівень модуля — «<модуль>»."""
    вихід = []

    def обхід(в, ім):
        for д in ast.iter_child_nodes(в):
            if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef)):
                обхід(д, д.name)
            else:
                вихід.append((д, ім))
                обхід(д, ім)
    обхід(дерево, "<модуль>")
    return вихід


_СЛОВО_В_КОДІ = re.compile(r"власник\w*[^\n]{0,40}?\d{1,2}\.(?:09|10|11)|\d{1,2}\.(?:09|10|11)[^\n]{0,10}власник")


def частина_в():
    _імпорт()
    import ід_правил
    одиниці = []
    ід_у_коді = {}
    for ф in _продукт():
        дерево = _ast(ф)
        файл = _відн(ф)
        докс = _докстрінги(дерево)
        # константи реєстрів провенансу: словник рівня модуля REGISTRY / РЕЄСТР / КОНСТАНТИ
        for в in дерево.body:
            if isinstance(в, ast.Assign) and isinstance(в.value, ast.Dict) and any(
                    isinstance(ц, ast.Name) and ц.id in ("REGISTRY", "РЕЄСТР", "КОНСТАНТИ") for ц in в.targets):
                for к in в.value.keys:
                    if isinstance(к, ast.Constant):
                        одиниці.append(("в:реєстр:%s:%s" % (os.path.basename(ф), к.value), "%s:%d" % (файл, к.lineno),
                                        "константа реєстру"))
            # стала рівня модуля: ім'я = число чи кортеж чисел
            if isinstance(в, ast.Assign) and _числове(в.value) and all(isinstance(ц, ast.Name) for ц in в.targets):
                for ц in в.targets:
                    одиниці.append(("в:стала:%s:%s" % (os.path.basename(ф), ц.id), "%s:%d" % (файл, в.lineno),
                                    "стала модуля = %s" % ast.unparse(в.value)[:60]))
        # поріг-літерал: порівняння <, <=, >, >= з числом поза БЕЗПЕЧНІ всередині функції
        бачено = set()
        for в, ім in _функції(дерево):
            if ім != "<модуль>" and isinstance(в, ast.Compare) and any(
                    isinstance(о, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for о in в.ops):
                for x in [в.left] + в.comparators:
                    ч = _число(x)
                    if ч is not None and ч not in БЕЗПЕЧНІ:
                        к = (в.lineno, ч)
                        if к in бачено:
                            continue
                        бачено.add(к)
                        одиниці.append(("в:поріг:%s:%d:%s" % (os.path.basename(ф), в.lineno, ч), "%s:%d" % (файл, в.lineno),
                                        "%s · %s" % (ім, ast.unparse(в)[:80])))
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in докс:
                for б in ід_правил.бази_в_тексті(в.value):
                    ід_у_коді.setdefault(б, set()).add("%s:%d" % (файл, в.lineno))
        # слово власника з датою в коді (коментар чи рядок): чи діє воно на ту нагоду, про яку сказано (п.5)
        for н, рядок in enumerate(open(ф, encoding="utf-8"), 1):
            if _СЛОВО_В_КОДІ.search(рядок):
                одиниці.append(("в:слово:%s:%d" % (os.path.basename(ф), н), "%s:%d" % (файл, н), рядок.strip()[:140]))
    for б in sorted(ід_у_коді):
        місця = sorted(ід_у_коді[б])
        одиниці.append(("в:ід:" + б, місця[0], "ід правила в коді · місць %d · %s" % (len(місця), " ".join(місця[:6]))))
    return одиниці


# ───────────────────────────── б: значення, які код виводить сам ─────────────────────────────
ЗАГАЛЬНІ = {"value", "quote", "quotes", "code", "text", "id", "kind", "type", "name", "items", "item", "answer",
            "note", "notes", "reason", "why", "ід", "назва", "текст", "код", "решта", "невідомо", "звідки", "запити"}


def _ключі_паспорта():
    """Ключі паспорта й сцени: записи `ПОЛЯ_ПАСПОРТА`, їхні англійські поля й властивості форм сценарію й ходу
    розмови внутрішньої мови (листки), без загальних слів (`ЗАГАЛЬНІ`)."""
    _імпорт()
    import паспорт_поля
    к = set()
    for ім, з in паспорт_поля.ПОЛЯ_ПАСПОРТА.items():
        if not ім.startswith("@"):
            к.add(ім)
        if isinstance(з, dict) and isinstance(з.get("поле"), str):
            к.add(з["поле"])
    мова = json.load(open(os.path.join(ДЖ, "внутрішня_мова.schema.json"), encoding="utf-8"))
    for ф in ("scenario", "conversation_turn"):
        вузли = []
        _властивості_json(мова["$defs"][ф], ф, вузли, мова["$defs"])
        к |= {ш.rsplit(".", 1)[-1].rstrip("[]") for ш, _ in вузли}
    return {x for x in к if x not in ЗАГАЛЬНІ and len(x) > 2}


def _читання_ключа(в, ключі):
    """Рядковий ключ паспорта, який вузол читає: `x["к"]`, `x.get("к", …)`, аксесор `ф("к", …)`."""
    if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and в.slice.value in ключі:
        return в.slice.value
    if isinstance(в, ast.Call) and в.args and isinstance(в.args[0], ast.Constant) and в.args[0].value in ключі:
        if isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "pop", "setdefault"):
            return в.args[0].value
        if isinstance(в.func, ast.Name):
            return в.args[0].value
    return None


def _ознаки_виведення(функція):
    """Ознаки, що функція виводить значення сама: поріг (порівняння з числом), арифметика, регулярка, підрядок,
    типове (`.get(к, x)` з x не None, `… or x`), таблиця відповідностей."""
    о = set()
    for в in ast.walk(функція):
        # таблиця відповідностей: `ТАБЛИЦЯ[x]` чи `ТАБЛИЦЯ.get(x…)` зі змінним ключем (ім'я великими літерами)
        if isinstance(в, ast.Subscript) and isinstance(в.value, ast.Name) and в.value.id.isupper() \
                and not isinstance(в.slice, ast.Constant):
            о.add("таблиця")
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" \
                and isinstance(в.func.value, ast.Name) and в.func.value.id.isupper() and в.args \
                and not isinstance(в.args[0], ast.Constant):
            о.add("таблиця")
        if isinstance(в, ast.Compare):
            if _порівняння_з_порогом(в):
                о.add("поріг")
            if any(isinstance(оп, (ast.In, ast.NotIn)) for оп in в.ops) and isinstance(в.left, ast.Constant) \
                    and isinstance(в.left.value, str):
                о.add("підрядок")
        elif isinstance(в, ast.BinOp) and isinstance(в.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)) \
                and not (isinstance(в.left, ast.Constant) and isinstance(в.left.value, str)):
            if _число(в.left) is not None or _число(в.right) is not None:
                о.add("арифметика")
        elif isinstance(в, ast.Call):
            ф = в.func
            if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id == "re":
                о.add("регулярка")
            if isinstance(ф, ast.Attribute) and ф.attr in ("search", "match", "fullmatch", "findall", "sub", "finditer"):
                о.add("регулярка")
            if isinstance(ф, ast.Attribute) and ф.attr in ("startswith", "endswith", "find", "split"):
                о.add("підрядок")
            if isinstance(ф, ast.Attribute) and ф.attr == "get" and len(в.args) == 2 and isinstance(в.args[1], ast.Constant) \
                    and в.args[1].value not in (None, "", 0, False):
                о.add("типове")
        elif isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or) and isinstance(в.values[-1], ast.Constant) \
                and в.values[-1].value not in (None, "", False):
            о.add("типове")
    return о


def _порівняння_з_порогом(в):
    """Порівняння <, <=, >, >= з числом-літералом чи з порогом за іменем великими літерами (`ПОРІГ`,
    `РЕЄСТР["к"]["val"]`)."""
    if not any(isinstance(оп, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for оп in в.ops):
        return False
    for x in [в.left] + в.comparators:
        if _число(x) is not None:
            return True
        корінь = x
        while isinstance(корінь, (ast.Subscript, ast.Attribute)):
            корінь = корінь.value
        if isinstance(корінь, ast.Name) and корінь.id.isupper() and корінь is not x or (
                isinstance(x, ast.Name) and x.id.isupper()):
            return True
    return False


def частина_б():
    """Функція — одиниця, коли до неї доходить ключ паспорта — читанням (`x["к"]`, `.get("к")`, аксесор `ф("к")`)
    чи аргументом виклику (позиційним чи іменованим; у виклику — читання чи локальне ім'я, присвоєне з читання), потік
    між функціями — до нерухомої точки за іменем функції, — і в ній є ознака виведення."""
    ключі = _ключі_паспорта()
    функції = [(ф, в) for ф in _продукт() for в in ast.walk(_ast(ф))
               if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))]
    читає = {}
    for ф, в in функції:
        к = {к for x in ast.walk(в) if (к := _читання_ключа(x, ключі))}
        if к:
            читає[(ф, в.lineno)] = к
    носії = {}  # ім'я функції → {позиція чи ім'я параметра: ключі}

    def мітки(вираз, мічені):
        з = {к for y in ast.walk(вираз) if (к := _читання_ключа(y, ключі))}
        for y in ast.walk(вираз):
            if isinstance(y, ast.Name) and y.id in мічені:
                з |= мічені[y.id]
        return з

    for _ in range(6):
        змін = False
        for ф, в in функції:
            мічені = {}
            параметри = в.args.posonlyargs + в.args.args
            for поз, к in носії.get(в.name, {}).items():
                ім = параметри[поз].arg if isinstance(поз, int) and поз < len(параметри) else поз
                if isinstance(ім, str):
                    мічені.setdefault(ім, set()).update(к)
            for y in ast.walk(в):
                if isinstance(y, ast.Assign):
                    з = {к for z in ast.walk(y.value) if (к := _читання_ключа(z, ключі))}
                    if з:
                        for ц in y.targets:
                            if isinstance(ц, ast.Name):
                                мічені.setdefault(ц.id, set()).update(з)
            if not (мічені or (ф, в.lineno) in читає):
                continue
            for x in ast.walk(в):
                if not isinstance(x, ast.Call):
                    continue
                ім = x.func.id if isinstance(x.func, ast.Name) else x.func.attr if isinstance(x.func, ast.Attribute) else None
                if not ім or ім in ("get", "pop", "setdefault", "int", "float", "str", "round", "len", "dict", "list",
                                    "append", "update", "join", "format", "isinstance", "set", "tuple", "sorted", "any", "all"):
                    continue
                пари = list(enumerate(x.args)) + [(кв.arg, кв.value) for кв in x.keywords if кв.arg]
                for поз, а in пари:
                    з = мітки(а, мічені)
                    if з and not з <= носії.get(ім, {}).get(поз, set()):
                        носії.setdefault(ім, {}).setdefault(поз, set()).update(з)
                        змін = True
        if not змін:
            break
    одиниці = []
    for ф, в in функції:
        прямо = читає.get((ф, в.lineno), set())
        аргументом = set().union(*носії.get(в.name, {}).values()) - прямо if в.name in носії else set()
        if not (прямо or аргументом):
            continue
        ознаки = _ознаки_виведення(в)
        if not ознаки:
            continue
        опис = "читає %s" % ",".join(sorted(прямо)[:8]) if прямо else ""
        if аргументом:
            опис += ("; " if опис else "") + "аргументом %s" % ",".join(sorted(аргументом)[:6])
        одиниці.append(("б:%s:%s:%d" % (os.path.basename(ф), в.name, в.lineno), "%s:%d" % (_відн(ф), в.lineno),
                        "%s · %s" % (опис, ",".join(sorted(ознаки)))))
    return одиниці

ЧАСТИНИ = {"а": частина_а, "б": частина_б, "в": частина_в, "г": частина_г}


def main():
    п = argparse.ArgumentParser()
    п.add_argument("--частина", choices=sorted(ЧАСТИНИ))
    п.add_argument("--перелік")
    а = п.parse_args()
    if а.частина:
        for од in ЧАСТИНИ[а.частина]():
            print("\t".join(од))
        return
    покрито = set()
    if а.перелік:
        for рядок in open(os.path.join(КОРІНЬ, а.перелік), encoding="utf-8"):
            м = re.match(r"\|\s*`?([абвг]:[^|`]+?)`?\s*\|", рядок)
            if м:
                покрито.add(м.group(1))
    for к, ф in sorted(ЧАСТИНИ.items()):
        усі = [о[0] for о in ф()]
        є = sum(1 for і in усі if і in покрито)
        print("частина %s: одиниць %d, з вердиктом %d (%.0f %%)" % (к, len(усі), є, 100.0 * є / max(1, len(усі))))


if __name__ == "__main__":
    main()
