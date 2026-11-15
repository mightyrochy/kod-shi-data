# -*- coding: utf-8 -*-
"""прилади/корінь_е3_сила_правила.py — прилад кореня Е3-сила-правила: місця за класом паспорта
`аудит/корені/Е3-сила-правила.md` (розділ «Клас місць», «Стан і що лишилось» і «Рішення менеджера 31.10»).

Клас — правило, а не перелік прикладів: місце — точка коду продукту, де сила знахідки правила на виході може бути не
тією, що дає єдиний шлях `реєстр_сила.зн` з реєстром модуля, у якому голосують лише константи, прочитані гілкою, що цю
знахідку емітує. Прилад не править коду й не бере місць руками: усе — з AST Python і тексту JS показу.

ОБСЯГ — код продукту: модулі `джерела/*.py`, які тягне статичне замикання імпортів (і в тілах функцій) від `bridge`
(вантаж артефакту, як `склад.модулі_системи`) і від `фід_каталог` (побудова каталогу, як
`таблиця_каталогу.модулі_побудови`), плюс `джерела/показ/*.js`. Проби, прилади, стенди, тести, лабораторія, жнива й
гейти аудиту в замикання не входять — вони не код продукту (паспорт, «Клас місць»).

ЄДИНИЙ ШЛЯХ. Конструктор — `реєстр_сила.зн`; обгортка — функція чи лямбда, що кличе конструктор (чи іншу обгортку),
передаючи ід правила своїм параметром (виводиться до нерухомої точки, не перелічується); `functools.partial` над
конструктором — теж обгортка. Емісія правила — виклик конструктора з ід правила (літерал; ім'я, якому функція
присвоює літерали чи перебирає їх циклом; ім'я модуля з літералом). Тіло `зн` і функції, які він кличе, — сам шлях.

ВАГА. Ключ `сила_нп` (вага знахідки; клас — рішення 01.11) лічиться нарівні з `сила` і `регістр` у п.1а–в: готова
знахідка з новою вагою (`dict(зн(…), сила_нп=…)`, `з["сила_нп"] = …`), запис правила повз конструктор з вагою. Єдиний шлях
ваги — тіло `зн` і ще `реєстр_сила.перезважити` та `обмежити_вагу` з їхніми викликами; вага, узята з іншого запису тим
самим ключем (`з.get("сила_нп")`), — копія, не місце.
Параметри механізму, що несуть число ваги (`ПАРАМЕТРИ_ВАГИ`): `частка` у `зн` (і обгортках над ним), `неперервна_сила`
і `перезважити`, `вага_від` у `перезважити`. Число без джерела в такому параметрі (літерал, вираз лише з літералів, гілка
`a if c else b` з літералом, ім'я, прив'язане лише до літерала, параметр із літералом за замовчуванням) — та сама ручна
вага, що `dict(зн(…), сила_нп=<літерал>)`: п.1б. Вираз із вимірів, константа реєстру з джерелом, шкала механізму
(`КАТ_У_НП[…]`) — не місце: ваги їм дає шкала й стеля конструктора.
ІНДЕКС `X[…]` у такому параметрі (наряд Е3-сила-правила-прилад-реєстр, вада 15686) — не місце, лише коли зводиться до:
константи реєстру (запис словника рівня модуля з тіром і значенням, як `константи`; прямо, через похідний словник
значень `C = {k: R[k]["val"] for k in R}` чи реекспорт) з полем провенансу (`ПОЛЯ_ДЖЕРЕЛА`, паспорт і #3921: «з `прав` і
приміткою»; рішення 15638 — `джерело`); шкали модуля механізму (`реєстр_сила`); виміру — словника, який дає параметр,
виклик чи інше обчислення. Індекс у словник-літерал (рівня модуля чи локальний), що не реєстр, із числовим літералом
на кінці ланцюга ключів, і константа реєстру без провенансу — число без джерела: п.1б.
ЧИСЛО ВСЕРЕДИНІ ВИРАЗУ (вада 15698): вираз із виміром, у якому стоїть число без джерела (`round(min(0.8, (розрив - 0.3)
/ 0.7 * 0.6 + 0.2), 2)`, `вимір / 40.0`, `п * ТАБЛ["а"]`; через ім'я — за присвоєннями, що доходять до вжитку), — теж
п.1б (`літерали_всередині`). Не числа ваги: 0 і 1 (межі частки, нейтральні елементи), запобіжник ділення (|x| < 1e-3),
`ndigits` у `round`, умова гілки, ключ індексу, аргументи виклику функції, що не перетворення числа.

ПУНКТИ КЛАСУ (кожен — механічне правило; рядок виводу `пN · файл:рядок · чому`):
  1  запис знахідки правила будується повз конструктор: (а) словник `{…}`/`dict(…)` з ключем `правило` (ід правила
     літералом чи виразом) і ключем `сила` чи `регістр`, що несе текст знахідки (`суть`, `чому` чи `заяви`) і
     потоком значення доходить до списку (append/extend/insert, літерал списку чи кортежу, генератор, `yield`) —
     прямо, через змінну чи через повернення функції (до нерухомої точки по викликах); (б) запис із розгортання
     знахідки (`dict(з, сила=…)`, `{**з, "регістр": …}`) з новою силою чи регістром; (в) присвоєння сили чи регістру
     в записі знахідки (`з["сила"] = …`, `з.update(регістр=…)`; запис, складений присвоєнням ключів з нуля, — за
     правилом (а)) — місце — перше таке присвоєння в функції для цієї змінної. Знахідка — змінна, яку функція читає
     чи пише за ключем `правило` або `регістр`, чи значення конструктора, чи запис (а)/(б). Сила чи регістр, узяті
     з іншого запису тим самим ключем (`з.get("сила")`), — копія (проєкція звіту), не місце. JS показу — літерал
     об'єкта з `правило:` і `сила:`/`регістр:`/`сила_нп:`, де сила не копія поля іншого об'єкта.
  2  константа реєстру (словник рівня модуля, чиї записи мають тір `t`/`тир` і значення `val`/`значення`; також
     `РЕЄСТР.update({…})`) голосує за правило полем `прав` (семантика `реєстр_константи.за_кого`: список — кожен,
     рядок — цілим; тір `визначення` не голосує), а жодна гілка, що його емітує, константи не читає: (мертва)
     рядка-ключа ніде в коді продукту, крім самого запису, нема; (читана лише іншим правилом — для правила, що
     виходить через конструктор, бо лише там голос діє) кожен читач — функція верхнього рівня, найближчі емітери над якою (зворотний граф посилань:
     виклики й імена) емітують інші правила; (читана не всіма гілками правила — рішення 15697) читає гілка правила,
     а інша гілка емісії через конструктор того самого правила чи правила з тією самою основою константи не читає:
     ні сама транзитивно вниз, ні як найближчий емітер над читачем, ні як функція, досяжна з читача. Читач, від якого шлях іде до даних без емітера (рівень модуля, JS, функція
     без викликачів), — на користь сумніву: не місце. Ід емітера — як у `реєстр_тіри.тір_правила` (ід чи його основа).
  3  гілка емісії правила (функція верхнього рівня, що містить емісію й транзитивно не читає ключа) порівнює
     (`< <= > >= == !=`) з числовим літералом, рівним `val` константи, що голосує за це правило й сама є місцем п.2
     (двійник: «стелю ставить те, якого рішення не читає»). Рівний літерал при константі, яку емісія правила читає, —
     збіг числа (лічба речей, множник): не місце, `--докладно` його друкує.
  4  запис реєстру констант без поля `прав` (чи з порожнім), рядок-ключ якого ніде в коді продукту (Python і JS),
     крім рядка самого запису, не стоїть.

НЕ МІСЦЯ (паспорт): знахідка через конструктор чи обгортку; словник, що не несе знахідки (без тексту, не доходить до
списку — запис виміру, палітри, сліду; ід не правила — `площа`, `сегментація`); копія сили іншого запису; константа,
яку читає гілка емісії. Тіло конструктора й функції, які він кличе, — єдиний шлях, не місце.

Вивід: рядок на місце, підсумок за пунктами, останній рядок `місць: <N>` (N — різних `файл:рядок`), код 0.
`--докладно` — ще кандидати, які прилад відкинув, з причиною. `--самоперевірка` — штучні випадки кожного пункту й
не-місць, код 1 при розбіжності. Запуск з кореня репозиторію (чи `--корінь <шлях>`):
python3 джерела/прилади/корінь_е3_сила_правила.py [--докладно] [--самоперевірка]
"""
import ast
import os
import re
import sys
import warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

# ── ід правила: той самий шаблон, що `ід_правил.ШАБЛОН` (копія, щоб прилад не залежав від модуля продукту) ──
ШАБЛОН = (r'\b([KRPE]-[A-ZА-Я0-9]{2,5}-(?:\d{2}[a-zа-я]?|CONF|JOIN|UA))'
          r'(?:-([TMLAN]))?\b')
ЦІЛИЙ = re.compile(r'^' + ШАБЛОН + r'$')
СИЛИ = ("hard", "strong", "default", "soft", "hint")
НЕСИЛИ = ("питання", "ok", "утримано")
ТЕКСТ = ("суть", "чому", "заяви")
КЛЮЧІ_СИЛИ = ("сила", "регістр", "сила_нп")
СТАРТИ = ("bridge", "фід_каталог")
КОНСТРУКТОР = ("реєстр_сила", "зн")
# Єдиний шлях ваги готової знахідки (`сила_нп`): `перезважити` і `обмежити_вагу` — ті самі правила шкали, що й в `зн`.
ШЛЯХ_ВАГИ = (("реєстр_сила", "перезважити"), ("реєстр_сила", "обмежити_вагу"))
# Параметри механізму, що несуть число ваги (з коду `реєстр_сила.py`, крок #3870): функція → параметри. Обгортки над
# `зн` передають `частка` іменем — їхні виклики лічаться за ключем, як і самого `зн`.
ПАРАМЕТРИ_ВАГИ = {("реєстр_сила", "зн"): ("частка",), ("реєстр_сила", "неперервна_сила"): ("частка",),
                  ("реєстр_сила", "перезважити"): ("частка", "вага_від")}
# Вбудовані перетворення числа: `float(0.95)`, `round(0.3, 2)` — той самий літерал.
_ЧИСЛОВІ = ("float", "int", "round", "min", "max", "abs")
# Поля провенансу запису реєстру констант: текст, що каже, звідки число (паспорт, «Клас місць», #3921 — «з `прав` і
# приміткою»; рішення диспетчера 15638 — поле `джерело`). Усі 148 записів реєстрів `main` a97b49dc мають одне з них.
ПОЛЯ_ДЖЕРЕЛА = ("джерело", "суть", "src", "родовід", "примітка")


def цілий(р):
    return isinstance(р, str) and bool(ЦІЛИЙ.match(р))


def основа(правило):
    """Як `реєстр_тіри.тір_правила`: відкинути останній сегмент, якщо він з самих літер."""
    ч = правило.rsplit("-", 1)
    return ч[0] if ч[-1].isalpha() else правило


# ───────────────────────────── обсяг ─────────────────────────────

