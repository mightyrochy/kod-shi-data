# -*- coding: utf-8 -*-
"""прилади/межі_моделі.py — перелік меж моделі з коду: кожен виклик моделі (показ JS і Python) і кожне місце, де
Python читає сирий текст моделі, — через реєстр форм відповіді чи повз нього. Лічба «повз» — лічба обходів одної точки.

ЧОМУ ЦЕ Є (наряд Е2-межі-поза-реєстром, п.1; ПС-13, ПС-24). Перелік меж лежав неповним коментарем у `показ/міст.js`, і
кожна нова форма відповіді діставала свій розбір повз реєстр (`схема_відповіді` / `схеми_розбору`). Прилад не править
коду й не тримає списку меж руками: усе — з AST Python і з тексту показу.

ЯК РАХУЄ PYTHON. Сирий текст моделі — «мічене» значення. Звідки мітка:
  · поза — читання ключа, яким показ віддає мосту відповідь моделі (ключі бере з показу: обʼєкт `містП(...)`, чиє
    значення — змінна з виклику `модельП`), і відповідь сервера моделі в Python (`["choices"]`);
  · реєстр — перший параметр розбору чи сторожа, прив'язаного до форми в реєстрі (`схема_відповіді.СхемаВідповіді(...,
    розбір=, сторож=)`, `схеми_розбору.РОЗБІР`), і метод реєстру `СхемаВідповіді.прочитати`.
Мітка йде присвоєнням (сама змінна, `str()`, `.strip()`, зріз, `or`, умова), аргументом у функцію джерел (параметр
тієї функції) і поверненням (виклик функції, що повертає мічене). Виклик методу реєстру (`виконати_розбір`,
`прочитати`, `перевірити`) мітку не несе далі: там уже реєстр. ЧИТАЧ ФОРМАТУ — `протокол.розбір`, `розібрати_json`,
`розбір_останній`, `розбір_за_схемою`, `json.loads` і регулярка над міченим текстом. Читач із міткою «поза» — обхід;
межа — функція, де мітку «поза» поставлено.

ЯК РАХУЄ JS. Кожен виклик `модельП` / `модельП_блоки` у `показ/*.js`: функція верхнього рівня, у якій він стоїть,
скільки викликів моделі в ній (два й більше чи виклик у циклі — є повтор), ендпойнти мосту, які вона кличе, і ключі,
якими віддає мосту відповідь моделі.

Запуск (з кореня репозиторію): python3 джерела/прилади/межі_моделі.py [--json]
"""
import ast
import json
import os
import re
import sys
import warnings

warnings.simplefilter("ignore", SyntaxWarning)    # чужі модулі з `\w` у звичайних рядках — не справа приладу

ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ПОКАЗ = os.path.join(ДЖЕРЕЛА, "показ")
# Модулі, які не є шляхом продукту чи каталогу: тести, гейти й збирачі — вони кличуть читачі з вигаданим текстом.
НЕ_ШЛЯХ = re.compile(r"^(тест|gate|audit|build_|стенд|рв\d|replay)")
ЧИТАЧІ_ПРОТОКОЛУ = {"розбір", "розібрати_json", "розбір_останній", "розбір_за_схемою"}
МЕТОДИ_РЕЄСТРУ = {"виконати_розбір", "прочитати", "перевірити"}
РЕГУЛЯРКИ = {"search", "match", "fullmatch", "findall", "finditer"}
ТЕКСТОВІ = {"strip", "lstrip", "rstrip", "replace", "lower", "upper", "casefold", "removeprefix", "removesuffix"}
БУКВА = r"[\wА-Яа-яЇїІіЄєҐґʼ'$]"


# ── JS ───────────────────────────────────────────────────────────────────────
def функції_js(текст):
    """[(імʼя, рядок початку, тіло)] — функції верхнього рівня (рядок починається з `function` чи `async function`)."""
    рядки = текст.split("\n")
    почат = [(і, м.group(1)) for і, р in enumerate(рядки)
             for м in [re.match(r"(?:async\s+)?function\s+(%s+)" % БУКВА, р)] if м]
    вих = []
    for н, (і, ім) in enumerate(почат):
        кін = почат[н + 1][0] if н + 1 < len(почат) else len(рядки)
        вих.append((ім, і + 1, "\n".join(рядки[і:кін])))
    return вих


def без_коментарів_js(т):
    """Текст без коментарів `/* */` і `//` (рядки з лапками не розбираються — досить для пошуку викликів)."""
    т = re.sub(r"/\*.*?\*/", lambda м: "\n" * м.group(0).count("\n"), т, flags=re.S)
    return re.sub(r"(?m)(^|[^:\\'\"])//.*$", r"\1", т)


