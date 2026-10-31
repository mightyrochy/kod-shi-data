# -*- coding: utf-8 -*-
"""прилади/корінь_е3_поле_без_писача.py — прилад кореня Е3-поле-без-писача (`аудит/корені/Е3-поле-без-писача.md`).

Клас — з паспорта («Клас місць», «Стан і що лишилось»), не перелік прикладів. Місце — точка коду продукту, де рішення
читає вхід про неї чи нагоду (поле паспорта нагоди, сценарію чи профілю), а на шляху продукту цього входу ніхто не
пише: п.1 — писача нема, рішення діє на типовому значенні; п.2 — писач є, але гілка порівнює вхід із літералом, якого
серед значень писача нема. Прилад не править коду й не бере переліку місць руками: читачі й писачі — з AST Python і
тексту показу, потоком значення від межі JS → Python.

ЧИТАЧІ — ПОТІК ВІД ВХОДУ МОСТА (а не ключі `ПОЛЯ_ПАСПОРТА`):
  джерело  — вхід кожного ендпойнта `bridge.виклик` (JSON з показу) і все, що з нього виходить;
  носій    — словник входу: присвоєння, `dict(…)`, `{**…}`, зріз-включення за `.items()` (фільтр `_приймає`),
             `json.loads`, параметр, у який його передано, `**kw`, що його прийняв, повернення функції, ключ
             носія (`d.get("сценарій")`), словник, у який код склав значення з носія (`з_показу` → нагода);
  читач    — `носій.get("к")`, `носій["к"]`, `носій.pop("к")`, `"к" in носій`; параметр функції, не
             зв'язаний у виклику з `**носій` (ключ — ім'я параметра, типове — значення без писача); параметр,
             у який передано значення читача (`к=к`, позиційно); змінна, якій його присвоєно; повернення;
  рішення  — кожне вживання значення читача, крім передачі далі (аргумент функції продукту, присвоєння,
             повернення, словник-аргумент): умова, порівняння, ітерація, арифметика, поле пакета/дроту
             (словник, що йде далі як факт), виклик поза продуктом. Місце — `файл:рядок` рішення.

ПИСАЧІ (ключ має писача, якщо хоч один):
  показ    — ключ об'єкта чи присвоєння властивості в JS показу (`показ/*.js`, `показ.html`, `показ_шаблон.js`):
             поле панелі, сценарій `зібратиВхід`, тіло запиту мосту; поле `ПОЛЯ_ПАСПОРТА[к]["показ"]`, чий ід є
             в `показ.html`;
  паспорт  — ключ словника, який повертає ендпойнт полем «паспорт» (розбір відповіді моделі й код паспорта:
             літерал, `dict(к=…)`, `п["к"] = …`, запис циклом за таблицею модуля — таблицю обчислено імпортом),
             транзитивно через повернення й мутацію параметра;
  код      — запис ключа в носій (`носій["к"] = …`, `setdefault`, `update`, `dict(носій, к=…)`).
  Не писач: копія того самого ключа з носія (`к=носій.get("к")`, `к=к`), стала порожня (`None`, `False`, `0`,
  `""`, `[]`, `{}`), описи (`паспорт_поля.ПОЛЯ_ПАСПОРТА`, `profile.СЦЕНАРІЙ_ПИТАННЯ`, `profile.ПОГОДА_КОНТРАКТ` —
  поза потоком), проби, прилади, тести, стенди й батареї (не в імпортному замиканні продукту чи відкинуті за іменем).

НЕ МІСЦЕ: ключ `суд_чеклісти.ЗОВНІШНІ_ВХОДИ` (чекліст називає «немає входу» сам); рішення у функції, що сама
розрізняє «не передали» (`к is None` у функції, чий текст каже «входу нема» / «немає входу» / «без входу»), — окремий
рядок «сам каже», у `місць` не входить.

П.2 лічиться лише для ключів, чиї значення писача визначено: сталі літерали записів коду, коди осі
(`внутрішня_мова.ключ(вісь, …)` → слова `ТАБЛИЦЯ[вісь]`), опції `<select>` поля панелі. Ключі з невизначеними
значеннями друкуються рядком «п.2 не визначено» — це межа приладу, а не «нема місць».

ОБМЕЖЕННЯ (гіпотеза, не висновок): потік атрибутів об'єктів, методів класів і читачів JS поза ключами носіїв не
простежено; читачі JS — лише читання `.к`/`["к"]` для ключів без писача. Самоперевірка — 11 відомих полів паспорта
серед місць; `тренд_сезону`, `реєстр_людини`, `виміри` — ні.

Вивід: `файл:рядок · п.N · поле · функція · шлях`, підсумки, самоперевірка, останній рядок `місць: <N>` (різні
`файл:рядок`), код 0. Запуск з кореня репозиторію (чи `--корінь <шлях>`):
python3 джерела/прилади/корінь_е3_поле_без_писача.py [--json] [--тихо]
"""
import argparse
import ast
import importlib
import json
import os
import re
import sys
import warnings

warnings.simplefilter("ignore", SyntaxWarning)

ВХІД_МОСТА = ("bridge", "виклик")
НЕ_ПРОДУКТ = re.compile(r"^(тест|стенд|батарея|проба|gate_|audit_|measure_|pair_test|жнива|мутанти|лабораторія|"
                        r"гейти|verify_|звірка|зведення|траса_петлі|status_перевірки|build_|покроковик|досяжність|"
                        r"відбиток|run_outfit|rule_genus|поломки|скласти$|корпус$|таблиця_збирання)")
ОБГОРТКИ = {"bool", "int", "float", "str", "list", "tuple", "set", "frozenset", "sorted", "reversed", "abs", "round",
            "loads", "deepcopy", "copy", "dict"}
ПОРОЖНІ = (None, False, 0, "", 0.0)
ЧЕСНЕ = re.compile(r"входу\s+нема|немає\s+входу|без\s+входу|not_passed|rule_input_unknown")
ВІДОМІ = ("господар", "креативне", "супутник_рівень", "сонце", "гардероб", "життєвий_перехід", "заявлений_злам",
          "заявлена_колона", "тон_колготи", "роль", "сезон")
НЕ_МІСЦЯ = ("тренд_сезону", "реєстр_людини", "виміри")
JS_ФАЙЛИ = ("показ.html", "показ_шаблон.js")


def _const_str(n):
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def _порожня(n):
    if isinstance(n, ast.Constant):
        return n.value in ПОРОЖНІ and not isinstance(n.value, bool) or n.value is False or n.value is None
    if isinstance(n, (ast.List, ast.Tuple, ast.Set)) and not n.elts:
        return True
    if isinstance(n, ast.Dict) and not n.keys:
        return True
    return False


