# -*- coding: utf-8 -*-
"""ГЕЙТ: ЯКІР БЕЗ РЕЄСТРУ І ВІСЬ, ОДНОСТОРОННЯ НА СВОЇЙ ПОПУЛЯЦІЇ.

ЯКИЙ КОНКРЕТНИЙ ПРОВАЛ ЦЕ ЛОВИТЬ (і вже спіймало):
  colorspace._температура_шкіри рахує підтон як (h − 57.0)/12.0. Обидва числа —
  голі локальні літерали: не в REGISTRY, без тіру, без `де`, без src, і жодного з
  них нема в корпусі. Тому аудит_контрактів їх не бачить ЗА ПОБУДОВОЮ: він
  перевіряє провенанс ЗАРЕЄСТРОВАНИХ констант, а незареєстрована константа
  невидима. Наслідок на реальному рішенні: межа «холодна» = h<51.0°, а T1-діапазон
  тону європейської шкіри (Weatherall & Coombs 1992) = 54.0–77.8°. Отже на цільовій
  популяції клас «холодна» НЕДОСЯЖНИЙ — 0.0% діапазону. Не рідкісний: неможливий.
  palette.температура споживає тепло_силу як ЗНАКОВУ величину → українська
  користувачка майже завжди дістає теплу палітру, і холодний колорит не існує
  за побудовою, а не за виміром.

ДВІ ПЕРЕВІРКИ, І ОБИДВІ ПРО ОДНЕ:
  A. ЯКІР БЕЗ РЕЄСТРУ — числовий літерал у порівнянні чи в нормуванні (x−c)/s
     всередині функції, якої нема в жодному реєстрі провенансу.
  B. ОДНОСТОРОННЯ ВІСЬ — вісь, чий ЗНАК щось означає, перевіряється проти
     діапазону, який вона реально побачить. Якщо одна зі сторін порожня на
     оголошеній популяції — вісь не міряє, вона зсуває.

ДЕ ЛАМАЄТЬСЯ. A дає хибні спрацювання на арифметиці одиниць (×0.5, /2, +1) і на
індексах. Тому «безпечні» числа виключені явним списком, і кожне спрацювання —
питання до людини, не вирок. B вимагає ОГОЛОШЕНОЇ популяції: без неї перевірка
не запускається, бо порівнювати нема з чим.
"""
import ast, sys, os, re, math, importlib

БЕЗПЕЧНІ = {0, 1, 2, -1, 0.0, 1.0, 2.0, 0.5, 100, 100.0, 10, 10.0, 3, 4, 60, 360, 180}
ПОРІВНЯННЯ = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _реєстрові_числа(мод):
    """Усі числа, що вже мають провенанс у реєстрі цього модуля."""
    out = set()
    for nm in ("REGISTRY", "РЕЄСТР", "КОНСТАНТИ"):
        R = getattr(мод, nm, None)
        if not isinstance(R, dict): continue
        for v in R.values():
            val = v.get("val") if isinstance(v, dict) else v
            if isinstance(val, (int, float)) and not isinstance(val, bool): out.add(float(val))
            elif isinstance(val, (tuple, list)):
                out.update(float(x) for x in val if isinstance(x, (int, float)))
    return out