def аргументи_містП(т):
    """Текст аргументів кожного виклику, що несе вхід мосту (`містП(...)`, обгортки руки `відМоделі…(`,
    `зОбривом(`), — до парної дужки."""
    вих = []
    for м in re.finditer(r"(?:містП|відМоделі%s*|зОбривом)\(" % БУКВА, т):
        глиб, і = 1, м.end()
        while і < len(т) and глиб:
            глиб += {"(": 1, ")": -1}.get(т[і], 0)
            і += 1
        вих.append(т[м.end():і])
    return вих


МОДЕЛЬ_JS = r"(?:await\s+)?(?:блокиВТекст\(\s*)?(?:await\s+)?(?:%s+\.)?модель%s*\(" % (БУКВА, БУКВА)


def ключі_файлу(т):
    """Ключі обʼєктів, чиє значення — текст відповіді моделі: змінна з виклику `модель…(` (`модельП`, `модельП_блоки`,
    обгортки показу `модельПРуки`, `модельЗФото` — їх імʼя починається з «модель») чи сам такий виклик."""
    змінні = {м.group(1).split(".")[-1] for м in re.finditer(
        r"(%s+(?:\.%s+)?)\s*=\s*%s" % (БУКВА, БУКВА, МОДЕЛЬ_JS), т)}
    for м in re.finditer(r"(%s+(?:\.%s+)?)\s*=\s*(?:String\()?(%s+)\b" % (БУКВА, БУКВА, БУКВА), т):
        if м.group(2) in змінні:          # змінна зі змінної відповіді (`сира` → `запис.відповідь_сира`)
            змінні.add(м.group(1).split(".")[-1])
    вих = set()
    for арг in аргументи_містП(т):
        for м in re.finditer(r"(%s+)\s*:\s*(?:String\()?(?:%s+\.)?(%s+)\s*[,})\n]" % (БУКВА, БУКВА, БУКВА), арг):
            if м.group(2) in змінні:
                вих.add(м.group(1))
        вих |= set(re.findall(r"(%s+)\s*:\s*%s" % (БУКВА, МОДЕЛЬ_JS), арг))
    return вих


def виклики_js():
    """Кожен виклик моделі в показі → запис; і множина ключів, якими показ віддає мосту відповідь моделі."""
    вих, ключі = [], set()
    for ім_ф in sorted(os.listdir(ПОКАЗ)):
        if not ім_ф.endswith(".js"):
            continue
        with open(os.path.join(ПОКАЗ, ім_ф), encoding="utf-8") as ф:
            текст = ф.read()
        ключі |= ключі_файлу(без_коментарів_js(текст))
        for ім, рядок, тіло in функції_js(текст):
            чисте = без_коментарів_js(тіло)
            if ім in ("модельП", "модельП_блоки"):
                continue
            виклики = [м for м in re.finditer(r"(?<![\w`])модельП(?:_блоки)?\(", чисте)]
            if not виклики:
                continue
            свої = ключі_файлу(чисте)
            ендп = sorted(set(re.findall(r"містП\('([^']+)'", чисте)))
            у_циклі = bool(re.search(r"\bfor\s*\(", чисте[:виклики[-1].start()]))
            for м in виклики:
                вих.append(dict(файл="показ/" + ім_ф, рядок=рядок + чисте[:м.start()].count("\n"), функція=ім,
                                викликів_у_функції=len(виклики), у_циклі=у_циклі, ендпойнти=ендп,
                                ключі_відповіді=sorted(свої) if ендп else []))
    # ОБГОРТКА (функція з викликом моделі без ендпойнта: `викликОцінкиП`, `модельМовиП`) — ендпойнти й повтор
    # беруться з тих, хто її кличе: скільки разів кличуть і які ендпойнти кличуть ті самі функції
    тіла = []
    for ім_ф in sorted(os.listdir(ПОКАЗ)):
        if ім_ф.endswith(".js"):
            with open(os.path.join(ПОКАЗ, ім_ф), encoding="utf-8") as ф:
                тіла += [(ім, без_коментарів_js(т)) for ім, _, т in функції_js(ф.read())]
    for в in вих:
        if в["ендпойнти"]:
            continue
        хто = [(ім, т) for ім, т in тіла if ім != в["функція"]
               and re.search(r"(?<!%s)%s\(" % (БУКВА, re.escape(в["функція"])), т)]
        if хто:
            в["кличуть"] = sorted({ім for ім, _ in хто})
            в["викликів_у_функції"] = max(len(re.findall(r"(?<!%s)%s\(" % (БУКВА, re.escape(в["функція"])), т))
                                          for _, т in хто)
            в["ендпойнти"] = sorted({е for _, т in хто for е in re.findall(r"містП\('([^']+)'", т)})
    return вих, ключі


