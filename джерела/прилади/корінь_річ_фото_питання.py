# -*- coding: utf-8 -*-
"""Прилад кореня Річ-фото-питання: місця шляху «її фото → палітра → річ з фото → вердикт → слова стилістки», де жінка
на питання про свою річ дістає службовий рядок, мовчазне «невідомо» чи вердикт без осі, яку продукт уміє судити
(паспорт `аудит/корені/Річ-фото-питання.md`).

ШЛЯХ — ВИКЛИК, А НЕ ПЕРЕЛІК ФАЙЛІВ. Входи беруться з викликів показу до моста, а не з переліку ендпойнтів:
ендпойнт, якому `показ/*.js` передає її фото (`містП('ім', {…})` з ключем `фото`, `фото_речей`, `пікселі`,
`пікселі_фото` чи `опис_фото`: на `main` — `річ_з_фото`, `оцінка`, `стилістка`), і ендпойнт файлу показу, що несе
промпт, зібраний із продукту під час збірки (`build_артефакт.py`: заповнювач `__ПРОМПТ_КОЛІР_ПОКАЗУ__` ←
`міст_вхід.промпт_кольору()`; у тому файлі — `колір`), разом із тим викликом. Ім'я ендпойнта → функція — за
диспетчером `bridge.виклик`. Ендпойнт без її фото (`мова`, `запити`, `паспорт`…) — не вхід: туди йдуть її слова чи
записи коду, а не питання про річ із фото. Шлях — замикання викликів від входів по `джерела/*.py` продукту (без
`батарея_ gate_ measure_ стенд_ тест_ audit_ pair_test run_outfit status_перевірки`): виклик імені модуля, псевдоніма
`import М as А`, `from М import ф as г`. У показі — функції `показ/*.js`, що кличуть ендпойнти входів і збирають
`збої`, і ті, що кличуть їх.

ЇЇ ВХІД — «сирий» (форма невідома): параметр входу й те, що з нього взято без перебудови (`json.loads`, `.get`,
`[...]`, `dict(сирий, …)`, `сирий or …`, прохід циклом чи генератором, функція шляху, що повертає сирий);
міжпроцедурно — через аргументи викликів шляху до нерухомої точки. Новий словник із ключами коду, `float(...)`,
результат обчислення — не сирий: їхні ключі й форму задає код. Протокол — теж не її дане: кадр пікселів
(`пікселі`, `пікселі_фото`) і вихід кроку коду, який показ несе назад (`суд` оцінки, `речі`, розібрані кодом).

КЛАС (а) — крок вимагає даного, якого суд слота не читає, або падає без нього замість назвати, чого бракує:
  а1  `сирий["ключ"]` / `сирий[0]` без сторожа — `KeyError`/`IndexError` замість назви поля. Сторож — той самий ключ
      чи ім'я в умові над місцем (`if`, `and`, `if` генератора, вихід `return/raise/continue` вище в блоці, `try`) чи в
      умові функції, що кличе цю (фільтр `р.get("ід")` перед `_річ(р)`), чи функція шляху, з чийого результату
      взято ключ, сама його знає (перевіряє, будує чи називає у винятку: `місце_речі._елемент`).
      місце: `d["очі"]` у `міст_вхід.features`; не місце: `d["пікселі"]` під `if d.get("пікселі")`, `с["ціль"]`
      змін із `суд` оцінки (протокол).
  а2  зведення можливо порожнього сирого списку (`median`, `mean`, `min`/`max` без `default`, `next` без запасного)
      без сторожа — `StatisticsError`/`ValueError` (паспорт п.2). Не місце: `сп or [d["шкіра"]]` — не порожній.
  а3  `raise` під умовою відсутності її даного (`x in (None, "")`, `x is None`, `not x`, `"k" not in x`, ім'я,
      збудоване з такої умови) — виняток іде жінці службовим рядком, навіть коли поле названо (паспорт п.3:
      зріст і обхвати, яких вердикт низу не читає). Не місце: `raise` на невідомому значенні протоколу
      (`джерело кольору not in AXIS_RELIABILITY` — не відсутність, не її дане).
  а4  правило промпту шляху (`Оголошення(правила=…)`), що на формі входу вимагає порожнього виходу — «лише причину» замість
      того, що видно, і назви того, чого не видно (паспорт п.1: обличчя менше чверті кадру — палітри нема зовсім).
      Не місце: межа «невідомо» на одне поле (кільце ока — null), поправка світла.
  а5  показ: текст жінці за умовою збою кроку (`збої.length`, `.помилка`, `catch`) сталим рядком без причини.
      Не місце: `збої.push(…)` — технічний рядок у запис ходу для звіту власника, не їй.
  а6  крок шляху пише її речі поле-причину, яке суд речі кладе заявою в її відповідь (`чому_не_закріплена`), за
      умовою на даному, якого суд речі не читає: інші речі, порядок, чий свідок (паспорт п.5: «пізніша твоя річ стоїть
      на цьому місці» — кілька речей одного місця читано як заміну). Не місце: умова на полі, яке суд читає (`слот`),
      чи на її власному слові «не збирати з нею» (`рука`).

КЛАС (б) — відповідь жінці про річ, у якій вісь, яку продукт уміє судити для слота, не суджено й про це не сказано:
  б1  суддя речі (функція шляху з переліком `без_входу` і повідомленням їй) пропускає вісь (`без_входу.append`), а
      заяви про це в повідомленні нема: ні в тому самому блоці, ні під умовою, рівною умові пропуску чи її диз'юнктом
      (і в будівнику повідомлення, куди умову передано аргументом). Чекліст «без входу» жінці не йде — лише в
      запис. Місце: «крій проти фігури: верх чи низ сам контуру не дає» (паспорт п.4, `річ_з_фото.py:1722`).
      Не місце: «тон поверхні невизначений» — під тією самою умовою заява `colour_partly_measured`; «нагода не
      названа» — `occasion_not_named_everyday`; рядок-застереження блоку, що сам дає вхід суду далі (зона слова
      кольору ставить `lab`, який суд читає), — вісь суджено.
  б2  ознака речі, яку крок опису речі записує (`_ПОЛЯ_ФОТО`), передає в запис речі для суду образу
      (`запис_каталогу`) і яку там читає суддя продукту (функція з `зн(…)`/`заява(…)`), а суддя речі не читає зовсім
      — вісь не суджено і не названо (паспорт п.4: довжина проти рівнів тіла). Місце — рядок `def` судді речі.
      Не місце: ознака, яку суддя речі читає (`крій`, `матеріал`), чи яку жоден суддя не читає.
  б3  правило відповіді на її питання, що обрізає відповідь числом речень, — будь-де на шляху: текст у функції шляху
      чи в сталій, яку вона називає (правила `Оголошення`, `наприкінці`, правило допиту), і цей текст сам називає
      питання (`question`) чи стоїть в `Оголошення` з питанням на вході (паспорт п.7: «Two to four sentences»;
      «one to three sentences» оцінки). Не місце: «one sentence for her: what you understood or what you ask» —
      підтвердження паспорта, не відповідь про річ.

Рядки паспорта п.4 `річ_з_фото.py:1591` і `:1654` — не місця: колір далеко від обличчя суджено й сказано
(`colour_outside_palette_far_from_face`), а `:1654` — походження кольору (корінь Річ-колір-вимір); п.4 прилад бачить
місцями б1 і б2 того самого судді. Кольорові симптоми проби (п.6) — корінь Річ-колір-вимір, тут не лічаться.

ВИВІД: `файл:рядок · клас · правило · чому`, підсумки за правилами, останній рядок `місць: <N>`; код 0 (формат
храповика). Нерозбірний файл чи відсутній вузол класу (`_ПОЛЯ_ФОТО`, `запис_каталогу`, вхід шляху) — `обсяг_приладу`
називає його і дає код 1: нуль від «не бачу» не схожий на «виправлено».
Запуск: python3 -W ignore джерела/прилади/корінь_річ_фото_питання.py [--корінь <дерево>]"""
import argparse
import ast
import collections
import copy
import glob
import os
import re
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import обсяг_приладу as _ОБ  # noqa: E402