# ── МОДУЛІ ПРОДУКТУ: імпортне замикання від моста ───────────────────────────────────────────────────────────────

class Модуль:
    def __init__(self, ім, шлях):
        self.ім, self.шлях = ім, шлях
        self.текст = open(шлях, encoding="utf-8").read()
        self.рядки = self.текст.splitlines()
        self.дерево = ast.parse(self.текст)
        self.імпорти = {}          # ім'я → ("мод", м) | ("сим", м, ориг)
        self.функції = {}          # кваліфіковане ім'я → вузол
        for n in ast.walk(self.дерево):
            if isinstance(n, ast.Import):
                for a in n.names:
                    self.імпорти[a.asname or a.name.split(".")[0]] = ("мод", a.name if a.asname else a.name.split(".")[0])
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for a in n.names:
                    self.імпорти[a.asname or a.name] = ("сим", n.module, a.name)

        def збір(тіло, префікс):
            for n in тіло:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    кв = префікс + n.name
                    self.функції[кв] = n
                    збір(n.body, кв + ".")
                elif isinstance(n, (ast.If, ast.Try)):
                    збір(n.body, префікс)
                    збір(getattr(n, "orelse", []), префікс)
                    for h in getattr(n, "handlers", []):
                        збір(h.body, префікс)
        збір(self.дерево.body, "")


def модулі_продукту(дж):
    є = {f[:-3] for f in os.listdir(дж) if f.endswith(".py")}
    мод, черга = {}, [ВХІД_МОСТА[0]]
    while черга:
        м = черга.pop()
        if м in мод or м not in є or НЕ_ПРОДУКТ.match(м):
            continue
        try:
            мод[м] = Модуль(м, os.path.join(дж, м + ".py"))
        except SyntaxError:
            continue
        for в in мод[м].імпорти.values():
            черга.append(в[1].split(".")[0])
    return мод


# ── АНАЛІЗ ПОТОКУ ───────────────────────────────────────────────────────────────────────────────────────────────

