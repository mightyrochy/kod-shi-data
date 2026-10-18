"""Портативне середовище для знімка (крок 0.2-Б): дослід «чи libm — єдина причина розбіжності CPython і Pyodide».

CPython (системний libm) і Pyodide (musl у wasm) дають різні останні біти для `sin cos atan2 exp pow erf tanh`, а `+ − × ÷ sqrt` за IEEE
однакові всюди. Тут ці функції написано лише на `+ − × ÷ sqrt ldexp frexp`, тож будь-яке середовище дає ті самі біти. Якщо знімок із ними
в CPython і в Pyodide збігається байт у байт, а без них ні, то різницю дала саме libm. Точність: розбіжність із libm ≤ кількох ulp
(`python3 знімок_математика.py` друкує її на тисячі точок) — підміна не спотворює результат, лише робить його однаковим.

Другий відомий розбіг платформ — порядок обходу `set`: хеш `float` залежить від ширини `Py_hash_t` (64 біти в CPython, 32 у Pyodide/wasm32),
тож `for C in {16.6, 11.3}` іде в різному порядку. Тут множини в модулях теки замінено на `_Множина` з обходом за значенням.

Підміна не торкається продукту: `встановити(тека)` ставить функції в `math` і вмикає завантажувач, що в модулях теки замінює `a ** b` на
`_pow(a, b)`; файли на диску не міняються."""
import ast, builtins, importlib.abc, importlib.machinery, importlib.util, math, os, sys

PI = 3.141592653589793
PIO2_1, PIO2_2, PIO2_3 = 1.5707963267341256, 6.077100506303966e-11, 2.0222662487959506e-21    # π/2 трьома частинами (Cody–Waite)
LN2_HI, LN2_LO = 6.93147180369123816490e-01, 1.90821492927058770002e-10
INV_LN2 = 1.4426950408889634
СПРАВЖНЄ = {н: getattr(math, н) for н in ('sin', 'cos', 'atan2', 'atan', 'asin', 'acos', 'exp', 'log', 'pow', 'erf', 'tanh', 'hypot')}


def _многочлен(х, коеф):
    р = 0.0
    for к in reversed(коеф):
        р = р * х + к
    return р


_SIN = [(-1.0) ** i / math.factorial(2 * i + 1) for i in range(10)]    # x·(1 − x²/3! + …)
_COS = [(-1.0) ** i / math.factorial(2 * i) for i in range(11)]


def _звести(x):
    """x = k·π/2 + r, |r| ≤ π/4; k за модулем 4. Для великих |x| (не трапляються в кольорі) — справжня функція."""
    k = math.floor(x * (2.0 / PI) + 0.5)
    return int(k) & 3, ((x - k * PIO2_1) - k * PIO2_2) - k * PIO2_3


def sin(x):
    if not math.isfinite(x) or abs(x) > 1e6:
        return СПРАВЖНЄ['sin'](x)
    k, r = _звести(x)
    р2 = r * r
    s, c = r * _многочлен(р2, _SIN), _многочлен(р2, _COS)
    return (s, c, -s, -c)[k]


def cos(x):
    if not math.isfinite(x) or abs(x) > 1e6:
        return СПРАВЖНЄ['cos'](x)
    k, r = _звести(x)
    р2 = r * r
    s, c = r * _многочлен(р2, _SIN), _многочлен(р2, _COS)
    return (c, -s, -c, s)[k]


def atan(x):
    if not math.isfinite(x):
        return math.copysign(PI / 2, x) if math.isinf(x) else x
    знак, x = (-1.0, -x) if x < 0 else (1.0, x)
    обернути = x > 1.0
    if обернути:
        x = 1.0 / x
    for _ in range(3):    # atan t = 2·atan(t / (1 + √(1+t²))): три півкути зводять t до < 0.1
        x = x / (1.0 + math.sqrt(1.0 + x * x))
    х2 = x * x
    р = x * _многочлен(х2, [(-1.0) ** i / (2 * i + 1) for i in range(9)]) * 8.0
    return знак * ((PI / 2 - р) if обернути else р)