ТУТ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)")
МІСТ = "bridge"                        # диспетчер ендпойнтів: `виклик(ім, вхід)` → {ім: функція}[ім]
ЗБІРКА = "build_артефакт.py"            # збірка показу: заповнювачі `__…__` — виклики продукту під час збірки
# ключі виклику моста, якими показ передає її фото: ід фото, кадр за рамкою, опис речей із фото
КЛЮЧІ_ФОТО = ("фото", "фото_речей", "пікселі", "пікселі_фото", "опис_фото")
# протокол, а не її дане: кадр пікселів (вирізку з її фото за формою {дані, ширина, висота, ядро} будує код показу,
# `пікселіРечіП`) і вихід кроку коду, який показ несе назад у наступний крок (`суд` — вихід кроку «суд» оцінки, `речі` —
# речі, розібрані кроком «речі» чи паспортом, з ід коду). Їхню форму задає код: ламаний запис — вада коду чи показу, а
# не брак її даного; сирість через ці ключі не йде
ПРОТОКОЛ = frozenset(("пікселі", "пікселі_фото", "суд", "речі"))
ЗВЕДЕННЯ = frozenset(("median", "mean", "fmean", "mode", "median_low", "median_high"))
ПРОХІДНІ = frozenset(("dict", "list", "tuple", "sorted", "reversed", "set"))
МЕТОДИ_СИРОГО = frozenset(("get", "items", "values", "keys", "copy", "pop", "setdefault"))
ВІДМОВА = re.compile(r"(?i)\bonly the reason\b|\bgive no (answer|colours?|colors?|items?)\b|\brefuse\b")
РЕЧЕННЯ = re.compile(r"(?i)\b(one|two|three|four|five|six)( to (two|three|four|five|six|seven))? sentences?\b")
ПИТАННЯ_EN = re.compile(r"(?i)\bquestion\b")
СПИСОК_ПРОПУСКІВ = "без_входу"
ПОЛЕ_ПРИЧИНИ = "чому_не_закріплена"
ЇЇ_РУКА = frozenset(("рука",))          # її власне слово «не збирати з нею» — не вимога кроку
ОПИС_ОЗНАК = "_ПОЛЯ_ФОТО"               # ознаки речі, які записує крок опису речі з фото
ЗАПИС_РЕЧІ = "запис_каталогу"           # річ → запис, який читають судді образу
JS_ТЕКСТ = re.compile(r"'[А-ЯІЇЄҐа-яіїєґ][^'\\]* [^'\\]*'")     # речення їй: літера на початку, кілька слів

Місце = collections.namedtuple("Місце", "файл рядок клас правило чому")


# ─────────────────────────── модулі й виклики ───────────────────────────
class Модуль:
    def __init__(self, ім, шлях, дерево):
        self.ім, self.шлях, self.дерево = ім, шлях, дерево
        self.батьки = {}
        for n in ast.walk(дерево):
            for c in ast.iter_child_nodes(n):
                self.батьки[c] = n
        self.функції, self.модулі, self.імена, self.сталі = {}, {}, {}, {}
        for n in дерево.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.функції[n.name] = n
            elif isinstance(n, ast.ClassDef):
                for м in n.body:
                    if isinstance(м, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.функції["%s.%s" % (n.name, м.name)] = м
            elif isinstance(n, ast.Assign):
                for ц in n.targets:
                    if isinstance(ц, ast.Name):
                        self.сталі[ц.id] = n.value
        for n in ast.walk(дерево):
            if isinstance(n, ast.Import):
                for а in n.names:
                    self.модулі[а.asname or а.name.split(".")[0]] = а.name.split(".")[-1]
            elif isinstance(n, ast.ImportFrom):
                for а in n.names:
                    if n.module:
                        self.імена[а.asname or а.name] = (n.module.split(".")[-1], а.name)
                    else:
                        self.модулі[а.asname or а.name] = а.name


def завантажити(корінь):
    модулі = {}
    for ш in sorted(glob.glob(os.path.join(корінь, "джерела", "*.py"))):
        ім = os.path.basename(ш)[:-3]
        if ВИКЛЮЧЕНО.match(ім):
            continue
        with open(ш, encoding="utf-8") as ф:
            текст = ф.read()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            дерево = _ОБ.розібрати(текст, os.path.relpath(ш, корінь))
        if дерево is not None:
            модулі[ім] = Модуль(ім, os.path.relpath(ш, корінь), дерево)
    return модулі


def ім_виклику(n):
    if isinstance(n.func, ast.Name):
        return n.func.id
    if isinstance(n.func, ast.Attribute):
        return n.func.attr
    return None


def розв(модулі, м, n):
    """Ціль виклику в продукті: (модуль, функція) чи None."""
    ф = n.func
    if isinstance(ф, ast.Name):
        if ф.id in м.функції:
            return (м.ім, ф.id)
        if ф.id in м.імена:
            мм, нн = м.імена[ф.id]
            if мм in модулі and нн in модулі[мм].функції:
                return (мм, нн)
    elif isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name):
        мм = м.модулі.get(ф.value.id)
        if мм in модулі and ф.attr in модулі[мм].функції:
            return (мм, ф.attr)
    return None