def замикання(дж, старти=СТАРТИ):
    мод = {f[:-3] for f in os.listdir(дж) if f.endswith(".py")}
    треба, край = set(), {с for с in старти if с in мод}
    while край:
        м = край.pop()
        треба.add(м)
        дерево = ОБСЯГ.розібрати(open(os.path.join(дж, м + ".py"), encoding="utf-8").read(), "джерела/%s.py" % м)
        if дерево is None:
            continue
        for в in ast.walk(дерево):
            if isinstance(в, ast.Import):
                край |= {а.name.split(".")[0] for а in в.names} & мод - треба
            elif isinstance(в, ast.ImportFrom) and в.level == 0 and в.module:
                край |= {в.module.split(".")[0]} & мод - треба
    return sorted(треба)


class Модуль:
    def __init__(self, ім, шлях, джерело):
        self.ім, self.шлях, self.текст = ім, шлях, джерело
        self.дерево = ast.parse(джерело)
        self.батько = {}
        for в in ast.walk(self.дерево):
            for д in ast.iter_child_nodes(в):
                self.батько[д] = в
        self.аліаси = {}        # ім'я → модуль (import m as a)
        self.з_модуля = {}      # ім'я → (модуль, ім'я) (from m import f as g)
        self.функції = {}       # ім'я верхнього рівня → вузол (def / class / присвоєння лямбди чи partial)
        self.імена = {}         # ім'я рівня модуля → вираз значення (останнє присвоєння)
        for в in self.дерево.body:
            self._верх(в)
        for в in ast.walk(self.дерево):
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.аліаси.setdefault(а.asname or а.name.split(".")[0], а.name.split(".")[0])
            elif isinstance(в, ast.ImportFrom) and в.level == 0 and в.module:
                for а in в.names:
                    self.з_модуля.setdefault(а.asname or а.name, (в.module.split(".")[0], а.name))

    def _верх(self, в):
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self.функції[в.name] = в
        elif isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None:
            цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
            for ц in цілі:
                if isinstance(ц, ast.Name):
                    self.імена[ц.id] = в.value
                    if isinstance(в.value, (ast.Lambda, ast.Call)):
                        self.функції.setdefault(ц.id, в.value)
        elif isinstance(в, (ast.If, ast.Try)):
            for д in ast.iter_child_nodes(в):
                if isinstance(д, ast.stmt):
                    self._верх(д)

    def рядок(self, в):
        return "%s:%d" % (self.шлях, в.lineno)

    def верхній(self, в):
        """Вузол верхнього рівня модуля (def/class/присвоєння), що містить `в`."""
        while в in self.батько and not isinstance(self.батько[в], ast.Module):
            в = self.батько[в]
        return в

    def функція(self, в):
        """Найближча def/lambda, що містить `в` (None — рівень модуля)."""
        в = self.батько.get(в)
        while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            в = self.батько.get(в)
        return в


class Продукт:
    def __init__(self, корінь, модулі=None, js=None):
        self.корінь = корінь
        дж = os.path.join(корінь, "джерела")
        if модулі is None:
            модулі = {}
            for м in замикання(дж):
                ф = os.path.join(дж, м + ".py")
                модулі[м] = (os.path.relpath(ф, корінь), open(ф, encoding="utf-8").read())
        if js is None:
            т = os.path.join(дж, "показ")
            js = {os.path.relpath(os.path.join(т, ф), корінь): open(os.path.join(т, ф), encoding="utf-8").read()
                  for ф in sorted(os.listdir(т)) if ф.endswith(".js")} if os.path.isdir(т) else {}
        self.М = {}
        for м, (шлях, текст) in модулі.items():
            try:
                self.М[м] = Модуль(м, шлях, текст)
            except SyntaxError as е:
                ОБСЯГ.непрочитано(шлях, "SyntaxError: %s" % е)
        self.js = js
        self._визн = {}
        self._конструктори()

    # ── розв'язання імен ──
    def визначення(self, м, ім, глиб=0):
        """(модуль, ім'я) верхнього рівня, куди веде ім'я `ім` у модулі `м` (крізь реекспорт)."""
        if глиб > 8 or м not in self.М:
            return None
        к = (м, ім)
        if к in self._визн:
            return self._визн[к]
        мм = self.М[м]
        р = None
        if ім in мм.функції and not (isinstance(мм.функції[ім], ast.Call) and self._псевдонім(мм, мм.функції[ім])):
            р = (м, ім)
        elif ім in мм.імена and isinstance(мм.імена[ім], (ast.Name, ast.Attribute)):
            р = self.виклик_куди(м, мм.імена[ім], глиб + 1)
        elif ім in мм.з_модуля:
            мод, ім2 = мм.з_модуля[ім]
            р = self.визначення(мод, ім2, глиб + 1)
        if р is None and ім in мм.функції:
            р = (м, ім)
        self._визн[к] = р
        return р

    def _псевдонім(self, мм, в):
        return False

    def виклик_куди(self, м, ф, глиб=0):
        """(модуль, ім'я) для виразу функції виклику: `f`, `M.f`."""
        if isinstance(ф, ast.Name):
            return self.визначення(м, ф.id, глиб)
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name):
            мм = self.М.get(м)
            if мм is None:
                return None
            мод = мм.аліаси.get(ф.value.id)
            if мод is None and ф.value.id in мм.з_модуля:
                мод2, ім2 = мм.з_модуля[ф.value.id]
                мод = ім2 if ім2 in self.М else None
            if мод in self.М:
                return self.визначення(мод, ф.attr, глиб)
        return None

    # ── конструктор і обгортки ──
    def _параметри(self, ф):
        а = ф.args
        return [x.arg for x in а.posonlyargs + а.args + а.kwonlyargs] + \
               ([а.vararg.arg] if а.vararg else []) + ([а.kwarg.arg] if а.kwarg else [])

    def _ід_арг(self, виклик):
        """Вираз ід правила у виклику конструктора: перший позиційний чи `правило=`."""
        for к in виклик.keywords:
            if к.arg == "правило":
                return к.value
        if виклик.args:
            return виклик.args[0]
        return None

    def _конструктори(self):
        self.К = {КОНСТРУКТОР}
        if КОНСТРУКТОР[0] not in self.М:
            return
        while True:
            нові = set()
            for м, мм in self.М.items():
                for в in ast.walk(мм.дерево):
                    if not isinstance(в, ast.Call) or not self.конструктор(м, в.func):
                        continue
                    ф = мм.функція(в)
                    if ф is None:
                        continue
                    а = self._ід_арг(в)
                    пр = self._параметри(ф)
                    проходить = isinstance(а, ast.Name) and а.id in пр or isinstance(а, ast.Starred) and \
                        isinstance(а.value, ast.Name) and а.value.id in пр
                    if not проходить:
                        continue
                    ім = self._ім_функції(мм, ф)
                    if ім and (м, ім) not in self.К:
                        нові.add((м, ім))
                    # конструктор параметром: `f(…, _зн, …)` → параметр `_зн` функції `f` — конструктор
                for в in ast.walk(мм.дерево):
                    if not isinstance(в, ast.Call):
                        continue
                    for і, а in list(enumerate(в.args)) + [(к.arg, к.value) for к in в.keywords if к.arg]:
                        if isinstance(а, (ast.Name, ast.Attribute)) and self.конструктор(м, а):
                            ц = self.виклик_куди(м, в.func)
                            if not ц or ц[0] not in self.М:
                                continue
                            цф = self.М[ц[0]].функції.get(ц[1])
                            if not isinstance(цф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                continue
                            пр = [x.arg for x in цф.args.posonlyargs + цф.args.args]
                            ім_п = і if isinstance(і, str) else (пр[і] if і < len(пр) else None)
                            if ім_п and (ц[0], ім_п) not in self.К:
                                нові.add((ц[0], ім_п))
                # partial(конструктор, …)
                for ім, з in мм.імена.items():
                    if isinstance(з, ast.Call) and ast.unparse(з.func).split(".")[-1] == "partial" and з.args \
                            and self.конструктор(м, з.args[0]) and (м, ім) not in self.К:
                        нові.add((м, ім))
            if not нові:
                break
            self.К |= нові
            self._визн.clear()

    def _ім_функції(self, мм, ф):
        """Ім'я, під яким функцію/лямбду видно з викликів: def — її ім'я; лямбда — ім'я присвоєння."""
        if isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ф.name
        б = мм.батько.get(ф)
        if isinstance(б, ast.Assign) and isinstance(б.targets[0], ast.Name):
            return б.targets[0].id
        return None

    def конструктор(self, м, ф):
        к = self.виклик_куди(м, ф)
        if к in self.К:
            return True
        # локальне ім'я обгортки (вкладена def/лямбда в тій самій функції)
        if isinstance(ф, ast.Name) and (м, ф.id) in self.К:
            return True
        return False

    def тіло_конструктора(self):
        """Функції, які кличе `реєстр_сила.зн` (транзитивно), разом із ним: сам єдиний шлях."""
        if КОНСТРУКТОР[0] not in self.М:
            return set()
        return self.досяжні({КОНСТРУКТОР} | {к for к in ШЛЯХ_ВАГИ if к[1] in self.М[к[0]].функції},
                            крізь_конструктор=True)

    def посилання(self):
        """{(модуль, ім'я) верхнього вузла: {(модуль, ім'я) верхніх вузлів, на які він посилається}} — виклики й
        передача імені (зворотний виклик, таблиця обробників)."""
        if hasattr(self, "_пос"):
            return self._пос
        self._пос = {}
        for м, мм in self.М.items():
            for в in мм.дерево.body:
                for ім in _імена_верху(в):
                    out = self._пос.setdefault((м, ім), set())
                    for д in ast.walk(в):
                        if isinstance(д, ast.Name) and isinstance(д.ctx, ast.Load) or \
                                isinstance(д, ast.Attribute) and isinstance(д.value, ast.Name):
                            ц = self.виклик_куди(м, д)
                            if ц and ц != (м, ім):
                                out.add(ц)
        return self._пос

    def досяжні(self, старт, крізь_конструктор=False):
        """(модуль, ім'я) функцій верхнього рівня, досяжних викликами від `старт`."""
        бачені, край = set(), set(старт)
        while край:
            к = край.pop()
            if к in бачені:
                continue
            бачені.add(к)
            м, ім = к
            мм = self.М.get(м)
            if мм is None or ім not in мм.функції:
                continue
            for в in ast.walk(мм.функції[ім]):
                if isinstance(в, ast.Call):
                    if not крізь_конструктор and self.конструктор(м, в.func):
                        continue
                    ц = self.виклик_куди(м, в.func)
                    if ц and ц not in бачені:
                        край.add(ц)
        return бачені


# ───────────────────────────── допоміжне AST ─────────────────────────────

def _імена_верху(в):
    """Імена, під якими вузол рівня модуля видно ззовні (def/class — ім'я; присвоєння — цілі)."""
    if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [в.name]
    if isinstance(в, ast.Assign):
        return [ц.id for ц in в.targets if isinstance(ц, ast.Name)]
    if isinstance(в, ast.AnnAssign) and isinstance(в.target, ast.Name):
        return [в.target.id]
    if isinstance(в, (ast.If, ast.Try)):
        return [і for д in ast.iter_child_nodes(в) if isinstance(д, ast.stmt) for і in _імена_верху(д)]
    return []


def поля(в):
    """(явні ключі → вузол значення, бази розгортання) запису `{…}`/`dict(…)`; інакше None."""
    if isinstance(в, ast.Dict):
        явні, бази = {}, []
        for к, з in zip(в.keys, в.values):
            if к is None:
                бази.append(з)
            elif isinstance(к, ast.Constant) and isinstance(к.value, str):
                явні[к.value] = з
        return явні, бази
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
        явні = {к.arg: к.value for к in в.keywords if к.arg}
        бази = list(в.args) + [к.value for к in в.keywords if к.arg is None]
        return явні, бази
    return None


def копія(з, ключ):
    """`X["ключ"]`, `X.get("ключ"…)` — значення взяте з іншого запису тим самим ключем."""
    if isinstance(з, ast.Subscript) and isinstance(з.slice, ast.Constant) and з.slice.value == ключ:
        return True
    if isinstance(з, ast.Call) and isinstance(з.func, ast.Attribute) and з.func.attr == "get" and з.args \
            and isinstance(з.args[0], ast.Constant) and з.args[0].value == ключ:
        return True
    if isinstance(з, ast.BoolOp):
        return all(копія(х, ключ) or isinstance(х, ast.Constant) for х in з.values) and \
            any(копія(х, ключ) for х in з.values)
    return False


def літерали_імені(функція, ім):
    """Рядкові літерали, які функція присвоює імені `ім` чи перебирає в ньому циклом."""
    out = set()
    if функція is None:
        return out
    for в in ast.walk(функція):
        if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets):
            out |= {д.value for д in ast.walk(в.value) if isinstance(д, ast.Constant) and isinstance(д.value, str)}
        elif isinstance(в, (ast.For, ast.comprehension)) and isinstance(в.target, ast.Name) and в.target.id == ім:
            out |= {д.value for д in ast.walk(в.iter) if isinstance(д, ast.Constant) and isinstance(д.value, str)}
    return out