class _Скан(ast.NodeVisitor):
    def __init__(self, реєстрові):
        self.реєстрові = реєстрові; self.знахідки = []; self.func = None

    def visit_FunctionDef(self, node):
        поп, self.func = self.func, node.name
        self.generic_visit(node); self.func = поп

    def _число(self, n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) \
           and not isinstance(n.value, bool):
            return float(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            v = self._число(n.operand)
            return None if v is None else -v
        return None

    def _подати(self, v, node, вид):
        if v is None or v in БЕЗПЕЧНІ or float(v) in self.реєстрові: return
        if abs(v) >= 1900 and abs(v) <= 2100 and float(v).is_integer(): return   # роки
        self.знахідки.append(dict(функція=self.func, рядок=node.lineno,
                                  число=v, вид=вид))

    def visit_Compare(self, node):
        for c in node.comparators:
            if any(isinstance(o, ПОРІВНЯННЯ) for o in node.ops):
                self._подати(self._число(c), node, "поріг у порівнянні")
        self.generic_visit(node)

    def visit_BinOp(self, node):
        # нормування (x − ЦЕНТР) / РОЗКИД — саме та форма, що дала цей провал
        if isinstance(node.op, ast.Div) and isinstance(node.left, ast.BinOp) \
           and isinstance(node.left.op, ast.Sub):
            self._подати(self._число(node.left.right), node, "центр нормування")
            self._подати(self._число(node.right), node, "розкид нормування")
        self.generic_visit(node)


def якорі_без_реєстру(шлях, модуль):
    дерево = ast.parse(open(шлях, encoding="utf-8").read())
    s = _Скан(_реєстрові_числа(модуль)); s.visit(дерево)
    # присвоєння вигляду _Ц = 57.0 всередині функції теж рахуємо, якщо число
    # потім іде в нормування — беремо просто всі іменовані локальні константи ВЕЛИКИМИ
    for node in ast.walk(дерево):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                імена = ([e.id for e in t.elts if isinstance(e, ast.Name)]
                         if isinstance(t, ast.Tuple) else
                         [t.id] if isinstance(t, ast.Name) else [])
                if not імена or not any(і.lstrip("_").isupper() for і in імена): continue
                знач = (node.value.elts if isinstance(node.value, ast.Tuple) else [node.value])
                for і, z in zip(імена, знач):
                    v = s._число(z)
                    if v is None or v in БЕЗПЕЧНІ or v in s.реєстрові: continue
                    s.знахідки.append(dict(функція=f"<локальна {і}>", рядок=node.lineno,
                                           число=v, вид="локальна іменована константа"))
    return s.знахідки


# ─────────── B. ВІСЬ, ОДНОСТОРОННЯ НА ОГОЛОШЕНІЙ ПОПУЛЯЦІЇ ───────────
def односторонність(центр, розкид, діапазон, межа_класу=0.5, N=2000):
    """Яку частку ОГОЛОШЕНОГО діапазону вісь віддає кожному знаку.
    Порожня сторона = вісь не міряє знак, вона його призначає."""
    lo, hi = діапазон; частки = {"−": 0, "0": 0, "+": 0}
    for i in range(N + 1):
        x = lo + (hi - lo) * i / N
        s = (x - центр) / розкид
        частки["+" if s > межа_класу else "−" if s < -межа_класу else "0"] += 1
    return {k: round(100 * v / (N + 1), 1) for k, v in частки.items()}


# ─────────── C. ТВЕРДЖЕННЯ «ТА САМА, ЩО В X» БЕЗ ЖОДНОЇ ЗВ'ЯЗКИ ───────────
# ЯКИЙ ПРОВАЛ ЛОВИТЬ. palette.py оголошував НЕЙТРАЛЬ_C_СТЕЛЯ=24.0, ГУЧНО=40.0,
# КРОК=12.0 з коментарями «той самий, що в outfit.нейтраль», «та сама, що в
# outfit.гучність», «як у outfit». Числа справді збігались — і не трималися нічим.
# Перевірено прямо: зсув outfit.hi_C з 40 на 28 не помітив ЖОДЕН із п'яти гейтів.
# Докстрінг palette.поріг_кольору фіксує, що цей самий провал уже стався ТРИЧІ
# («третій рецидив "генератор проти перевіряльника"»), був полагоджений в одному
# місці — і двійники нагорі файлу пережили лагодження.
#
# ДЕ ЛАМАЄТЬСЯ: збіг ЗНАЧЕНЬ сам по собі нічого не означає — 0.05 трапляється в
# семи модулях без будь-якого спільного сенсу. Тому гейт дивиться не на числа, а
# на ТЕКСТ ТВЕРДЖЕННЯ поруч із присвоєнням: якщо код каже «та сама, що в X», то
# або там має стояти читання з X, або твердження хибне.
# ЗВУЖЕНО ПІСЛЯ ПЕРШОГО ПРОГОНУ: широка версія дала 5 хибних із 6 (ловила прозу
# «та сама річ чи інша», «Те саме зроблять маски try-on»). Гейт із 83% хибних
# спрацювань буде проігнорований, тобто гірший за відсутній. Тепер потрібні ТРИ
# ознаки разом: (1) твердження стоїть у # коментарі, не в докстрінгу; (2) названо
# КОНКРЕТНУ адресу «модуль.імʼя», а не просто модуль; (3) присвоєння несе число.
_ЗАЯВА = r"(та\s+сам\w*|той\s+сам\w*|те\s+саме|як\s+у|береться\s+з|не\s+нов\w+\s+числ\w+)"
_АДРЕСА = r"\b(outfit|colorspace|silhouette|fit|coordination|areas|feed|palette)\.\w+"
# ПОРЯДОК СЛІВ ВІЛЬНИЙ — і це не дрібниця. Перша звужена версія вимагала
# «заява ... адреса» і через це пропустила рівно той рядок, заради якого гейт
# написаний: «# з outfit.нейтраль, не нові числа» ставить адресу ПЕРЕД заявою.
# Перевірено на зіпсованій копії: 0 спрацювань. Гейт, який не ловить свій власний
# провал, — не гейт, тому правило або лагодиться, або йде геть.
ТВЕРДЖЕННЯ = re.compile(
    f"(?:{_ЗАЯВА}[^\n]{{0,50}}?{_АДРЕСА}|{_АДРЕСА}[^\n]{{0,50}}?{_ЗАЯВА})",
    re.IGNORECASE)


def твердження_без_зв_язки(шлях):
    """Присвоєння з голим числом, поруч із яким текст обіцяє тотожність іншому модулю."""
    рядки = open(шлях, encoding="utf-8").read().splitlines()
    дерево = ast.parse("\n".join(рядки))
    голі = {}; кінці = {}
    for node in ast.walk(дерево):
        if not isinstance(node, ast.Assign): continue
        джерело = ast.get_source_segment("\n".join(рядки), node.value) or ""
        # читання з чужого реєстру = зв'язка є
        if re.search(r"\b[A-Za-zА-Яа-я_]+\.(C|REGISTRY|РЕЄСТР)\b", джерело): continue
        if not re.search(r"\d", джерело): continue
        голі[node.lineno] = (ast.get_source_segment("\n".join(рядки), node.targets[0]) or "?",
                             джерело[:40])
        кінці[node.lineno] = getattr(node, "end_lineno", node.lineno) or node.lineno
    знах = []
    for ln, (ім, знач) in голі.items():
        # ВІКНО МУСИТЬ НАКРИВАТИ ВЕСЬ ПРИСВОЄНИЙ ВИРАЗ, а не лише рядки над ним:
        # у B_НЕЙТРАЛЬ = dict(...) обіцянка стояла ВСЕРЕДИНІ дужок, на третьому рядку.
        # Перша версія дивилась тільки вгору й через це втратила рівно той дефект,
        # заради якого гейт написаний (перевірено на зіпсованій копії: 0 спрацювань).
        кінець = кінці.get(ln, ln)
        сирі = рядки[max(0, ln - 6):кінець]
        вікно = "\n".join(l[l.index("#"):] for l in сирі if "#" in l)   # лише коментарі
        m = ТВЕРДЖЕННЯ.search(вікно)
        # «той самий ФОРМАТ» — твердження про схему, не про число: це не двійник.
        if m and "формат" not in m.group(0).lower():
            знах.append(dict(рядок=ln, імʼя=ім, значення=знач,
                             твердження=m.group(0).strip()[:70]))
    return знах


# ─────────── D. МОВЧАЗНИЙ ДВІЙНИК: те саме число проти того самого імені ───────────
# ЧОМУ ОКРЕМО ВІД C. Гейт C ловить копію, БІЛЯ ЯКОЇ Є ОБІЦЯНКА («та сама, що в X»).
# Але найгірший різновид двійника — мовчазний: `whr <= 0.78` стояло в посадка.зони
# і в силует.ролі_зон із тим самим сенсом і БЕЗ ЖОДНОГО коментаря, тож C був сліпий
# за побудовою. Те саме — межі касту ББ (4/10) у colorspace й extract, і `сила_нп`
# проти 0.05 / 0.5 у трьох модулях одразу.
# ЩО САМЕ ЗІСТАВЛЯЄТЬСЯ: не значення (0.05 трапляється всюди без спільного сенсу), а
# ПАРА «ім'я лівого операнда + число». Однакове ім'я проти однакового числа у двох
# модулях — це або одна константа, розмножена копіюванням, або збіг, який треба
# назвати вголос.
# ДЕ ЛАМАЄТЬСЯ: імена мусять збігатися буквально. Двійник, у якого змінні названі
# по-різному (`whr` тут і `відношення_талії` там), лишається невидимим.
def мовчазні_двійники(модулі):
    import collections
    пари = collections.defaultdict(list)
    for м in модулі:
        try: дерево = ast.parse(open(f"{м}.py", encoding="utf-8").read())
        except Exception: continue
        for n in ast.walk(дерево):
            if not isinstance(n, ast.Compare): continue
            л = n.left
            ім = (л.id if isinstance(л, ast.Name) else
                  л.attr if isinstance(л, ast.Attribute) else
                  (л.slice.value if isinstance(л, ast.Subscript)
                   and isinstance(л.slice, ast.Constant)
                   and isinstance(л.slice.value, str) else None))
            if not isinstance(ім, str) or len(ім) < 3: continue
            for c in n.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)) \
                   and not isinstance(c.value, bool) and abs(c.value) > 1e-4:
                    пари[(ім, float(c.value))].append((м, n.lineno))
    return {k: v for k, v in пари.items() if len({m for m, _ in v}) > 1}


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print("=" * 78)
    print("A. ЯКОРІ БЕЗ РЕЄСТРУ  (число вирішує, але провенансу не несе)")
    print("=" * 78)
    всього = 0
    for м in ("colorspace", "outfit", "silhouette", "fit", "coordination",
              "palette", "areas", "feed"):
        try: мод = importlib.import_module(м)
        except Exception as e:
            print(f"  {м}: не імпортується — {e}"); continue
        зн = якорі_без_реєстру(f"{м}.py", мод)
        if not зн: continue
        всього += len(зн)
        print(f"\n  {м}.py — {len(зн)} якорів поза реєстром")
        for z in sorted(зн, key=lambda d: d["рядок"])[:8]:
            print(f"     ряд {z['рядок']:5d}  {z['число']:>10}  {z['вид']:26s} "
                  f"у {z['функція']}")
        if len(зн) > 8: print(f"     … ще {len(зн)-8}")
    print(f"\n  УСЬОГО ЯКОРІВ ПОЗА РЕЄСТРОМ: {всього}")

    print()
    print("=" * 78)
    print("B. ЧИ ДВОСТОРОННЯ ВІСЬ ТЕПЛОТИ НА СВОЇЙ ПОПУЛЯЦІЇ")
    print("=" * 78)
    import colorspace as cs
    Ц, Р = cs.ЦЕНТР_ПІДТОНУ, cs.РОЗКИД_ПІДТОНУ
    for ім, ключ in (("глобальна (Van Song 2026)", "skin_h"),
                     ("європейська (Weatherall & Coombs 1992)", "skin_h_eu")):
        д = cs.REGISTRY[ключ]["val"]
        ч = односторонність(Ц, Р, д)
        порожня = [k for k, v in ч.items() if v == 0.0]
        print(f"\n  {ім}  діапазон {д[0]}–{д[1]}°")
        print(f"     холодна {ч['−']:5.1f}%   нейтральна {ч['0']:5.1f}%   тепла {ч['+']:5.1f}%")
        print(f"     {'✗ ПОРОЖНЯ СТОРОНА: ' + ','.join(порожня) if порожня else '✓ обидві сторони населені'}")
    print()
    print("=" * 78)
    print("C. «ТА САМА, ЩО В X» — ОБІЦЯНКА В КОМЕНТАРІ ПРОТИ ЗВʼЯЗКИ В КОДІ")
    print("=" * 78)
    всього_c = 0
    for м in ("palette", "outfit", "colorspace", "silhouette", "fit",
              "coordination", "areas", "feed"):
        зн = твердження_без_зв_язки(f"{м}.py")
        if not зн: continue
        всього_c += len(зн)
        print(f"\n  {м}.py — {len(зн)}")
        for z in зн:
            print(f"     ряд {z['рядок']:5d}  {z['імʼя'][:24]:24s} = {z['значення'][:20]:20s}")
            print(f"                 обіцяє: «{z['твердження']}» — але читання з того модуля нема")
    print(f"\n  ТВЕРДЖЕНЬ БЕЗ ЗВʼЯЗКИ: {всього_c}")
    if всього_c == 0:
        print("  ✓ кожне «та сама, що в X» підперте читанням з X, а не збігом чисел")

    print()
    print("=" * 78)
    print("D. МОВЧАЗНИЙ ДВІЙНИК: те саме імʼя проти того самого числа у двох модулях")
    print("=" * 78)
    _мод = ["outfit", "colorspace", "palette", "silhouette", "fit", "coordination",
            "areas", "feed", "profile", "extract", "composer", "pipeline",
            "status", "language_gate", "verify"]
    дв = мовчазні_двійники(_мод)
    for (ім, val), місця in sorted(дв.items()):
        print(f"\n  «{ім}» проти {val}")
        for м, ln in місця: print(f"      {м}.py:{ln}")
    print(f"\n  МОВЧАЗНИХ ДВІЙНИКІВ: {len(дв)}")
    if not дв:
        print("  ✓ жодне число не розмножене копіюванням між модулями під тим самим імʼям")

    print()
    print("  ЦІЛЬОВИЙ РИНОК ПРОЄКТУ — український, тобто другий рядок.")
    print("  Поки сторона порожня, знак тепло_сили не є виміром на цій популяції.")