def шлях(модулі, входи):
    стек, бачено, викликачі = list(входи), set(), collections.defaultdict(set)
    for в in входи:
        if в[0] not in модулі or в[1] not in модулі[в[0]].функції:
            _ОБ.непрочитано("джерела/%s.py" % в[0], "вхід шляху %s.%s не знайдено" % в)
    стек = [в for в in стек if в[0] in модулі and в[1] in модулі[в[0]].функції]
    while стек:
        к = стек.pop()
        if к in бачено:
            continue
        бачено.add(к)
        м = модулі[к[0]]
        for n in ast.walk(м.функції[к[1]]):
            if isinstance(n, ast.Call):
                ц = розв(модулі, м, n)
                if ц:
                    викликачі[ц].add(к)
                    стек.append(ц)
    return бачено, викликачі


# ─────────────────────────── сирий вхід ───────────────────────────
def параметри(ф):
    а = ф.args
    return [x.arg for x in а.posonlyargs + а.args + а.kwonlyargs]


def цілі(т):
    if isinstance(т, ast.Name):
        yield т.id
    elif isinstance(т, (ast.Tuple, ast.List)):
        for е in т.elts:
            yield from цілі(е)
    elif isinstance(т, ast.Starred):
        yield from цілі(т.value)


class Сирість:
    """Міжпроцедурна нерухома точка: які параметри, імена й повернення — її сирий вхід (і чи можуть бути порожні)."""

    def __init__(self, модулі, шлях_, входи):
        self.модулі, self.шлях = модулі, шлях_
        self.пар = collections.defaultdict(lambda: [False, False])     # (ключ, ім) → [сирий, порожній]
        self.пов = collections.defaultdict(lambda: [False, False])
        for в in входи:
            if в in шлях_:
                п = параметри(модулі[в[0]].функції[в[1]])
                if п:
                    self.пар[(в, п[0])] = [True, True]
        self.сер = {}
        for _ in range(30):
            if not self._крок():
                break

    def оцінка(self, е, env, м):
        """(сирий, може_порожній) виразу."""
        с, п, _в = env
        if е is None:
            return False, False
        if isinstance(е, ast.Name):
            return е.id in с, е.id in п
        if isinstance(е, ast.Subscript):
            if isinstance(е.slice, ast.Constant) and е.slice.value in ПРОТОКОЛ:
                return False, False
            r, e = self.оцінка(е.value, env, м)
            return (r, True) if not isinstance(е.slice, ast.Slice) else (r, e)
        if isinstance(е, ast.BoolOp):
            оц = [self.оцінка(в, env, м) for в in е.values]
            r = any(o[0] for o in оц)
            if isinstance(е.op, ast.Or):
                ост = е.values[-1]
                непор = isinstance(ост, (ast.List, ast.Tuple, ast.Set)) and ост.elts or \
                    isinstance(ост, ast.Dict) and ост.keys
                return r, (not непор) and (оц[-1][1] or not оц[-1][0])
            return r, True
        if isinstance(е, ast.IfExp):
            а, б = self.оцінка(е.body, env, м), self.оцінка(е.orelse, env, м)
            return а[0] or б[0], а[1] or б[1]
        if isinstance(е, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            г = е.generators[0]
            r, e = self.оцінка(г.iter, env, м)
            return r, r and (e or any(x.ifs for x in е.generators))
        if isinstance(е, ast.Dict):
            r = any(к is None and self.оцінка(в, env, м)[0] for к, в in zip(е.keys, е.values))
            return r, False
        if isinstance(е, ast.Call):
            ім = ім_виклику(е)
            if isinstance(е.func, ast.Attribute) and ім in МЕТОДИ_СИРОГО:
                if е.args and isinstance(е.args[0], ast.Constant) and е.args[0].value in ПРОТОКОЛ:
                    return False, False
                r = self.оцінка(е.func.value, env, м)[0]
                return r, r
            перший = е.args[0] if е.args else None
            if ім in ("loads",) and перший is not None:
                return self.оцінка(перший, env, м)[0], True
            if ім in ПРОХІДНІ and isinstance(е.func, ast.Name) and перший is not None:
                return self.оцінка(перший, env, м)
            ц = розв(self.модулі, м, е)
            if ц in self.шлях:
                return tuple(self.пов[ц])
        return False, False

    def середовище(self, к):
        м = self.модулі[к[0]]
        ф = м.функції[к[1]]
        с = {п for п in параметри(ф) if self.пар[(к, п)][0]}
        п_ = {п for п in параметри(ф) if self.пар[(к, п)][1]}
        в = set()
        env = (с, п_, в)
        while True:
            до = (len(с), len(п_), len(в))
            for n in ast.walk(ф):
                пари = []
                if isinstance(n, ast.Assign):
                    пари = [(т, n.value) for т in n.targets]
                elif isinstance(n, (ast.AnnAssign, ast.NamedExpr)) and n.value is not None:
                    пари = [(n.target, n.value)]
                elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
                    r, _ = self.оцінка(n.iter, env, м)
                    if r:
                        for ім in цілі(n.target):
                            с.add(ім)
                            п_.add(ім)
                for т, з in пари:
                    r, e = self.оцінка(з, env, м)
                    for ім in цілі(т):
                        if r:
                            с.add(ім)
                        if r and e:
                            п_.add(ім)
                        if відсутність(з, env):
                            в.add(ім)
            if (len(с), len(п_), len(в)) == до:
                return env

    def _крок(self):
        зміна = False
        for к in self.шлях:
            м = self.модулі[к[0]]
            env = self.середовище(к)
            self.сер[к] = env
            for n in власні(м.функції[к[1]]):
                if isinstance(n, ast.Return) and n.value is not None:
                    r, e = self.оцінка(n.value, env, м)
                    ст = self.пов[к]
                    if (r and not ст[0]) or (r and e and not ст[1]):
                        ст[0] = ст[0] or r
                        ст[1] = ст[1] or (r and e)
                        зміна = True
            for n in ast.walk(м.функції[к[1]]):
                if not isinstance(n, ast.Call):
                    continue
                ц = розв(self.модулі, м, n)
                if ц not in self.шлях:
                    continue
                пп = параметри(self.модулі[ц[0]].функції[ц[1]])
                пари = list(zip(пп, n.args)) + [(кв.arg, кв.value) for кв in n.keywords if кв.arg]
                for пім, арг in пари:
                    if isinstance(арг, ast.Starred):
                        continue
                    r, e = self.оцінка(арг, env, м)
                    ст = self.пар[(ц, пім)]
                    if (r and not ст[0]) or (r and e and not ст[1]):
                        ст[0] = ст[0] or r
                        ст[1] = ст[1] or (r and e)
                        зміна = True
        return зміна


def власні(ф):
    """Вузли функції без вкладених функцій."""
    стек = list(ast.iter_child_nodes(ф))
    while стек:
        n = стек.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            стек.extend(ast.iter_child_nodes(n))


def _порожнє(в):
    return isinstance(в, ast.Constant) and в.value in (None, "")


def відсутність(е, env):
    """Умова «її даного нема»: `x in (None, "")`, `x is None`, `not x`, `"k" not in x` на сирому, чи ім'я з такої."""
    с, _п, в = env
    def сир(x):
        return isinstance(x, ast.Name) and x.id in с or (isinstance(x, (ast.Subscript, ast.Call)) and any(
            isinstance(y, ast.Name) and y.id in с for y in ast.walk(x)) and not (isinstance(x, ast.Call) and not (
                isinstance(x.func, ast.Attribute) and x.func.attr in МЕТОДИ_СИРОГО)))
    for n in ast.walk(е):
        if isinstance(n, ast.Name) and n.id in в:
            return True
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not) and сир(n.operand):
            return True
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            оп, пр = n.ops[0], n.comparators[0]
            if isinstance(оп, ast.In) and сир(n.left) and isinstance(пр, (ast.Tuple, ast.List, ast.Set)) \
                    and any(_порожнє(x) for x in пр.elts):
                return True
            if isinstance(оп, (ast.Is, ast.Eq)) and сир(n.left) and _порожнє(пр):
                return True
            if isinstance(оп, ast.NotIn) and сир(пр):
                return True
    return False