# ── PYTHON ───────────────────────────────────────────────────────────────────
class Модуль:
    def __init__(self, ім, дерево):
        self.ім, self.дерево = ім, дерево
        self.модулі, self.імена = {}, {}       # аліас → модуль; імʼя → (модуль, функція)
        self.функції = {}
        # скомпільовані зразки модуля: `ІМʼЯ = re.compile(...)` на верхньому рівні
        self.зразки = {ц.id for в in дерево.body if isinstance(в, ast.Assign) and isinstance(в.value, ast.Call)
                       and isinstance(в.value.func, ast.Attribute) and в.value.func.attr == "compile"
                       for ц in в.targets if isinstance(ц, ast.Name)}
        for в in ast.walk(дерево):
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.модулі[а.asname or а.name] = а.name
            elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
                for а in в.names:
                    self.імена[а.asname or а.name] = (в.module, а.name)
        for в in дерево.body:
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.функції[в.name] = в
            elif isinstance(в, ast.ClassDef):
                for м in в.body:
                    if isinstance(м, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.функції["%s.%s" % (в.name, м.name)] = м


def модулі_python():
    вих = {}
    for ім_ф in sorted(os.listdir(ДЖЕРЕЛА)):
        if not ім_ф.endswith(".py") or НЕ_ШЛЯХ.match(ім_ф):
            continue
        with open(os.path.join(ДЖЕРЕЛА, ім_ф), encoding="utf-8") as ф:
            try:
                вих[ім_ф[:-3]] = Модуль(ім_ф[:-3], ast.parse(ф.read()))
            except SyntaxError:
                continue
    return вих


def _параметри(ф):
    п = [а.arg for а in ф.args.posonlyargs + ф.args.args]
    return п[1:] if п and п[0] == "self" else п


class Аналіз:
    def __init__(self, модулі, ключі):
        self.м, self.ключі = модулі, ключі
        self.мітки = {}          # (модуль, функція) → {параметр: {(мітка, межа)}}
        self.повертає = {}       # (модуль, функція) → {(мітка, межа)}
        self.читачі = {}         # (модуль, функція, рядок, що) → {(мітка, межа)}
        self.моделі_py = []      # (модуль, функція, рядок): відповідь сервера моделі в Python

    def ціль(self, мод, виклик):
        """Функція джерел, яку кличе `виклик`, → (модуль, функція) або None."""
        ф = виклик.func
        if isinstance(ф, ast.Name):
            if ф.id in мод.функції:
                return (мод.ім, ф.id)
            if ф.id in мод.імена:
                м, ім = мод.імена[ф.id]
                if м in self.м and ім in self.м[м].функції:
                    return (м, ім)
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id in мод.модулі:
            м = мод.модулі[ф.value.id]
            if м in self.м and ф.attr in self.м[м].функції:
                return (м, ф.attr)
        return None

    def чий(self, мод, виклик):
        """Модуль бібліотеки, з якого кличуть (`json`, `re`, `протокол`), і імʼя функції."""
        ф = виклик.func
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name):
            return мод.модулі.get(ф.value.id, ф.value.id), ф.attr
        if isinstance(ф, ast.Name) and ф.id in мод.імена:
            return мод.імена[ф.id]
        return None, None

    def мітка_виразу(self, мод, вираз, змінні):
        """Мітки сирого тексту моделі, які несе `вираз` (порожньо — не сирий текст)."""
        if isinstance(вираз, ast.Name):
            return set(змінні.get(вираз.id, ()))
        if isinstance(вираз, ast.Subscript):
            к = вираз.slice
            if isinstance(к, ast.Constant) and к.value in self.ключі | {"choices"}:
                return {("поза", None)}
            return self.мітка_виразу(мод, вираз.value, змінні)
        if isinstance(вираз, (ast.Tuple, ast.List)):
            return set().union(set(), *(self.мітка_виразу(мод, з, змінні) for з in вираз.elts))
        if isinstance(вираз, ast.BoolOp):
            return set().union(*(self.мітка_виразу(мод, з, змінні) for з in вираз.values))
        if isinstance(вираз, ast.IfExp):
            return self.мітка_виразу(мод, вираз.body, змінні) | self.мітка_виразу(мод, вираз.orelse, змінні)
        if isinstance(вираз, ast.Call):
            ф = вираз.func
            if isinstance(ф, ast.Attribute) and ф.attr == "get" and вираз.args \
                    and isinstance(вираз.args[0], ast.Constant) and вираз.args[0].value in self.ключі | {"choices"}:
                return {("поза", None)}
            if isinstance(ф, ast.Attribute) and ф.attr == "get":      # конверт сервера: `.get("message")` над міченим
                return self.мітка_виразу(мод, ф.value, змінні)
            if isinstance(ф, ast.Name) and ф.id == "str" and вираз.args:
                return self.мітка_виразу(мод, вираз.args[0], змінні)
            if isinstance(ф, ast.Attribute) and ф.attr in ТЕКСТОВІ:
                return self.мітка_виразу(мод, ф.value, змінні)
            if isinstance(ф, ast.Attribute) and ф.attr == "group":
                return self.мітка_виразу(мод, ф.value, змінні)
            if isinstance(ф, ast.Attribute) and ф.attr in МЕТОДИ_РЕЄСТРУ:
                return set()
            ц = self.ціль(мод, вираз)
            if ц:
                return set(self.повертає.get(ц, ()))
            б, ім = self.чий(мод, вираз)
            if б == "re" and ім in РЕГУЛЯРКИ and len(вираз.args) > 1:
                return self.мітка_виразу(мод, вираз.args[1], змінні)
        return set()

    def пройти(self, мод, ім, ф):
        """Один прохід функції: мітки змінних, читачі формату, мітки параметрів функцій, які вона кличе."""
        змінні = {п: set(м) for п, м in self.мітки.get((мод.ім, ім), {}).items()}
        змінилось = False
        for _ in range(3):
            for в in ast.walk(ф):
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                    м = self.мітка_виразу(мод, в.value, змінні)
                    if not м:
                        continue
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    for ц in цілі:
                        for н in ast.walk(ц):
                            if isinstance(н, ast.Name):
                                змінні.setdefault(н.id, set()).update(
                                    {(л, межа or "%s.%s" % (мод.ім, ім)) for л, межа in м})
                elif isinstance(в, (ast.For, ast.comprehension)):
                    м = self.мітка_виразу(мод, в.iter, змінні)
                    if м:
                        for н in ast.walk(в.target):
                            if isinstance(н, ast.Name):
                                змінні.setdefault(н.id, set()).update(
                                    {(л, межа or "%s.%s" % (мод.ім, ім)) for л, межа in м})
        тут = "%s.%s" % (мод.ім, ім)
        повна = lambda м: {(л, межа or тут) for л, межа in м}
        for в in ast.walk(ф):
            if isinstance(в, ast.Return) and в.value is not None:
                м = повна(self.мітка_виразу(мод, в.value, змінні))
                if м - self.повертає.get((мод.ім, ім), set()):
                    self.повертає.setdefault((мод.ім, ім), set()).update(м)
                    змінилось = True
            if not isinstance(в, ast.Call):
                continue
            if isinstance(в.func, ast.Subscript) or "choices" in ast.dump(в.func):
                pass
            б, ч = self.чий(мод, в)
            арг0 = в.args[0] if в.args else None
            що = None
            if б == "протокол" and ч in ЧИТАЧІ_ПРОТОКОЛУ:
                що = "протокол." + ч
            elif б == "json" and ч == "loads":
                що = "json.loads"
            elif б == "re" and ч in РЕГУЛЯРКИ and len(в.args) > 1:
                арг0, що = в.args[1], "re." + ч
            elif isinstance(в.func, ast.Attribute) and в.func.attr in РЕГУЛЯРКИ \
                    and isinstance(в.func.value, ast.Name) and в.func.value.id in мод.зразки:
                що = "регулярка." + в.func.attr
            if що and арг0 is not None:
                м = повна(self.мітка_виразу(мод, арг0, змінні))
                if м:
                    к = (мод.ім, ім, в.lineno, що)
                    if м - self.читачі.get(к, set()):
                        self.читачі.setdefault(к, set()).update(м)
            if isinstance(в.func, ast.Attribute) and в.func.attr in МЕТОДИ_РЕЄСТРУ:
                continue
            ц = self.ціль(мод, в)
            if not ц or ц[0] == "протокол":      # читачі протоколу — самі читачі формату, вглиб не йдемо
                continue
            цф = self.м[ц[0]].функції[ц[1]]
            параметри = _параметри(цф)
            пари = list(zip(параметри, в.args)) + [(к.arg, к.value) for к in в.keywords if к.arg in параметри]
            for п, а in пари:
                м = повна(self.мітка_виразу(мод, а, змінні))
                if м - self.мітки.get(ц, {}).get(п, set()):
                    self.мітки.setdefault(ц, {}).setdefault(п, set()).update(м)
                    змінилось = True
        return змінилось

    def зареєстровані(self):
        """Функції, прив'язані до форми в реєстрі: `розбір=` / `сторож=` у `СхемаВідповіді(...)` і в `РОЗБІР`."""
        вих = set()
        for мод in self.м.values():
            for в in ast.walk(мод.дерево):
                if isinstance(в, ast.Call) and isinstance(в.func, (ast.Name, ast.Attribute)) \
                        and (getattr(в.func, "id", None) or getattr(в.func, "attr", None)) in ("СхемаВідповіді", "dict"):
                    for к in в.keywords:
                        if к.arg in ("розбір", "сторож"):
                            ц = self.ціль(мод, ast.Call(func=к.value, args=[], keywords=[]))
                            if ц:
                                вих.add(ц)
        if "схема_відповіді" in self.м and "СхемаВідповіді.прочитати" in self.м["схема_відповіді"].функції:
            вих.add(("схема_відповіді", "СхемаВідповіді.прочитати"))
        return вих

    def виконати(self):
        for ц in self.зареєстровані():
            п = _параметри(self.м[ц[0]].функції[ц[1]])
            if п:
                self.мітки.setdefault(ц, {})[п[0]] = {("реєстр", "%s.%s" % ц)}
        for мод in self.м.values():
            for ім, ф in мод.функції.items():
                if "choices" in {в.value for в in ast.walk(ф) if isinstance(в, ast.Constant)}:
                    self.моделі_py.append((мод.ім, ім, ф.lineno))
        for _ in range(12):
            if not any([self.пройти(мод, ім, ф) for мод in self.м.values() for ім, ф in мод.функції.items()]):
                break
        return self