class Прилад:
    """Носії входу двох родів: «з» — запит із показу (корінь JSON ендпойнта), «с» — сценарій і паспорт нагоди
    (`запит["сценарій"]`, `запит["паспорт"]`, `з_показу`, їхні копії, параметри, `**kw`, ключ, під яким код
    поклав носій «с» в інший словник). Рядок входу ендпойнта — рід «р» (до `json.loads`)."""

    def __init__(self, корінь):
        self.корінь = корінь
        self.дж = os.path.join(корінь, "джерела")
        self.мод = модулі_продукту(self.дж)
        self.носії_пар = {}             # (fid, параметр) → {рід}
        self.читачі_пар = {}            # (fid, параметр) → {ключ}
        self.походження = {}            # (fid, параметр, ключ) → рядок шляху
        self.пов_носій = {}             # fid → {рід}
        self.пов_читач = {}             # fid → {ключ}
        self.ключі_носія = set()        # ключ, під яким код кладе носій «с» у словник (`сценарій_сирий`)
        self.рішення = {}               # (файл, рядок, ключ) → (fid, вид)
        self.записи_носія = {}          # ключ → {(файл:рядок, значення|None)}
        self.порівняння = []            # (файл, рядок, ключ, fid, [літерали])
        self._стан = {}                 # fid → (C, R) — для вкладених функцій
        self._ітер = {}                 # fid → імена змінних циклу над носієм
        self._змінено = True

    # ── розв'язання викликів ──
    def _символ(self, м, ім, глибина=0):
        if глибина > 6 or м not in self.мод:
            return None
        М = self.мод[м]
        if ім in М.функції:
            return (м, ім)
        в = М.імпорти.get(ім)
        if в and в[0] == "сим":
            return self._символ(в[1].split(".")[0], в[2], глибина + 1)
        return None

    def розв(self, fid, func):
        м, кв = fid
        М = self.мод[м]
        if isinstance(func, ast.Name):
            частини = кв.split(".")
            for i in range(len(частини), 0, -1):
                кандидат = ".".join(частини[:i]) + "." + func.id
                if кандидат in М.функції:
                    return (м, кандидат)
            return self._символ(м, func.id)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            в = М.імпорти.get(func.value.id)
            if в and в[0] == "мод":
                return self._символ(в[1].split(".")[0], func.attr)
            if в and в[0] == "сим":
                return self._символ(в[2], func.attr)
        return None

    @staticmethod
    def _ім_виклику(func):
        return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""

    def параметри(self, fid):
        f = self.мод[fid[0]].функції[fid[1]]
        a = f.args
        поз = [x.arg for x in a.posonlyargs + a.args]
        n_def = len(a.defaults)
        з_типовим = set(поз[len(поз) - n_def:]) if n_def else set()
        kwo = [x.arg for x in a.kwonlyargs]
        з_типовим |= {x.arg for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None}
        return поз, kwo, (a.kwarg.arg if a.kwarg else None), з_типовим

    # ── зміна стану ──
    def _носій_пар(self, fid, p, роди):
        с = self.носії_пар.setdefault((fid, p), set())
        if not роди <= с:
            с |= роди
            self._змінено = True

    def _читач_пар(self, fid, p, ключі, шлях):
        с = self.читачі_пар.setdefault((fid, p), set())
        for к in ключі:
            if к not in с:
                с.add(к)
                self.походження.setdefault((fid, p, к), шлях)
                self._змінено = True

    def _пов(self, fid, роди, ключі):
        if роди:
            с = self.пов_носій.setdefault(fid, set())
            if not роди <= с:
                с |= роди
                self._змінено = True
        if ключі:
            с = self.пов_читач.setdefault(fid, set())
            if not ключі <= с:
                с |= ключі
                self._змінено = True

    def прогін(self):
        мод, ім = ВХІД_МОСТА
        вхід = self.мод[мод].функції[ім]
        for n in ast.walk(вхід):
            if isinstance(n, ast.Dict):
                for v in n.values:
                    if isinstance(v, ast.Name):
                        fid = self.розв((мод, ім), v)
                        if fid:
                            поз = self.параметри(fid)[0]
                            if поз:
                                self._носій_пар(fid, поз[0], {"р"})
        крок = 0
        while self._змінено and крок < 60:
            self._змінено = False
            крок += 1
            for м in sorted(self.мод):
                for кв in self.мод[м].функції:
                    self.функція((м, кв))
        return крок

    # ── одна функція ──
    def функція(self, fid):
        м, кв = fid
        f = self.мод[м].функції[кв]
        поз, kwo, kwarg, _ = self.параметри(fid)
        C, R = {}, {}
        if "." in кв:
            бC, бR = self._стан.get((м, кв.rsplit(".", 1)[0]), ({}, {}))
            for к, в in бC.items():
                C.setdefault(к, set()).update(в)
            for к, в in бR.items():
                if к != "**":
                    R.setdefault(к, set()).update(в)
        for p in поз + kwo + ([kwarg] if kwarg else []):
            if (fid, p) in self.носії_пар:
                C.setdefault(p, set()).update(self.носії_пар[(fid, p)])
            if (fid, p) in self.читачі_пар:
                R.setdefault("**" if p == kwarg else p, set()).update(self.читачі_пар[(fid, p)])
        тіло = list(self._вузли(f))
        for _ in range(5):                      # потік у межах функції без порядку — до нерухомої точки
            до = (sum(len(v) for v in C.values()), sum(len(v) for v in R.values()))
            іт = {}
            for n in тіло:
                if isinstance(n, (ast.For, ast.comprehension)) and isinstance(n.iter, ast.Call) and \
                        isinstance(n.iter.func, ast.Attribute) and n.iter.func.attr in ("items", "values"):
                    р = self.носій(fid, n.iter.func.value, C) - {"р"}
                    if р:
                        for x in ast.walk(n.target):
                            if isinstance(x, ast.Name):
                                іт.setdefault(x.id, set()).update(р)
            self._ітер[fid] = іт
            for n in тіло:
                self._присвоєння(fid, n, C, R)
            if до == (sum(len(v) for v in C.values()), sum(len(v) for v in R.values())):
                break
        self._стан[fid] = (C, R)
        батьки = {}
        for n in тіло:
            for ч in ast.iter_child_nodes(n):
                батьки[ч] = n
        for n in тіло:
            self._вживання(fid, n, C, R, батьки)

    @staticmethod
    def _вузли(f):
        """Вузли тіла функції без вкладених функцій і класів (їх аналізує окремий прохід)."""
        стек = list(f.body) + list(f.args.defaults) + [d for d in f.args.kw_defaults if d is not None]
        while стек:
            n = стек.pop()
            yield n
            for ч in ast.iter_child_nodes(n):
                if not isinstance(ч, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    стек.append(ч)

    # ── вирази ──
    def носій(self, fid, e, C):
        """Роди носія, які несе вираз (порожньо — не носій)."""
        if isinstance(e, ast.Name):
            return set(C.get(e.id, ()))
        if isinstance(e, ast.Call):
            ім = self._ім_виклику(e.func)
            if ім == "loads" and e.args and "р" in self.носій(fid, e.args[0], C):
                return {"з"}
            if e.args and (ім == "deepcopy" or ім in ("dict", "OrderedDict") and isinstance(e.func, ast.Name)):
                return self.носій(fid, e.args[0], C) - {"р"}
            if isinstance(e.func, ast.Attribute):
                if e.func.attr == "copy":
                    return self.носій(fid, e.func.value, C)
                if e.func.attr in ("get", "pop", "setdefault") and e.args:
                    return self._під_носій(fid, e.func.value, _const_str(e.args[0]), C)
            ц = self.розв(fid, e.func)
            if ц and ц in self.пов_носій:
                return set(self.пов_носій[ц])
            return set()
        if isinstance(e, ast.Subscript):
            к = _const_str(e.slice)
            if к is not None:
                return self._під_носій(fid, e.value, к, C)
            if isinstance(e.slice, ast.Constant) and isinstance(e.slice.value, int):
                return self.носій(fid, e.value, C)
            return set()
        if isinstance(e, ast.BoolOp):
            return set().union(*(self.носій(fid, v, C) for v in e.values))
        if isinstance(e, ast.IfExp):
            return self.носій(fid, e.body, C) | self.носій(fid, e.orelse, C)
        if isinstance(e, ast.Dict):
            return set().union(set(), *(self.носій(fid, v, C) - {"р"} for k, v in zip(e.keys, e.values)
                                        if k is None))
        if isinstance(e, ast.DictComp):
            out = set()
            for g in e.generators:
                if isinstance(g.iter, ast.Call) and isinstance(g.iter.func, ast.Attribute) and \
                        g.iter.func.attr in ("items", "keys", "values"):
                    out |= self.носій(fid, g.iter.func.value, C)
                else:
                    out |= self.носій(fid, g.iter, C)
            return out - {"р"}
        if isinstance(e, ast.Tuple):
            return set().union(set(), *(self.носій(fid, x, C) for x in e.elts))
        if isinstance(e, ast.NamedExpr):
            return self.носій(fid, e.value, C)
        if isinstance(e, ast.Await):
            return self.носій(fid, e.value, C)
        return set()

    def _під_носій(self, fid, база, ключ, C):
        """Значення під ключем — носій «с»: сценарій чи паспорт запиту; ключ, під яким код поклав носій «с»."""
        if ключ is None:
            return set()
        if ключ in ("сценарій", "паспорт") and "з" in self.носій(fid, база, C):
            return {"с"}
        if ключ in self.ключі_носія and ключ not in ("сценарій", "паспорт"):
            return {"с"}
        return set()

    def читання(self, fid, e, C):
        """Ключ, коли `e` — пряме читання носія: .get("к"), ["к"], .pop("к")."""
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ("get", "pop") and \
                e.args and _const_str(e.args[0]) and self.носій(fid, e.func.value, C) - {"р"}:
            return _const_str(e.args[0])
        if isinstance(e, ast.Subscript) and isinstance(e.ctx, ast.Load) and _const_str(e.slice) and \
                self.носій(fid, e.value, C) - {"р"}:
            return _const_str(e.slice)
        return None

    def читання_kw(self, fid, e, R):
        """`kw.get("к")` над `**kw`, у який передано іменоване значення читача `к`."""
        kwarg = self.параметри(fid)[2]
        if not kwarg or not R.get("**"):
            return None
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ("get", "pop") and \
                isinstance(e.func.value, ast.Name) and e.func.value.id == kwarg and e.args and \
                _const_str(e.args[0]) in R["**"]:
            return _const_str(e.args[0])
        if isinstance(e, ast.Subscript) and isinstance(e.ctx, ast.Load) and isinstance(e.value, ast.Name) and \
                e.value.id == kwarg and _const_str(e.slice) in R["**"]:
            return _const_str(e.slice)
        return None

    def ключі(self, fid, e, C, R):
        """Ключі входу, значення яких несе вираз."""
        if isinstance(e, ast.Name):
            return set(R.get(e.id, ())) if e.id != "**" else set()
        к = self.читання(fid, e, C) or self.читання_kw(fid, e, R)
        if к:
            return {к}
        if isinstance(e, ast.Call):
            ім = self._ім_виклику(e.func)
            if ім in ОБГОРТКИ and isinstance(e.func, ast.Name) and e.args:
                return self.ключі(fid, e.args[0], C, R)
            ц = self.розв(fid, e.func)
            if ц and ц in self.пов_читач:
                return set(self.пов_читач[ц])
            return set()
        if isinstance(e, ast.BoolOp):
            return set().union(*(self.ключі(fid, v, C, R) for v in e.values))
        if isinstance(e, ast.IfExp):
            return self.ключі(fid, e.body, C, R) | self.ключі(fid, e.orelse, C, R)
        if isinstance(e, (ast.NamedExpr, ast.Await)):
            return self.ключі(fid, e.value, C, R)
        return set()

    def _присвоєння(self, fid, n, C, R):
        цілі, знач = [], None
        if isinstance(n, ast.Assign):
            цілі, знач = n.targets, n.value
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)) and n.value is not None:
            цілі, знач = [n.target], n.value
        elif isinstance(n, ast.NamedExpr):
            цілі, знач = [n.target], n.value
        if знач is None:
            return
        роди = self.носій(fid, знач, C)
        кл = self.ключі(fid, знач, C, R)
        for ц in цілі:
            імена = ([ц] if isinstance(ц, ast.Name) else
                     [x for x in ast.walk(ц) if isinstance(x, ast.Name)] if isinstance(ц, (ast.Tuple, ast.List))
                     else [])
            for t in імена:
                if роди:
                    C.setdefault(t.id, set()).update(роди)
                if кл:
                    R.setdefault(t.id, set()).update(кл)
            # копія носія ключ за ключем робить словник носієм (`нагода[k] = v` у `з_показу`): ключ — змінна,
            # значення — з носія; запис сталого ключа — писач коду, а не копія входу
            if isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and _const_str(ц.slice) is None:
                р = self._рід_копії(fid, знач, C)
                if р and not р <= C.get(ц.value.id, set()):
                    C.setdefault(ц.value.id, set()).update(р)

    def _рід_копії(self, fid, e, C):
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ("get", "pop") and \
                e.args and _const_str(e.args[0]) is None:
            return self.носій(fid, e.func.value, C) - {"р"}
        if isinstance(e, ast.Name):
            return set(self._ітер.get(fid, {}).get(e.id, ()))
        return set()

    def _прямий_с(self, fid, e, C):
        """Вираз — сам носій «с» чи його копія (не значення з нього): ім'я, `dict(носій)`, `{**носій}`, `.copy()`."""
        if isinstance(e, ast.Name):
            return "с" in C.get(e.id, ())
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id == "dict" and e.args:
            return self._прямий_с(fid, e.args[0], C)
        if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr == "copy":
            return self._прямий_с(fid, e.func.value, C)
        if isinstance(e, ast.Dict):
            return any(k is None and self._прямий_с(fid, v, C) for k, v in zip(e.keys, e.values))
        if isinstance(e, ast.BoolOp):
            return any(self._прямий_с(fid, v, C) for v in e.values)
        return False

    # ── вживання: передача далі чи рішення ──
    def _вживання(self, fid, n, C, R, батьки):
        if isinstance(n, ast.Call):
            self._виклик(fid, n, C, R)
            if isinstance(n.func, ast.Attribute) and n.func.attr in ("setdefault", "update") and \
                    self.носій(fid, n.func.value, C) - {"р"}:
                if n.func.attr == "setdefault" and n.args and _const_str(n.args[0]):
                    self._запис(fid, n, _const_str(n.args[0]), n.args[1] if len(n.args) > 1 else None, C, R)
                for kw in n.keywords:
                    if kw.arg:
                        self._запис(fid, n, kw.arg, kw.value, C, R)
            if isinstance(n.func, ast.Name) and n.func.id == "dict":
                if n.args and self.носій(fid, n.args[0], C) - {"р"}:
                    for kw in n.keywords:
                        if kw.arg:
                            self._запис(fid, n, kw.arg, kw.value, C, R)
                for kw in n.keywords:
                    if kw.arg and self._прямий_с(fid, kw.value, C):
                        self._ключ_носія(kw.arg)
        if isinstance(n, ast.Dict):
            if any(k is None and self.носій(fid, v, C) - {"р"} for k, v in zip(n.keys, n.values)):
                for k, v in zip(n.keys, n.values):
                    if _const_str(k):
                        self._запис(fid, n, _const_str(k), v, C, R)
            for k, v in zip(n.keys, n.values):
                if _const_str(k) and self._прямий_с(fid, v, C):
                    self._ключ_носія(_const_str(k))
        if isinstance(n, (ast.Assign, ast.AugAssign)):
            for ц in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                пари = [(ц, n.value)]
                if isinstance(ц, ast.Tuple) and isinstance(n.value, ast.Tuple):
                    пари = list(zip(ц.elts, n.value.elts))
                for t, v in пари:
                    if isinstance(t, ast.Subscript) and _const_str(t.slice):
                        if self.носій(fid, t.value, C) - {"р"}:
                            self._запис(fid, n, _const_str(t.slice), v, C, R)
                        if self._прямий_с(fid, v, C):
                            self._ключ_носія(_const_str(t.slice))
        if isinstance(n, ast.Return) and n.value is not None:
            self._пов(fid, self.носій(fid, n.value, C), self.ключі(fid, n.value, C, R))
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.In, ast.NotIn)) and \
                _const_str(n.left) and self.носій(fid, n.comparators[0], C) - {"р"}:
            self._рішення(fid, n.lineno, _const_str(n.left), "ключ in носій")
        # вживання значення читача
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in R:
            кл = R[n.id]
        else:
            к = self.читання(fid, n, C) or self.читання_kw(fid, n, R)
            кл = {к} if к else set()
        if not кл:
            return
        вид = self._контекст(fid, n, батьки)
        if вид is None:
            return
        for к in кл:
            self._рішення(fid, n.lineno, к, вид)
        self._порівняння(fid, n, кл, батьки)

    def _ключ_носія(self, к):
        if к not in self.ключі_носія:
            self.ключі_носія.add(к)
            self._змінено = True

    def _контекст(self, fid, n, батьки):
        """None — передача далі; інакше — вид рішення."""
        ч, б = n, батьки.get(n)
        while б is not None:
            if isinstance(б, (ast.BoolOp, ast.NamedExpr, ast.Starred, ast.Await, ast.keyword)) or \
                    (isinstance(б, ast.IfExp) and ч is not б.test):
                ч, б = б, батьки.get(б)
                continue
            if isinstance(б, ast.Call) and ч is not б.func:
                ім = self._ім_виклику(б.func)
                if isinstance(б.func, ast.Name) and ім in ОБГОРТКИ - {"dict"}:
                    ч, б = б, батьки.get(б)
                    continue
                if isinstance(б.func, ast.Name) and ім == "dict":
                    return "поле пакета"
                if self.розв(fid, б.func):
                    return None
                if isinstance(б.func, ast.Attribute) and ч is б.func.value:
                    return "вживання значення"
                return "виклик поза продуктом"
            if isinstance(б, (ast.Attribute, ast.Subscript)) and ч is б.value:
                return "вживання значення"
            if isinstance(б, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and ч is б.value:
                цілі = б.targets if isinstance(б, ast.Assign) else [б.target]
                if all(isinstance(t, (ast.Name, ast.Tuple, ast.List)) for t in цілі):
                    return None
                return "поле пакета"
            if isinstance(б, (ast.Return, ast.Expr)):
                return None
            if isinstance(б, ast.Dict):
                return "поле пакета"
            if isinstance(б, (ast.For, ast.comprehension)) and ч is б.iter:
                return "ітерація"
            if isinstance(б, (ast.If, ast.While, ast.IfExp, ast.Assert, ast.comprehension)):
                return "умова"
            if isinstance(б, ast.Compare):
                return "порівняння"
            if isinstance(б, ast.UnaryOp):
                return "умова" if isinstance(б.op, ast.Not) else "арифметика"
            if isinstance(б, ast.BinOp):
                return "арифметика"
            if isinstance(б, (ast.JoinedStr, ast.FormattedValue)):
                return "текст"
            if isinstance(б, (ast.Tuple, ast.List, ast.Set)):
                ч, б = б, батьки.get(б)
                continue
            return "вживання значення"
        return None

    def _виклик(self, fid, n, C, R):
        ц = self.розв(fid, n.func)
        if not ц:
            return
        поз, kwo, kwarg, _ = self.параметри(ц)
        файл = self.мод[fid[0]].ім + ".py"
        шлях = "%s:%d %s" % (файл, n.lineno, fid[1])
        зв = set()
        for i, a in enumerate(n.args):
            if isinstance(a, ast.Starred):          # `*а` зв'язує решту позиційних
                зв |= set(поз[i:])
                break
            if i < len(поз):
                зв.add(поз[i])
                р = self.носій(fid, a, C)
                if р:
                    self._носій_пар(ц, поз[i], р)
                кл = self.ключі(fid, a, C, R)
                if кл:
                    self._читач_пар(ц, поз[i], кл, шлях)
        for kw in n.keywords:
            if kw.arg is None:
                continue
            зв.add(kw.arg)
            ціль = kw.arg if kw.arg in поз or kw.arg in kwo else kwarg
            if not ціль:
                continue
            кл = self.ключі(fid, kw.value, C, R)
            if ціль == kwarg:
                кл = {kw.arg} if кл else set()
            else:
                р = self.носій(fid, kw.value, C)
                if р:
                    self._носій_пар(ц, ціль, р)
            if кл:
                self._читач_пар(ц, ціль, кл, шлях)
        власний_kw = self.параметри(fid)[2]
        for kw in n.keywords:
            if kw.arg is not None:
                continue
            р = self.носій(fid, kw.value, C) - {"р"}
            if р:
                for p in поз + kwo:
                    if p not in зв and p != "self":
                        self._читач_пар(ц, p, {p}, шлях + " **")
                if kwarg:
                    self._носій_пар(ц, kwarg, р)
            elif isinstance(kw.value, ast.Name) and kw.value.id == власний_kw and R.get("**"):
                # `**kw`, що зібрав іменовані значення читачів, — кожне до параметра з тим самим іменем
                for к in R["**"]:
                    if к in поз or к in kwo:
                        if к not in зв:
                            self._читач_пар(ц, к, {к}, шлях + " **")
                    elif kwarg:
                        self._читач_пар(ц, kwarg, {к}, шлях + " **")

    def _запис(self, fid, n, ключ, знач, C, R):
        if знач is None or _порожня(знач):
            return
        if ключ in self.ключі(fid, знач, C, R):        # копія того самого ключа — не писач
            return
        файл = self.мод[fid[0]].ім + ".py"
        self.записи_носія.setdefault(ключ, set()).add(("%s:%d" % (файл, n.lineno), _const_str(знач)))

    def _рішення(self, fid, рядок, ключ, вид):
        к = (self.мод[fid[0]].ім + ".py", рядок, ключ)
        if к not in self.рішення:
            self.рішення[к] = (fid, вид)

    def _порівняння(self, fid, n, кл, батьки):
        ч, б = n, батьки.get(n)
        while isinstance(б, ast.Call) and self._ім_виклику(б.func) in ОБГОРТКИ:
            ч, б = б, батьки.get(б)
        if not isinstance(б, ast.Compare) or len(б.ops) != 1:
            return
        інше = б.comparators[0] if б.left is ч else б.left
        літ = []
        if isinstance(б.ops[0], (ast.Eq, ast.NotEq)) and _const_str(інше):
            літ = [_const_str(інше)]
        elif isinstance(б.ops[0], (ast.In, ast.NotIn)) and б.left is ч and \
                isinstance(інше, (ast.Tuple, ast.List, ast.Set)):
            літ = [_const_str(x) for x in інше.elts if _const_str(x)]
        if літ:
            for к in кл:
                self.порівняння.append((self.мод[fid[0]].ім + ".py", n.lineno, к, fid, літ))

    # ── чесне «немає входу» ──
    def чесна(self, fid, ключ):
        f = self.мод[fid[0]].функції[fid[1]]
        текст = "\n".join(self.мод[fid[0]].рядки[f.lineno - 1:(f.end_lineno or f.lineno)])
        if not ЧЕСНЕ.search(текст):
            return False
        for n in ast.walk(f):
            if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Is, ast.IsNot)) for o in n.ops) and \
                    isinstance(n.left, ast.Name) and ключ in self.читачі_пар.get((fid, n.left.id), ()):
                return True
        return False