# ─────────────────────────── сторожі ───────────────────────────
def походження(ф):
    """Ім'я → вирази, з яких його збудовано у функції (присвоєння, ціль циклу чи генератора — його ітерований)."""
    вих = collections.defaultdict(list)
    for n in ast.walk(ф):
        if isinstance(n, ast.Assign):
            for т in n.targets:
                for ім in цілі(т):
                    вих[ім].append(n.value)
        elif isinstance(n, (ast.AnnAssign, ast.NamedExpr)) and n.value is not None:
            for ім in цілі(n.target):
                вих[ім].append(n.value)
        elif isinstance(n, (ast.For, ast.AsyncFor, ast.comprehension)):
            for ім in цілі(n.target):
                вих[ім].append(n.iter)
    return вих


def згадує(вузол, мітка, пох=None, м=None, глиб=2):
    """Умова згадує ключ (`("k", K)`) чи ім'я (`("n", N)`): прямо, через ім'я, збудоване з виразу з ключем, чи через
    сталу модуля-кортеж із ключем."""
    вид, зн = мітка
    for n in ast.walk(вузол):
        if вид == "k" and isinstance(n, ast.Constant) and n.value == зн:
            return True
        if вид == "n" and isinstance(n, ast.Name) and n.id == зн:
            return True
        if вид == "k" and isinstance(n, ast.Name) and глиб > 0:
            if пох is not None and any(згадує(в, мітка, пох, м, глиб - 1) for в in пох.get(n.id, ())):
                return True
            ст = м.сталі.get(n.id) if м is not None else None
            if isinstance(ст, (ast.Tuple, ast.List, ast.Set)) and any(
                    isinstance(е, ast.Constant) and е.value == зн for е in ст.elts):
                return True
    return False


def виходить(тіло):
    return any(isinstance(n, (ast.Return, ast.Raise, ast.Continue, ast.Break)) for с in тіло for n in ast.walk(с))


def присвоює(тіло, ім):
    return any(isinstance(n, ast.Name) and n.id == ім and isinstance(n.ctx, ast.Store) for с in тіло for n in ast.walk(с))


def пише_ключ(с, база, ключ):
    return any(isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store) and isinstance(n.value, ast.Name)
               and n.value.id == база and isinstance(n.slice, ast.Constant) and n.slice.value == ключ
               for n in ast.walk(с))


def умови(ф):
    for n in ast.walk(ф):
        if isinstance(n, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            yield n.test
        elif isinstance(n, ast.comprehension):
            yield from n.ifs
        elif isinstance(n, ast.BoolOp):
            yield from n.values


def охоронено(м, ф, вузол, мітки, викликачі_ф, база=None):
    """Чи місце під сторожем: ключ чи ім'я в умові над ним, вихід вище в блоці, `try`, запис того самого ключа вище,
    фільтр ітерованого, з якого взято базу, чи умова функції, що кличе цю."""
    пох = походження(ф)
    мітки = list(мітки) + ([("n", база)] if база else [])
    ключі = [мт for мт in мітки if мт[0] == "k"]

    def зг(у):
        return any(згадує(у, мт, пох, м) for мт in мітки)
    cur = вузол
    while cur is not ф and cur in м.батьки:
        p = м.батьки[cur]
        if isinstance(p, (ast.If, ast.While, ast.IfExp)) and cur is not p.test and зг(p.test):
            return True
        if isinstance(p, ast.BoolOp) and cur in p.values and any(зг(в) for в in p.values[:p.values.index(cur)]):
            return True
        if isinstance(p, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)) and cur not in p.generators:
            if any(зг(і) for г in p.generators for і in г.ifs):
                return True
        if isinstance(p, ast.Try) and cur in p.body and p.handlers:
            return True
        for поле in ("body", "orelse", "finalbody"):
            бл = getattr(p, поле, None)
            if isinstance(бл, list) and cur in бл:
                for попер in бл[:бл.index(cur)]:
                    if isinstance(попер, ast.If) and зг(попер.test):
                        if виходить(попер.body) or any(вид == "n" and присвоює(попер.body, зн) for вид, зн in мітки):
                            return True
                    if база and any(пише_ключ(попер, база, к) for _в, к in ключі):
                        return True
        cur = p
    # база — ціль циклу чи генератора: фільтр її ітерованого (`[р for р in … if р.get("ід")]`) — сторож
    if база:
        for в in пох.get(база, ()):
            for ім in [в.id] if isinstance(в, ast.Name) else []:
                for вв in пох.get(ім, ()):
                    for n in ast.walk(вв):
                        if isinstance(n, ast.comprehension) and any(згадує(і, мт) for і in n.ifs for мт in ключі):
                            return True
    return bool(ключі) and any(згадує(у, мт) for в in викликачі_ф for у in умови(в) for мт in ключі)


# ─────────────────────────── правила ───────────────────────────
def рядок_тексту(е):
    """Рядкова стала чи склейка сталих `+` → текст; інакше None."""
    if isinstance(е, ast.Constant) and isinstance(е.value, str):
        return е.value
    if isinstance(е, ast.BinOp) and isinstance(е.op, ast.Add):
        а, б = рядок_тексту(е.left), рядок_тексту(е.right)
        return а + б if а is not None and б is not None else None
    return None