def звіт(js, ан):
    поза = {}
    for (мод, ім, рядок, що), мітки in sorted(ан.читачі.items()):
        for л, межа in мітки:
            if л == "поза":
                поза.setdefault(межа, []).append("%s.py:%d %s (%s)" % (мод, рядок, що, ім))
    в_реєстрі = sorted({"%s.py:%d %s" % (мод, р, що) for (мод, _, р, що), м in ан.читачі.items()
                        if all(л == "реєстр" for л, _ in м)})
    return dict(
        js=js,
        python_виклики=["%s.py:%d (%s)" % (м, р, ф) for м, ф, р in sorted(ан.моделі_py)],
        межі_поза_реєстром={к: sorted(set(в)) for к, в in sorted(поза.items())},
        читачів_у_реєстрі=len(в_реєстрі),
        поза=len(поза),
    )


def main():
    js, ключі = виклики_js()
    ан = Аналіз(модулі_python(), ключі).виконати()
    з = звіт(js, ан)
    з["ключі_відповіді"] = sorted(ключі)
    if "--json" in sys.argv:
        print(json.dumps(з, ensure_ascii=False, indent=1))
        return
    print("## Виклики моделі в показі (%d)\n" % len(js))
    print("| місце | функція | викликів у функції | у циклі | ендпойнти | ключі відповіді |\n|---|---|---|---|---|---|")
    for в in js:
        print("| %s:%d | %s | %d | %s | %s | %s |" % (в["файл"], в["рядок"], в["функція"] + (
            " ← " + ", ".join(в["кличуть"]) if в.get("кличуть") else ""), в["викликів_у_функції"],
                                                     "так" if в["у_циклі"] else "—", ", ".join(в["ендпойнти"]) or "—",
                                                     ", ".join(в["ключі_відповіді"]) or "—"))
    print("\n## Виклики моделі в Python (%d)\n" % len(з["python_виклики"]))
    for р in з["python_виклики"]:
        print("- " + р)
    print("\nКлючі, якими показ віддає мосту відповідь моделі: %s" % ", ".join(з["ключі_відповіді"]))
    print("\n## Межі Python поза реєстром: %d (читачів формату в реєстрі: %d)\n" % (з["поза"], з["читачів_у_реєстрі"]))
    for межа, місця in з["межі_поза_реєстром"].items():
        print("- **%s** — %s" % (межа, "; ".join(місця)))


if __name__ == "__main__":
    main()