def ключі_доступу(функція, ім):
    """Ключі-рядки, якими функція читає чи пише змінну `ім` (`ім["k"]`, `ім.get("k")`, `ім.update(k=…)`)."""
    out = set()
    for в in ast.walk(функція):
        if isinstance(в, ast.Subscript) and isinstance(в.value, ast.Name) and в.value.id == ім \
                and isinstance(в.slice, ast.Constant) and isinstance(в.slice.value, str):
            out.add(в.slice.value)
        elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) \
                and в.func.value.id == ім:
            if в.func.attr in ("get", "setdefault", "pop") and в.args and isinstance(в.args[0], ast.Constant):
                out.add(в.args[0].value)
            elif в.func.attr == "update":
                out |= {к.arg for к in в.keywords if к.arg}
                for а in в.args:
                    if isinstance(а, ast.Dict):
                        out |= {к.value for к in а.keys if isinstance(к, ast.Constant)}
    return out


def рядки_ключів(вузол, без=()):
    """Рядкові літерали вузла, крім піддерев `без`."""
    out, стоп = set(), {id(б) for б in без}
    стек = [вузол]
    while стек:
        в = стек.pop()
        if id(в) in стоп:
            continue
        if isinstance(в, ast.Constant) and isinstance(в.value, str):
            out.add(в.value)
        стек.extend(ast.iter_child_nodes(в))
    return out


# ───────────────────────────── реєстри констант ─────────────────────────────

def константи(П):
    """[dict(мод, словник, ключ, рядок, місце, t, val, прав)] — записи словників рівня модуля з тіром і значенням."""
    out = []
    for м, мм in sorted(П.М.items()):
        for в in мм.дерево.body:
            ціль = в.targets[0] if isinstance(в, ast.Assign) else (в.target if isinstance(в, ast.AnnAssign) else None)
            словник = getattr(в, "value", None)
            if isinstance(в, ast.Expr) and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Attribute) \
                    and в.value.func.attr == "update" and isinstance(в.value.func.value, ast.Name) and в.value.args:
                ціль, словник = в.value.func.value, в.value.args[0]
            if not isinstance(ціль, ast.Name) or not isinstance(словник, ast.Dict):
                continue
            for к, з in zip(словник.keys, словник.values):
                п = поля(з)
                if not isinstance(к, ast.Constant) or not isinstance(к.value, str) or not п:
                    continue
                п = п[0]
                тір = п.get("t", п.get("тир"))
                if тір is None or not ({"val", "значення"} & set(п) or isinstance(тір, ast.Constant)
                                      and str(тір.value).startswith("T")):
                    continue
                val = п.get("val", п.get("значення"))
                прав = п.get("прав")
                if прав is None:
                    за = ()
                elif isinstance(прав, ast.Constant):
                    за = (прав.value,) if прав.value else ()
                elif isinstance(прав, (ast.List, ast.Tuple, ast.Set)):
                    за = tuple(е.value for е in прав.elts if isinstance(е, ast.Constant))
                else:
                    за = ()
                out.append(dict(мод=м, словник=ціль.id, ключ=к.value, рядок=к.lineno, місце=мм.рядок(к),
                                t=тір.value if isinstance(тір, ast.Constant) else None,
                                val=val.value if isinstance(val, ast.Constant) and isinstance(val.value, (int, float))
                                and not isinstance(val.value, bool) else None,
                                прав=за, вузол=з, мм=мм))
    return out


# ───────────────────────────── емісії ─────────────────────────────

def верх_ім(мм, в):
    """Ім'я верхнього вузла модуля, що містить `в` (None — вираз рівня модуля без імені)."""
    і = _імена_верху(мм.верхній(в))
    return і[0] if і else None


def емісії(П):
    """[(модуль, вузол виклику, {ід}, верхнє ім'я)] — виклики конструктора з ід правила (тіло обгортки, що
    передає свій параметр, — не емісія)."""
    out = []
    for м, мм in П.М.items():
        for в in ast.walk(мм.дерево):
            if not isinstance(в, ast.Call) or not П.конструктор(м, в.func):
                continue
            а = П._ід_арг(в)
            ф = мм.функція(в)
            if isinstance(а, ast.Starred):
                continue
            if ф is not None and isinstance(а, ast.Name) and а.id in П._параметри(ф) \
                    and (м, П._ім_функції(мм, ф)) in П.К:
                continue
            out.append((м, в, ід_виразу(П, м, мм, а, ф), верх_ім(мм, в)))
    return out


def ід_виразу(П, м, мм, а, ф):
    """Ід правил, які може нести вираз: літерал; ім'я з літералами присвоєння чи циклу; ім'я модуля."""
    if а is None:
        return set()
    if isinstance(а, ast.Constant):
        return {а.value} if цілий(а.value) else set()
    іди = {д.value for д in ast.walk(а) if isinstance(д, ast.Constant) and цілий(д.value)}
    if isinstance(а, ast.Name):
        іди |= {р for р in літерали_імені(ф, а.id) if цілий(р)}
        if not іди and а.id in мм.імена:
            іди |= {д.value for д in ast.walk(мм.імена[а.id]) if isinstance(д, ast.Constant) and цілий(д.value)}
    return іди


def _імена_в(в):
    return {д.id for д in ast.walk(в) if isinstance(д, ast.Name)}


# ───────────────────────────── п.1: записи знахідок повз конструктор ─────────────────────────────