def оголошення(модулі, м, ф):
    """Виклики `Оголошення(...)` у тілі функції шляху та в сталих модуля, які вона називає."""
    вих = []
    for n in ast.walk(ф):
        if isinstance(n, ast.Call) and ім_виклику(n) == "Оголошення":
            вих.append((м, n))
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in м.сталі:
            з = м.сталі[n.id]
            if isinstance(з, ast.Call) and ім_виклику(з) == "Оголошення":
                вих.append((м, з))
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and м.модулі.get(n.value.id) in модулі:
            мм = модулі[м.модулі[n.value.id]]
            з = мм.сталі.get(n.attr)
            if isinstance(з, ast.Call) and ім_виклику(з) == "Оголошення":
                вих.append((мм, з))
    return вих


def тексти_функції(модулі, м, ф):
    """(модуль, вузол) рядкових сталих і склейок `+`: у власних вузлах функції без докстрінга й у сталих модуля, які
    вона називає (`ІМЯ`, `модуль.ІМЯ`), до двох кроків називання."""
    док = ф.body[0].value if ф.body and isinstance(ф.body[0], ast.Expr) and isinstance(ф.body[0].value, ast.Constant) \
        else None
    вих, черга, бачені = [], [(м, n) for n in власні(ф) if n is not док], set()
    for глиб in range(3):
        далі = []
        for мм, n in черга:
            if isinstance(n, ast.BinOp) and рядок_тексту(n) is not None or \
                    isinstance(n, ast.Constant) and isinstance(n.value, str):
                вих.append((мм, n))
            ст = None
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in мм.сталі:
                ст = (мм, мм.сталі[n.id])
            elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and мм.модулі.get(n.value.id) in модулі:
                ін = модулі[мм.модулі[n.value.id]]
                if n.attr in ін.сталі:
                    ст = (ін, ін.сталі[n.attr])
            if ст and глиб < 2 and id(ст[1]) not in бачені:
                бачені.add(id(ст[1]))
                далі.extend((ст[0], x) for x in ast.walk(ст[1]))
        черга = далі
    return вих


def про_питання(м, е, т):
    """Текст — правило відповіді на ЇЇ ПИТАННЯ: сам називає питання (`question`) чи стоїть в `Оголошення`, що має його
    на вході. Не так — інша репліка (підтвердження паспорта «what you understood or what you ask»), не відповідь про річ."""
    if ПИТАННЯ_EN.search(т):
        return True
    cur = е
    while cur in м.батьки:
        cur = м.батьки[cur]
        if isinstance(cur, ast.Call) and ім_виклику(cur) == "Оголошення":
            return any(isinstance(x, ast.Constant) and isinstance(x.value, str) and ПИТАННЯ_EN.search(x.value)
                       for x in ast.walk(cur))
    return False


def правила_промпту(виклик):
    for кв in виклик.keywords:
        if кв.arg == "правила" and isinstance(кв.value, (ast.Tuple, ast.List)):
            for е in кв.value.elts:
                т = рядок_тексту(е)
                if т is not None:
                    yield е, т


def заява(n):
    return isinstance(n, ast.Call) and ім_виклику(n) == "заява"


def диз(т):
    return list(т.values) if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.Or) else [т]


class Підстановка(ast.NodeTransformer):
    def __init__(self, мапа):
        self.мапа = мапа

    def visit_Name(self, n):
        return copy.deepcopy(self.мапа[n.id]) if n.id in self.мапа else n


def умови_заяв(модулі, м, ф, шлях_):
    """Тексти умов (`ast.unparse`), під якими функція (і будівник повідомлення, якому вона передає умову) кладе
    заяву жінці: тест `if`/`IfExp` над викликом `заява(...)` і кожен його диз'юнкт."""
    вих = set()

    def з_функції(мод, фн, мапа):
        for n in ast.walk(фн):
            if not isinstance(n, (ast.If, ast.IfExp)):
                continue
            тіло = n.body if isinstance(n, ast.If) else [n.body]
            if any(заява(x) for с_ in тіло for x in ast.walk(с_)):
                for д in диз(n.test):
                    вих.add(ast.unparse(Підстановка(мапа).visit(copy.deepcopy(д))))
    з_функції(м, ф, {})
    for n in ast.walk(ф):
        if isinstance(n, ast.Call):
            ц = розв(модулі, м, n)
            if ц in шлях_ and ц != (м.ім, ф.name):
                фц = модулі[ц[0]].функції[ц[1]]
                пп = параметри(фц)
                мапа = dict(zip(пп, n.args))
                мапа.update({кв.arg: кв.value for кв in n.keywords if кв.arg})
                if any(заява(x) for x in ast.walk(фц)):
                    з_функції(модулі[ц[0]], фц, мапа)
    return вих


def судді(модулі, шлях_):
    """Функції шляху з переліком пропусків `без_входу` і повідомленням їй (виклик `…повідомлення…`)."""
    вих = []
    for к in sorted(шлях_):
        ф = модулі[к[0]].функції[к[1]]
        пропуск = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "append"
                      and isinstance(n.func.value, ast.Name) and n.func.value.id == СПИСОК_ПРОПУСКІВ for n in ast.walk(ф))
        пов = any(isinstance(n, ast.Call) and "повідомлення" in (ім_виклику(n) or "") for n in ast.walk(ф))
        if пропуск and пов:
            вих.append(к)
    return вих


def ключі_читання(ф, змінна):
    """Ключі, які функція читає з `змінна` (`.get("k")`, `["k"]`)."""
    вих = set()
    for n in ast.walk(ф):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == змінна and n.args \
                and isinstance(n.args[0], ast.Constant):
            вих.add(n.args[0].value)
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == змінна \
                and isinstance(n.slice, ast.Constant):
            вих.add(n.slice.value)
    return вих


def блок_містить(м, вузол):
    """(If-батько, перелік операторів), у якому стоїть оператор із вузлом."""
    cur = вузол
    while cur in м.батьки:
        p = м.батьки[cur]
        if isinstance(cur, ast.stmt):
            for поле in ("body", "orelse"):
                бл = getattr(p, поле, None)
                if isinstance(бл, list) and cur in бл:
                    return p, бл, cur
        cur = p
    return None, None, None


def _аргумент(т, і):
    """Текст аргументів виклику від позиції після імені до парної дужки."""
    г, j = 1, і
    while г and j < len(т):
        г += {"(": 1, ")": -1}.get(т[j], 0)
        j += 1
    return т[і:j - 1]