def atan2(y, x):
    if x != x or y != y:
        return float('nan')
    if x == 0.0 and y == 0.0 or math.isinf(x) or math.isinf(y):
        return СПРАВЖНЄ['atan2'](y, x)    # нуль і нескінченності: спец. значення однакові скрізь
    if x > 0:
        return atan(y / x)
    if x < 0:
        return (atan(y / x) + (PI if y >= 0 else -PI)) if y != 0 else math.copysign(PI, y)
    return math.copysign(PI / 2, y)


def asin(x):
    if not -1.0 <= x <= 1.0:
        return СПРАВЖНЄ['asin'](x)
    return atan2(x, math.sqrt((1.0 - x) * (1.0 + x)))


def exp(x):
    if not math.isfinite(x) or abs(x) > 700:
        return СПРАВЖНЄ['exp'](x)
    k = math.floor(x * INV_LN2 + 0.5)
    r = (x - k * LN2_HI) - k * LN2_LO
    return math.ldexp(_многочлен(r, [1.0 / math.factorial(i) for i in range(15)]), int(k))


def log(x):
    if not (x > 0.0) or not math.isfinite(x):
        return СПРАВЖНЄ['log'](x)
    m, e = math.frexp(x)
    if m < 0.7071067811865476:
        m, e = m * 2.0, e - 1
    s = (m - 1.0) / (m + 1.0)
    s2 = s * s
    return e * LN2_HI + (e * LN2_LO + 2.0 * s * _многочлен(s2, [1.0 / (2 * i + 1) for i in range(14)]))


def _pow(a, b):
    """`a ** b` без libm: цілі — точно, цілий показник — множенням, дробовий при a>0 — через exp/log; решта — як у Python."""
    ціле = lambda v: isinstance(v, int) and not isinstance(v, bool)
    if ціле(a) and ціле(b):
        return a ** b if b >= 0 else 1 / (a ** -b)
    if isinstance(a, complex) or isinstance(b, complex):
        return a ** b
    a, b = float(a), float(b)
    if b == int(b) and abs(b) <= 1024 and math.isfinite(a):
        n, р, основа = int(abs(b)), 1.0, a
        while n:
            if n & 1:
                р *= основа
            основа *= основа
            n >>= 1
        return р if b >= 0 else 1.0 / р
    if a > 0.0 and math.isfinite(a) and math.isfinite(b):
        return exp(b * log(a))
    return a ** b


def erf(x):
    """erf = 2/√π · e^{−a²} · Σ 2ⁿ a^{2n+1} / (2n+1)!! (члени одного знаку — без втрати точності) до |x| < 3, далі 1 − erfc ланцюговим дробом."""
    if not math.isfinite(x):
        return СПРАВЖНЄ['erf'](x)
    a = abs(x)
    if a < 3.0:
        член, сума, n = a, a, 0
        while член > 1e-18 * сума:
            n += 1
            член *= 2.0 * a * a / (2 * n + 1)
            сума += член
        р = 2.0 / math.sqrt(PI) * exp(-a * a) * сума
    else:
        t = 0.0
        for k in range(60, 0, -1):    # erfc(a) = e^{-a²}/√π · 1/(a + (1/2)/(a + 1/(a + (3/2)/(a + …))))
            t = k / 2.0 / (a + t)
        р = 1.0 - exp(-a * a) / math.sqrt(PI) / (a + t)
    return math.copysign(р, x)


def _expm1_мале(y):
    """e^y − 1 рядом для малих |y| (без віднімання одиниці)."""
    член, сума, n = y, y, 1
    while abs(член) > 1e-18 * abs(сума):
        n += 1
        член *= y / n
        сума += член
    return сума


def tanh(x):
    if abs(x) > 20.0:
        return math.copysign(1.0, x)
    if abs(x) < 0.35:
        е = _expm1_мале(2.0 * x)
        return е / (е + 2.0)
    е = exp(2.0 * x)
    return (е - 1.0) / (е + 1.0)


def hypot(*v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1]) if len(v) == 2 else СПРАВЖНЄ['hypot'](*v)


def _ключ_порядку(х):
    return (type(х).__name__, х) if not isinstance(х, tuple) else ('tuple', tuple(_ключ_порядку(е) for е in х))


def _впорядкувати(елементи):
    try:
        return sorted(елементи, key=_ключ_порядку)
    except TypeError:
        return sorted(елементи, key=repr)


