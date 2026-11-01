"""Контекст одного виконання функції у потоці ознак обличчя."""
import ast, collections, functools
from ознаки_основа import (
    B, C, E, F, HEX_РЕГ, K, P, Q, R, S, _без_мапи, _без_першого, _ел, _з_префіксом, _звузити, _злити_ел,
    _злити_ключі, _корінь_імені, _пара, _перебір, _під, _рядок, _сітка, _текст, _токени, _усі, _шлях,
    _ім_виклику, _імена, БУЛЕВІ, ВИМІР, ВМІСТИЩА, ГЛИБИНА, МАПА, МАПА_М, МУТАЦІЇ, НЕВІДОМЕ, ПОЗИЦІЙНІ,
    ПОРЯДОК, СЛУЖБОВІ, ТОКЕН, ФАЙЛОВІ
)

class Стан:
    """Один аналіз функції в контексті: env імен → мітки, без порядку інструкцій (до нерухомої точки)."""

    def __init__(self, а, ф, контекст):
        self.а, self.ф, self.м = а, ф, ф.модуль
        self.env = {}
        self.ключі = collections.defaultdict(lambda: collections.defaultdict(frozenset))
        self.розгорнуті = collections.defaultdict(dict)   # `*а`/`**к` → номер чи ім'я → (мітки, ключі)
        for п, мітки, км in контекст:
            if "#" in п:
                осн, _, де = п.partition("#")
                self.розгорнуті[осн][int(де) if де.isdigit() else де] = (мітки, (dict(км) or None))
                continue
            if мітки:
                self.env[п] = мітки
            for кл, в in км:
                self.ключі[п][кл] = в
        self.ключі_пов = {}
        self.ключі_циклу = {}    # ім'я циклу над кортежем рядків → ці рядки (`kw.get(k)` читає лише їх)
        self.пари_мап = {}       # ключ .items() → (ім'я значення, вираз словника)
        self.ключі_викликів = {}  # id(виклик) → (мітки поза ключами, ключі повернення)
        self.глобальні = set()
        self.псевдоніми = {}     # ім'я → мапа, елементом якої воно є (`е = d.setdefault(к, …)`)
        self.невідомо = {}       # ім'я → гілка «невідомо» ("так"/"ні"), коли ім'я — перевірка невідомого на S
        self.пов = E
        self.кортеж, self.кортеж_зламано = None, False
        self.кортежі_викликів = {}
        self.локальні = set(self.env) | set(self.ключі) | set(ф.позиційні) | set(ф.іменні) | {ф.зірка, ф.дві_зірки}
        self.локальні.update(ф.локальні)
        self.глобальні.update(ф.глобальні)
        self.локальні -= self.глобальні
        # інструкції верхнього рівня тіла: тут присвоєння імені замінює попереднє значення (далі по тілу ім'я
        # несе лише нове); у гілці чи циклі — додає, бо інший шлях міг лишити старе
        self.верх = ф.верх
        self.зерно = ф.повне in а.функції_зерна

    def виконати(self):
        в = self.ф.вузол
        for _ in range(8):
            до = (dict(self.env), self.пов)
            if isinstance(в, ast.Lambda):
                self.пов |= self.e(в.body)
            else:
                self.тіло(в.body)
            if (self.env, self.пов) == до:
                break
        return frozenset(x for x in self.пов)

    # ── імена ──
    def читати(self, ім):
        return self.читати_env(ім) | _усі(self.ключі.get(ім))

    def ключ_імені(self, ім, ключ, вузол, типове=None):
        """`ім["к"]` / `ім.get("к")`: значення ключа, записане тут, і правило індексу на решті міток імені."""
        км = self.ключі.get(ім, {})
        return self.готове_поле(ключ, км.get(ключ, E) | _усі(_під(км, ключ)) |
                               self.індекс(self.читати_env(ім), ast.Constant(ключ), вузол, типове))

    def готове_поле(self, ключ, мітки):
        """Походження поля ваги з протоколу є походженням рішення також після мутації запису."""
        return (мітки - {S}) | ({Q} if S in мітки else set()) if ключ in self.а.готові_поля else мітки

    def читати_env(self, ім):
        if ім in self.env:
            return self.env[ім]
        if ім not in self.локальні:
            о = self.ф.батько
            while о is not None:
                в = self.а.середовища.get(о.повне, {}).get(ім)
                if в:
                    return в
                о = о.батько
            return self.а.глоб.get((self.м.ім, ім), E)
        return E

    def наступний(self, в):
        return isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "next" and bool(в.args) \
            and not self.а.викликані(self.м, в.func, self.ф)

    def можливі_ключі(self, в):
        """Рядки, якими може бути ключ-вираз: ім'я циклу над кортежем рядків чи поле запису, якому літерали
        модуля дають лише рядки (`сп["поле"]`, `сп.get("поле")`); інакше None."""
        if isinstance(в, ast.Name):
            return self.ключі_циклу.get(в.id)
        поле = None
        if isinstance(в, ast.Subscript) and _рядок(в.slice):
            поле = в.slice.value
        elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                and _рядок(в.args[0]):
            поле = в.args[0].value
        return self.а.значення_полів.get(self.м.ім, {}).get(поле) if поле else None

    def писати(self, ім, мітки, мутація=False):
        """Мутація контейнера модуля з функції (`КЕШ[к] = …`, `ЗАПИСИ.append(…)`) — кеш чи слід: його читання в
        іншому виклику не несе її значення далі (на шляху, що рахує, значення й так іде поверненням)."""
        if not мітки:
            return
        if мутація and ім not in self.локальні and ім not in self.глобальні:
            return
        if ім in self.локальні or ім not in self.м.присвоєння:
            self.env[ім] = self.env.get(ім, E) | мітки
        if ім in self.глобальні or (ім not in self.локальні and ім in self.м.присвоєння):
            к = (self.м.ім, ім)
            if мітки - self.а.глоб[к]:
                self.а.глоб[к] = self.а.глоб[к] | мітки
                self.а.змінилось = True

    def присвоїти(self, ціль, мітки, значення=None):
        if isinstance(ціль, ast.Name):
            сам = значення.value if isinstance(значення, (ast.Await, ast.YieldFrom)) else значення
            if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "setdefault" \
                    and isinstance(сам.func.value, ast.Name) and сам.func.value.id in self.локальні:
                self.псевдоніми[ціль.id] = сам.func.value.id
            if isinstance(сам, (ast.IfExp, ast.BoolOp)):
                мітки, кл = self.значення(сам)
                for к, в in (кл or {}).items():
                    self.ключі[ціль.id][к] = self.ключі[ціль.id][к] | в
            elif self.з_ключами(значення):
                мітки = self.без_ключів(значення)
            elif isinstance(сам, ast.Call) and id(сам) in self.ключі_викликів and self.ключі_викликів[id(сам)][1]:
                мітки = self.ключі_викликів[id(сам)][0]
            elif isinstance(сам, ast.Name) and any(self.ключі.get(сам.id, {}).values()):
                мітки = self.читати_env(сам.id)
            elif isinstance(сам, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.List, ast.Subscript, ast.BinOp,
                                  ast.DictComp, ast.Tuple)) or self.наступний(сам) or (
                    isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute)
                    and сам.func.attr in ("get", "pop", "values")):
                м, кл = self.значення(сам)
                if кл:
                    мітки = м
                    for к, в in кл.items():
                        self.ключі[ціль.id][к] = self.ключі[ціль.id][к] | в
            self.писати(ціль.id, мітки)
            if isinstance(значення, ast.Compare):
                г = self.гілка_невідомо(значення)
                if г:
                    self.невідомо[ціль.id] = г
            if значення is not None:
                self.ключі_з(ціль.id, значення)
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            к = self.кортежі_викликів.get(id(значення)) if isinstance(значення, (ast.Call, ast.Await, ast.YieldFrom)) else None
            if isinstance(значення, (ast.Tuple, ast.List)) and len(значення.elts) == len(ціль.elts):
                for ц, з in zip(ціль.elts, значення.elts):
                    self.присвоїти(ц, self.e(з), з)
            elif к and len(к) == len(ціль.elts) and not any(isinstance(ц, ast.Starred) for ц in ціль.elts):
                for ц, (мк, кл) in zip(ціль.elts, к):
                    if isinstance(ц, ast.Name) and кл:
                        self.писати(ц.id, мк)
                        for кк, вв in кл:
                            self.ключі[ц.id][кк] = self.ключі[ц.id][кк] | вв
                    elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and кл \
                            and ц.value.id in self.локальні:
                        # `d[к], інше = f(…)`: запис позиції кортежу — як `d[к] = запис`, ключі окремо від міток
                        self.e(ц.slice)
                        км = self.ключі[ц.value.id]
                        if _рядок(ц.slice):
                            км[ц.slice.value] = км[ц.slice.value] | (мк - {F})
                            for кк, вв in _з_префіксом(ц.slice.value, dict(кл)).items():
                                км[кк] = км[кк] | вв
                        else:
                            for кк, вв in кл:
                                км[кк] = км[кк] | вв
                            км[МАПА] = МАПА_М
                            self.писати(ц.value.id, мк - {F}, мутація=True)
                    else:
                        self.присвоїти(ц, мк | _усі(dict(кл)))
            else:
                for ц in ціль.elts:
                    self.присвоїти(ц, мітки)
        elif isinstance(ціль, ast.Starred):
            self.присвоїти(ціль.value, мітки)
        elif isinstance(ціль, (ast.Subscript, ast.Attribute)):
            if isinstance(ціль, ast.Subscript):
                self.e(ціль.slice)
                вм, вк = self.значення(значення) if значення is not None else (мітки, None)
                if isinstance(ціль.value, ast.Name) and _рядок(ціль.slice):
                    for ім in (ціль.value.id, self.псевдоніми.get(ціль.value.id)):
                        if ім is None:
                            continue   # псевдонім елемента мапи (`е = d.setdefault(…)`): запис у е — запис в елемент d
                        к = self.ключі[ім]
                        к[ціль.slice.value] = к[ціль.slice.value] | вм
                        for кл, в in _з_префіксом(ціль.slice.value, вк).items():
                            к[кл] = к[кл] | в
                elif isinstance(ціль.value, ast.Subscript) and self.у_шлях(ціль, вм, вк):
                    return
                elif isinstance(ціль.value, ast.Subscript) and isinstance(ціль.value.value, ast.Name) \
                        and not _рядок(ціль.value.slice) and _рядок(ціль.slice) \
                        and ціль.value.value.id in self.локальні and ціль.value.value.id not in self.глобальні:
                    # `d[к]["поле"] = x`: поле елемента мапи d, а не мітка всієї d
                    self.e(ціль.value.slice)
                    км = self.ключі[ціль.value.value.id]
                    км[ціль.slice.value] = км[ціль.slice.value] | (вм - {F})
                    for кл, в in _з_префіксом(ціль.slice.value, вк).items():
                        км[кл] = км[кл] | в
                    км[МАПА] = МАПА_М
                    return
                elif isinstance(ціль.value, ast.Name) and вк and ціль.value.id in self.локальні:
                    # `d[ід] = запис`: ключі запису — ключі елемента d, d — мапа
                    к = self.ключі[ціль.value.id]
                    for кл, в in вк.items():
                        к[кл] = к[кл] | в
                    к[МАПА] = МАПА_М
                    self.писати(ціль.value.id, вм - {F}, мутація=True)
                    return
            корінь = _корінь_імені(ціль)
            ключем = isinstance(ціль, ast.Subscript) and isinstance(ціль.value, ast.Name) and _рядок(ціль.slice)
            if корінь and ключем and ціль.slice.value == "_meta":
                self.писати(корінь, frozenset({F}), мутація=True)
            elif корінь and not ключем:
                self.писати(корінь, мітки - {F}, мутація=True)

    def у_шлях(self, ціль, вм, вк):
        """Запис у `d["а"]["б"]…` (чи `.append` на ньому): мітки — ключу «а/б», ключі значення — під ним.
        Змінний ключ у кінці — як `d[ід] = запис`; змінний посередині — усе значення ключу префікса."""
        корінь, префікс, змінний = _шлях(ціль)
        if not корінь or not префікс or корінь not in self.локальні or корінь in self.глобальні:
            return False
        if len(префікс) > ГЛИБИНА:
            префікс, змінний = префікс[:ГЛИБИНА], True
            вм, вк = вм | _усі(вк), None
        шлях = "/".join(префікс)
        км = self.ключі[корінь]
        км[шлях] = км[шлях] | (вм - {F})
        for кл, в in _з_префіксом(шлях, вк).items():
            км[кл] = км[кл] | в
        return True

    def значення(self, в):
        """Вираз → (мітки поза сталими ключами, ключі dict чи None): ключі dict ідуть у виклик і з повернення окремо."""
        сам = в.value if isinstance(в, (ast.Await, ast.YieldFrom)) else в
        if isinstance(сам, ast.Subscript) and isinstance(сам.slice, ast.Constant) and type(сам.slice.value) is int:
            self.e(сам.value)
            кортеж = self.кортежі_викликів.get(id(сам.value))
            if кортеж and -len(кортеж) <= сам.slice.value < len(кортеж):
                м, кл = кортеж[сам.slice.value]
                return м, (dict(кл) or None)
        if isinstance(сам, (ast.IfExp, ast.BoolOp)):
            гілки = [сам.body, сам.orelse] if isinstance(сам, ast.IfExp) else list(сам.values)
            if isinstance(сам, ast.IfExp):
                self.e(сам.test)
            вих, ключі = E, {}
            for г in гілки:
                м, к = self.значення(г)
                вих |= м
                for кл, з in (к or {}).items():
                    ключі[кл] = ключі.get(кл, E) | з
            self.e(сам)   # місця гілки «невідомо» й запасного числа
            return вих, (ключі or None)
        if self.наступний(сам):
            # `next(р for р in речі if …)`: елемент послідовності — запис із її ключами, а не всі ключі разом
            м, к = self.значення(сам.args[0])
            if к:
                self.e(сам)
                к = dict(к)
                for д in сам.args[1:]:
                    мд, кд = self.значення(д)
                    м |= мд
                    for кл, з in (кд or {}).items():
                        к[кл] = к.get(кл, E) | з
                return м - {F}, к
        if isinstance(сам, ast.Subscript) and isinstance(сам.value, ast.Name) and self.ключі.get(сам.value.id):
            км = self.ключі[сам.value.id]
            self.e(сам)
            if _рядок(сам.slice):
                к = сам.slice.value
                м = self.готове_поле(к, км.get(к, E) | self.індекс(self.читати_env(сам.value.id), сам.slice, сам))
                під = _під(км, к)
                return м, ({п: self.готове_поле(к, з) for п, з in під.items()} or None)
            if isinstance(сам.slice, ast.Constant) and type(сам.slice.value) is int and ("#%d" % сам.slice.value) in км:
                к = "#%d" % сам.slice.value
                return (км[к] | self.індекс(self.читати_env(сам.value.id), ast.Constant(к), сам)), (_під(км, к) or None)
            return self.індекс(self.читати_env(сам.value.id), сам.slice, сам), (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") and сам.args \
                and _рядок(сам.args[0]) and isinstance(сам.func.value, ast.Name) and self.ключі.get(сам.func.value.id) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            км = self.ключі[сам.func.value.id]
            к = сам.args[0].value
            self.e(сам)
            типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
            м = self.готове_поле(к, км.get(к, E) | типове | self.індекс(self.читати_env(сам.func.value.id), сам.args[0], сам))
            return м, ({п: self.готове_поле(к, з) for п, з in _під(км, к).items()} or None)
        if isinstance(сам, (ast.List, ast.Set)) or (isinstance(сам, ast.BinOp) and isinstance(сам.op, ast.Add)):
            частини = сам.elts if isinstance(сам, (ast.List, ast.Set)) else [сам.left, сам.right]
            вих, ключі = E, {}
            for ч in частини:
                м, к = self.значення(ч.value if isinstance(ч, ast.Starred) else ч)
                вих |= м
                ключі = _злити_ключі(ключі, к)
            return вих, (ключі or None)
        if isinstance(сам, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            self.e(сам)
            збережено = self.область(сам)
            try:
                м, к = self.значення(сам.elt)
            finally:
                self.відновити(збережено)
            return ((м - {F, S}) | {K} if _сітка(сам) else м - {F}), к
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and not _рядок(сам.args[0]) and isinstance(сам.func.value, ast.Name) \
                and self.ключі.get(сам.func.value.id) and not self.а.викликані(self.м, сам.func, self.ф) \
                and not self.можливі_ключі(сам.args[0]):
            # `d.get(змінний)`: елемент d за змінним ключем — як `d[змінний]`
            self.e(сам)
            км = self.ключі[сам.func.value.id]
            типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
            return (self.індекс(self.читати_env(сам.func.value.id), сам.args[0], сам) | типове) - {F}, \
                (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and not _рядок(сам.args[0]) and not isinstance(сам.func.value, ast.Name) \
                and not self.а.викликані(self.м, сам.func, self.ф) and not self.можливі_ключі(сам.args[0]):
            # `d["к"].get(змінний)`: елемент мапи під ключем — запис із ключами, а не сума всіх ключів
            мз, кз = self.значення(сам.func.value)
            if кз:
                self.e(сам)
                типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
                return (self.індекс(мз, сам.args[0], сам) | типове) - {F}, (_без_першого(кз) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and _рядок(сам.args[0]) and not isinstance(сам.func.value, ast.Name) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            мз, кз = self.значення(сам.func.value)
            к = сам.args[0].value
            if кз and (к in кз or _під(кз, к)):
                self.e(сам)
                типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
                return (кз.get(к, E) | типове | self.індекс(мз, сам.args[0], сам)), (_під(кз, к) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "pop" \
                and isinstance(сам.func.value, ast.Name) and self.ключі.get(сам.func.value.id) \
                and (not сам.args or (isinstance(сам.args[0], ast.Constant) and type(сам.args[0].value) is int)) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            # `список.pop(і)`: елемент списку записів — ключі запису, не їхня сума
            self.e(сам)
            км = self.ключі[сам.func.value.id]
            return self.індекс(self.читати_env(сам.func.value.id), ast.Constant(0), сам), (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "values" \
                and not сам.args and not self.а.викликані(self.м, сам.func, self.ф):
            мз, кз = self.значення(сам.func.value)
            if кз and МАПА in кз:
                # `d.values()` мапи — її записи з ключами, а не сума всіх ключів
                self.e(сам)
                return мз - {F}, _без_мапи(кз)
        if isinstance(сам, ast.Subscript) and isinstance(сам.slice, ast.Slice):
            self.e(сам)
            return self.значення(сам.value)
        if isinstance(сам, ast.Subscript) and not isinstance(сам.value, ast.Name):
            мз, кз = self.значення(сам.value)
            if кз:
                self.e(сам)
                if _рядок(сам.slice):
                    к = сам.slice.value
                    return (кз.get(к, E) | self.індекс(мз, сам.slice, сам)), (_під(кз, к) or None)
                return self.індекс(мз, сам.slice, сам), (_без_першого(кз) or None)
        if isinstance(сам, ast.DictComp):
            self.e(сам)
            збережено = self.область(сам)
            try:
                мв, кв = self.значення(сам.value)
                мк = self.значення(сам.key)[0]
            finally:
                self.відновити(збережено)
            if кв:
                # ключ dict — рядок чи число, не запис: ключі запису, що їх несе ім'я ключа, у мітки не йдуть;
                # значення — запис чи список записів за змінним ключем: мапа
                return (мк | мв) - {F}, dict(_без_мапи(кв) or {}, **{МАПА: МАПА_М})
        if isinstance(сам, ast.Tuple) and сам.elts and not any(isinstance(x, ast.Starred) for x in сам.elts):
            ключі = {}
            for і, x in enumerate(сам.elts):
                м, к = self.значення(x)
                if м:
                    ключі["#%d" % і] = м
                ключі.update(_з_префіксом("#%d" % і, к))
            return E, (ключі or None)
        if isinstance(сам, ast.Name):
            к = self.ключі.get(сам.id)
            if к and any(к.values()):
                return self.читати_env(сам.id), dict(к)
            return self.читати(сам.id), None
        if self.з_ключами(сам):
            self.e(сам)
            return self.без_ключів(сам), (self.ключі_виразу(сам) or None)
        мітки = self.e(в)
        if isinstance(сам, ast.Call) and id(сам) in self.ключі_викликів:
            поза, ключі = self.ключі_викликів[id(сам)]
            return поза, (dict(ключі) or None)
        return мітки, None

    def область(self, в):
        """Генератори виразу-включення у власній області (Python 3): імена циклу не чіпають однойменних імен функції."""
        імена = {n.id for г in в.generators for n in ast.walk(г.target) if isinstance(n, ast.Name)}
        збережено = {ім: (self.env.get(ім), dict(self.ключі[ім]) if ім in self.ключі else None,
                          self.ключі_циклу.get(ім), self.невідомо.get(ім)) for ім in імена}
        for г in в.generators:
            self.ітерація(г.target, г.iter)
            for у in г.ifs:
                self.e(у)
        return збережено

    def відновити(self, збережено):
        for ім, (env, ключі, цикл, невідомо) in збережено.items():
            for сховище, значення in ((self.env, env), (self.ключі_циклу, цикл), (self.невідомо, невідомо)):
                if значення is None:
                    сховище.pop(ім, None)
                else:
                    сховище[ім] = значення
            self.ключі.pop(ім, None)
            if ключі is not None:
                self.ключі[ім].update(ключі)

    def ітерація(self, ціль, ітер):
        """`for ціль in ітер`: номер `enumerate` і ключ `.items()` — позиція й ім'я, не значення про колорит.
        Ім'я циклу щоразу прив'язане заново (сильне оновлення): два цикли з тим самим ім'ям не зливають елементів."""
        for n in ast.walk(ціль):
            if isinstance(n, ast.Name) and n.id in self.локальні and n.id not in self.глобальні:
                self.env.pop(n.id, None)
                self.ключі.pop(n.id, None)
        if isinstance(ціль, ast.Tuple) and len(ціль.elts) == 2 and isinstance(ітер, ast.Call) and \
                isinstance(ітер.func, ast.Name) and ітер.func.id == "enumerate" and ітер.args:
            self.e(ітер)
            self.присвоїти(ціль.elts[0], E)
            self.елемент(ціль.elts[1], *_перебір(*self.значення(ітер.args[0])))
            return
        if isinstance(ціль, ast.Tuple) and isinstance(ітер, ast.Call) and isinstance(ітер.func, ast.Name) and \
                ітер.func.id == "zip" and len(ітер.args) == len(ціль.elts) and not ітер.keywords and \
                not any(isinstance(x, ast.Starred) for x in ітер.args + ціль.elts):
            self.e(ітер)
            for ц, а in zip(ціль.elts, ітер.args):
                self.елемент(ц, *_перебір(*self.значення(а)))
            return
        if isinstance(ціль, ast.Tuple) and not any(isinstance(x, ast.Starred) for x in ціль.elts) and \
                not (isinstance(ітер, ast.Call) and _ім_виклику(ітер.func) in ("enumerate", "items")):
            м, кл = self.значення(ітер)
            if кл and any(isinstance(к, str) and к.startswith("#") for к in кл):
                self.e(ітер)
                for і, ц in enumerate(ціль.elts):
                    п = "#%d" % і
                    self.елемент(ц, (м | кл.get(п, E)) - {F}, _під(кл, п) or None)
                return
        мітки = self.e(ітер) - {F}
        if isinstance(ціль, ast.Tuple) and len(ціль.elts) == 2 and isinstance(ітер, ast.Call) and \
                isinstance(ітер.func, ast.Attribute) and ітер.func.attr == "items" and not ітер.args:
            if all(isinstance(ц, ast.Name) for ц in ціль.elts):
                self.пари_мап[ціль.elts[0].id] = (ціль.elts[1].id, ітер.func.value)
            self.присвоїти(ціль.elts[0], E)
            м, кл = self.значення(ітер.func.value)
            if кл:
                # значення dict за змінним ключем: мітки поза ключами й ключі елемента
                self.елемент(ціль.elts[1], м - {F}, _без_першого(кл))
            else:
                self.присвоїти(ціль.elts[1], мітки)
            return
        if isinstance(ціль, ast.Name):
            if isinstance(ітер, (ast.Tuple, ast.List, ast.Set)) and ітер.elts and all(_рядок(x) for x in ітер.elts):
                self.ключі_циклу[ціль.id] = self.ключі_циклу.get(ціль.id, frozenset()) | {x.value for x in ітер.elts}
            self.елемент(ціль, *_перебір(*self.значення(ітер)))
            return
        self.присвоїти(ціль, мітки)

    def за_ключем_мапи(self, тест):
        """Звужує значення .items() у решті AND після рівності ключа сталому рядку."""
        if not (isinstance(тест, ast.Compare) and len(тест.ops) == 1 and isinstance(тест.ops[0], ast.Eq)
                and isinstance(тест.left, ast.Name) and тест.left.id in self.пари_мап
                and _рядок(тест.comparators[0])):
            return {}
        ім, вираз = self.пари_мап[тест.left.id]
        збережено = {ім: (self.env.get(ім), dict(self.ключі[ім]) if ім in self.ключі else None,
                          self.ключі_циклу.get(ім), self.невідомо.get(ім))}
        м, кл = self.значення(вираз)
        if not кл:
            return {}
        к = тест.comparators[0].value
        self.env[ім] = кл.get(к, E) | self.індекс(м, тест.comparators[0], тест)
        self.ключі.pop(ім, None)
        self.ключі[ім].update(_під(кл, к))
        return збережено

    def елемент(self, ціль, мітки, ключі):
        """Елемент списку записів: мітки поза ключами й ключі запису."""
        if isinstance(ціль, ast.Name) and ключі:
            self.писати(ціль.id, мітки - {F})
            for кл, в in ключі.items():
                self.ключі[ціль.id][кл] = self.ключі[ціль.id][кл] | в
        else:
            self.присвоїти(ціль, (мітки | _усі(ключі)) - {F})

    def з_ключами(self, в):
        return isinstance(в, ast.Dict) or (isinstance(в, ast.Call) and _ім_виклику(в.func) == "dict"
                                           and isinstance(в.func, ast.Name))

    def без_ключів(self, в):
        """Мітки dict-літерала поза сталими ключами (розгортання, змінні ключі, позиційні аргументи `dict`)."""
        вих = E
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if к is None:
                    вих |= self.значення(з)[0]
                elif not _рядок(к):
                    вих |= self.e(з)
        else:
            for а in в.args:
                вих |= self.значення(а)[0]
            for к in в.keywords:
                if к.arg is None:
                    вих |= self.значення(к.value)[0]
        return вих

    def ключі_з(self, ім, в):
        """Ключі dict-літерала чи `dict(...)`, присвоєного імені (для повернення й опису полів)."""
        for к, з in self.ключі_виразу(в).items():
            self.ключі[ім][к] = self.ключі[ім][к] | з

    def ключі_виразу(self, в):
        вих = {}
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if _рядок(к):
                    м, кк = self.значення(з)
                    if к.value in self.а.готові_поля:
                        м = м - {S}
                    вих[к.value] = вих.get(к.value, E) | м
                    вих = _злити_ключі(вих, _з_префіксом(к.value, кк))
                elif к is None:
                    вих = _злити_ключі(вих, self.значення(з)[1])
        elif isinstance(в, ast.Call) and _ім_виклику(в.func) == "dict":
            for а in в.args:
                вих = _злити_ключі(вих, self.значення(а)[1])
            for к in в.keywords:
                if к.arg:
                    м, кк = self.значення(к.value)
                    if к.arg in self.а.готові_поля:
                        м = м - {S}
                    вих[к.arg] = вих.get(к.arg, E) | м
                    вих = _злити_ключі(вих, _з_префіксом(к.arg, кк))
                else:
                    вих = _злити_ключі(вих, self.значення(к.value)[1])
        elif isinstance(в, (ast.Await, ast.YieldFrom)):
            вих.update(self.ключі_виразу(в.value))
        elif isinstance(в, ast.Call):
            вих.update(self.ключі_викликів.get(id(в), (E, {}))[1])
        elif isinstance(в, ast.Name):
            вих.update(self.ключі.get(в.id, {}))
        токени = _токени(вих.get("code"))
        if self.а.будує_сітку(self.ф) and {'L', 'C', 'h'} <= вих.keys() and any(K in вих[к] for к in ('L', 'C', 'h')):
            for к in ('L', 'C', 'h'):
                вих[к] = (вих[к] - {S}) | {K}
        if токени and self.з_ключами(в):
            for к in list(вих):
                if (к == "values" or к.startswith("values/")) and S in вих[к]:
                    вих[к] = вих[к] | токени
        return вих

    # ── інструкції ──
    def тіло(self, інструкції):
        for н, і in enumerate(інструкції):
            self.інструкція(і)
            if isinstance(і, ast.If) and not і.orelse and і.body \
                    and isinstance(і.body[-1], (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                # `if код not in ТАБЛ: return` — решта тіла йде лише з кодів, що пройшли охорону
                self.у_звуженні(self.звуження(і.test)[1], інструкції[н + 1:])
                return

    def звуження(self, т):
        """Тест на код заяви → (дозволені токени в тілі, в гілці else) чи None. Код — вираз, що несе токени кодів
        (`код`, `з["code"]`); порівняння з рядком чи переліком сталих рядків (літерал чи таблиця модуля).
        Таблицю з включенням беремо з запасом (більше кодів): лише для тіла, для else потрібен точний перелік."""
        if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And):
            тіла = [x for x in (self.звуження(у)[0] for у in т.values) if x is not None]
            return (frozenset.intersection(*тіла) if тіла else None), None
        if not (isinstance(т, ast.Compare) and len(т.ops) == 1 and len(т.comparators) == 1):
            return None, None
        токени = _токени(self.e(т.left))
        if not токени:
            return None, None
        оп, право = т.ops[0], т.comparators[0]
        коди, точно = None, False
        if isinstance(оп, (ast.Eq, ast.NotEq)) and _рядок(право):
            коди, точно = {право.value}, True
        elif isinstance(оп, (ast.In, ast.NotIn)):
            вузол = право
            if isinstance(право, ast.Name) and право.id in self.м.присвоєння and право.id not in self.локальні:
                вузол = self.м.присвоєння[право.id]
            if isinstance(вузол, (ast.Tuple, ast.List, ast.Set)) and all(_рядок(x) for x in вузол.elts):
                коди, точно = {x.value for x in вузол.elts}, True
            elif isinstance(вузол, ast.Dict) and None not in вузол.keys and all(_рядок(x) for x in вузол.keys):
                коди, точно = {x.value for x in вузол.keys}, True
            elif isinstance(вузол, (ast.Dict, ast.Tuple, ast.List, ast.Set, ast.DictComp, ast.SetComp, ast.ListComp,
                                    ast.Call)):
                коди = {n.value for n in ast.walk(вузол) if _рядок(n)}
        if коди is None:
            return None, None
        в_наборі = frozenset(токени & {ТОКЕН + к for к in коди})
        поза = frozenset(токени - {ТОКЕН + к for к in коди}) if точно else None
        return (в_наборі, поза) if isinstance(оп, (ast.Eq, ast.In)) else (поза, в_наборі if точно else None)

    def у_звуженні(self, дозволені, інструкції):
        """Тіло гілки з кодами `дозволені`: мітка S лишається лише на значеннях, чий код серед них (токени без
        перетину з дозволеними знімають S). Без звуження — як є. Записане в гілці додається до незвуженого."""
        if not інструкції:
            return
        if дозволені is None:
            self.тіло(інструкції)
            return
        до_env = dict(self.env)
        до_ключі = {ім: dict(км) for ім, км in self.ключі.items()}
        self.env = {ім: _звузити(м, дозволені) for ім, м in до_env.items()}
        self.ключі = collections.defaultdict(lambda: collections.defaultdict(frozenset),
                                             {ім: collections.defaultdict(frozenset, {к: _звузити(м, дозволені)
                                                                                      for к, м in км.items()})
                                              for ім, км in до_ключі.items()})
        try:
            self.тіло(інструкції)
        finally:
            for ім, м in до_env.items():
                self.env[ім] = self.env.get(ім, E) | м
            for ім, км in до_ключі.items():
                for к, м in км.items():
                    self.ключі[ім][к] = self.ключі[ім][к] | м

    def інструкція(self, і):
        if isinstance(і, ast.Assign):
            мітки = self.e(і.value)
            if id(і) in self.ф.прогресії:
                мітки = (мітки - {S}) | {K}
            ц = і.targets[0]
            if id(і) in self.верх and len(і.targets) == 1 and isinstance(ц, ast.Name) and ц.id in self.локальні \
                    and ц.id not in _імена(і.value):
                self.env.pop(ц.id, None); self.ключі.pop(ц.id, None); self.невідомо.pop(ц.id, None)
            for ц in і.targets:
                self.присвоїти(ц, мітки, і.value)
        elif isinstance(і, ast.AugAssign):
            мк = self.значення(і.value) if isinstance(і.target, ast.Name) and isinstance(і.op, ast.Add) else (E, None)
            if мк[1] and МАПА not in мк[1]:
                # `записи += інші_записи`: список записів росте записами — ключі ідуть ключами, а не в мітки списку
                self.писати(і.target.id, мк[0] - {F}, мутація=True)
                for кл, в in мк[1].items():
                    self.ключі[і.target.id][кл] = self.ключі[і.target.id][кл] | в
            else:
                мітки = self.e(і.value) | self.e(і.target)
                self.присвоїти(і.target, мітки - {F})
        elif isinstance(і, ast.AnnAssign):
            if і.value is not None:
                self.присвоїти(і.target, self.e(і.value), і.value)
        elif isinstance(і, (ast.For, ast.AsyncFor)):
            self.ітерація(і.target, і.iter)
            self.тіло(і.body); self.тіло(і.orelse)
        elif isinstance(і, ast.While):
            self.e(і.test); self.тіло(і.body); self.тіло(і.orelse)
        elif isinstance(і, ast.If):
            self.e(і.test)
            self.невідоме_в_гілці(і)
            в_тілі, в_іншому = self.звуження(і.test)
            self.у_звуженні(в_тілі, і.body)
            self.у_звуженні(в_іншому, і.orelse)
        elif isinstance(і, (ast.With, ast.AsyncWith)):
            for п in і.items:
                м = self.e(п.context_expr)
                if п.optional_vars is not None:
                    self.присвоїти(п.optional_vars, м)
            self.тіло(і.body)
        elif isinstance(і, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            self.тіло(і.body)
            for о in і.handlers:
                self.тіло(о.body)
            self.тіло(і.orelse); self.тіло(і.finalbody)
        elif isinstance(і, ast.Return):
            if і.value is not None:
                мітки, ключі = self.значення(і.value)
                self.пов |= мітки
                for к, з in (ключі or {}).items():
                    self.ключі_пов[к] = self.ключі_пов.get(к, E) | з
                ел = [_ел(*self.значення(x)) for x in і.value.elts] if isinstance(і.value, ast.Tuple) \
                    and not any(isinstance(x, ast.Starred) for x in і.value.elts) else self.кортежі_викликів.get(id(і.value))
                if ел:
                    if self.кортеж is None and not self.кортеж_зламано:
                        self.кортеж = ел
                    elif self.кортеж is not None and len(self.кортеж) == len(ел):
                        self.кортеж = [_злити_ел(x, y) for x, y in zip(self.кортеж, ел)]
                    else:
                        self.кортеж, self.кортеж_зламано = None, True
                elif not (isinstance(і.value, ast.Constant) and і.value.value is None):
                    self.кортеж, self.кортеж_зламано = None, True
        elif isinstance(і, ast.Expr):
            self.e(і.value)
        elif isinstance(і, (ast.Raise,)):
            if і.exc is not None:
                self.e(і.exc)
        elif isinstance(і, ast.Assert):
            self.e(і.test)
        elif isinstance(і, ast.Match):
            self.e(і.subject)
            for к in і.cases:
                self.тіло(к.body)

    # ── п.2: гілка «невідомо» ──
    def гілка_невідомо(self, т):
        """Тест → "так" (гілка тіла — невідомо), "ні" (гілка else — невідомо) чи None; лише коли тест дивиться на S."""
        if isinstance(т, ast.Compare) and len(т.ops) == 1:
            ліво, оп, право = т.left, т.ops[0], т.comparators[0]
            if S not in self.наявне(ліво):
                return None
            if isinstance(право, ast.Constant) and (право.value is None or право.value is False):
                return "так" if isinstance(оп, (ast.Is, ast.Eq)) else "ні" if isinstance(оп, (ast.IsNot, ast.NotEq)) else None
            if _рядок(право) and НЕВІДОМЕ.search(право.value):
                return "так" if isinstance(оп, (ast.Is, ast.Eq)) else "ні" if isinstance(оп, (ast.IsNot, ast.NotEq)) else None
            return None
        if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
            if isinstance(т.operand, ast.Name) and т.operand.id in self.невідомо:
                return {"так": "ні", "ні": "так"}[self.невідомо[т.operand.id]]
            if isinstance(т.operand, ast.Name) and т.operand.id in self.послідовності():
                return None   # порожній перелік, зібраний тут (знахідки, речі), — «нема жодного», а не незнання
            return "так" if S in self.наявне(т.operand) and not isinstance(т.operand, (ast.Compare, ast.Call)) else None
        if isinstance(т, ast.Name) and т.id in self.невідомо:
            return self.невідомо[т.id]
        if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And):
            for в in т.values:
                г = self.гілка_невідомо(в)
                if г == "так":
                    return "так"
        return None

    ПОСЛІДОВНІСТЬ = (ast.List, ast.ListComp, ast.Set, ast.SetComp, ast.Tuple)

    def послідовності(self):
        """Локальні імена, яким функція присвоює лише перелік (`[]`, `[… for …]`, `list(…)`, `sorted(…)`)."""
        if not hasattr(self.ф, "_послідовності"):
            види = collections.defaultdict(set)
            for n in self.ф.власні:
                if isinstance(n, ast.Assign):
                    пари = [(ц, n.value) for ц in n.targets]
                    for ц, з in list(пари):   # `а, б = [], []` — поелементно
                        if isinstance(ц, ast.Tuple) and isinstance(з, (ast.Tuple, ast.List)) \
                                and len(ц.elts) == len(з.elts):
                            пари.extend(zip(ц.elts, з.elts))
                    for ц, з in пари:
                        if isinstance(ц, ast.Name):
                            види[ц.id].add(isinstance(з, self.ПОСЛІДОВНІСТЬ) or (
                                isinstance(з, ast.Call) and isinstance(з.func, ast.Name)
                                and з.func.id in ("list", "sorted", "tuple", "set")))
            self.ф._послідовності = {ім for ім, в in види.items() if в == {True}}
        return self.ф._послідовності

    def наявне(self, в):
        """Мітки, на які дивиться перевірка «є / нема» (`not x`, `x is None`) запису чи списку записів з ключами: як пара
        (`_пара`) — запис, у чиїх ключах поруч з її значенням є дані входу чи файлу (речі з полем її палітри), про річ,
        і його порожнеча — не незнання про неї; її власний запис (смуга, риса) лишається її."""
        км = self.ключі.get(в.id, {}) if isinstance(в, ast.Name) else {}
        if any(км.values()):
            return _пара(self.читати_env(в.id), *[з for к, з in км.items() if к != МАПА])
        return self.e(в)

    @staticmethod
    def ціла_область(в):
        """Пара сталих (−c, c), c > 0: межі обох боків симетричні й однакові — діапазон усієї області, а не число замість незнання."""
        ч = []
        for x in в.elts:
            знак = 1
            if isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub):
                x, знак = x.operand, -1
            if not (isinstance(x, ast.Constant) and isinstance(x.value, (int, float)) and not isinstance(x.value, bool)):
                return False
            ч.append(знак * x.value)
        return ч[0] < 0 < ч[1] and ч[0] == -ч[1]

    def значення_замість(self, в, число=False):
        """Вираз — клас чи число, поставлене кодом (стала, стала модуля, параметр зі сталим типовим).
        `число`: запасне за `or`/`.get` — лише число; рядок там — ім'я, шлях чи підпис, а не її клас (клас замість
        незнання ловить гілка «невідомо»), крім рядка, що зве незнання виміром."""
        if isinstance(в, ast.Constant):
            з = в.value
            if з is None or isinstance(з, bool) or з == "":
                return False
            if isinstance(з, str):
                return bool(ВИМІР.search(з)) if число else not НЕВІДОМЕ.search(з)
            # ±1e9 замість межі — «межі нема», а не число замість її значення
            return isinstance(з, (int, float)) and abs(з) < 1e6
        if isinstance(в, ast.UnaryOp) and isinstance(в.operand, ast.Constant):
            return self.значення_замість(в.operand, число)
        if isinstance(в, ast.Tuple) and len(в.elts) == 2 and self.ціла_область(в):
            return False   # (−c, c): інтервал на всю область, «будь-яка» — межі нема, як ±1e9
        if isinstance(в, ast.Tuple) and в.elts:
            return all(self.значення_замість(x, число) for x in в.elts)
        if isinstance(в, ast.Name) and not self.e(в):
            if в.id in self.ф.типові:
                return self.значення_замість(self.ф.типові[в.id], число)
            з = self.м.присвоєння.get(в.id)
            if з is not None and в.id not in self.локальні:
                return self.значення_замість(з, число)
        return False

    def невідоме_в_гілці(self, і):
        if id(і.test) in self.ф.вільні_пари:
            return
        г = self.гілка_невідомо(і.test)
        if not г:
            return
        гілка = і.body if г == "так" else і.orelse
        for x in гілка:
            в = x.value if isinstance(x, (ast.Assign, ast.Return)) else None
            if в is not None and self.значення_замість(в):
                self.а.місце(self.м, і.test, 2, "гілка «невідомо» (%s) ставить %s"
                             % (_текст(і.test)[:60], _текст(в)[:40]))
                return

    # ── вирази ──
    def e(self, в):
        if в is None:
            return E
        if isinstance(в, ast.Constant):
            return E
        if isinstance(в, ast.Name):
            return self.читати(в.id)
        if isinstance(в, ast.Attribute):
            if в.attr == "AXIS_RELIABILITY":
                return frozenset({R})
            if isinstance(в.value, ast.Name) and в.value.id in self.м.імпорти:
                мод = self.м.імпорти[в.value.id].split(".")[-1]
                return self.а.глоб.get((мод, в.attr), E)
            return self.e(в.value)
        if isinstance(в, ast.Subscript):
            if isinstance(в.value, ast.Name) and _рядок(в.slice):
                return self.ключ_імені(в.value.id, в.slice.value, в)
            if isinstance(в.value, ast.Name) and isinstance(в.slice, ast.Constant) \
                    and type(в.slice.value) is int and в.slice.value >= 0:
                км = self.ключі.get(в.value.id, {})
                if any(isinstance(к, str) and к.startswith('#') for к in км):
                    к = '#%d' % в.slice.value
                    return км.get(к, E) | _усі(_під(км, к)) | self.індекс(self.читати_env(в.value.id), в.slice, в)
            if isinstance(в.value, ast.Subscript) and _рядок(в.slice):
                корінь, префікс, змінний = _шлях(в)
                if корінь and not змінний and len(префікс) <= ГЛИБИНА and self.ключі.get(корінь):
                    км = self.ключі[корінь]
                    вих = self.індекс(self.читати_env(корінь), ast.Constant(префікс[0]), в)
                    for і in range(1, len(префікс) + 1):
                        вих = вих | км.get("/".join(префікс[:і]), E)
                    return вих | _усі(_під(км, "/".join(префікс)))
            if isinstance(в.value, ast.Name) and isinstance(в.slice, ast.Constant) and type(в.slice.value) is int \
                    and ("#%d" % в.slice.value) in self.ключі.get(в.value.id, {}):
                return self.ключ_імені(в.value.id, "#%d" % в.slice.value, в)
            база = self.e(в.value)
            if isinstance(в.slice, ast.Constant) and type(в.slice.value) is int:
                кортеж = self.кортежі_викликів.get(id(в.value))
                if кортеж and -len(кортеж) <= в.slice.value < len(кортеж):
                    м, кл = кортеж[в.slice.value]
                    return м | _усі(dict(кл))
            if isinstance(в.value, ast.Call) and _рядок(в.slice) and id(в.value) in self.ключі_викликів:
                поза, ключі = self.ключі_викликів[id(в.value)]
                return ключі.get(в.slice.value, E) | self.індекс(поза, в.slice, в)
            if isinstance(в.value, ast.Call) and isinstance(в.slice, ast.Constant) \
                    and type(в.slice.value) is int and в.slice.value >= 0 and id(в.value) in self.ключі_викликів:
                поза, ключі = self.ключі_викликів[id(в.value)]
                if any(isinstance(к, str) and к.startswith('#') for к in ключі):
                    к = '#%d' % в.slice.value
                    return ключі.get(к, E) | _усі(_під(ключі, к)) | self.індекс(поза, в.slice, в)
            return self.індекс(база, в.slice, в)
        if isinstance(в, ast.Call):
            return self.виклик(в)
        if isinstance(в, ast.BinOp):
            # число з довіри (вага × значення) — нове число, а не сама довіра: R далі не йде
            л, п = self.e(в.left), self.e(в.right)
            м = _пара(л, п) - {F, R}
            стала_пара = id(в) in self.а.кутові.get(self.ф.повне, ()) and (not л or not п)
            if id(в) in self.пари and S in л | п and (стала_пара or л & {S, P, C, K} and п & {S, P, C, K}):
                if not self.а.пара_глибина:
                    self.а.місце(self.м, в, 1, "її значення входить в арифметику пари: %s" % _текст(в)[:70], вхід=True)
                    self.а.пара_глибина += 1
                    self.вхід_пари = True
                return (м - {S}) | {Q}
            return (м - {S}) | {Q} if self.а.пара_глибина and S in м else м
        if isinstance(в, ast.UnaryOp):
            return self.e(в.operand) - {F}
        if isinstance(в, ast.BoolOp):
            мітки, збережено = [], {}
            try:
                for x in в.values:
                    мітки.append(self.e(x))
                    if isinstance(в.op, ast.And):
                        for ім, стан in self.за_ключем_мапи(x).items():
                            збережено.setdefault(ім, стан)
            finally:
                self.відновити(збережено)
            if isinstance(в.op, ast.Or) and len(в.values) >= 2 and any(S in м for м in мітки[:-1]) \
                    and self.значення_замість(в.values[-1], число=True) \
                    and not all(isinstance(х, ast.BinOp) or isinstance(х, ast.UnaryOp) and not isinstance(х.op, ast.Not)
                                for х in в.values[:-1]):
                self.а.місце(self.м, в, 2, "запасне число: %s" % _текст(в)[:70])
            вих = E
            for м in мітки:
                вих |= м
            return вих
        if isinstance(в, ast.Compare):
            return self.порівняння(в)
        if isinstance(в, ast.IfExp):
            self.e(в.test)
            г = self.гілка_невідомо(в.test)
            if г:
                гілка = в.body if г == "так" else в.orelse
                інша = в.orelse if г == "так" else в.body
                if self.значення_замість(гілка) and not (_рядок(інша) and НЕВІДОМЕ.search(інша.value)):
                    # інша гілка сама каже «невідомо» — отже ця гілка не про незнання (`не_вимір(x) is None` — «вимір»)
                    self.а.місце(self.м, в, 2, "гілка «невідомо» (%s) ставить %s"
                                 % (_текст(в.test)[:50], _текст(гілка)[:40]))
            return self.e(в.body) | self.e(в.orelse)
        if isinstance(в, ast.Dict):
            мітки = [self.e(з) for з in в.values]
            for к in в.keys:
                self.e(к)
            self.довіра(в, мітки, [(м, з) for к, м, з in zip(в.keys, мітки, в.values) if к is not None])
            вих = E
            for к, м in zip(в.keys, мітки):
                вих |= м if к is None else (м - {F})
            return вих
        if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
            вих = E
            for x in в.elts:
                вих |= self.e(x)
            return вих
        if isinstance(в, ast.Starred):
            return self.e(в.value)
        if isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            збережено = self.область(в)
            try:
                if isinstance(в, ast.DictComp):
                    self.e(в.key)
                    return self.e(в.value) - {F}
                м = self.e(в.elt)
                return (м - {F, S}) | {K} if _сітка(в) else м - {F}
            finally:
                self.відновити(збережено)
        if isinstance(в, ast.JoinedStr):
            вих = E
            for x in в.values:
                вих |= self.e(x)
            return вих - {F}
        if isinstance(в, ast.FormattedValue):
            return self.e(в.value)
        if isinstance(в, (ast.Await, ast.YieldFrom)):
            м = self.e(в.value)
            if id(в.value) in self.кортежі_викликів:
                self.кортежі_викликів[id(в)] = self.кортежі_викликів[id(в.value)]
            return м
        if isinstance(в, ast.Yield):
            if в.value is not None:
                self.e(в.value)
                м, кл = self.значення(в.value)
                self.пов |= м
                for к, з in (кл or {}).items():
                    self.ключі_пов[к] = self.ключі_пов.get(к, E) | з
            return E
        if isinstance(в, ast.NamedExpr):
            м = self.e(в.value)
            self.присвоїти(в.target, м, в.value)
            return м
        if isinstance(в, ast.Lambda):
            return self.e(в.body)
        if isinstance(в, ast.Slice):
            self.e(в.lower); self.e(в.upper); self.e(в.step)
            return E
        return E

    def індекс(self, база, ключ, вузол, типове=None):
        if isinstance(ключ, ast.Constant):
            к = ключ.value
        else:
            self.e(ключ)
            к = None
        вих = set()
        if K in база:
            вих.add(K)
        if R in база:
            вих.add(R)
        if Q in база:
            вих.add(Q)
        if self.зерно and isinstance(к, str) and self.а.зерно and к in self.а.зерно["ключі"]:
            вих.add(S)
            self.а.місце(self.м, вузол, 1, "поле відповіді моделі зору `%s` (hex) стає її рисою без позначки оцінки" % к)
        if S in база:
            if isinstance(к, str) and (СЛУЖБОВІ.match(к) or к in self.а.готові_поля):
                pass
            else:
                вих.add(S)
        if P in база:
            if B in база and isinstance(к, str) and к in self.а.носії:
                вих.add(S)
            else:
                вих.add(P)
        if типове is not None:
            мт = self.e(типове)
            вих |= мт
            if S in вих and not мт and self.значення_замість(типове, число=True):
                self.а.місце(self.м, вузол, 2, "запасне число: %s" % _текст(вузол)[:70])
        return frozenset(вих)

    def порівняння(self, в):
        мітки = [self.e(в.left)] + [self.e(x) for x in в.comparators]
        операнди = [в.left] + list(в.comparators)
        if all(isinstance(х, (ast.Set, ast.SetComp)) or isinstance(х, ast.Name) and х.id in self.ф.множини
               or isinstance(х, ast.Call) and isinstance(х.func, ast.Name) and х.func.id in ('set', 'frozenset') for х in операнди):
            return E
        if id(в) in self.а.словесні:
            return E
        for i, оп in enumerate(в.ops):
            л, п = мітки[i], мітки[i + 1]
            if S not in л and S not in п:
                continue
            if S not in _пара(л, п):   # її ознака проти запису з файлу — порівняння про річ
                continue
            if isinstance(оп, ПОРЯДОК):
                if id(в) in self.а.формульні:
                    continue
                self.а.місце(self.м, в, 1, "поріг на пораховане з hex моделі: %s" % _текст(в)[:70])
            elif isinstance(оп, (ast.Eq, ast.NotEq)):
                інший = операнди[i + 1] if S in л else операнди[i]
                if isinstance(інший, ast.Constant) and isinstance(інший.value, (int, float)) \
                        and not isinstance(інший.value, bool):
                    self.а.місце(self.м, в, 1, "рівність числу на порахованому з hex моделі: %s" % _текст(в)[:70])
        return E

    def довіра(self, вузол, мітки, прямі):
        """п.1: запис поєднує оцінку моделі (S без R) і довіру знімку (R) — оцінка дістає довіру виміру камери.
        Довіру дає пряме значення ключа (`прямі`: мітки й вираз), узяте з таблиці довіри тут: вираз читає
        `AXIS_RELIABILITY`, кличе `reliability` чи ім'я, присвоєне з них у цій функції. Запис, що лише копіюється
        (`dict(р, …)`, `{**р}`), чи число, пораховане з довіри далі, несе довіру, дану раніше, — місце там, де її дали."""
        if any(S in м and R not in м for м in мітки) and \
                any(R in м and self.з_таблиці_довіри(з) for м, з in прямі):
            self.а.місце(self.м, вузол, 1, "оцінці моделі дано довіру знімку (`AXIS_RELIABILITY`)")

    def з_таблиці_довіри(self, вираз):
        if not hasattr(self.ф, "_імена_довіри"):
            імена = set()
            присвоєння = [(ц.id, n.value) for n in self.ф.власні if isinstance(n, ast.Assign)
                          for ц in n.targets if isinstance(ц, ast.Name)]
            while True:
                нові = {ім for ім, з in присвоєння if ім not in імена and self._джерело_довіри(з, frozenset(імена))}
                if not нові:
                    break
                імена |= нові
            self.ф._імена_довіри = frozenset(імена)
        return self._джерело_довіри(вираз, self.ф._імена_довіри)

    @staticmethod
    @functools.cache
    def _джерело_довіри(вираз, імена):
        for n in ast.walk(вираз):
            if isinstance(n, ast.Attribute) and n.attr == "AXIS_RELIABILITY":
                return True
            if isinstance(n, ast.Call) and "reliab" in (_ім_виклику(n.func) or ""):
                return True
            if isinstance(n, ast.Name) and n.id in імена:
                return True
        return False

    def виклик(self, в):
        ім = _ім_виклику(в.func)
        if ім == "map" and isinstance(в.func, ast.Name) and len(в.args) == 2 and not в.keywords \
                and not isinstance(в.args[0], ast.Lambda) and not any(isinstance(x, ast.Starred) for x in в.args):
            # `map(f, xs)`: f над елементом xs (мітки й ключі елемента), не над сумою списку
            с = self.а.синтетичні.get(id(в))
            if с is None:
                с = ast.Call(func=в.args[0], args=[ast.Subscript(value=в.args[1], slice=ast.Name(id="_і"))],
                             keywords=[])
                ast.copy_location(с, в); ast.copy_location(с.args[0], в)
                self.а.синтетичні[id(в)] = с
                self.а.тримати.append((в, с))
            self.e(в.args[1])
            вих = self.e(с)
            if id(с) in self.ключі_викликів:
                self.ключі_викликів[id(в)] = self.ключі_викликів[id(с)]
            return вих
        приймач = E
        if isinstance(в.func, ast.Attribute):
            приймач = self.e(в.func.value)
        elif isinstance(в.func, ast.Subscript):
            self.e(в.func.slice)
        позиційні, іменні, зірка, дві = [], {}, E, E
        поз_к, імен_к = [], {}   # те саме з ключами dict: (мітки поза ключами, ключі)
        лямбди = []
        for а in в.args:
            рз = self.розгорнуті.get(а.value.id) if isinstance(а, ast.Starred) and isinstance(а.value, ast.Name) \
                and а.value.id == self.ф.зірка else None
            if рз:
                for кл in sorted(рз):
                    мітки, ключі = рз[кл]
                    позиційні.append(мітки | _усі(ключі))
                    поз_к.append((мітки, ключі) if ключі else мітки)
            elif isinstance(а, ast.Starred):
                зірка |= self.e(а.value)
            elif isinstance(а, ast.Lambda):
                лямбди.append(а)
                позиційні.append(E)
                поз_к.append(E)
            else:
                мітки, ключі = self.значення(а)
                позиційні.append(мітки | _усі(ключі))
                поз_к.append((мітки, ключі) if ключі else мітки)
        for к in в.keywords:
            if isinstance(к.value, ast.Lambda):
                лямбди.append(к.value)
                if к.arg:
                    іменні[к.arg] = E
                    імен_к[к.arg] = E
                continue
            рз = self.розгорнуті.get(к.value.id) if isinstance(к.value, ast.Name) and к.arg is None \
                and к.value.id == self.ф.дві_зірки else None
            if рз:
                for кл, (мітки, ключі) in рз.items():
                    іменні[кл] = мітки | _усі(ключі)
                    імен_к[кл] = (мітки, ключі) if ключі else мітки
            elif к.arg is None:
                мітки, ключі = self.значення(к.value)
                дві |= мітки
                for кл in {str(x).split("/")[0] for x in (ключі or {}) if x != МАПА}:   # `**запис`: ключ — аргумент
                    м, під = ключі.get(кл, E), _під(ключі, кл)
                    іменні[кл] = іменні.get(кл, E) | м | _усі(під)
                    імен_к[кл] = (м, під) if під else м
            else:
                мітки, ключі = self.значення(к.value)
                іменні[к.arg] = мітки | _усі(ключі)
                імен_к[к.arg] = (мітки, ключі) if ключі else мітки
        усі = приймач | зірка | дві
        for м in позиційні:
            усі |= м
        for м in іменні.values():
            усі |= м
        елемент = None
        if ім in ("sorted", "sort", "min", "max", "filter", "map", "nsmallest", "nlargest", "groupby"):
            джерело = в.func.value if ім == "sort" and isinstance(в.func, ast.Attribute) else \
                next((x for x in в.args if not isinstance(x, (ast.Lambda, ast.Starred, ast.Constant))), None)
            if джерело is not None:
                елемент = _перебір(*self.значення(джерело))
        for л in лямбди:
            for а in л.args.args:
                if елемент is not None and len(л.args.args) == 1:
                    # ключ сорту чи фільтр: параметр — елемент послідовності з ключами запису
                    м, кл = елемент
                    м = self.індекс(м, ast.Constant(0), в)
                    self.env[а.arg] = self.env.get(а.arg, E) | (м - {F})
                    for кк, вв in (_без_першого(кл) or {}).items():
                        self.ключі[а.arg][кк] = self.ключі[а.arg][кк] | вв
                else:
                    self.env[а.arg] = self.env.get(а.arg, E) | (усі - {F})
                self.локальні.add(а.arg)
            self.e(л.body)
        # методи-мутації й читання dict
        if isinstance(в.func, ast.Attribute):
            if ім in МУТАЦІЇ:
                корінь = _корінь_імені(в.func.value)
                if ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Name) and корінь in self.локальні:
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        if корінь in self.ф.сіткові_імена:
                            мітки = (мітки - {S}) | {K}
                        self.писати(корінь, мітки - {F})
                        for кл, вв in (ключі or {}).items():
                            self.ключі[корінь][кл] = self.ключі[корінь][кл] | вв
                elif ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Subscript) and isinstance(в.func.value.value, ast.Name) and \
                        not _рядок(в.func.value.slice) and корінь in self.локальні and корінь not in self.глобальні:
                    # `d[ключ].append(запис)`: як `d[ід] = запис` — ключі запису стають ключами елемента d
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        self.писати(корінь, мітки - {F}, мутація=True)
                        for кл, вв in (ключі or {}).items():
                            self.ключі[корінь][кл] = self.ключі[корінь][кл] | вв
                        if ключі:
                            self.ключі[корінь][МАПА] = МАПА_М
                elif ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Subscript) and _шлях(в.func.value)[1] and \
                        корінь in self.локальні and корінь not in self.глобальні:
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        self.у_шлях(ast.Subscript(value=в.func.value, slice=ast.Name(id="_")), мітки, ключі)
                elif ім == "update" and isinstance(в.func.value, ast.Name) and not в.args:
                    pass   # лише іменні: кожне — свій ключ (нижче)
                elif ім == "update" and isinstance(в.func.value, ast.Name):
                    for з in поз_к:
                        self.писати(корінь, (з[0] if isinstance(з, tuple) else з) - {F}, мутація=True)
                elif ім == "setdefault" and len(в.args) == 2 and isinstance(в.func.value, ast.Name) \
                        and корінь in self.локальні:
                    pass   # запис у мапу — нижче; ключ, як у `d[ід] = запис`, міток елемента не дає
                elif корінь:
                    self.писати(корінь, (усі - приймач) - {F}, мутація=True)
                if ім == "update" and isinstance(в.func.value, ast.Name):
                    for а in в.args:
                        self.ключі_з(в.func.value.id, а)
                    for к in в.keywords:
                        if к.arg:
                            кк = self.ключі[в.func.value.id]
                            м, підк = імен_к[к.arg] if isinstance(імен_к.get(к.arg), tuple) else (іменні.get(к.arg, E), None)
                            кк[к.arg] = кк[к.arg] | м
                            for кл, вв in _з_префіксом(к.arg, підк).items():
                                кк[кл] = кк[кл] | вв
                if ім == "setdefault" and isinstance(в.func.value, ast.Name) and len(в.args) == 2 \
                        and корінь in self.локальні:
                    # `е = d.setdefault(к, запис)`: елемент мапи d — запис із ключами, а не сума всіх ключів d
                    мд, кд = self.значення(в.args[1])
                    км = self.ключі[корінь]
                    for кл, вв in (кд or {}).items():
                        км[кл] = км[кл] | вв
                    км[МАПА] = МАПА_М
                    self.писати(корінь, мд - {F}, мутація=True)
                    ключі = _злити_ключі(_без_першого(км), кд)
                    поза = (self.читати_env(корінь) | мд) - {F}
                    if ключі:
                        self.ключі_викликів[id(в)] = (поза, ключі)
                    return поза | _усі(ключі)
                return (приймач | усі) - {F} if ім == "setdefault" else E
            if ім in ("get", "pop") and в.args and not self.а.викликані(self.м, в.func, self.ф):
                if isinstance(в.func.value, ast.Name) and _рядок(в.args[0]):
                    return self.ключ_імені(в.func.value.id, в.args[0].value, в, в.args[1] if len(в.args) > 1 else None)
                if not isinstance(в.func.value, ast.Name) and _рядок(в.args[0]):
                    мз, кз = self.значення(в.func.value)
                    к = в.args[0].value
                    if кз and (к in кз or _під(кз, к)):
                        return кз.get(к, E) | _усі(_під(кз, к)) | self.індекс(мз, в.args[0], в,
                                                                             в.args[1] if len(в.args) > 1 else None)
                if isinstance(в.func.value, ast.Name) and self.можливі_ключі(в.args[0]) \
                        and self.ключі.get(в.func.value.id):
                    self.e(в.args[0])
                    вих = set()
                    for к in self.можливі_ключі(в.args[0]):
                        вих |= self.ключ_імені(в.func.value.id, к, в, в.args[1] if len(в.args) > 1 else None)
                    return frozenset(вих)
                return self.індекс(приймач, в.args[0], в, в.args[1] if len(в.args) > 1 else None)
            if ім == "keys" or (ім in ПОЗИЦІЙНІ and not self.а.викликані(self.м, в.func, self.ф)):
                return E
            if ім in ("items", "values", "copy"):
                return приймач - ({F} if ім != "copy" else set())
            if ім in ("pop",) and в.args:
                return self.індекс(приймач, в.args[0], в, в.args[1] if len(в.args) > 1 else None)
        # зерно: hex із тексту відповіді (запасний хід читача)
        if self.зерно and ім in ("finditer", "findall", "fullmatch", "match", "search"):
            шаблон = в.args[0] if ім != "fullmatch" or not isinstance(в.func, ast.Attribute) else None
            текст_шаблону = ""
            if isinstance(шаблон, ast.Constant) and isinstance(шаблон.value, str):
                текст_шаблону = шаблон.value
            if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                з = self.м.присвоєння.get(в.func.value.id)
                if isinstance(з, ast.Call) and з.args and _рядок(з.args[0]):
                    текст_шаблону += з.args[0].value
            if HEX_РЕГ.search(текст_шаблону) and (P in усі) and S not in усі:
                self.а.місце(self.м, в, 1, "hex із тексту відповіді моделі зору (запасний хід) стає її рисою")
                return frozenset({S})
            if HEX_РЕГ.search(текст_шаблону) and S in усі:
                return frozenset({S})
        if ім in ("any", "all", "bool") and isinstance(в.func, ast.Name) and self.ф.повне in self.а.перевірки:
            self.наявність(в)
        цілі = self.а.викликані(self.м, в.func, self.ф)
        if not цілі:
            if ім in БУЛЕВІ and isinstance(в.func, ast.Name):
                return E
            вих = усі
            if ім in ФАЙЛОВІ:
                return frozenset((усі | {C}) - {S, F})
            if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) \
                    and self.м.імпорти.get(в.func.value.id) == 'math' and ім in ('erf', 'tanh'):
                # Нелінійна обмежена шкала повертає силу/певність; її читачі не є новими входами.
                if S in усі and not self.а.пара_глибина:
                    self.а.місце(self.м, в, 1, "її значення входить у нелінійну шкалу рішення: %s" % _текст(в)[:70])
                return frozenset((усі - {S, F}) | ({Q} if S in усі else set()))
            if ім in ("loads", "deepcopy", "copy", "list", "sorted", "tuple", "set", "reversed", "frozenset") \
                    and len(поз_к) == 1 and isinstance(поз_к[0], tuple):
                мітки, ключі = поз_к[0]   # той самий запис: ключі dict ідуть далі
                if МАПА in ключі and ім not in ("loads", "deepcopy", "copy"):
                    return мітки     # `list(d)`, `sorted(d)` над мапою — її ключі-рядки
                self.ключі_викликів[id(в)] = (мітки, ключі)
                return мітки | _усі(ключі)
            if ім not in ВМІСТИЩА:
                # зовнішня функція над записом бачить запис цілим, але число з неї — не поле запису: ключі запису
                # з її колоритом у нього не йдуть (інакше один ключ із S робив S кожне число з пакета)
                поза = [з[0] if isinstance(з, tuple) else з for з in поз_к + list(імен_к.values())]
                пр = приймач
                if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) \
                        and self.ключі.get(в.func.value.id):
                    пр = self.читати_env(в.func.value.id)
                вих = _пара(пр, зірка, дві, *поза)
            if ім == "reliability":
                вих = вих | {R}
            if ім == "dict" and isinstance(в.func, ast.Name):
                if в.args:
                    вих = self.e(в.args[0]) | ((усі - self.e(в.args[0])) - {F})
                self.довіра(в, позиційні + list(іменні.values()),
                            [(іменні.get(к.arg, E), к.value) for к in в.keywords if к.arg])
                return frozenset(вих)
            return frozenset(вих - {F})
        вих = E
        кортеж = None
        ключі_пов = {}
        for ц in цілі:
            if в.args and _рядок(в.args[0]) and ц.позиційні and ц.позиційні[0] == "код" and поз_к:
                # заява за кодом: сталий код несе токен, і значення її заяви (`ключі_виразу`) знають, з якого
                # вони коду; неоднорідний перелік заяв читач звужує перевіркою коду (`звуження`)
                поз_к = [frozenset({ТОКЕН + в.args[0].value})] + list(поз_к[1:])
            пов = self.а.виклик(ц, поз_к, імен_к, зірка, дві)
            for кл, з in (self.а.останні_ключі or {}).items():
                ключі_пов[кл] = ключі_пов.get(кл, E) | з
            к = self.а.останній_кортеж
            кортеж = к if кортеж is None else ([_злити_ел(x, y) for x, y in zip(кортеж, к)] if к and len(к) == len(кортеж) else [])
            if ц.ім == "reliability" or (ц.модуль.ім.endswith("надійність") and "reliab" in ц.ім):
                пов = пов | {R}
            вих |= пов
            self.риса(в, ц, позиційні, іменні, пов)
            if ц.ім == "зібрати" and ц.модуль.ім == "збирач_промптів":
                self.опис_полів(в)
        if кортеж:
            self.кортежі_викликів[id(в)] = кортеж
        if ключі_пов:
            self.ключі_викликів[id(в)] = (вих, ключі_пов)
        return вих | _усі(ключі_пов)

    def наявність(self, в):
        """п.3: перевірка причини дивиться, чи є запис (`x.get(k) or {}`, `x.get(k, {})`), а не на його значення."""
        for а in в.args:
            вираз = а.elt if isinstance(а, ast.GeneratorExp) else а
            запис = None
            if isinstance(вираз, ast.BoolOp) and isinstance(вираз.op, ast.Or) and isinstance(вираз.values[-1], ast.Dict) \
                    and not вираз.values[-1].keys:
                запис = вираз.values[0]
            elif isinstance(вираз, ast.Call) and _ім_виклику(вираз.func) == "get" and len(вираз.args) == 2 \
                    and isinstance(вираз.args[1], ast.Dict) and not вираз.args[1].keys:
                запис = вираз
            if запис is not None and S in self.e(запис):
                self.а.місце(self.м, в, 3, "причина проходить за наявністю запису, не за значенням: %s" % _текст(в)[:60])
                for м, к, код in self.а.перевірки[self.ф.повне]:
                    self.а.місця.setdefault((м.шлях, к.lineno), set()).add(
                        (3, "причина `%s` звіряється наявністю запису її ознаки, а не значенням" % код))

    def риса(self, в, ц, позиційні, іменні, пов):
        """п.1: hex моделі (S) стає рисою з довірою знімку — виклик будівника рис (`from_photo`) чи запис рис (F)."""
        аргументи = позиційні + list(іменні.values())
        є_оцінка = any(S in м and F not in м for м in аргументи)
        if not є_оцінка:
            return
        if "from_photo" in іменні or any(к.arg == "from_photo" for к in в.keywords):
            self.а.місце(self.м, в, 1, "hex моделі стає рисою з довірою знімку (`from_photo`): %s" % _текст(в.func))
        elif F in пов and any(F in м for м in аргументи):
            self.а.місце(self.м, в, 1, "hex моделі додано рисою в запис рис з довірою знімку: %s" % _текст(в.func))

    def опис_полів(self, в):
        """п.4: поле оголошення, якому дано значення з цього джерела, а опис зве його виміром коду."""
        if len(в.args) < 2:
            return
        оголошення = None
        for а in [в.args[0]] + (list(в.args[0].args) if isinstance(в.args[0], ast.Call) else []):
            if isinstance(а, ast.Name):
                if (self.м.ім, а.id) in self.а.оголошення:
                    оголошення = (self.м.ім, а.id)
                elif а.id in self.м.з_імпортів:
                    мод, ім = self.м.з_імпортів[а.id]
                    if (мод, ім) in self.а.оголошення:
                        оголошення = (мод, ім)
            if оголошення:
                break
        if not оголошення:
            return
        ключі = self.ключі_виразу(в.args[1])
        поля = self.а.оголошення[оголошення]
        м = self.а.модулі[оголошення[0]]
        for к in sorted({str(кл).split("/")[0] for кл in ключі}):
            мітки = ключі.get(к, E) | _усі(_під(ключі, к))
            if S in мітки and к in поля and ВИМІР.search(поля[к][1]):
                рядок, текст = поля[к]
                self.а.місця.setdefault((м.шлях, рядок), set()).add(
                    (4, "опис поля `%s` для моделі зве оцінку моделі виміром: «%s»"
                     % (к, ВИМІР.search(текст).group(0))))
