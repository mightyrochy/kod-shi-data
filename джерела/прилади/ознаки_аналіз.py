"""Міжпроцедурний потік і межа шва для приладу ознак обличчя."""
import ast, collections, functools, glob, os, re, warnings
from ознаки_основа import (
    B, E, K, P, Q, S, _ваги_знахідки, _властивості, _злити_ел, _значення_полів, _рядок, _словесні_пороги,
    _сітка, _текст, _усі, _формульні, _число, _ім_виклику, ВИКЛЮЧЕНО, Модуль, кутові_пари, пари_функції,
    шкали_ваги, поля_підписів
)
from ознаки_стан import Стан

class Аналіз:
    def __init__(self, корінь):
        self.корінь = корінь
        self.модулі = {}
        self.синтетичні, self.тримати = {}, []   # `map(f, xs)` → виклик f(xs[і]); вузли тримаються, щоб id не мінявся
        self.формульні = set()
        self.ваги = _ваги_знахідки(корінь)
        self.готові_поля = self.ваги | _ваги_знахідки(корінь, супровід=True) | {'довіра', 'надійність'}
        self.словесні = set()
        self.сіткові = {}
        self.значення_полів = {}   # модуль → поле → рядки, які літерали словників модуля кладуть у це поле
        for шлях in sorted(glob.glob(os.path.join(корінь, "джерела", "*.py"))):
            ім = os.path.basename(шлях)[:-3]
            if ВИКЛЮЧЕНО.match(ім):
                continue
            with open(шлях, encoding="utf-8") as ф:
                текст = ф.read()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    дерево = ast.parse(текст)
                except SyntaxError:
                    continue
            self.модулі[ім] = Модуль(ім, os.path.relpath(шлях, корінь).replace(os.sep, "/"), дерево)
            self.формульні |= _формульні(дерево)
            self.формульні.update(п for ф in self.модулі[ім].функції.values() for п in ф.предикати_формул)
            self.значення_полів[ім] = _значення_полів(дерево)
        підписи = поля_підписів([м.дерево for м in self.модулі.values()])
        for м in self.модулі.values():
            self.словесні |= _словесні_пороги(м.дерево, підписи)
        self.пам = {}             # (функція, контекст) → мітки повернення
        self.ключі_пов = collections.defaultdict(lambda: collections.defaultdict(frozenset))  # функція → ключ → мітки
        self.глоб = collections.defaultdict(frozenset)                                       # (модуль, ім) → мітки
        self.середовища = collections.defaultdict(dict)                                     # функція → останнє env
        self.місця = {}
        self.змінилось = False
        self.у_роботі = set()
        self.відвідано = set()
        self.зерно = None         # (модуль оголошення, ім оголошення, hex-ключі, форма, читач)
        self.функції_зерна = set()
        self.носії = set()        # ключі входу моста, що несуть hex (з JS)
        self.межа = {}
        self.оголошення = {}      # (модуль, ім) → {поле: (рядок, текст)}
        self.перевірки = {}
        self.звідки, self.поточний = {}, None
        self.кортежі, self.останній_кортеж = {}, None    # (функція, контекст) → мітки елементів повернутого кортежу
        self.ключі_пам, self.останні_ключі = {}, None    # (функція, контекст) → ключ повернутого dict → мітки
        self.виходи_шкал = шкали_ваги(self)
        self.шкали = {ф.повне for м in self.модулі.values() for ф in м.функції.values()
                      if ф.повне in self.виходи_шкал and (None in self.виходи_шкал[ф.повне] or
                         0 in self.виходи_шкал[ф.повне] and not any(isinstance(в, ast.Return) and
                         isinstance(в.value, ast.Tuple) and len(в.value.elts) > 2 for в in ast.walk(ф.вузол)))}
        self.пари = {ф.повне: пари_функції(ф) for м in self.модулі.values() for ф in м.функції.values()}
        self.кутові = {ф.повне: кутові_пари(ф) for м in self.модулі.values() for ф in м.функції.values()}
        self.пара_глибина = 0

    # ── розв'язання імен ──────────────────────────────────────────────
    def у_модулі(self, мод, ім, глибина=0):
        м = self.модулі.get(мод)
        if not м or глибина > 6:
            return None
        if ім in м.функції and "." not in ім:
            return м.функції[ім]
        if ім in м.з_імпортів:
            return self.у_модулі(*м.з_імпортів[ім], глибина=глибина + 1)
        в = м.присвоєння.get(ім)
        if isinstance(в, (ast.Name, ast.Attribute)):
            return self.вираз_функції(м, в, None, глибина + 1)
        for з in м.зірки:
            ф = self.у_модулі(з, ім, глибина + 1)
            if ф:
                return ф
        return None

    @functools.cache
    def вираз_функції(self, м, в, ф, глибина=0):
        if глибина > 6:
            return None
        if isinstance(в, ast.Name):
            о = ф
            while о is not None:
                кандидат = м.функції.get(о.ім + "." + в.id)
                if кандидат:
                    return кандидат
                о = о.батько
            return self.у_модулі(м.ім, в.id, глибина)
        if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name):
            мод = м.імпорти.get(в.value.id)
            if мод is None and в.value.id in м.з_імпортів:
                мм, ім = м.з_імпортів[в.value.id]
                мод = мм + "." + ім if (мм + "." + ім) in self.модулі else (ім if ім in self.модулі else None)
            if мод:
                return self.у_модулі(мод.split(".")[-1], в.attr, глибина)
        return None

    @functools.cache
    def викликані(self, м, в, ф):
        """Вираз виклику → функції продукту (пряма, таблиця функцій, фабрика лямбди, лямбда)."""
        if isinstance(в, ast.Lambda):
            л = м.лямбди.get(id(в))
            return [л] if л else []
        if isinstance(в, ast.Subscript):
            табл = в.value
            if isinstance(табл, ast.Name) and табл.id in м.присвоєння:
                табл = м.присвоєння[табл.id]
            if isinstance(табл, ast.Dict):
                вих = []
                for з in табл.values:
                    вих.extend(self.значення_функції(м, з, ф))
                return вих
            return []
        ц = self.вираз_функції(м, в, ф)
        return [ц] if ц else []

    def значення_функції(self, м, в, ф):
        """Значення таблиці → функції: лямбда, ім'я функції, виклик фабрики (її повернені лямбди й функції)."""
        if isinstance(в, ast.Lambda):
            л = м.лямбди.get(id(в))
            return [л] if л else []
        if isinstance(в, (ast.Name, ast.Attribute)):
            ц = self.вираз_функції(м, в, ф)
            return [ц] if ц else []
        if isinstance(в, ast.Call):
            фабрика = self.вираз_функції(м, в.func, ф)
            if фабрика and isinstance(фабрика.вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
                вих = []
                for n in ast.walk(фабрика.вузол):
                    if isinstance(n, ast.Return) and n.value is not None:
                        вих.extend(self.значення_функції(фабрика.модуль, n.value, фабрика))
                return вих
        return []

    # ── місця ─────────────────────────────────────────────────────────
    def місце(self, м, вузол, пункт, чому, вхід=False):
        if not вхід and пункт in (1, 2) and (self.пара_глибина or
                self.поточний and self.поточний[0] in self.шкали):
            return
        ключ = (м.шлях, вузол.lineno)
        self.місця.setdefault(ключ, set()).add((пункт, чому))

    # ── аналіз функції ────────────────────────────────────────────────
    def будує_сітку(self, ф):
        р = self.сіткові.get(ф.повне)
        if р is None:
            р = self.сіткові[ф.повне] = ф.повертає_сітку or any(_сітка(n) or isinstance(n, ast.Return) and isinstance(n.value, ast.List)
                and any(isinstance(в, ast.BinOp) and isinstance(в.op, ast.Mod) and _число(в.right)
                        and в.right.value == 360 for в in ast.walk(n.value)) for n in ast.walk(ф.вузол))
        return р

    def аналізувати(self, ф, контекст):
        ключ = (ф.повне, контекст)
        if ключ in self.у_роботі or ключ in self.відвідано:
            return self.пам.get(ключ, E)
        self.у_роботі.add(ключ)
        с = Стан(self, ф, контекст)
        попередній, self.поточний = self.поточний, ключ
        с.пари = {id(в) for в, _, _ in self.пари.get(ф.повне, ())}
        с.вхід_пари = False
        пов = с.виконати()
        self.пара_глибина -= с.вхід_пари
        if ф.числовий_пошук and any(K in м or any(K in з for _, з in кл) for _, м, кл in контекст):
            пов = пов | {K}
        if ф.повне in self.виходи_шкал:
            def вага(м):
                """Залишає походження рішення, знімаючи походження сирої ознаки."""
                return (м - {S}) | ({Q} if S in м else set())
            слоти = self.виходи_шкал[ф.повне]
            ціла = ф.повне in self.шкали
            if ціла:
                пов = вага(пов)
            с.ключі_пов = {к: вага(м) if ціла or any(к == '#%s' % і or к.startswith('#%s/' % і)
                           for і in слоти if і is not None) else м for к, м in с.ключі_пов.items()}
            if с.кортеж:
                с.кортеж = [(вага(м), frozenset((к, вага(v)) for к, v in кл)) if ціла or і in слоти else (м, кл)
                             for і, (м, кл) in enumerate(с.кортеж)]
        if self.будує_сітку(ф):
            # функція будує сітку кандидатів у вікні з її значень: повертає кандидатів, а не її значення; вхід її
            # значень у вікно лічиться там, де вікно рахується (рішення менеджера 01.11, кандидат палітри)
            пов = (пов - {S}) | {K}
            с.ключі_пов = {к: (в - {S}) | {K} for к, в in с.ключі_пов.items()}
            if с.кортеж:
                с.кортеж = [((м - {S}) | {K}, frozenset((к, (v - {S}) | {K}) for к, v in кл)) for м, кл in с.кортеж]
        self.поточний = попередній
        self.у_роботі.discard(ключ)
        self.відвідано.add(ключ)
        if с.кортеж:
            було = self.кортежі.get(ключ)
            нове = [_злити_ел(x, y) for x, y in zip(було, с.кортеж)] if було and len(було) == len(с.кортеж) else list(с.кортеж)
            if нове != було:
                self.кортежі[ключ] = нове
                self.змінилось = True
        кп = self.ключі_пам.setdefault(ключ, {})
        загальні = self.ключі_пов[ф.повне]
        for к, в in с.ключі_пов.items():
            if в - кп.get(к, E):
                кп[к] = кп.get(к, E) | в
                self.змінилось = True
            загальні[к] = загальні[к] | в
        старе = self.пам.get(ключ, E)
        if пов - старе:
            self.пам[ключ] = старе | пов
            self.змінилось = True
        стар_env = self.середовища[ф.повне]
        for к, в in с.env.items():
            if в - стар_env.get(к, E):
                стар_env[к] = стар_env.get(к, E) | в
                self.змінилось = True
        return self.пам.get(ключ, E)

    def виклик(self, ф, позиційні, іменні, зірка=E, дві_зірки=E):
        """Аргументи (мітки, ключі dict чи None) → контекст параметрів → (мітки повернення, ключі повернення)."""
        к, км = {}, {}

        def дати(п, значення):
            мітки, ключі = значення if isinstance(значення, tuple) else (значення, None)
            к[п] = к.get(п, E) | мітки
            if ключі:
                ц = км.setdefault(п, {})
                for кл, в in ключі.items():
                    ц[кл] = ц.get(кл, E) | в
        for i, з in enumerate(позиційні):
            if i < len(ф.позиційні):
                дати(ф.позиційні[i], з)
            elif ф.зірка:   # `*а` — ключі за номером, щоб `f(*а)` далі ліг на ті самі параметри
                дати(ф.зірка, з[0] | _усі(з[1]) if isinstance(з, tuple) else з)
                дати("%s#%d" % (ф.зірка, i - len(ф.позиційні)), з)
        for ім, з in іменні.items():
            if ім in ф.позиційні or ім in ф.іменні:
                дати(ім, з)
            elif ф.дві_зірки:   # `**к` — ключ за іменем аргументу
                дати(ф.дві_зірки, (E, {ім: з[0] | _усі(з[1]) if isinstance(з, tuple) else з}))
                дати("%s#%s" % (ф.дві_зірки, ім), з)
        if зірка:
            for п in ф.позиційні + ([ф.зірка] if ф.зірка else []):
                дати(п, зірка)
        if дві_зірки:
            for п in ф.позиційні + ф.іменні + ([ф.дві_зірки] if ф.дві_зірки else []):
                дати(п, дві_зірки)
        контекст = frozenset((п, frozenset(к.get(п, E)), frozenset((кл, frozenset(в)) for кл, в in км.get(п, {}).items()
                                                                  if в))
                             for п in set(к) | set(км) if к.get(п) or any(км.get(п, {}).values()))
        if self.пара_глибина and any(S in м or any(S in з for _, з in кл) for _, м, кл in контекст):
            контекст = контекст | frozenset({("!пара", E, frozenset())})
        if контекст and (ф.повне, контекст) not in self.звідки:
            self.звідки[(ф.повне, контекст)] = self.поточний
        пов = self.аналізувати(ф, контекст)
        self.останній_кортеж = self.кортежі.get((ф.повне, контекст))
        self.останні_ключі = self.ключі_пам.get((ф.повне, контекст)) or None
        return пов

    # ── зерно й межа ──────────────────────────────────────────────────
    def знайти_зерно(self):
        """Оголошення, чий скелет відповіді несе `<hex>`, його hex-поля, форма й читач форми (`схеми_розбору`)."""
        for м in self.модулі.values():
            for ім, в in м.присвоєння.items():
                if not (isinstance(в, ast.Call) and _ім_виклику(в.func) == "Оголошення"):
                    continue
                кв = {к.arg: к.value for к in в.keywords}
                поля = {}
                for п in (кв.get("вхід").elts if isinstance(кв.get("вхід"), ast.Tuple) else []):
                    if isinstance(п, ast.Call) and п.args and isinstance(п.args[0], ast.Constant):
                        тексти = [а.value for а in п.args[1:] if isinstance(а, ast.Constant) and isinstance(а.value, str)]
                        тексти += [к.value.value for к in п.keywords if к.arg in ("що", "як") and
                                   isinstance(к.value, ast.Constant) and isinstance(к.value.value, str)]
                        поля[str(п.args[0].value).split(".")[0]] = (п.lineno, " ".join(тексти))
                self.оголошення[(м.ім, ім)] = поля
                скелет = кв.get("скелет")
                if not isinstance(скелет, ast.Dict):
                    continue
                hexи = [к.value for к, з in zip(скелет.keys, скелет.values) if isinstance(к, ast.Constant)
                        and "<hex>" in _текст(з)]
                if hexи and isinstance(кв.get("вихід"), ast.Constant):
                    self.зерно = dict(модуль=м.ім, ім=ім, ключі=frozenset(hexи), форма=кв["вихід"].value,
                                      рядок=в.lineno)
        if not self.зерно:
            return
        for м in self.модулі.values():
            for n in ast.walk(м.дерево):
                if isinstance(n, ast.Dict):
                    for к, з in zip(n.keys, n.values):
                        if isinstance(к, ast.Constant) and к.value == self.зерно["форма"] and isinstance(з, ast.Call):
                            for кв in з.keywords:
                                if кв.arg == "розбір":
                                    ц = self.вираз_функції(м, кв.value, None)
                                    if ц:
                                        self.зерно["читач"] = ц
        читач = self.зерно.get("читач")
        if читач:
            черга = [читач]
            while черга:
                ф = черга.pop()
                if ф.повне in self.функції_зерна:
                    continue
                self.функції_зерна.add(ф.повне)
                for n in ast.walk(ф.вузол):
                    if isinstance(n, ast.Call):
                        ц = self.вираз_функції(ф.модуль, n.func, ф)
                        if ц and ц.модуль is ф.модуль:
                            черга.append(ц)

    def межа_js(self, поля_читача):
        """Поля відповіді читача → поля `КОЛІР` показу → ключі входу моста, що несуть hex."""
        тексти = {}
        for шлях in sorted(glob.glob(os.path.join(self.корінь, "джерела", "показ", "*.js"))):
            with open(шлях, encoding="utf-8") as ф:
                тексти[os.path.relpath(шлях, self.корінь).replace(os.sep, "/")] = ф.read()
        поля = "|".join(sorted(re.escape(п) for п in поля_читача)) or "^$"
        поля_колір = set()
        for т in тексти.values():
            for м in re.finditer(r"\bКОЛІР\s*=\s*\{(.*?)\};", т, re.S):
                for к, з in _властивості(м.group(1)):
                    if re.search(r"\.(%s)\b" % поля, з):
                        поля_колір.add(к)
        пк = "|".join(sorted(re.escape(п) for п in поля_колір)) or "^$"
        носії, читачі, обчислення = set(), [], []
        for шлях, т in тексти.items():
            аліаси = set(re.findall(r"\b([\wа-яіїєґʼ']+)\s*=\s*[\wа-яіїєґʼ']+\.колір\s*(?:\|\|\s*\{\})?\s*[,;]", т))
            імена = ["КОЛІР"] + sorted(аліаси)
            шаблон = r"\b(?:%s)\.(?:точки\s*\|\|\s*\{\}\)\.)?(?:%s)\b" % ("|".join(map(re.escape, імена)), пк)
            for к, з in _властивості(т):
                if re.match(r"\s*\(?\s*" + шаблон, з):
                    носії.add(к)
            for н, рядок in enumerate(т.splitlines(), 1):
                if re.search(r"\bКОЛІР\.(?:%s)\b" % пк, рядок):
                    читачі.append((шлях, н))
                    без_стрілок = рядок.replace("=>", " ")
                    if re.search(r"\bКОЛІР\.(?:%s)\b[^;]*?(?<![=!<>])[<>](?!=?>)|[-+*/]\s*КОЛІР\.(?:%s)\b|\bКОЛІР\.(?:%s)"
                                 r"(?:\.\w+)?\s*[-+*/](?!/)" % (пк, пк, пк), без_стрілок):
                        обчислення.append((шлях, н, рядок.strip()[:90]))
        self.носії = носії | {п for п in поля_колір if п in носії}
        self.межа = dict(поля_читача=sorted(поля_читача), поля_колір=sorted(поля_колір), носії=sorted(self.носії),
                         читачі=читачі, обчислення=обчислення)
        return обчислення

    def входи_шва(self):
        """Ендпойнти, які кличе шов показу (`bridge.<ім>` у `показ/воркер_міст.js`), і таблиця `bridge.виклик`."""
        шлях = os.path.join(self.корінь, "джерела", "показ", "воркер_міст.js")
        імена = set()
        if os.path.isfile(шлях):
            with open(шлях, encoding="utf-8") as ф:
                імена = set(re.findall(r"\bbridge\.([\wа-яіїєґʼ']+)\s*\(", ф.read()))
        вих = []
        м = self.модулі.get("bridge")
        for ім in sorted(імена):
            ф = self.у_модулі("bridge", ім) if м else None
            if ф:
                вих.append(ф)
        return вих

    def таблиці_причин(self):
        """Таблиці звірки: dict модуля, значення якого — функції, і який кличуть за ключем (`ТАБЛ[к](...)`)."""
        self.перевірки = collections.defaultdict(list)     # функція → [(модуль, рядок рядка таблиці, ключ)]
        for м in self.модулі.values():
            кличуть = {n.func.value.id for n in ast.walk(м.дерево) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Subscript) and isinstance(n.func.value, ast.Name)}
            for ім in кличуть:
                табл = м.присвоєння.get(ім)
                if not isinstance(табл, ast.Dict):
                    continue
                for к, з in zip(табл.keys, табл.values):
                    if not _рядок(к):
                        continue
                    for ц in self.значення_функції(м, з, None):
                        self.перевірки[ц.повне].append((м, к, к.value))

    def прогін(self):
        self.знайти_зерно()
        self.таблиці_причин()
        входи = self.входи_шва()
        for _ in range(12):
            self.змінилось = False
            self.відвідано = set()
            if self.зерно and self.зерно.get("читач"):
                ч = self.зерно["читач"]
                self.виклик(ч, [frozenset({P})] * len(ч.позиційні), {})
                поля = sorted({str(к).split("/")[0] for к, в in self.ключі_пов[ч.повне].items() if S in в})
                if not self.носії:
                    self.межа_js(поля)
            for ф in входи:
                self.виклик(ф, [frozenset({P, B})] * max(1, len(ф.позиційні)), {})
            if not self.змінилось:
                break