class _Множина(set):
    """Множина з обходом за значенням, а не за хешем. Хеш `float`/великих `int` залежить від ширини `Py_hash_t` (64 біти в CPython,
    32 у Pyodide/wasm32), тож `for x in {16.6, 11.3}` дає різний порядок; тут порядок однаковий скрізь."""
    def __iter__(self):
        return iter(_впорядкувати(set.__iter__(self)))

    def pop(self):
        х = _впорядкувати(set.__iter__(self))[0]
        self.discard(х)
        return х

    def copy(self): return _Множина(set.copy(self))
    def union(self, *і): return _Множина(set.union(self, *і))
    def intersection(self, *і): return _Множина(set.intersection(self, *і))
    def difference(self, *і): return _Множина(set.difference(self, *і))
    def symmetric_difference(self, і): return _Множина(set.symmetric_difference(self, і))
    def __or__(self, і): return _Множина(set.__or__(self, і))
    def __and__(self, і): return _Множина(set.__and__(self, і))
    def __sub__(self, і): return _Множина(set.__sub__(self, і))
    def __xor__(self, і): return _Множина(set.__xor__(self, і))
    __ror__, __rand__, __rxor__ = __or__, __and__, __xor__


class _Заморожена(frozenset):
    def __iter__(self):
        return iter(_впорядкувати(frozenset.__iter__(self)))


def _мн(*арг):
    return _Множина(*арг)


def _зам(*арг):
    return _Заморожена(*арг)


class _ЗамінаСтепеня(ast.NodeTransformer):
    def __init__(self, математика, множини):
        self.математика, self.множини = математика, множини

    def visit_Set(self, вузол):
        self.generic_visit(вузол)
        if not self.множини:
            return вузол
        return ast.copy_location(ast.Call(ast.Name('__пгв_set__', ast.Load()), [вузол], []), вузол)

    visit_SetComp = visit_Set

    def visit_Call(self, вузол):
        self.generic_visit(вузол)
        if self.множини and isinstance(вузол.func, ast.Name) and вузол.func.id in ('set', 'frozenset'):
            вузол.func = ast.copy_location(ast.Name('__пгв_set__' if вузол.func.id == 'set' else '__пгв_frozenset__', ast.Load()), вузол.func)
        return вузол

    def visit_BinOp(self, вузол):
        self.generic_visit(вузол)
        if self.математика and isinstance(вузол.op, ast.Pow):
            return ast.copy_location(ast.Call(ast.Name('__пгв_pow__', ast.Load()), [вузол.left, вузол.right], []), вузол)
        return вузол

    def visit_AugAssign(self, вузол):
        self.generic_visit(вузол)
        if self.математика and isinstance(вузол.op, ast.Pow):
            цільове = ast.parse(ast.unparse(вузол.target), mode='eval').body
            ast.copy_location(цільове, вузол)
            for в in ast.walk(цільове):
                if hasattr(в, 'ctx'):
                    в.ctx = ast.Load()
            нове = ast.Assign([вузол.target], ast.Call(ast.Name('__пгв_pow__', ast.Load()), [цільове, вузол.value], []))
            return ast.copy_location(нове, вузол)
        return вузол


_ПЛАН = dict(математика=True, множини=True)
_МОДУЛІ_МНОЖИН = None    # лише ці модулі (перелік через кому в `множини:модуль,модуль`); None — усі


class _Завантажувач(importlib.machinery.SourceFileLoader):
    def source_to_code(self, дані, шлях, *, _optimize=-1):
        план = dict(_ПЛАН, множини=_ПЛАН['множини'] and (_МОДУЛІ_МНОЖИН is None or self.name in _МОДУЛІ_МНОЖИН))
        дерево = ast.fix_missing_locations(_ЗамінаСтепеня(**план).visit(ast.parse(дані, шлях)))
        return compile(дерево, шлях, 'exec', dont_inherit=True, optimize=_optimize)

    def exec_module(self, модуль):
        модуль.__dict__.update(__пгв_pow__=_pow, __пгв_set__=_мн, __пгв_frozenset__=_зам)
        super().exec_module(модуль)