# ── ПИСАЧІ ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _js_без_коментарів(т):
    т = re.sub(r"/\*.*?\*/", " ", т, flags=re.S)
    return re.sub(r"(?m)(^|[^:\\'\"])//[^\n]*", r"\1", т)


ЛІТЕРА = r"[\wА-Яа-яЇїІіЄєҐґʼ$]"


def писачі_js(дж):
    файли = [os.path.join(дж, "показ", f) for f in sorted(os.listdir(os.path.join(дж, "показ"))) if f.endswith(".js")]
    файли += [os.path.join(дж, f) for f in JS_ФАЙЛИ if os.path.exists(os.path.join(дж, f))]
    ключі, ід, читання, опції = {}, set(), {}, {}
    for ш in файли:
        т = open(ш, encoding="utf-8").read()
        if ш.endswith(".html"):
            ід |= set(re.findall(r'id="([^"]+)"', т))
            for сел_ід, тіло in re.findall(r'<select[^>]*id="([^"]+)"[^>]*>(.*?)</select>', т, flags=re.S):
                опції[сел_ід] = set(re.findall(r'<option[^>]*value="([^"]*)"', тіло))
        т = _js_без_коментарів(т)
        ім = os.path.relpath(ш, дж)
        for мітка in re.finditer(r"(?:[{,]\s*)(%s+)\s*:(?!:)" % ЛІТЕРА, т):
            ключі.setdefault(мітка.group(1), "%s:%d" % (ім, т.count("\n", 0, мітка.start()) + 1))
        for мітка in re.finditer(r"(?:[{,]\s*)['\"](%s+)['\"]\s*:" % ЛІТЕРА, т):
            ключі.setdefault(мітка.group(1), "%s:%d" % (ім, т.count("\n", 0, мітка.start()) + 1))
        for мітка in re.finditer(r"\.(%s+)\s*=(?!=)" % ЛІТЕРА, т):
            ключі.setdefault(мітка.group(1), "%s:%d" % (ім, т.count("\n", 0, мітка.start()) + 1))
        for мітка in re.finditer(r"\[\s*['\"](%s+)['\"]\s*\]\s*=(?!=)" % ЛІТЕРА, т):
            ключі.setdefault(мітка.group(1), "%s:%d" % (ім, т.count("\n", 0, мітка.start()) + 1))
        for мітка in re.finditer(r"(?:\.(%s+)(?!%s)(?!\s*=[^=])|\[\s*['\"](%s+)['\"]\s*\](?!\s*=[^=]))"
                                 % (ЛІТЕРА, ЛІТЕРА, ЛІТЕРА), т):
            к = мітка.group(1) or мітка.group(2)
            читання.setdefault(к, "%s:%d" % (ім, т.count("\n", 0, мітка.start()) + 1))
    return ключі, ід, читання, опції