def входи_показу(корінь, модулі):
    """Входи шляху — з викликів показу до моста, а не переліком: ендпойнт, якому `показ/*.js` передає її фото
    (`містП('ім', {…})` з ключем `КЛЮЧІ_ФОТО`), і ендпойнт файлу показу, що несе промпт, зібраний із продукту під час
    збірки (`ЗБІРКА`: заповнювач `__…__` ← виклик `модуль.функція()`; її кольори з портрета), разом із тим викликом.
    Ім'я ендпойнта → функція — за диспетчером `МІСТ.виклик`. → (входи, імена ендпойнтів для показу)."""
    б = модулі.get(МІСТ)
    мапа = {}
    if б is not None and "виклик" in б.функції:
        for n in ast.walk(б.функції["виклик"]):
            if isinstance(n, ast.Dict):
                for к, в in zip(n.keys, n.values):
                    if isinstance(к, ast.Constant) and isinstance(в, ast.Name):
                        ц = б.імена.get(в.id) or ((МІСТ, в.id) if в.id in б.функції else None)
                        if ц:
                            мапа[к.value] = ц
    if not мапа:
        _ОБ.непрочитано("джерела/%s.py" % МІСТ, "диспетчер ендпойнтів `виклик` не знайдено")
    файли = {}
    for ш in sorted(glob.glob(os.path.join(корінь, "джерела", "показ", "*.js"))):
        with open(ш, encoding="utf-8") as ф:
            файли[ш] = ф.read()
    ендпойнти, входи = set(), []
    ключ = re.compile(r"(?<![\wА-ЯІЇЄҐа-яіїєґ.])(%s)\b(?=\s*[:,}])" % "|".join(КЛЮЧІ_ФОТО))
    for т in файли.values():
        for мт in re.finditer(r"містП\(\s*'([^']+)'", т):
            if ключ.search(_аргумент(т, мт.end())):
                ендпойнти.add(мт.group(1))
    # промпт збірки: заповнювач у показі ← функція збірки, що кличе `модуль.функція(` продукту
    збірка = os.path.join(корінь, "джерела", ЗБІРКА)
    if os.path.exists(збірка):
        with open(збірка, encoding="utf-8") as ф:
            тз = ф.read()
        for мт in re.finditer(r'\.replace\("(__[^"]+__)",\s*(\w+)\(', тз):
            заповнювач, фн = мт.groups()
            тіло = re.search(r"def %s\(.*?(?=\ndef |\Z)" % re.escape(фн), тз, re.S)
            for т in файли.values():
                if заповнювач in т and тіло:
                    for мм, фф in re.findall(r"([^\W\d]\w*)\.([^\W\d]\w*)\(\)", тіло.group(0)):
                        if мм in модулі and фф in модулі[мм].функції:
                            входи.append((мм, фф))
                            ендпойнти |= set(re.findall(r"містП\(\s*'([^']+)'", т))
    for е in sorted(ендпойнти):
        if е in мапа and мапа[е] not in входи:
            входи.append(мапа[е])
    if not входи:
        _ОБ.непрочитано("джерела/показ", "жодного виклику моста з її фото не знайдено")
    return tuple(sorted(set(входи))), ендпойнти