class П1:
    def __init__(self, П):
        self.П = П
        self.шлях = П.тіло_конструктора()
        self.індекс = Індекс(П)
        self.місця, self.відкинуті = [], []
        self.повертають = set()       # (модуль, ім'я) функцій, що повертають запис знахідки (не в списку)
        self.обгортки = {}            # (модуль, ім'я) функції-словника → позиція параметра ід
        self.емісії_словником = []    # (модуль, верхнє ім'я, {ід})
        self._виклики = None

    # ── індекс викликів ──
    def виклики_функції(self, к):
        """Вузли викликів функції верхнього рівня `к`: [(модуль, Модуль, вузол)]."""
        if self._виклики is None:
            self._виклики = {}
            for м, мм in self.П.М.items():
                for в in ast.walk(мм.дерево):
                    if isinstance(в, ast.Call):
                        ц = self.П.виклик_куди(м, в.func)
                        if ц:
                            self._виклики.setdefault(ц, []).append((м, мм, в))
        return self._виклики.get(к, [])

    def _виклики_ф(self, м, мм, ф):
        """Виклики функції `ф` (верхньої — через індекс; вкладеної — за іменем у її верхньому вузлі)."""
        ім = self.П._ім_функції(мм, ф)
        if ім is None:
            return []
        if мм.верхній(ф) is ф or (isinstance(мм.батько.get(ф), ast.Assign) and
                                   isinstance(мм.батько.get(мм.батько.get(ф)), ast.Module)):
            return self.виклики_функції((м, ім))
        return [(м, мм, д) for д in ast.walk(мм.верхній(ф)) if isinstance(д, ast.Call)
                and isinstance(д.func, ast.Name) and д.func.id == ім]

    def у_шляху(self, м, мм, в):
        return (м, верх_ім(мм, в)) in self.шлях

    # ── чи значення — знахідка ──
    def знахідка_значення(self, м, мм, ф, в, бачені):
        if isinstance(в, ast.Call) and self.П.конструктор(м, в.func):
            return True
        if isinstance(в, ast.Call):
            ц = self.П.виклик_куди(м, в.func)
            if ц and self.повертає_знахідку(ц, бачені):
                return True
        if isinstance(в, ast.IfExp):
            return self.знахідка_значення(м, мм, ф, в.body, бачені) or \
                self.знахідка_значення(м, мм, ф, в.orelse, бачені)
        if isinstance(в, ast.BoolOp):
            return any(self.знахідка_значення(м, мм, ф, х, бачені) for х in в.values)
        if isinstance(в, ast.BinOp) and isinstance(в.op, ast.BitOr):  # знахідка | спільне
            return self.знахідка_значення(м, мм, ф, в.left, бачені) or \
                self.знахідка_значення(м, мм, ф, в.right, бачені)
        п = поля(в)
        if п is not None:
            return "правило" in п[0] or any(self.знахідка_значення(м, мм, ф, б, бачені) for б in п[1])
        if isinstance(в, ast.Name):
            return self.знахідка_змінна(м, мм, ф, в.id, бачені)
        return False

    def повертає_знахідку(self, к, бачені):
        """Функція продукту повертає знахідку хоч одним `return` (до нерухомої точки)."""
        if ("ф", к) in бачені or к[0] not in self.П.М:
            return False
        бачені.add(("ф", к))
        мм = self.П.М[к[0]]
        ф = мм.функції.get(к[1])
        if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        return any(isinstance(в, ast.Return) and в.value is not None and мм.функція(в) is ф and
                   self.знахідка_значення(к[0], мм, ф, в.value, бачені) for в in ast.walk(ф))

    def знахідка_змінна(self, м, мм, ф, ім, бачені=None):
        """Змінна — знахідка: функція читає чи пише її ключем `правило` чи `регістр`; присвоєна зі значення-
        знахідки; параметр, куди виклики передають знахідку."""
        бачені = set() if бачені is None else бачені
        if ф is None or (id(ф), ім) in бачені or len(бачені) > 60:
            return False
        бачені.add((id(ф), ім))
        if {"правило", "регістр"} & ключі_доступу(ф, ім):
            return True
        for в in ast.walk(ф):
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets):
                if self.знахідка_значення(м, мм, ф, в.value, бачені):
                    return True
            elif isinstance(в, (ast.For, ast.comprehension)) and isinstance(в.target, ast.Name) and \
                    в.target.id == ім and isinstance(в.iter, ast.List):
                if any(self.знахідка_значення(м, мм, ф, е, бачені) for е in в.iter.elts):
                    return True
        пр = [x.arg for x in ф.args.posonlyargs + ф.args.args] if not isinstance(ф, ast.Lambda) else []
        if ім in пр:
            поз = пр.index(ім)
            for м2, мм2, виклик in self._виклики_ф(м, мм, ф):
                а = виклик.args[поз] if поз < len(виклик.args) and not any(
                    isinstance(х, ast.Starred) for х in виклик.args[:поз + 1]) else \
                    next((к.value for к in виклик.keywords if к.arg == ім), None)
                if а is not None and self.знахідка_значення(м2, мм2, мм2.функція(виклик), а, бачені):
                    return True
        return False

    # ── потік до списку ──
    def до_списку(self, м, мм, в, глиб=0):
        """Чи значення вузла `в` доходить до списку. 'так' | 'ні' | 'повертає'."""
        if глиб > 12:
            return "ні"
        б = мм.батько.get(в)
        if isinstance(б, (ast.IfExp, ast.BoolOp, ast.Starred)):
            return self.до_списку(м, мм, б, глиб + 1)
        if isinstance(б, ast.keyword) and б.arg is None:
            б2 = мм.батько.get(б)
            return self.до_списку(м, мм, б2, глиб + 1) if поля(б2) is not None else "ні"
        if isinstance(б, ast.Dict) and any(к is None and з is в for к, з in zip(б.keys, б.values)):
            return self.до_списку(м, мм, б, глиб + 1)
        if isinstance(б, (ast.List, ast.Tuple, ast.Set, ast.ListComp, ast.SetComp, ast.GeneratorExp,
                          ast.Yield, ast.YieldFrom)):
            return "так"
        if isinstance(б, ast.Call):
            if isinstance(б.func, ast.Attribute) and б.func.attr in ("append", "insert", "extend", "appendleft"):
                return "так" if в in б.args else "ні"
            if isinstance(б.func, ast.Name) and б.func.id == "dict" and в in б.args:
                return self.до_списку(м, мм, б, глиб + 1)
            if в in б.args and self._повертає_параметр(м, б, б.args.index(в)):
                return self.до_списку(м, мм, б, глиб + 1)
            return "ні"
        if isinstance(б, ast.Return):
            return "повертає"
        if isinstance(б, (ast.Assign, ast.AnnAssign)) and б.value is в:
            цілі = б.targets if isinstance(б, ast.Assign) else [б.target]
            ф = мм.функція(в)
            рез = "ні"
            for ц in цілі:
                if isinstance(ц, ast.Name):
                    р = self._змінна_до_списку(м, мм, ф, ц.id, глиб)
                    if р == "так":
                        return "так"
                    if р == "повертає":
                        рез = р
            return рез
        if isinstance(б, ast.AugAssign) and б.value is в:
            return "так"
        return "ні"

    def _повертає_параметр(self, м, виклик, поз):
        """Функція продукту повертає свій параметр на позиції `поз` (як є чи розгорнутим у запис)."""
        ц = self.П.виклик_куди(м, виклик.func)
        if not ц or ц[0] not in self.П.М:
            return False
        ф = self.П.М[ц[0]].функції.get(ц[1])
        if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        пр = [x.arg for x in ф.args.posonlyargs + ф.args.args]
        if поз >= len(пр):
            return False
        ім = пр[поз]
        for в in ast.walk(ф):
            if isinstance(в, ast.Return) and в.value is not None:
                з = в.value
                if isinstance(з, ast.Name) and з.id == ім:
                    return True
                п = поля(з)
                if п and any(isinstance(х, ast.Name) and х.id == ім for х in п[1]):
                    return True
        return False

    def _змінна_до_списку(self, м, мм, ф, ім, глиб):
        обл = ф if ф is not None else мм.дерево
        рез = "ні"
        for в in ast.walk(обл):
            if isinstance(в, ast.Name) and в.id == ім and isinstance(в.ctx, ast.Load):
                р = self.до_списку(м, мм, в, глиб + 1)
                if р == "так":
                    return "так"
                if р == "повертає":
                    рез = р
        return рез

    def потік(self, м, мм, в):
        """True, якщо значення доходить до списку прямо чи через повернення функцій (до нерухомої точки)."""
        бачені = set()
        черга = [(м, мм, в)]
        while черга:
            м1, мм1, в1 = черга.pop()
            р = self.до_списку(м1, мм1, в1)
            if р == "так":
                return True
            if р == "повертає":
                ф = мм1.функція(в1)
                if ф is None:
                    continue
                к = (м1, id(ф))
                if к in бачені:
                    continue
                бачені.add(к)
                ім = self.П._ім_функції(мм1, ф)
                if ім:
                    self.повертають.add((м1, ім))
                черга.extend(self._виклики_ф(м1, мм1, ф))
        return False

    # ── прохід ──
    def прогін(self):
        for м, мм in sorted(self.П.М.items()):
            мутовані = set()
            for в in ast.walk(мм.дерево):
                п = поля(в)
                if п is not None:
                    self._запис(м, мм, в, п)
                elif isinstance(в, ast.Assign):
                    self._присвоєння(м, мм, в, мутовані)
                elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "update" \
                        and isinstance(в.func.value, ast.Name):
                    self._оновлення(м, мм, в, мутовані)
                if isinstance(в, ast.Call):
                    self._параметр_ваги(м, мм, в)
        self._емісії_обгорток()
        return self

    def _ключі_похідних(self, ф, ім):
        """Ключі записів, що розгортають змінну `ім` (`dict(ім, суть=…)`), і ключі доступу до неї."""
        out = set(ключі_доступу(ф, ім)) if ф is not None else set()
        for в in ast.walk(ф) if ф is not None else ():
            п = поля(в)
            if п and any(isinstance(б, ast.Name) and б.id == ім for б in п[1]):
                out |= set(п[0])
        return out

    def _запис(self, м, мм, в, п):
        явні, бази = п
        нові = {к: з for к, з in явні.items() if к in КЛЮЧІ_СИЛИ and not копія(з, к)}
        if not нові or self.у_шляху(м, мм, в):
            return
        ф = мм.функція(в)
        if "правило" in явні:
            пр = явні["правило"]
            if isinstance(пр, ast.Constant):
                if not цілий(пр.value):
                    self.відкинуті.append((мм.рядок(в), "ід не правила: %r" % (пр.value,)))
                    return
            джерела = self._джерела_правила(пр)
            if джерела and all(self._похідне(ф, з, джерела) for з in нові.values()):
                return                          # проєкція знахідки: сила й регістр — з того самого запису
            ключі = set(явні)
            for б in бази:
                if isinstance(б, ast.Name):
                    ключі |= self._ключі_похідних(ф, б.id)
            б_ = мм.батько.get(в)
            if isinstance(б_, ast.Assign):
                for ц in б_.targets:
                    if isinstance(ц, ast.Name):
                        ключі |= self._ключі_похідних(ф, ц.id)
            if not (ключі & set(ТЕКСТ) or any(isinstance(б, ast.Call) and self.П.конструктор(м, б.func)
                                              for б in бази)):
                self.відкинуті.append((мм.рядок(в), "запис без тексту знахідки (%s)" % ", ".join(sorted(явні))[:80]))
                return
            if not self.потік(м, мм, в):
                self.відкинуті.append((мм.рядок(в), "запис не доходить до списку знахідок"))
                return
            self.місця.append((мм.рядок(в), "п1а", "словник %s %s повз конструктор" % (
                _ід_опис(пр), ", ".join("%s=%s" % (к, ast.unparse(з)[:30]) for к, з in нові.items()))))
            іди = ід_виразу(self.П, м, мм, пр, ф)
            if іди:
                self.емісії_словником.append((м, верх_ім(мм, в), іди))
            if ф is not None and isinstance(пр, ast.Name) and not isinstance(ф, ast.Lambda):
                пп = [x.arg for x in ф.args.posonlyargs + ф.args.args]
                if пр.id in пп:
                    self.обгортки[(м, self.П._ім_функції(мм, ф))] = (пп.index(пр.id), ф, мм)
            return
        if бази and any(self.знахідка_значення(м, мм, ф, б, set()) for б in бази):
            self.місця.append((мм.рядок(в), "п1б", "розгортання знахідки з новим %s" % ", ".join(
                "%s=%s" % (к, ast.unparse(з)[:30]) for к, з in нові.items())))


    # ── число ваги параметром механізму (`частка=`, `вага_від=`) ──
    def _параметри_виклику(self, м, в):
        """{параметр ваги: вираз} у виклику механізму (`зн`, обгортки, `неперервна_сила`, `перезважити`,
        `partial` над ними); позиційні — лише при прямому виклику функції реєстру (відоме оголошення)."""
        ф, арги, кл = в.func, list(в.args), в.keywords
        if ast.unparse(ф).split(".")[-1] == "partial" and арги:
            ф, арги = арги[0], арги[1:]
        ц = self.П.виклик_куди(м, ф)
        if ц in ПАРАМЕТРИ_ВАГИ:
            імена = ПАРАМЕТРИ_ВАГИ[ц]
        elif self.П.конструктор(м, ф):
            імена = ПАРАМЕТРИ_ВАГИ[КОНСТРУКТОР]
        else:
            return {}
        out = {к.arg: к.value for к in кл if к.arg in імена}
        оголошення = self.П.М[ц[0]].функції.get(ц[1]) if ц in ПАРАМЕТРИ_ВАГИ and ц[0] in self.П.М else None
        if isinstance(оголошення, (ast.FunctionDef, ast.AsyncFunctionDef)):
            пп = [x.arg for x in оголошення.args.posonlyargs + оголошення.args.args]
            for і, а in enumerate(арги):
                if isinstance(а, ast.Starred):
                    break
                if і < len(пп) and пп[і] in імена:
                    out.setdefault(пп[і], а)
        return out

    def _параметр_ваги(self, м, мм, в):
        if self.у_шляху(м, мм, в):
            return
        ф = мм.функція(в)
        інд = lambda с: self.індекс.без_джерела(м, ф, с)
        for ім, з in sorted(self._параметри_виклику(м, в).items()):
            чому = літерал_без_джерела(мм, ф, з, інд=інд)
            if not чому:
                лл = літерали_всередині(мм, ф, з, інд)
                if лл:
                    чому = "числа без джерела у виразі: " + ", ".join(лл)
            if чому:
                self.місця.append((мм.рядок(в), "п1б", "вага параметром %s=%s — %s" % (
                    ім, ast.unparse(з)[:30], чому)))
            elif not (isinstance(з, ast.Constant) and з.value is None):
                self.відкинуті.append((мм.рядок(в), "%s=%s: число з виміру, реєстру з джерелом чи шкали механізму" % (
                    ім, ast.unparse(з)[:30])))

    @staticmethod
    def _джерела_правила(пр):
        """Змінні, з яких `правило` скопійовано (`з["правило"]`, `з.get("правило")`, `str(з["правило"])`)."""
        out = set()
        for д in ast.walk(пр):
            if копія(д, "правило"):
                x = д.value if isinstance(д, ast.Subscript) else д.func.value
                if isinstance(x, ast.Name):
                    out.add(x.id)
        return out

    def _похідне(self, ф, з, джерела):
        """Значення сили чи регістру виведене з того самого запису (містить його ім'я прямо чи через локальне
        присвоєння)."""
        імена = _імена_в(з)
        if імена & джерела:
            return True
        if ф is None:
            return False
        for в in ast.walk(ф):
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id in імена for ц in в.targets):
                if _імена_в(в.value) & джерела:
                    return True
        return False

    def _емісії_обгорток(self):
        """Виклики функцій-словників (параметр іде в `правило` запису п.1) — емісії правила словником."""
        for (м, ім), (поз, ф, мм) in self.обгортки.items():
            for м2, мм2, виклик in self._виклики_ф(м, мм, ф):
                а = виклик.args[поз] if поз < len(виклик.args) else \
                    next((к.value for к in виклик.keywords if к.arg == ф.args.args[поз].arg), None) \
                    if поз < len(ф.args.args) else None
                іди = ід_виразу(self.П, м2, мм2, а, мм2.функція(виклик))
                if іди:
                    self.емісії_словником.append((м2, верх_ім(мм2, виклик), іди))

    def _присвоєння(self, м, мм, в, мутовані):
        for ц in в.targets:
            if not (isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and isinstance(ц.slice, ast.Constant)
                    and ц.slice.value in КЛЮЧІ_СИЛИ):
                continue
            if копія(в.value, ц.slice.value):
                continue
            self._мутація(м, мм, в, ц.value.id, ц.slice.value, мутовані)

    def _оновлення(self, м, мм, в, мутовані):
        кл = {к.arg: к.value for к in в.keywords if к.arg}
        for а in в.args:
            п = поля(а)
            if п:
                кл.update(п[0])
        кл = {к: з for к, з in кл.items() if к in КЛЮЧІ_СИЛИ and not копія(з, к)}
        if кл:
            self._мутація(м, мм, в, в.func.value.id, ",".join(sorted(кл)), мутовані)

    def _мутація(self, м, мм, в, ім, ключ, мутовані):
        if self.у_шляху(м, мм, в):
            return
        ф = мм.функція(в)
        if ф is None or isinstance(ф, ast.Lambda):
            return
        ключ_м = (id(ф), ім)
        if ключ_м in мутовані:
            return
        доступ = ключі_доступу(ф, ім)
        if self._з_нуля(ф, ім):
            # запис, складений присвоєнням ключів: правило (а) — ід, текст і потік до списку
            if "правило" not in доступ:
                return
            мутовані.add(ключ_м)
            пр = self._присвоєне(ф, ім, "правило")
            if isinstance(пр, ast.Constant) and not цілий(пр.value):
                self.відкинуті.append((мм.рядок(в), "ід не правила: %r" % (пр.value,)))
                return
            if not (set(ТЕКСТ) & self._ключі_похідних(ф, ім)):
                self.відкинуті.append((мм.рядок(в), "запис з нуля без тексту знахідки"))
                return
            присв = [д for д in ast.walk(ф) if isinstance(д, ast.Assign) and any(
                isinstance(ц, ast.Name) and ц.id == ім for ц in д.targets)]
            if not any(self.потік(м, мм, д.value) for д in присв):
                self.відкинуті.append((мм.рядок(в), "запис з нуля не доходить до списку знахідок"))
                return
            self.місця.append((мм.рядок(в), "п1а", "запис знахідки складено присвоєнням ключів (%s)" % ключ))
            if пр is not None:
                іди = ід_виразу(self.П, м, мм, пр, ф)
                if іди:
                    self.емісії_словником.append((м, верх_ім(мм, в), іди))
            return
        if not self.знахідка_змінна(м, мм, ф, ім):
            return
        мутовані.add(ключ_м)
        self.місця.append((мм.рядок(в), "п1в", "знахідці «%s» присвоєно %s повз конструктор" % (ім, ключ)))

    @staticmethod
    def _з_нуля(ф, ім):
        """Змінна присвоєна лише словниками без `правило` і без розгортання (`з = {}`)."""
        присв = [в for в in ast.walk(ф) if isinstance(в, ast.Assign) and any(
            isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets)]
        for в in присв:
            п = поля(в.value)
            if п is None or п[1] or "правило" in п[0]:
                return False
        return bool(присв)

    @staticmethod
    def _присвоєне(ф, ім, ключ):
        for в in ast.walk(ф):
            if isinstance(в, ast.Assign):
                for ц in в.targets:
                    if isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and ц.value.id == ім \
                            and isinstance(ц.slice, ast.Constant) and ц.slice.value == ключ:
                        return в.value
        return None