class Паспорт:
    """Ключі словника, який ендпойнт повертає полем «паспорт» (повернення й мутація параметра — транзитивно)."""

    def __init__(self, прилад):
        self.п = прилад
        self.пов = {}          # fid → {ключ: (місце, значення)}
        self.мут = {}          # (fid, i) → {ключ: …}
        self._в_роботі = set()
        self._модулі = {}

    def _модуль(self, м):
        if м not in self._модулі:
            try:
                self._модулі[м] = importlib.import_module(м)
            except Exception:
                self._модулі[м] = None
        return self._модулі[м]

    def _таблиця(self, м, e):
        """Ключі таблиці модуля, за якою пише цикл (`for к in ПОЛЯ_…`), — обчислено імпортом модуля."""
        мод = self._модуль(м)
        if мод is None:
            return None
        try:
            з = eval(compile(ast.Expression(e), "<таблиця>", "eval"), dict(vars(мод)))
        except Exception:
            return None
        out = []
        try:
            for x in з:
                out.append(x)
        except Exception:
            return None
        return out

    def ключі_функції(self, fid):
        if fid in self.пов:
            return self.пов[fid]
        if fid in self._в_роботі:
            return {}
        self._в_роботі.add(fid)
        f = self.п.мод[fid[0]].функції[fid[1]]
        лок = self._локальні(fid, f)
        вих = {}
        for n in Прилад._вузли(f):
            if isinstance(n, ast.Return) and n.value is not None:
                вих.update(self.ключі_виразу(fid, n.value, лок))
        self._в_роботі.discard(fid)
        self.пов[fid] = вих
        return вих

    def мутація(self, fid, i):
        if (fid, i) in self.мут:
            return self.мут[(fid, i)]
        self.мут[(fid, i)] = {}
        f = self.п.мод[fid[0]].функції[fid[1]]
        поз = self.п.параметри(fid)[0]
        if i >= len(поз):
            return {}
        лок = self._локальні(fid, f, лише=поз[i])
        self.мут[(fid, i)] = лок.get(поз[i], {})
        return self.мут[(fid, i)]

    def _місце(self, fid, n):
        return "%s:%d" % (self.п.мод[fid[0]].ім + ".py", n.lineno)

    def _значення(self, fid, n, v, ключ, лок=None):
        """(місце, літерал|«код осі»|None) — або None, коли це не писач (порожня стала, копія того самого ключа)."""
        if v is None or _порожня(v):
            return None
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr in ("get", "pop") and \
                v.args and _const_str(v.args[0]) == ключ:
            return None
        if isinstance(v, ast.Subscript) and _const_str(v.slice) == ключ:
            return None
        if isinstance(v, ast.Name) and v.id == ключ:
            return None
        return (self._місце(fid, n), _const_str(v))

    def _локальні(self, fid, f, лише=None):
        м = fid[0]
        лок = {}
        вузли = list(Прилад._вузли(f))
        # пари з таблиці-літерала: for поле, ім in (("activity", "активність"), …)
        for n in вузли:
            if isinstance(n, ast.For):
                ключі_циклу = self._ключі_циклу(м, n)
                if not ключі_циклу:
                    continue
                for ім_змінної, значення_ключів in ключі_циклу.items():
                    for x in ast.walk(n):
                        if isinstance(x, ast.Assign):
                            for t in x.targets:
                                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and \
                                        isinstance(t.slice, ast.Name) and t.slice.id == ім_змінної and \
                                        (лише is None or t.value.id == лише):
                                    for к in значення_ключів:
                                        if not _порожня(x.value):
                                            лок.setdefault(t.value.id, {})[к] = (self._місце(fid, x), None)
        for n in вузли:
            if isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name) and (лише is None or t.id == лише):
                        лок.setdefault(t.id, {}).update(self.ключі_виразу(fid, n.value, лок))
                    elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and _const_str(t.slice) and \
                            (лише is None or t.value.id == лише):
                        з = self._значення(fid, n, n.value, _const_str(t.slice))
                        if з:
                            лок.setdefault(t.value.id, {})[_const_str(t.slice)] = з
                    elif isinstance(t, ast.Tuple) and isinstance(n.value, ast.Tuple):
                        for tt, vv in zip(t.elts, n.value.elts):
                            if isinstance(tt, ast.Subscript) and isinstance(tt.value, ast.Name) and \
                                    _const_str(tt.slice) and (лише is None or tt.value.id == лише):
                                з = self._значення(fid, n, vv, _const_str(tt.slice))
                                if з:
                                    лок.setdefault(tt.value.id, {})[_const_str(tt.slice)] = з
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                    isinstance(n.func.value, ast.Name) and (лише is None or n.func.value.id == лише):
                ім = n.func.value.id
                if n.func.attr == "setdefault" and n.args and _const_str(n.args[0]):
                    з = self._значення(fid, n, n.args[1] if len(n.args) > 1 else None, _const_str(n.args[0]))
                    if з:
                        лок.setdefault(ім, {})[_const_str(n.args[0])] = з
                elif n.func.attr == "update":
                    for kw in n.keywords:
                        if kw.arg:
                            з = self._значення(fid, n, kw.value, kw.arg)
                            if з:
                                лок.setdefault(ім, {})[kw.arg] = з
                    for a in n.args:
                        лок.setdefault(ім, {}).update(self.ключі_виразу(fid, a, лок))
            if isinstance(n, ast.Call):
                ц = self.п.розв(fid, n.func)
                if ц and ц != fid:
                    for i, a in enumerate(n.args):
                        if isinstance(a, ast.Name) and (лише is None or a.id == лише):
                            м_кл = self.мутація(ц, i)
                            if м_кл:
                                лок.setdefault(a.id, {}).update(м_кл)
        return лок

    def _ключі_циклу(self, м, n):
        """{змінна_ключа: [ключі]} для циклу за таблицею: літерал пар чи таблиця модуля."""
        out = {}
        if isinstance(n.target, ast.Name):
            імена = [n.target.id]
        elif isinstance(n.target, ast.Tuple) and all(isinstance(x, ast.Name) for x in n.target.elts):
            імена = [x.id for x in n.target.elts]
        else:
            return out
        it = n.iter
        if isinstance(it, (ast.Tuple, ast.List)) and all(isinstance(x, (ast.Tuple, ast.List)) for x in it.elts):
            for j, ім in enumerate(імена):
                кл = [_const_str(x.elts[j]) for x in it.elts if j < len(x.elts) and _const_str(x.elts[j])]
                if кл:
                    out[ім] = кл
            return out
        if isinstance(it, (ast.Tuple, ast.List)) and len(імена) == 1:
            кл = [_const_str(x) for x in it.elts if _const_str(x)]
            if кл:
                out[імена[0]] = кл
            return out
        вільні = {x.id for x in ast.walk(it) if isinstance(x, ast.Name)}
        мод = self._модуль(м)
        if мод is None or any(v not in vars(мод) and v not in dir(__builtins__) for v in вільні):
            return out
        знач = self._таблиця(м, it)
        if not знач:
            return out
        for j, ім in enumerate(імена):
            кл = []
            for x in знач:
                y = x if len(імена) == 1 else (x[j] if isinstance(x, (tuple, list)) and j < len(x) else None)
                if isinstance(y, str):
                    кл.append(y)
            if кл:
                out[ім] = кл
        return out

    def ключі_виразу(self, fid, e, лок):
        if isinstance(e, ast.Dict):
            вих = {}
            for k, v in zip(e.keys, e.values):
                if k is None:
                    вих.update(self.ключі_виразу(fid, v, лок))
                elif _const_str(k):
                    з = self._значення(fid, e, v, _const_str(k))
                    if з:
                        вих[_const_str(k)] = з
            return вих
        if isinstance(e, ast.DictComp):
            вих = {}
            for g in e.generators:
                if isinstance(g.target, ast.Name) and isinstance(e.key, ast.Name) and e.key.id == g.target.id:
                    знач = None
                    вільні = {x.id for x in ast.walk(g.iter) if isinstance(x, ast.Name)}
                    мод = self._модуль(fid[0])
                    if мод is not None and all(v in vars(мод) or v in dir(__builtins__) for v in вільні):
                        знач = self._таблиця(fid[0], g.iter)
                    for x in знач or ():
                        if isinstance(x, str) and not _порожня(e.value):
                            вих[x] = (self._місце(fid, e), None)
            return вих
        if isinstance(e, ast.Call):
            вих = {}
            ім = Прилад._ім_виклику(e.func)
            if ім in ("dict", "dumps", "OrderedDict") or ім in ОБГОРТКИ:
                for a in e.args:
                    вих.update(self.ключі_виразу(fid, a, лок))
                for kw in e.keywords:
                    if kw.arg:
                        з = self._значення(fid, e, kw.value, kw.arg)
                        if з:
                            вих[kw.arg] = з
                    else:
                        вих.update(self.ключі_виразу(fid, kw.value, лок))
                return вих
            ц = self.п.розв(fid, e.func)
            if ц:
                return dict(self.ключі_функції(ц))
            return {}
        if isinstance(e, ast.Name):
            return dict(лок.get(e.id, {}))
        if isinstance(e, (ast.BoolOp,)):
            вих = {}
            for v in e.values:
                вих.update(self.ключі_виразу(fid, v, лок))
            return вих
        if isinstance(e, ast.IfExp):
            вих = self.ключі_виразу(fid, e.body, лок)
            вих.update(self.ключі_виразу(fid, e.orelse, лок))
            return вих
        if isinstance(e, ast.Tuple):
            вих = {}
            for x in e.elts:
                вих.update(self.ключі_виразу(fid, x, лок))
            return вих
        return {}

    def ключі_паспорта(self):
        """Ключі, які ендпойнти віддають показу полем «паспорт» (показ кладе їх у `ПАСПОРТ_П` і шле назад)."""
        вих = {}
        for м in sorted(self.п.мод):
            for кв in self.п.мод[м].функції:
                fid = (м, кв)
                f = self.п.мод[м].функції[кв]
                лок = None
                for n in Прилад._вузли(f):
                    знач = None
                    if isinstance(n, ast.Call) and Прилад._ім_виклику(n.func) == "dict":
                        знач = next((kw.value for kw in n.keywords if kw.arg == "паспорт"), None)
                    elif isinstance(n, ast.Dict):
                        знач = next((v for k, v in zip(n.keys, n.values) if _const_str(k) == "паспорт"), None)
                    if знач is None:
                        continue
                    if лок is None:
                        лок = self._локальні(fid, f)
                    for к, з in self.ключі_виразу(fid, знач, лок).items():
                        вих.setdefault(к, з)
        return вих