def лічба(корінь=ТУТ, входи=None):
    модулі = завантажити(корінь)
    if входи is None:
        входи, ендпойнти = входи_показу(корінь, модулі)
    else:
        ендпойнти = {"річ_з_фото"}
    шлях_, викликачі = шлях(модулі, входи)
    сир = Сирість(модулі, шлях_, входи)
    місця, місця_а6 = [], []

    def до(м, n, клас, правило, чому):
        місця.append(Місце(м.шлях, n.lineno, клас, правило, чому))

    for к in sorted(шлях_):
        м = модулі[к[0]]
        ф = м.функції[к[1]]
        env = сир.сер.get(к) or (set(), set(), set())
        с, п_, _в = env
        вф = [модулі[в[0]].функції[в[1]] for в in викликачі.get(к, ())]
        for n in власні(ф):
            # а1: сирий["ключ"] / сирий[0] без сторожа
            if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Load) and isinstance(n.slice, ast.Constant):
                r, e = сир.оцінка(n.value, env, м)
                ключ = n.slice.value
                база = n.value.id if isinstance(n.value, ast.Name) else None
                # база — виклик функції шляху, що сама знає ключ (перевіряє, будує чи називає його у винятку)
                ц_ = розв(модулі, м, n.value) if isinstance(n.value, ast.Call) else None
                знає = ц_ in шлях_ and any(isinstance(x, ast.Constant) and x.value == ключ
                                           for x in ast.walk(модулі[ц_[0]].функції[ц_[1]]))
                if r and isinstance(ключ, str) and not знає:
                    if not охоронено(м, ф, n, [("k", ключ)], вф, база):
                        до(м, n, "а", "а1", "її вхід `%s[%r]` без сторожа — KeyError замість назви, чого бракує (%s)"
                           % (ast.unparse(n.value), ключ, к[1]))
            # а2: зведення можливо порожнього
            if isinstance(n, ast.Call) and n.args:
                ім = ім_виклику(n)
                арг = n.args[0]
                зв = ім in ЗВЕДЕННЯ or (ім in ("min", "max") and len(n.args) == 1 and not any(
                    кв.arg == "default" for кв in n.keywords)) or (ім == "next" and len(n.args) == 1)
                if зв:
                    r, e = сир.оцінка(арг, env, м)
                    if r and e:
                        джерело = арг.generators[0].iter if isinstance(арг, (ast.ListComp, ast.GeneratorExp)) else арг
                        мт = [("n", джерело.id)] if isinstance(джерело, ast.Name) else []
                        if not мт or not охоронено(м, ф, n, мт, []):
                            до(м, n, "а", "а2", "`%s` над можливо порожнім її входом — виняток замість назви, чого "
                               "бракує (%s)" % (ім, к[1]))
            # а3: raise під умовою відсутності її даного
            if isinstance(n, ast.Raise):
                cur = n
                while cur is not ф and cur in м.батьки:
                    p = м.батьки[cur]
                    if isinstance(p, ast.If) and cur is not p.test and відсутність(p.test, env):
                        до(м, n, "а", "а3", "виняток на відсутньому її даному (`%s`) — жінці йде службовий рядок (%s)"
                           % (ast.unparse(p.test)[:70], к[1]))
                        break
                    cur = p
            # а6: причина її речі за умовою на даному, якого суд речі не читає
            if isinstance(n, ast.Assign):
                for т in n.targets:
                    для_цілі = т.elts if isinstance(т, ast.Tuple) else [т]
                    for ц in для_цілі:
                        if isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant) \
                                and ц.slice.value == ПОЛЕ_ПРИЧИНИ:
                            місця_а6.append((м, ф, к, n, ц))
    # а4: правила промптів шляху
    бачені_оголошення = set()
    for к in sorted(шлях_):
        м = модулі[к[0]]
        for мм, ог in оголошення(модулі, м, м.функції[к[1]]):
            if id(ог) in бачені_оголошення:
                continue
            бачені_оголошення.add(id(ог))
            for е, т in правила_промпту(ог):
                if ВІДМОВА.search(т):
                    до(мм, е, "а", "а4", "правило промпту на формі фото вимагає порожнього виходу «лише причина» "
                       "замість того, що видно, і назви того, чого ні: «%s…»" % т[:60])
    # б3: правило довжини відповіді будь-де на шляху — текст у тілі функції шляху (без докстрінга) чи в сталій модуля,
    # яку вона називає (і сталих, які називає та стала: правила, поле промпту, `наприкінці`)
    бачені_тексти = set()
    for к in sorted(шлях_):
        м = модулі[к[0]]
        for мм, е in тексти_функції(модулі, м, м.функції[к[1]]):
            if (мм.шлях, id(е)) in бачені_тексти:
                continue
            бачені_тексти.add((мм.шлях, id(е)))
            т = рядок_тексту(е)
            if т is not None and РЕЧЕННЯ.search(т) and про_питання(мм, е, т):
                до(мм, е, "б", "б3", "правило промпту обрізає слова про її річ числом речень: «%s»"
                   % РЕЧЕННЯ.search(т).group(0))
    # судді речі: б1, б2, а6
    сд = судді(модулі, шлях_)
    читає_суддя, причини_судді = set(), set()
    for к in сд:
        м = модулі[к[0]]
        ф = м.функції[к[1]]
        пп = параметри(ф)
        річ = пп[0] if пп else None
        читає_суддя |= ключі_читання(ф, річ)
        # поле-причина, яке суддя кладе заявою жінці
        for n in ast.walk(ф):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.IfExp):
                for x in ast.walk(n.value):
                    if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == "get" \
                            and x.args and isinstance(x.args[0], ast.Constant):
                        причини_судді.add(x.args[0].value)
        заяви = умови_заяв(модулі, м, ф, шлях_)
        # змінні, які суд читає в умовах (вхід суду, що ставить блок-застереження)
        в_умовах = {x.id for у in умови(ф) for x in ast.walk(у) if isinstance(x, ast.Name)}
        for n in ast.walk(ф):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "append"
                    and isinstance(n.func.value, ast.Name) and n.func.value.id == СПИСОК_ПРОПУСКІВ):
                continue
            if_, бл, ст = блок_містить(м, n)
            if бл is not None and any(заява(x) for с_ in бл for x in ast.walk(с_)):
                continue
            if бл is not None and any(isinstance(с_, ast.Assign) and not isinstance(с_.value, ast.Constant) and any(
                    ім in в_умовах for т in с_.targets for ім in цілі(т)) for с_ in бл):
                continue      # застереження: блок сам дає вхід суду далі — вісь суджено
            тест = if_.test if isinstance(if_, ast.If) and бл is if_.body else None
            if тест is not None and any(ast.unparse(д) in заяви for д in диз(тест)):
                continue
            if тест is not None and ast.unparse(тест) in заяви:
                continue
            текст = рядок_тексту(n.args[0]) if n.args else None
            if текст is None and n.args and isinstance(n.args[0], (ast.BinOp, ast.JoinedStr)):
                текст = "".join(x.value for x in ast.walk(n.args[0]) if isinstance(x, ast.Constant) and isinstance(x.value, str))
            if текст is None and n.args and isinstance(n.args[0], ast.BinOp) is False:
                текст = ast.unparse(n.args[0])
            вісь = (текст or "?").split(":")[0].strip("%s «» ")
            до(м, n, "б", "б1", "суддя речі (%s) пропускає вісь «%s» і жінці цього не каже: «%s»"
               % (к[1], вісь, (текст or "")[:70]))
        # б2: ознаки опису, яких суддя не читає, а суддя образу читає
        опис = None
        for мм in модулі.values():
            if ОПИС_ОЗНАК in мм.сталі:
                опис = мм.сталі[ОПИС_ОЗНАК]
        зап = None
        for мм in модулі.values():
            if ЗАПИС_РЕЧІ in мм.функції:
                зап = мм.функції[ЗАПИС_РЕЧІ]
        if опис is None or зап is None:
            _ОБ.непрочитано("джерела", "вузол класу б2 не знайдено: %s" % (ОПИС_ОЗНАК if опис is None else ЗАПИС_РЕЧІ))
            continue
        ознаки = [ast.literal_eval(е)[1] for е in опис.elts]
        мапа = запис_ознак(зап)
        чит_суддів = судді_ключів(модулі, set(сд))
        for озн in ознаки:
            if озн in читає_суддя:
                continue
            суди = sorted({с_ for кл in мапа.get(озн, ()) for с_ in чит_суддів.get(кл, ())})
            if суди:
                до(м, ф, "б", "б2", "ознаку «%s» опис речі записує, суддя образу читає (%s → %s), а суддя речі (%s) "
                   "не судить і не називає" % (озн, озн, ", ".join(sorted(мапа[озн])), к[1]))
    # а6 — після того, як відомо, що суддя читає
    for м, ф, к, n, ц in місця_а6:
        if ПОЛЕ_ПРИЧИНИ not in причини_судді:
            continue
        тест = None
        cur = n
        while cur is not ф and cur in м.батьки:
            p = м.батьки[cur]
            if isinstance(p, ast.If) and cur is not p.test:
                тест = p.test
                break
            cur = p
        if тест is None:
            continue
        змінна = ц.value.id if isinstance(ц.value, ast.Name) else None
        свої = {змінна}
        for x in ast.walk(ф):
            if isinstance(x, ast.Assign) and any(isinstance(y, ast.Call) and isinstance(y.func, ast.Attribute)
                                                 and y.func.attr == "get" and isinstance(y.func.value, ast.Name)
                                                 and y.func.value.id == змінна and y.args
                                                 and isinstance(y.args[0], ast.Constant)
                                                 and y.args[0].value in читає_суддя for y in ast.walk(x.value)):
                свої |= {ім for т in x.targets for ім in цілі(т)}
        ключі = {y.args[0].value for y in ast.walk(тест) if isinstance(y, ast.Call) and isinstance(y.func, ast.Attribute)
                 and y.func.attr == "get" and y.args and isinstance(y.args[0], ast.Constant)}
        викл = {ім_виклику(y) for y in ast.walk(тест) if isinstance(y, ast.Call)}
        чужі = sorted({y.id for y in ast.walk(тест) if isinstance(y, ast.Name) and y.id not in свої and y.id not in викл}
                      | (ключі - читає_суддя - ЇЇ_РУКА))
        if чужі:
            до(м, n, "а", "а6", "причина її речі (%s) — за умовою на даному, якого суд речі не читає (%s): «%s»"
               % (ПОЛЕ_ПРИЧИНИ, ", ".join(чужі), ast.unparse(n.value)[:60]))
    місця.extend(js_місця(корінь, ендпойнти))
    унікальні = {}
    for м_ in місця:
        унікальні.setdefault((м_.файл, м_.рядок, м_.правило, м_.чому), м_)
    return sorted(унікальні.values(), key=lambda x: (x.файл, x.рядок, x.правило)), (len(шлях_), tuple(входи))