ЛІТЕРАЛ = "літерал без джерела"


def _без_джерела(в, інд=None):
    """Причина, чому вираз — число без джерела (літерали, арифметика над ними, `float(…)`/`round(…)` тощо, індекс
    `X[…]`, який `інд` визнав числом без джерела), чи None."""
    if isinstance(в, ast.Constant):
        return ЛІТЕРАЛ if isinstance(в.value, (int, float)) and not isinstance(в.value, bool) else None
    if isinstance(в, ast.Subscript):
        return інд(в) if інд else None
    if isinstance(в, ast.UnaryOp):
        return _без_джерела(в.operand, інд)
    чч = None
    if isinstance(в, ast.BinOp):
        чч = [_без_джерела(в.left, інд), _без_джерела(в.right, інд)]
    elif isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in _ЧИСЛОВІ and в.args \
            and not в.keywords:
        чч = [_без_джерела(а, інд) for а in в.args]
    if not чч or not all(чч):
        return None
    return next((ч for ч in чч if ч != ЛІТЕРАЛ), ЛІТЕРАЛ)


def _лише_літерали(в):
    """Вираз — число без джерела з самих літералів."""
    return _без_джерела(в) is not None


def літерал_без_джерела(мм, ф, в, глиб=0, інд=None):
    """Причина, чому вираз параметра ваги — число без джерела, чи None. Ім'я — за його присвоєннями в функції
    (усі — числа без джерела) чи на рівні модуля; параметр функції — за літералом за замовчуванням; індекс — за `інд`."""
    if глиб > 4 or в is None:
        return None
    ч = _без_джерела(в, інд)
    if ч:
        return ч
    if isinstance(в, ast.IfExp):
        for г in (в.body, в.orelse):
            if літерал_без_джерела(мм, ф, г, глиб + 1, інд):
                return "гілка з літералом без джерела"
        return None
    if not isinstance(в, ast.Name):
        return None
    if ф is not None and not isinstance(ф, ast.Lambda):
        а = ф.args
        пп = а.posonlyargs + а.args
        типові = dict(zip([x.arg for x in пп][len(пп) - len(а.defaults):], а.defaults))
        типові.update({x.arg: д for x, д in zip(а.kwonlyargs, а.kw_defaults) if д is not None})
        if в.id in [x.arg for x in пп + а.kwonlyargs]:
            д = типові.get(в.id)
            return "параметр «%s» з літералом за замовчуванням" % в.id if д is not None and _лише_літерали(д) \
                else None
        присв = _локальні(ф, в.id)
        if присв:
            чч = [_без_джерела(з, інд) for з in присв]
            return "ім'я «%s», прив'язане лише до числа без джерела (%s)" % (в.id, чч[0]) if all(чч) else None
    з = мм.імена.get(в.id)
    ч = _без_джерела(з, інд) if з is not None else None
    if ч:
        return "ім'я модуля «%s», прив'язане лише до числа без джерела (%s)" % (в.id, ч)
    return None


def _нейтральне(в):
    """Число, що не несе ваги: межі частки й нейтральні елементи (0, 1) і запобіжник ділення (|x| < 1e-3)."""
    return в in (0, 1) or abs(в) < 1e-3


def літерали_всередині(мм, ф, в, інд=None, глиб=0, бачені=None):
    """Числа без джерела всередині виразу параметра ваги (вада 15698): літерал, індекс, який `інд` визнав числом без
    джерела, ім'я модуля чи локальне ім'я з таким числом у присвоєнні, параметр із ним за замовчуванням. Не числа ваги:
    0 і 1 та запобіжник ділення (`_нейтральне`), `ndigits` у `round`, умова гілки, ключ індексу, аргументи виклику
    функції, що не перетворення числа (`_ЧИСЛОВІ`) — її результат вимір."""
    бачені = set() if бачені is None else бачені
    if в is None or глиб > 4:
        return []
    if isinstance(в, ast.Constant):
        ок = isinstance(в.value, (int, float)) and not isinstance(в.value, bool) and not _нейтральне(в.value)
        return [repr(в.value)] if ок else []
    if isinstance(в, ast.Subscript):
        ч = інд(в) if інд else None
        return [ast.unparse(в)[:30]] if ч else []
    if isinstance(в, ast.UnaryOp):
        return літерали_всередині(мм, ф, в.operand, інд, глиб, бачені)
    if isinstance(в, ast.BinOp):
        return літерали_всередині(мм, ф, в.left, інд, глиб, бачені) + \
            літерали_всередині(мм, ф, в.right, інд, глиб, бачені)
    if isinstance(в, ast.IfExp):
        return літерали_всередині(мм, ф, в.body, інд, глиб, бачені) + \
            літерали_всередині(мм, ф, в.orelse, інд, глиб, бачені)
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in _ЧИСЛОВІ and not в.keywords:
        арги = в.args[:1] if в.func.id == "round" else в.args
        return [л for а in арги for л in літерали_всередині(мм, ф, а, інд, глиб, бачені)]
    if not isinstance(в, ast.Name) or в.id in бачені:
        return []
    бачені.add(в.id)
    if ф is not None and not isinstance(ф, ast.Lambda):
        а = ф.args
        пп = а.posonlyargs + а.args
        if в.id in [x.arg for x in пп + а.kwonlyargs] + ([а.vararg.arg] if а.vararg else []) + \
                ([а.kwarg.arg] if а.kwarg else []):
            типові = dict(zip([x.arg for x in пп][len(пп) - len(а.defaults):], а.defaults))
            типові.update({x.arg: д for x, д in zip(а.kwonlyargs, а.kw_defaults) if д is not None})
            д = типові.get(в.id)
            return ["%s=%s" % (в.id, л) for л in літерали_всередині(мм, None, д, інд, глиб + 1, бачені)] \
                if д is not None else []
        присв = _досяжні_присвоєння(мм, ф, в)
        if присв:
            return ["%s←%s" % (в.id, л) for з in присв
                    for л in літерали_всередині(мм, ф, з.value, інд, глиб + 1, бачені)]
    з = мм.імена.get(в.id)
    if з is not None:
        return ["%s←%s" % (в.id, л) for л in літерали_всередині(мм, None, з, інд, глиб + 1, бачені)]
    return []