# ── ЗБІРКА ─────────────────────────────────────────────────────────────────────────────────────────────────────

def значення_осі(вм, писачі_місця, мод_прилад):
    return None


def лічба(корінь):
    дж = os.path.join(корінь, "джерела")
    if дж not in sys.path:
        sys.path.insert(0, дж)
    п = Прилад(корінь)
    кроків = п.прогін()
    паспорт = Паспорт(п).ключі_паспорта()
    js_ключі, js_ід, js_читання, опції = писачі_js(дж)
    try:
        пп = importlib.import_module("паспорт_поля").ПОЛЯ_ПАСПОРТА
    except Exception:
        пп = {}
    панель = {к: [i[0] for i in в.get("показ") or () if i and i[0] in js_ід] for к, в in пп.items()}
    зовнішні = set()
    try:
        дерево = ast.parse(open(os.path.join(дж, "суд_чеклісти.py"), encoding="utf-8").read())
        for n in ast.walk(дерево):
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ЗОВНІШНІ_ВХОДИ"
                                                 for t in n.targets) and isinstance(n.value, ast.Dict):
                зовнішні = {_const_str(k) for k in n.value.keys if _const_str(k)}
    except (OSError, SyntaxError):
        pass

    def писачі(к):
        out = []
        if к in js_ключі:
            out.append("показ " + js_ключі[к])
        if панель.get(к):
            out.append("панель " + ",".join(панель[к]))
        if к in паспорт:
            out.append("паспорт " + паспорт[к][0])
        for місце, _ in sorted(п.записи_носія.get(к, ()), key=str):
            out.append("код " + місце)
            break
        return out

    def значення_писача(к):
        """Множина значень писачів або None, коли хоч один писач дає невизначене значення."""
        зн = set()
        if к in js_ключі:
            return None
        for i in панель.get(к) or ():
            if i not in опції:
                return None
            зн |= опції[i]
        if к in паспорт:
            if паспорт[к][1] is None:
                return None
            зн.add(паспорт[к][1])
        for _, v in п.записи_носія.get(к, ()):
            if v is None:
                return None
            зн.add(v)
        return зн

    місця, сам_каже, без_писача, не_визначено = [], [], set(), set()
    for (файл, рядок, к), (fid, вид) in sorted(п.рішення.items()):
        if к in зовнішні:
            continue
        пис = писачі(к)
        if пис:
            continue
        if п.чесна(fid, к):
            сам_каже.append((файл, рядок, к, fid[1]))
            continue
        без_писача.add(к)
        шлях = ""
        for (ф, пар, кк), ш in sorted(п.походження.items()):
            if ф == fid and кк == к:
                шлях = "%s ← %s" % (пар, ш)
                break
        місця.append(dict(файл=файл, рядок=рядок, пункт=1, поле=к, функція=fid[1], вид=вид, шлях=шлях))
    for файл, рядок, к, fid, літ in sorted(set((a, b, c, d, tuple(e)) for a, b, c, d, e in п.порівняння)):
        if к in зовнішні or not писачі(к):
            continue
        зн = значення_писача(к)
        if зн is None:
            не_визначено.add(к)
            continue
        мертві = [x for x in літ if x not in зн]
        if мертві:
            місця.append(dict(файл=файл, рядок=рядок, пункт=2, поле=к, функція=fid[1], вид="порівняння",
                              шлях="літерали без писача: " + ", ".join(мертві)))
    js = {к: js_читання[к] for к in sorted(без_писача) if к in js_читання}
    return dict(місця=місця, сам_каже=сам_каже, без_писача=sorted(без_писача), js_читання=js,
                п2_не_визначено=sorted(не_визначено), кроків=кроків, модулів=len(п.мод),
                читачів=len(п.читачі_пар), рішень=len(п.рішення), писачі=писачі)