def запис_ознак(ф):
    """Ознака речі → ключі запису для суддів образу (`з["k"] = …річ["o"]…`, `з.update(k=…)`, `dict(k=…)`)."""
    пп = параметри(ф)
    річ = пп[0] if пп else None
    мапа = collections.defaultdict(set)

    def ознаки_в(е):
        return ключі_читання(ast.Module(body=[ast.Expr(е)], type_ignores=[]), річ)
    for n in ast.walk(ф):
        if isinstance(n, ast.Assign):
            for т in n.targets:
                if isinstance(т, ast.Subscript) and isinstance(т.slice, ast.Constant):
                    for о in ознаки_в(n.value):
                        мапа[о].add(т.slice.value)
                if isinstance(т, ast.Name) and isinstance(n.value, ast.Call) and ім_виклику(n.value) == "dict":
                    for кв in n.value.keywords:
                        if кв.arg:
                            for о in ознаки_в(кв.value):
                                мапа[о].add(кв.arg)
        if isinstance(n, ast.Call) and ім_виклику(n) == "update":
            for кв in n.keywords:
                if кв.arg:
                    for о in ознаки_в(кв.value):
                        мапа[о].add(кв.arg)
    # умова `if річ.get("o"): з["k"] = …` — ознака о дає ключ k
    for n in ast.walk(ф):
        if isinstance(n, ast.If):
            оо = ключі_читання(ast.Module(body=[ast.Expr(n.test)], type_ignores=[]), річ)
            for с_ in n.body:
                for x in ast.walk(с_):
                    if isinstance(x, ast.Subscript) and isinstance(x.ctx, ast.Store) and isinstance(x.slice, ast.Constant):
                        for о in оо:
                            мапа[о].add(x.slice.value)
    return мапа


def судді_ключів(модулі, крім):
    """Ключ запису → функції продукту, що його читають і судять (`зн(…)` чи `заява(…)`), крім судді речі."""
    вих = collections.defaultdict(set)
    for м in модулі.values():
        for ім, ф in м.функції.items():
            if (м.ім, ім) in крім:
                continue
            if not any(isinstance(n, ast.Call) and ім_виклику(n) in ("зн", "заява") for n in ast.walk(ф)):
                continue
            for n in ast.walk(ф):
                к = None
                if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant) and isinstance(n.ctx, ast.Load):
                    к = n.slice.value
                elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args \
                        and isinstance(n.args[0], ast.Constant):
                    к = n.args[0].value
                if isinstance(к, str):
                    вих[к].add("%s.%s" % (м.ім, ім))
    return вих


# ─────────────────────────── показ ───────────────────────────
def js_функції(рядки):
    """{ім'я: (перший, останній індекс рядка)} функцій верхнього рівня: `function ім(` з нульового стовпця до `}` там само."""
    вих, ім, поч = {}, None, None
    for і, р in enumerate(рядки):
        мт = re.match(r"(?:async\s+)?function\s+([^\s(]+)\s*\(", р)
        if мт:
            ім, поч = мт.group(1), і
        elif ім and р.startswith("}"):
            вих[ім] = (поч, і)
            ім = None
    return вих


def js_місця(корінь, ендпойнти):
    """а5: споживач результату моста речі (`збої`) — збій кроку жінці сталим рядком без причини чи лише в запис ходу.
    Функції показу, що кличуть міст `річ_з_фото` і збирають `збої` (технічні рядки для звіту власника, `збої.push`),
    — не місця; місце — рядок споживача, де `збої` не йдуть словами їй із причиною (`повідомленнямП`, `мовоюП`,
    `текстЖінціП`)."""
    файли = {}
    for ш in sorted(glob.glob(os.path.join(корінь, "джерела", "показ", "*.js"))):
        with open(ш, encoding="utf-8") as ф:
            рядки = ф.read().split("\n")
        файли[ш] = (рядки, js_функції(рядки))
    міст = set()
    for ш, (рядки, фн) in файли.items():
        for ім, (а, б) in фн.items():
            тіло = "\n".join(рядки[а:б + 1])
            if any(re.search(r"містП\(\s*'%s'" % re.escape(е), тіло) for е in ендпойнти) and "збої" in тіло:
                міст.add(ім)
    місця = []
    for ш, (рядки, фн) in файли.items():
        for ім, (а, б) in sorted(фн.items()):
            if ім in міст or not any(re.search(r"\b%s\s*\(" % re.escape(м), р) for р in рядки[а:б + 1] for м in міст):
                continue
            їй, запис = [], []
            for і in range(а, б + 1):
                р = рядки[і]
                с = р.strip()
                if с.startswith(("//", "/*", "*")) or not re.search(r"\.збої\b", р):
                    continue
                if re.search(r"(повідомленнямП|мовоюП|текстЖінціП)\([^)]*збої", р):
                    їй.append(None)       # збій іде словами їй разом із причиною — не місце
                    continue
                (їй if JS_ТЕКСТ.search(р) else запис).append(і)
            # рядки запису ходу — для звіту власника; місце — те, що чує вона: сталий рядок чи, коли його нема, тиша
            for і in [x for x in їй if x is not None] or ([] if їй else запис[:1]):
                т = JS_ТЕКСТ.search(рядки[і])
                чому = ("жінці сталий рядок без причини: %s" % т.group(0)[:40]) if т else "жінці нічого — лише в запис ходу"
                місця.append(Місце(os.path.relpath(ш, корінь), і + 1, "а", "а5",
                                   "показ (%s): збій кроку речі — %s" % (ім, чому)))
    return місця


def main():
    ап = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ап.add_argument("--корінь", default=ТУТ)
    а = ап.parse_args()
    місця, (довжина, входи) = лічба(а.корінь)
    for м in місця:
        print("%s:%d · %s · %s · %s" % (м.файл, м.рядок, м.клас, м.правило, м.чому))
    за = collections.Counter(м.правило for м in місця)
    print("шлях: %d функцій від входів %s" % (довжина, ", ".join("%s.%s" % в for в in входи)))
    print("за правилами: " + ", ".join("%s %d" % (к, за[к]) for к in sorted(за)))
    print("клас а: %d, клас б: %d" % (sum(1 for м in місця if м.клас == "а"), sum(1 for м in місця if м.клас == "б")))
    print("місць: %d" % len(місця))
    return 0


if __name__ == "__main__":
    sys.exit(main())