class _Шукач(importlib.abc.MetaPathFinder):
    def __init__(self, тека):
        self.тека = тека

    def find_spec(self, ім, шлях=None, ціль=None):
        файл = os.path.join(self.тека, ім + '.py')
        if шлях is None and os.path.isfile(файл):
            return importlib.util.spec_from_file_location(ім, файл, loader=_Завантажувач(ім, файл))
        return None


def встановити(тека, що='обидві'):
    """Підмінити те, що просять: `математика` (libm), `множини` (порядок обходу), `обидві`; `множини:palettes,fit` — множини лише
    в названих модулях (з'ясувати, де саме порядок міняє вихід). Викликати до першого імпорту модулів."""
    global _МОДУЛІ_МНОЖИН
    що, _, модулі = що.partition(':')
    _МОДУЛІ_МНОЖИН = set(модулі.split(',')) if модулі else None
    _ПЛАН.update(математика=що in ('математика', 'обидві'), множини=що in ('множини', 'обидві'))
    if _ПЛАН['математика']:
        for ім, ф in (('sin', sin), ('cos', cos), ('atan', atan), ('atan2', atan2), ('asin', asin), ('exp', exp), ('log', log),
                      ('pow', _pow), ('erf', erf), ('tanh', tanh), ('hypot', hypot)):
            setattr(math, ім, ф)
        builtins.pow = lambda a, b, c=None: _pow(a, b) if c is None else СПРАВЖНЄ_POW(a, b, c)
        _підмінити_в_завантажених()
    sys.meta_path.insert(0, _Шукач(тека))


def _підмінити_в_завантажених():
    """`random`, `statistics` та інші модулі стандартної бібліотеки зв'язали libm-функції при імпорті (`from math import log as _log`):
    підміна лише `math.<ім'я>` їх не зачепила б. Тут ті самі об'єкти замінюються в усіх уже завантажених модулях."""
    заміни = {id(СПРАВЖНЄ[ім]): getattr(math, ім) for ім in СПРАВЖНЄ if ім != 'pow'}
    for модуль in list(sys.modules.values()):
        слов = getattr(модуль, '__dict__', None)
        if not isinstance(слов, dict) or модуль is math or модуль is sys.modules.get(__name__):
            continue
        for ім, значення in list(слов.items()):
            if id(значення) in заміни and callable(значення):
                setattr(модуль, ім, заміни[id(значення)])


СПРАВЖНЄ_POW = builtins.pow


def самоперевірка():
    """Розбіжність із libm цього середовища в ulp на сітці точок: показує, що підміна не груба."""
    import random
    ГЕН = random.Random(1)
    вихід = []
    for ім, f, діапазон in (('sin', 'sin', (-20, 20)), ('cos', 'cos', (-20, 20)), ('exp', 'exp', (-20, 20)), ('log', 'log', (1e-6, 1e6)),
                            ('erf', 'erf', (-4, 4)), ('tanh', 'tanh', (-5, 5)), ('atan', 'atan', (-50, 50)), ('asin', 'asin', (-1, 1))):
        мій, справжній, найгірший = globals()[f], СПРАВЖНЄ[f], 0.0
        for _ in range(4000):
            x = ГЕН.uniform(*діапазон)
            a, b = мій(x), справжній(x)
            if a != b:
                найгірший = max(найгірший, abs(a - b) / math.ulp(b if b else 1e-300))
        вихід.append('%s ≤ %.0f ulp' % (ім, найгірший))
    найгірший = 0.0
    for _ in range(4000):
        y, x = ГЕН.uniform(-10, 10), ГЕН.uniform(-10, 10)
        a, b = atan2(y, x), СПРАВЖНЄ['atan2'](y, x)
        найгірший = max(найгірший, abs(a - b) / math.ulp(b) if a != b and b else 0.0)
    вихід.append('atan2 ≤ %.0f ulp' % найгірший)
    найгірший = 0.0
    for _ in range(4000):
        x, y = ГЕН.uniform(0.0, 3.0), ГЕН.uniform(-3.0, 3.0)
        a, b = _pow(x, y), x ** y
        найгірший = max(найгірший, abs(a - b) / math.ulp(b) if a != b and b else 0.0)
    вихід.append('pow ≤ %.0f ulp' % найгірший)
    return ' · '.join(вихід)


if __name__ == '__main__':
    print(самоперевірка())