def main():
    ар = argparse.ArgumentParser()
    ар.add_argument("--корінь", default=".")
    ар.add_argument("--json", action="store_true")
    ар.add_argument("--тихо", action="store_true")
    а = ар.parse_args()
    корінь = os.path.abspath(а.корінь)
    р = лічба(корінь)
    рядки = sorted({(м["файл"], м["рядок"]) for м in р["місця"]})
    if а.json:
        print(json.dumps({к: в for к, в in р.items() if к != "писачі"}, ensure_ascii=False, indent=1))
    elif not а.тихо:
        print("модулів продукту: %d; параметрів-читачів: %d; рішень над входом: %d; кроків до нерухомої точки: %d"
              % (р["модулів"], р["читачів"], р["рішень"], р["кроків"]))
        for м in р["місця"]:
            print("%s:%d · п.%d · %s · %s · %s · %s" % (м["файл"], м["рядок"], м["пункт"], м["поле"], м["функція"],
                                                       м["вид"], м["шлях"]))
        print()
        print("поля без писача (%d): %s" % (len(р["без_писача"]), ", ".join(р["без_писача"])))
        for п_ in (1, 2):
            print("п.%d: місць %d" % (п_, len({(м["файл"], м["рядок"]) for м in р["місця"] if м["пункт"] == п_})))
        if р["сам_каже"]:
            print("сам каже «входу нема» (не місце): " +
                  "; ".join("%s:%d %s" % (ф, р_, к) for ф, р_, к, _ in р["сам_каже"]))
        print("п.2 не визначено (значення писача невідомі): %s" % ", ".join(р["п2_не_визначено"]))
        if р["js_читання"]:
            print("JS читає поле без писача: " + "; ".join("%s %s" % (к, в) for к, в in р["js_читання"].items()))
        є = {м["поле"] for м in р["місця"]}
        нема = [к for к in ВІДОМІ if к not in є]
        зайві = [к for к in НЕ_МІСЦЯ if к in є]
        print("самоперевірка: відомих полів серед місць %d з %d%s; не-місця серед місць: %s"
              % (len(ВІДОМІ) - len(нема), len(ВІДОМІ), (" — бракує: " + ", ".join(нема)) if нема else "",
                 ", ".join(зайві) or "нема"))
    print("місць: %d" % len(рядки))


if __name__ == "__main__":
    main()