def _досяжні_присвоєння(мм, ф, в):
    """Присвоєння імені `в` у функції `ф`, що можуть дійти до вжитку `в`: стоять раніше й не перекриті пізнішим
    присвоєнням, яке домінує над вжитком (у тому самому списку інструкцій, що й предок вжитку). Гілки, цикли й ранні
    виходи — наближено: з різних гілок `if` доходять обидва; присвоєння після вжитку в циклі не береться."""
    предки = {}
    x = в
    while x is not None and x is not ф:
        б = мм.батько.get(x)
        if б is not None:
            предки[б] = x
        x = б

    def домінує(п):
        б = мм.батько.get(п)
        if б not in предки:
            return False
        дитина = предки[б]
        for поле in ("body", "orelse", "finalbody", "handlers"):
            сп = getattr(б, поле, None)
            if isinstance(сп, list) and п in сп and дитина in сп:
                return True
        return False
    вжиток = (в.lineno, в.col_offset)
    усі = sorted([д for д in ast.walk(ф) if isinstance(д, (ast.Assign, ast.AnnAssign)) and д.value is not None
                  and (д.lineno, д.col_offset) < вжиток and any(
                      isinstance(ц, ast.Name) and ц.id == в.id
                      for ц in (д.targets if isinstance(д, ast.Assign) else [д.target]))],
                 key=lambda д: (д.lineno, д.col_offset))
    перекрито = None
    for і, д in enumerate(усі):
        if домінує(д):
            перекрито = і
    return усі[перекрито:] if перекрито is not None else усі


def _локальні(ф, ім):
    """Значення присвоєнь імені `ім` у функції `ф`."""
    return [д.value for д in ast.walk(ф) if isinstance(д, (ast.Assign, ast.AnnAssign)) and д.value is not None
            and any(isinstance(ц, ast.Name) and ц.id == ім
                    for ц in (д.targets if isinstance(д, ast.Assign) else [д.target]))]


class Індекс:
    """Звідки число індексу `X[…]` у параметрі ваги: константа реєстру з джерелом, шкала механізму, вимір — чи число
    без джерела (словник-літерал, константа реєстру без провенансу)."""

    def __init__(self, П):
        self.П = П
        self.реєстри = {}      # (модуль, словник) → {ключ: запис `константи`}
        for к in константи(П):
            self.реєстри.setdefault((к["мод"], к["словник"]), {})[к["ключ"]] = к

    def значення(self, м, ім, глиб=0):
        """(модуль, ім'я, вираз) рівня модуля, куди веде ім'я (крізь `from … import` і присвоєння імені)."""
        if глиб > 8 or м not in self.П.М:
            return None
        мм = self.П.М[м]
        if ім in мм.імена:
            з = мм.імена[ім]
            if isinstance(з, (ast.Name, ast.Attribute)):
                return self.вираз(м, з, глиб + 1) or (м, ім, з)
            return м, ім, з
        if ім in мм.з_модуля:
            мод, ім2 = мм.з_модуля[ім]
            return self.значення(мод, ім2, глиб + 1)
        return None

    def вираз(self, м, в, глиб=0):
        """`значення` для `X` чи `мод.X`."""
        if isinstance(в, ast.Name):
            return self.значення(м, в.id, глиб)
        if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name) and м in self.П.М:
            мм = self.П.М[м]
            мод = мм.аліаси.get(в.value.id)
            if мод is None and в.value.id in мм.з_модуля:
                мод = мм.з_модуля[в.value.id][1]
            if мод in self.П.М:
                return self.значення(мод, в.attr, глиб)
        return None

    @staticmethod
    def _ланцюг(в):
        ключі = []
        while isinstance(в, ast.Subscript):
            ключі.insert(0, в.slice)
            в = в.value
        return в, ключі

    def без_джерела(self, м, ф, в):
        база, ключі = self._ланцюг(в)
        return self._база(м, ф, база, ключі, 0)

    def _база(self, м, ф, база, ключі, глиб):
        if глиб > 6:
            return None
        if isinstance(база, ast.Name) and ф is not None and not isinstance(ф, ast.Lambda):
            а = ф.args
            if база.id in [x.arg for x in а.posonlyargs + а.args + а.kwonlyargs] + \
                    ([а.vararg.arg] if а.vararg else []) + ([а.kwarg.arg] if а.kwarg else []):
                return None                                   # вимір: словник від викликача
            присв = _локальні(ф, база.id)
            if присв:
                чч = [self._словник("локальний «%s»" % база.id, з, ключі) if поля(з) else None for з in присв]
                return чч[0] if all(чч) else None             # інакше — вимір: виклик, обчислення
        р = self.вираз(м, база)
        if р is None:
            return None                                       # поза кодом продукту чи атрибут об'єкта — вимір
        мод, ім, з = р
        if мод == КОНСТРУКТОР[0]:
            return None                                       # шкала механізму (`КАТ_У_НП`)
        if (мод, ім) in self.реєстри:
            return self._реєстр((мод, ім), з, ключі)
        if isinstance(з, ast.Subscript):                      # `X = R["k"]` рівня модуля
            б2, к2 = self._ланцюг(з)
            return self._база(мод, None, б2, к2 + ключі, глиб + 1)
        if isinstance(з, ast.DictComp):
            return self._похідний(мод, ім, з, ключі)
        if поля(з):
            return self._словник("модуля «%s.%s»" % (мод, ім), з, ключі)
        return None                                           # обчислене значення — вимір

    def _реєстр(self, р, з, ключі):
        if not ключі:
            return None
        к = ключі[0]
        записи = self.реєстри[р]
        if isinstance(к, ast.Constant) and isinstance(к.value, str):
            запис = записи.get(к.value)
            if запис is None:                                 # не запис реєстру — звичайний ключ словника
                return self._словник("модуля «%s.%s»" % р, з, ключі) if поля(з) else None
            return self._провенанс(запис)
        for запис in записи.values():                         # ключ виразом — кожен запис мусить мати джерело
            ч = self._провенанс(запис)
            if ч:
                return ч + " (ключ виразом)"
        return None

    def _похідний(self, мод, ім, з, ключі):
        """`C = {k: R[k]["val"] for k in R}` — ключ C — запис R; `{… for к, з in R["e"]["val"].items()}` — запис e."""
        дж = з.generators[0].iter if з.generators else None
        if isinstance(дж, ast.Call) and isinstance(дж.func, ast.Attribute) and дж.func.attr in (
                "items", "keys", "values"):
            дж = дж.func.value
        б, кк = self._ланцюг(дж)
        р = self.вираз(мод, б) if б is not None else None
        if р is None or (р[0], р[1]) not in self.реєстри:
            return None                                       # похідний не від реєстру — обчислення
        if кк:
            return self._реєстр((р[0], р[1]), р[2], кк)
        return self._реєстр((р[0], р[1]), р[2], ключі)

    def _провенанс(self, запис):
        п = поля(запис["вузол"])[0]
        for к in ПОЛЯ_ДЖЕРЕЛА:
            з = п.get(к)
            if з is not None and not (isinstance(з, ast.Constant) and not з.value):
                return None                                   # константа реєстру з джерелом
        return "константа реєстру «%s» без джерела (%s)" % (запис["ключ"], запис["місце"])

    @staticmethod
    def _словник(опис, з, ключі):
        """Ланцюг ключів у словнику-літералі: число на кінці — без джерела."""
        значення = [з]
        for к in ключі:
            наступні = []
            for в in значення:
                п = поля(в)
                if not п:
                    continue
                if isinstance(к, ast.Constant):
                    if isinstance(в, ast.Dict):
                        наступні += [зз for кк, зз in zip(в.keys, в.values)
                                     if isinstance(кк, ast.Constant) and кк.value == к.value]
                    elif к.value in п[0]:
                        наступні.append(п[0][к.value])
                else:
                    наступні += list(в.values) if isinstance(в, ast.Dict) else list(п[0].values())
            значення = наступні
        if any(_лише_літерали(в) for в in значення):
            return "індекс у словник %s з літералом без джерела" % опис
        return None


def _ід_опис(в):
    return repr(в.value) if isinstance(в, ast.Constant) else ast.unparse(в)[:30]


def п1_js(П):
    """JS показу: літерал об'єкта з `правило:` і `сила:`/`регістр:`, де сила — не копія поля іншого об'єкта."""
    out = []
    взір = re.compile(r"\{[^{}]*\bправило\s*:[^{}]*\}")
    сила = re.compile(r"\b(сила|регістр|сила_нп)\s*:\s*([^,}]+)")
    for шлях, т in П.js.items():
        for м in взір.finditer(т):
            for с in сила.finditer(м.group(0)):
                з = с.group(2).strip()
                if re.match(r"^[\wА-Яа-яЇїІіЄєҐґʼ$]+(\?)?\.(сила|сила_нп|регістр)\b", з):
                    continue
                н = т.count("\n", 0, м.start()) + 1
                out.append(("%s:%d" % (шлях, н), "п1а", "JS: об'єкт з правилом і %s: %s" % (с.group(1), з[:30])))
    return out


# ───────────────────────────── п.2–п.4 ─────────────────────────────

class Читання:
    """Рядки, які верхній вузол (з досяжними викликами й іменами модуля) бачить — для п.3."""

    def __init__(self, П, реєстри):
        self.П, self.реєстри = П, реєстри      # реєстри: {(модуль, ім'я словника)}
        self._к = {}

    def рядки(self, к):
        if к in self._к:
            return self._к[к]
        П = self.П
        out = set()
        for (м, ім) in П.досяжні({к}):
            мм = П.М.get(м)
            if мм is None or ім not in мм.функції:
                continue
            вузол = мм.функції[ім]
            out |= рядки_ключів(вузол)
            out |= self._імена_модуля(м, вузол)
        self._к[к] = out
        return out

    def _імена_модуля(self, м, вузол, бачені=None):
        """Рядки імен рівня модуля, які бере вузол (транзитивно), крім самих реєстрів констант."""
        бачені = set() if бачені is None else бачені
        мм = self.П.М[м]
        out = set()
        for в in ast.walk(вузол):
            ц = None
            if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Load):
                if в.id in мм.імена:
                    ц = (м, в.id)
                elif в.id in мм.з_модуля:
                    ц = мм.з_модуля[в.id]
            elif isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name) and в.value.id in мм.аліаси:
                ц = (мм.аліаси[в.value.id], в.attr)
            if ц is None or ц in бачені or ц in self.реєстри or ц[0] not in self.П.М:
                continue
            бачені.add(ц)
            з = self.П.М[ц[0]].імена.get(ц[1])
            if з is None or isinstance(з, ast.Lambda):
                continue
            out |= рядки_ключів(з)
            out |= self._імена_модуля(ц[0], з, бачені)
        return out


def _права(к):
    """Ід правил, за які константа голосує (`за_кого` з ід правила; тір `визначення` не голосує)."""
    if к["t"] == "визначення":
        return ()
    return tuple(п for п in к["прав"] if цілий(п))


def читачі(П, кк):
    """{ключ: {верхні вузли (модуль, ім'я) | ('js', шлях) | ('модуль', м)}} — де рядок-ключ стоїть поза записом."""
    ключі = {к["ключ"] for к in кк}
    вузли_ключів = set()
    for к in кк:
        б = к["мм"].батько.get(к["вузол"])
        if isinstance(б, ast.Dict):
            for кл, з in zip(б.keys, б.values):
                if з is к["вузол"]:
                    вузли_ключів.add(id(кл))
    out = {}
    for м, мм in П.М.items():
        for ст in мм.дерево.body:
            імена = _імена_верху(ст)
            for в in ast.walk(ст):
                if isinstance(в, ast.Constant) and isinstance(в.value, str) and в.value in ключі \
                        and id(в) not in вузли_ключів:
                    for ім in імена or [None]:
                        out.setdefault(в.value, set()).add((м, ім) if ім else ("модуль", м))
    for шлях, т in П.js.items():
        for ключ in ключі:
            if re.search(r"[\"'`]" + re.escape(ключ) + r"[\"'`]", т):
                out.setdefault(ключ, set()).add(("js", шлях))
    return out


class Гілки:
    """Найближчі гілки емісії над вузлом: ідемо зворотними посиланнями вгору й зупиняємось на першому вузлі, що
    емітує правило; вузол без посилань, що нічого не емітує, — «дані» (значення може йти далі даними)."""

    def __init__(self, П, емітує):
        self.П, self.емітує = П, емітує
        self.зворотні = {}
        for к, цц in П.посилання().items():
            for ц in цц:
                self.зворотні.setdefault(ц, set()).add(к)
        self._к = {}

    def над(self, к):
        """(множина ід найближчих гілок, чи є шлях до «даних»)."""
        return self.вузли_над(к)[:2]

    def вузли_над(self, к):
        """(ід найближчих гілок, чи є шлях до «даних», вузли цих гілок)."""
        if к in self._к:
            return self._к[к]
        іди, дані, вузли = set(), False, set()
        бачені, край = set(), [к]
        while край:
            в = край.pop()
            if в in бачені:
                continue
            бачені.add(в)
            if в in self.емітує:
                іди |= self.емітує[в]
                вузли.add(в)
                continue
            вгору = self.зворотні.get(в, set()) - бачені
            if not вгору and not (self.зворотні.get(в, set()) & бачені):
                дані = True
            край.extend(вгору)
        self._к[к] = (іди, дані, вузли)
        return self._к[к]


def п2_п4(П, р1, ем):
    """п.2, п.3, п.4. Повертає (місця, не-місця п.3, кількість констант)."""
    кк = константи(П)
    реєстри = {(к["мод"], к["словник"]) for к in кк}
    емітує, через_конструктор = {}, set()
    for м, в, іди, верх in ем:
        if верх:
            емітує.setdefault((м, верх), set()).update(іди or {"?"})
        через_конструктор |= іди
    for м, верх, іди in р1.емісії_словником:
        if верх:
            емітує.setdefault((м, верх), set()).update(іди)
    гілки = Гілки(П, емітує)
    чит = читачі(П, кк)
    емітує_к = {}                                   # гілки емісії через конструктор: (модуль, верх) → {ід}
    for м, в, іди, верх in ем:
        с = next((к.value for к in в.keywords if к.arg == "сила"), в.args[1] if len(в.args) > 1 else None)
        if isinstance(с, ast.Constant) and с.value in НЕСИЛИ:
            continue                                # «утримано», «питання», «ok» — не сила: стелі нема що знижувати
        if верх and іди:
            емітує_к.setdefault((м, верх), set()).update(іди)
    рядки_гілок = Читання(П, реєстри)
    місця, незчитані, не_п3 = [], set(), []
    for к in кк:
        пп = _права(к)
        хто = чит.get(к["ключ"], set())
        if not хто:
            if пп:
                місця.append((к["місце"], "п2", "%s[%r] голосує за %s, мертва: ключ ніде не читається" % (
                    к["словник"], к["ключ"], ", ".join(пп))))
                незчитані |= {(к["місце"], п) for п in пп}
            else:
                місця.append((к["місце"], "п4", "%s[%r] без правила в `прав` і без читача в коді продукту" % (
                    к["словник"], к["ключ"])))
            continue
        if not пп:
            continue
        глухі_за = []                               # (правило, гілки емісії, що не читають) — рішення 15697
        for п in пп:
            if not any(і == п or основа(і) == п for і in через_конструктор):
                continue                            # правило не виходить через конструктор: голос не діє
            вгорі, дані, читають = set(), False, set()
            for в in хто:
                if в[0] in ("js", "модуль"):
                    дані = True
                    continue
                і, д, вв = гілки.вузли_над(в)
                вгорі |= і
                дані = дані or д
                читають |= вв | {в}
            if дані:
                continue
            if "?" in вгорі or any(і == п or основа(і) == п for і in вгорі):
                # (читана не всіма гілками правила) — гілка емісії правила (чи правила з тією самою основою), яка
                # не читає константи ні сама (транзитивно вниз), ні як найближчий емітер над читачем; емісія з
                # нерозв'язаним ід («?») над читачем знаних гілок правила не покриває
                глухі = sorted("%s.%s" % г for г, іди in емітує_к.items()
                               if any(і == п or основа(і) == п for і in іди) and г not in читають
                               and к["ключ"] not in рядки_гілок.рядки(г))
                if глухі:
                    глухі_за.append((п, глухі))
                    незчитані.add((к["місце"], п))
                continue
            місця.append((к["місце"], "п2", "%s[%r] голосує за %s, читають лише гілки інших правил (%s)" % (
                к["словник"], к["ключ"], п, ", ".join(sorted(вгорі))[:100])))
            незчитані.add((к["місце"], п))
            break
        else:
            if глухі_за:
                місця.append((к["місце"], "п2", "%s[%r] голосує за правило, а гілки його емісії не читають: %s" % (
                    к["словник"], к["ключ"], "; ".join("%s — %s" % (п, ", ".join(гг)) for п, гг in глухі_за)[:240])))
    # п.3: двійник голим літералом у гілці емісії правила, жодна гілка якого константи не читає (вона —
    # місце п.2). Константу, яку емісія правила читає, правило вже бере з реєстру: рівний їй літерал в іншій
    # гілці судить іншу величину (лічба речей, множник), не двійник — його друкує `--докладно` як не місце.
    рядки = Читання(П, реєстри)
    for к in кк:
        if к["val"] is None:
            continue
        for п in _права(к):
            for (м, ім), іди in емітує.items():
                if not any(і == п or основа(і) == п for і in іди):
                    continue
                мм = П.М.get(м)
                if мм is None or ім not in мм.функції or к["ключ"] in рядки.рядки((м, ім)):
                    continue
                for в in ast.walk(мм.функції[ім]):
                    if not isinstance(в, ast.Compare):
                        continue
                    for ч in [в.left] + в.comparators:
                        if _число(ч) is not None and _число(ч) == к["val"]:
                            if (к["місце"], п) not in незчитані:
                                не_п3.append((мм.рядок(в), "п3: літерал %s у гілці %s.%s дорівнює %s[%r], але "
                                              "константа не місце п.2 для %s (її читає емісія правила чи шлях даних) — збіг числа, не двійник" % (
                                                  _число(ч), м, ім, к["словник"], к["ключ"], п)))
                                continue
                            місця.append((мм.рядок(в), "п3", "%s: літерал %s у гілці %s.%s, а %s[%r] = %s (%s) "
                                          "гілка не читає" % (п, _число(ч), м, ім, к["словник"], к["ключ"],
                                                              к["val"], к["місце"])))
    return місця, не_п3, len(кк)


def _число(x):
    if isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool):
        return x.value
    if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub) and _число(x.operand) is not None:
        return -_число(x.operand)
    return None


def лічба(П):
    р1 = П1(П).прогін()
    ем = емісії(П)
    м24, не_п3, nк = п2_п4(П, р1, ем)
    return р1.місця + п1_js(П) + м24, р1.відкинуті + не_п3, nк, ем

# ───────────────────────────── самоперевірка ─────────────────────────────

_СТЕНД = {
    "bridge": "import реєстр_сила, суд_а, суд_б, суд_в, реєстр_акс\n",
    "реєстр_сила": (
        "def регістр(п, с, reg=None):\n    return 'гейт'\n"
        "def _допомога(d):\n    d['регістр'] = 'репліка'\n"
        "def зн(правило, сила, суть, речі, чому, reg=None):\n"
        "    d = dict(правило=правило, сила=сила, регістр=регістр(правило, сила), суть=суть, речі=речі, чому=чому)\n"
        "    _допомога(d)\n    d['сила_нп'] = неперервна_сила(сила)\n    return d\n"
        "def перезважити(z, нова, *, вага_від=None, частка=None):\n    z['сила_нп'] = 0.5\n    return z\n"  # не місце
        "def неперервна_сила(сила, вимір=None, поріг=None, розкид=None, повна=None, частка=None):\n"
        "    return перезважити({}, None, частка=1.0)\n"                   # не місце: у самому шляху
        "КАТ_У_НП = {'hint': 0.25, 'soft': 0.5}\n"),                         # шкала механізму
    "реєстр_акс": (
        "РЕЄСТР = {\n"
        " 'читана': dict(t='T2', val=2.5, прав='K-HAT-01', суть='с'),\n"
        " 'мертва_з_прав': dict(t='T3', val=1.5, прав='K-HAT-01'),\n"
        " 'визнач': dict(t='визначення', val=2, прав='K-HAT-01'),\n"
        " 'через_політику': dict(t='T3', val=3, прав='K-WEA-05'),\n"
        " 'мертва_без_прав': dict(t='T3', val=9),\n"
        " 'жива_без_прав': dict(t='T3', val=4),\n"
        " 'обидві': dict(t='T3', val=7, прав='K-HAT-02', суть='с'),\n"   # не місце: читають обидві гілки
        "}\n"
        "C3 = {k: РЕЄСТР[k]['val'] for k in РЕЄСТР}\n"),
    "суд_а": (
        "import реєстр_сила as РС\nfrom реєстр_акс import РЕЄСТР, C3\n"
        "ПОЛІТИКА = {'K-WEA-05': 'через_політику'}\n"
        "def _зн(правило, сила, *а, **к):\n    return РС.зн(правило, сила, *а, reg=РЕЄСТР, **к)\n"
        "def капелюх(р, out):\n"
        "    if р <= 1.5:\n        return\n"                                            # п.3
        "    if р > РЕЄСТР['читана']['val']:\n"
        "        out.append(_зн('K-HAT-01', 'strong', 'суть', [], 'чому'))\n"
        "def погода(out):\n    п = ПОЛІТИКА['K-WEA-05']\n"
        "    out.append(_зн('K-WEA-05', 'default', 'суть', [], 'чому'))\n"
        "def словник(out):\n"
        "    out.append(dict(правило='K-COL-03', сила='strong', суть='с', чому='ч'))\n"    # п.1а
        "    out.append(dict(правило='площа', сила='утримано', суть='с'))\n"                # не місце: не ід
        "    out.append(dict(правило='K-COL-04', сила='hint', бік='код'))\n"                # не місце: без тексту
        "def один():\n    return dict(правило='K-COL-05', сила='утримано', суть='с')\n"     # п.1а через повернення
        "def збір(out):\n    з = один()\n    if з:\n        out.append(з)\n"
        "def палітра():\n    return {'а': dict(правило='R-MUA-02', сила='hint', суть='с')}\n"  # не місце: не список
        "def проєкція(зз):\n    return [dict(правило=з['правило'], сила=з.get('сила'), суть=з['суть']) for з in зз]\n"
        "def знизити(зз):\n"
        "    for з in зз:\n        if з.get('правило') == 'K-COL-06':\n            з['сила'] = 'soft'\n"   # п.1в
        "            з['регістр'] = 'репліка'\n"
        "    return [dict(з, регістр='репліка') for з in зз if з.get('правило')]\n"        # п.1б
        "def вимір(п):\n    c = dict(L=1)\n    c['сила'] = 0.3\n    return c\n"              # не місце: не знахідка
        "def складений(out):\n    з = {}\n    з['правило'] = 'K-PAL-18'\n    з['сила'] = 'hint'\n"
        "    з['суть'] = 'с'\n    out.append(з)\n"                                            # п.1а з нуля
        "def вага(out):\n    з = РС.зн('K-COL-07', 'soft', 'с', [], 'ч')\n    з['сила_нп'] = 0.9\n"      # п.1в сила_нп
        "    out.append(dict(з, сила_нп=0.0))\n"                                                         # п.1б сила_нп
        "    out.append(dict(РС.зн('K-COL-08', 'soft', 'с', [], 'ч'), сила_нп=0.0, тримає=True))\n"      # п.1б сила_нп
        "    out.append(dict(правило='K-COL-09', сила_нп=0.3, суть='с'))\n"                              # п.1а сила_нп
        "    out.append(dict(з, сила_нп=з.get('сила_нп')))\n"                                            # не місце: копія
        "def перевага(з):\n    return перезважити(з, 'hard')\n"),                                       # не місце: єдиний шлях
    "суд_в": (
        "import реєстр_сила as РС\nfrom реєстр_сила import перезважити, неперервна_сила\n"
        "from суд_а import _зн\nЧАСТКА_М = 0.9\nC = {'межа': dict(t='T3', val=0.6, суть='с')}\n"
        "def частки(out, з, м, п, к=0.7, вим=None):\n"
        "    out.append(РС.зн('K-COL-10', 'soft', 'с', [], 'ч', частка=0.95))\n"            # 7  п.1б літерал
        "    out.append(_зн('K-COL-11', 'soft', 'с', [], 'ч', частка=ЧАСТКА_М))\n"           # 8  п.1б ім'я модуля
        "    out.append(перезважити(з, None, частка=1.0 - 0.2))\n"                          # 9  п.1б арифметика літералів
        "    out.append(перезважити(з, 'hard', вага_від=0.6))\n"                             # 10 п.1б вага_від
        "    н, _ = неперервна_сила('soft', None, None, None, None, 0.4)\n"                 # 11 п.1б позиційно
        "    out.append(_зн('K-COL-12', 'soft', 'с', [], 'ч', частка=0.3 if м else п))\n"   # 12 п.1б гілка
        "    out.append(_зн('K-COL-13', 'soft', 'с', [], 'ч', частка=к))\n"                  # 13 п.1б параметр-літерал
        "    л = 0.5\n    out.append(_зн('K-COL-14', 'soft', 'с', [], 'ч', частка=л))\n"   # 15 п.1б ім'я-літерал
        "    out.append(_зн('K-COL-15', 'soft', 'с', [], 'ч', частка=м))\n"                 # не місце: вимір
        "    out.append(_зн('K-COL-16', 'soft', 'с', [], 'ч', частка=round(min(1.0, п / 40.0), 2)))\n"  # 17 п1б 40.0
        "    out.append(перезважити(з, 'hard', вага_від=C['межа']['val']))\n"               # не місце: реєстр
        "    с = неперервна_сила('soft', частка=п) if п else 0.0\n"                         # не місце: вимір
        "    out.append(перезважити(з, None, частка=вим))\n"                                # не місце: None за замовч.
        "    out.append(_зн('K-COL-17', 'soft', 'с', [], 'ч', частка=None))\n"             # не місце: нема частки
        # індекс `X[…]` (вада 15686): число без джерела — словник-літерал, константа реєстру без провенансу
        "    out.append(перезважити(з, None, частка=ТАБЛ['а']))\n"                          # 22 п1б словник модуля
        "    out.append(перезважити(з, None, частка=1.0 - ТАБЛ['б']['в']))\n"               # 23 п1б вкладений
        "    out.append(перезважити(з, None, частка=Р['гола']['val']))\n"                   # 24 п1б реєстр без джерела
        "    т = {'а': 0.4}\n    out.append(перезважити(з, None, частка=т['а']))\n"         # 26 п1б локальний словник
        "    out.append(перезважити(з, None, частка=ТАБЛ[м]))\n"                            # 27 п1б ключ виразом
        "    ім_т = ТАБЛ['а']\n    out.append(перезважити(з, None, частка=ім_т))\n"       # 29 п1б ім'я індексу
        # не місця: реєстр з джерелом (прямо, похідний `C`, реекспорт), шкала механізму, вимір
        "    out.append(перезважити(з, None, частка=Р['з_дж']['val']))\n"                  # не місце: джерело
        "    out.append(перезважити(з, None, частка=C2['з_дж']))\n"                       # не місце: похідний C
        "    out.append(перезважити(з, None, частка=РА.C3['читана']))\n"                   # не місце: реекспорт
        "    out.append(перезважити(з, None, частка=РС.КАТ_У_НП['soft']))\n"              # не місце: шкала механізму
        "    out.append(перезважити(з, None, частка=п['частка']))\n"                       # не місце: параметр
        "    пр = вимір_ф(м)\n    out.append(перезважити(з, None, частка=пр['частка']))\n"  # не місце: виклик
        # числа без джерела всередині виразу з виміром (вада 15698)
        "    out.append(перезважити(з, None, частка=п * 0.6))\n"                           # 37 п1б множник
        "    с2 = п / 40.0\n    out.append(перезважити(з, None, частка=с2))\n"            # 39 п1б через ім'я
        "    out.append(перезважити(з, None, частка=min(1.0, п + ТАБЛ['а'] * м)))\n"       # 40 п1б індекс словника
        "    out.append(перезважити(з, None, частка=round(min(1.0, max(0.0, 1.0 - п)), 2)))\n"  # не місце: 0, 1, ndigits
        "    с3 = п * 0.5\n    с3 = п\n    out.append(перезважити(з, None, частка=с3))\n"  # не місце: перекрито
        "    out.append(перезважити(з, None, частка=п / max(1e-6, м) * C2['з_дж']))\n"     # не місце: запобіжник, реєстр
        "    out.append(перезважити(з, None, частка=вимір_ф(0.3)['частка']))\n"            # не місце: аргумент виклику
        "ТАБЛ = {'а': 0.5, 'б': {'в': 0.2}}\n"
        "Р = {'з_дж': dict(t='T3', val=0.0, джерело='власник 02.10'), 'гола': dict(t='T3', val=0.2)}\n"
        "C2 = {k: Р[k]['val'] for k in Р}\n"
        "import суд_а as РА\n"
        "def вимір_ф(м):\n    return dict(частка=float(м))\n"),
    "суд_б": "import суд_а\nfrom реєстр_акс import РЕЄСТР\nЖИВА = РЕЄСТР['жива_без_прав']\n"
             "def ще(out):\n    out.append(суд_а._зн('K-OUT-41', 'soft', 'с', [], 'ч'))\n"
             "def шапка(р, out):\n    if р == 2.5:\n"                       # п.3: 'читана' читає капелюх, шапка — ні
             "        out.append(суд_а._зн('K-HAT-01', 'hint', 'с', [], 'ч'))\n"
             "def х1(out):\n    if РЕЄСТР['обидві']['val']:\n"
             "        out.append(суд_а._зн('K-HAT-02', 'soft', 'с', [], 'ч'))\n"
             "def _пор():\n    return РЕЄСТР['обидві']['val']\n"                   # читач під гілкою х2
             "def х2(out):\n    if _пор():\n        out.append(суд_а._зн('K-HAT-02', 'soft', 'с', [], 'ч'))\n"
             "def х3(out):\n    out.append(суд_а._зн('K-HAT-02', 'утримано', 'с', [], 'ч'))\n",   # не місце: не сила
}
_JS = {"джерела/показ/а.js": "const а = {правило: з.правило, сила: з.сила_нп};\n"
                             "const б = {правило: 'K-X-01', сила: 'hard'};\n"}
_ОЧІКУВАНО = {
    ("суд_а", 7, "п3"), ("реєстр_акс", 3, "п2"), ("реєстр_акс", 4, "п4"), ("реєстр_акс", 6, "п4"),
    ("суд_а", 15, "п1а"), ("суд_а", 19, "п1а"), ("суд_а", 31, "п1в"), ("суд_а", 33, "п1б"), ("суд_а", 41, "п1а"),
    ("джерела/показ/а.js", 2, "п1а"),
    ("суд_а", 46, "п1в"), ("суд_а", 47, "п1б"), ("суд_а", 48, "п1б"), ("суд_а", 49, "п1а"),   # сила_нп
    ("суд_в", 7, "п1б"), ("суд_в", 8, "п1б"), ("суд_в", 9, "п1б"), ("суд_в", 10, "п1б"),       # параметр ваги
    ("суд_в", 11, "п1б"), ("суд_в", 12, "п1б"), ("суд_в", 13, "п1б"), ("суд_в", 15, "п1б"),
    ("суд_в", 22, "п1б"), ("суд_в", 23, "п1б"), ("суд_в", 24, "п1б"), ("суд_в", 26, "п1б"),   # індекс X[…]
    ("суд_в", 27, "п1б"), ("суд_в", 29, "п1б"),
    ("суд_в", 17, "п1б"), ("суд_в", 37, "п1б"), ("суд_в", 39, "п1б"), ("суд_в", 40, "п1б"),   # число у виразі
    ("реєстр_акс", 2, "п2"), ("суд_б", 7, "п3"),   # 15697: 'читана' читає капелюх, а не шапка — та сама K-HAT-01
}


def самоперевірка():
    модулі = {м: ("джерела/%s.py" % м, т) for м, т in _СТЕНД.items()}
    П = Продукт("/неіснує", модулі=модулі, js=_JS)
    місця, відкинуті, _, _ = лічба(П)
    є = set()
    for м_, пункт, чому in місця:
        ф, р = м_.rsplit(":", 1)
        мод = ф if ф.endswith(".js") else os.path.basename(ф)[:-3]
        є.add((мод, int(р), пункт))
    добре = є == _ОЧІКУВАНО
    for х in sorted(є - _ОЧІКУВАНО):
        print("зайве:", х)
    for х in sorted(_ОЧІКУВАНО - є):
        print("бракує:", х)
    print("самоперевірка: %s (%d місць, %d відкинуто)" % ("так" if добре else "НІ", len(є), len(відкинуті)))
    return 0 if добре else 1


def main():
    арг = sys.argv[1:]
    if "--самоперевірка" in арг:
        sys.exit(самоперевірка())
    корінь = os.getcwd()
    if "--корінь" in арг:
        корінь = арг[арг.index("--корінь") + 1]
    П = Продукт(корінь)
    місця, відкинуті, nк, ем = лічба(П)
    місця = sorted(set(місця), key=lambda х: (х[0].rsplit(":", 1)[0], int(х[0].rsplit(":", 1)[1]), х[1]))
    for м_, пункт, чому in місця:
        print("%s · %s · %s" % (пункт, м_, чому))
    if "--докладно" in арг:
        for м_, чому in sorted(set(відкинуті)):
            print("не місце · %s · %s" % (м_, чому))
    from collections import Counter
    л = Counter(п for _, п, _ in місця)
    print("обсяг: модулів %d, JS %d, констант реєстрів %d, емісій через конструктор %d, обгорток %d" % (
        len(П.М), len(П.js), nк, len(ем), len(П.К) - 1))
    print("за пунктами: " + ", ".join("%s %d" % (к, л[к]) for к in sorted(л)))
    print("місць: %d" % len({м_ for м_, _, _ in місця}))


if __name__ == "__main__":
    main()
