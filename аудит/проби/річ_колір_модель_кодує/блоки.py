"""Читає блоки ISCC–NBS і переносить свотчі у їхній простір Munsell.

Лабораторна лічба, без зміни класифікатора продукту. Межі, Bradford
і пряме renotation беруться з того самого модуля, що й межі сімей.
"""
import csv
from functools import lru_cache
import importlib.util
import itertools
import math
from pathlib import Path
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import colorspace as простір


def модуль(ім_я):
    """Читає лабораторний модуль за шляхом, не запускаючи його головну команду."""
    шлях = КОРІНЬ / "джерела/лабораторія" / (ім_я + ".py")
    опис = importlib.util.spec_from_file_location(ім_я, шлях)
    результат = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(результат)
    return результат


МЕЖІ = модуль("колір_сім_ї_межі")
ПЕРЕНОС = модуль("колір_сім_ї_контури")


@lru_cache(maxsize=1)
def бібліотека():
    """Звіряє версії з чинним лабораторним перетворенням."""
    return ПЕРЕНОС.залежності()


@lru_cache(maxsize=1)
def клітинки():
    """Дає всі 932 елементарні ділянки 267 блоків без обрізання хроми."""
    return МЕЖІ.прочитати_клітинки(МЕЖІ.КЛІТИНКИ.read_text(encoding="utf-8"))


def містить(межі, точка):
    """Перевіряє замкнену ділянку; на спільній грані приймаються обидва блоки."""
    return all(низ <= x <= верх for x, (низ, верх) in zip(точка, межі))


def коди_точки(точка):
    """Повертає номери всіх блоків, що містять точку H/V/C."""
    H, V, C = точка
    H = (H - 1) % 100 + 1
    тони = (H, 101.) if H == 1 else (H,)
    return {номер for номер, межі in клітинки()
            if any(містить(межі, (тон, V, C)) for тон in тони)}


@lru_cache(maxsize=None)
def свотч_у_munsell(hex):
    """Переносить sRGB свотча через Lab D65 → Bradford C → renotation H/V/C.

    Зворотний Bradford використовує білі й матриці прямого методу модуля.
    Тут немає відстані до центроїда чи розширення ділянки блоку.
    """
    colour = бібліотека()
    xyz = простір.to_xyz(простір.hx(hex))
    від = простір._множ(простір._BRADFORD, простір.БІЛІ["D65"])
    до = простір._множ(простір._BRADFORD, простір.БІЛІ["C"])
    lms = простір._множ(простір._BRADFORD, xyz)
    xyz = простір._множ(простір._BRADFORD_ОБЕРНЕНА,
                       tuple(lms[i] * до[i] / від[i] for i in range(3)))
    xyY = colour.XYZ_to_xyY(xyz)
    V = float(colour.notation.munsell.munsell_value_ASTMD1535(float(xyY[2]) * 100))
    if V < 1:
        H, V, C = низький_свотч(tuple(map(float, xyY)), V)
    else:
        try:
            специфікація = colour.notation.munsell.xyY_to_munsell_specification(xyY)
            тон, _, C, сектор = map(float, специфікація)
            if math.isnan(C):
                H, C = 30., 0.
            else:
                H = float(colour.notation.munsell.hue_to_ASTM_hue([тон, сектор]))
        except RuntimeError:
            if V <= 9:
                raise
            H, V, C = низький_свотч(tuple(map(float, xyY)), V)
        H, C = уточнити_обернення(H, V, C, простір.hx(hex))
    точка = ((H - 1) % 100 + 1, V, C)
    if not all(math.isfinite(x) for x in точка) or not коди_точки(точка):
        raise ValueError(f"Свотч {hex}: немає визначеного блоку для {точка}")
    return точка


def уточнити_обернення(H, V, C, lab):
    """Обертає саме прямий метод модуля, не округлюючи V до цілого.

    Штатний обертач Colour округлює майже цілі V й може не збігатися біля
    білого. Числове розв'язання H/C прибирає цю похибку; допуск залишку
    перевіряє обернення, ніколи не розширює вікно ISCC–NBS.
    """
    from scipy.optimize import least_squares
    пряме = ПЕРЕНОС.зробити_перетворення(бібліотека())

    def залишок(координати):
        """Повертає похибку прямого Lab для числового обернення."""
        тон, хрома = map(float, координати)
        результат, _ = пряме((тон - 1) % 100 + 1, V, хрома)
        return [a - b for a, b in zip(результат, lab)]

    розв_язок = least_squares(залишок, [H, max(C, 1e-8)],
        bounds=([-100, 1e-8], [200, 50]), xtol=1e-12, ftol=1e-12, gtol=1e-12)
    if not розв_язок.success or math.sqrt(sum(x * x for x in розв_язок.fun)) > 1e-5:
        raise ValueError(f"Обернення не підтверджено прямим методом: {розв_язок.fun}")
    return (float(розв_язок.x[0]) - 1) % 100 + 1, float(розв_язок.x[1])


@lru_cache(maxsize=1)
def нижні_вузли():
    """Читає 559 вузлів C=2, V=.2…10 з повної renotation Colour.

    Основний метод модуля викликає овоїд V=0 і відмовляє при V<1.
    Нижні табличні вузли вже є у тому самому джерелі; тут не вводиться
    екстраполяція до чорного чи затискання світлоти свотча до V=1.
    """
    munsell = бібліотека().notation.munsell
    вузли = {}
    for (тон, V, C), xyY in munsell.MUNSELL_COLOURS_ALL:
        if C != 2:
            continue
        h, _, _, сектор = munsell.munsell_colour_to_munsell_specification(f"{тон} {V}/2")
        H = float(munsell.hue_to_ASTM_hue([h, сектор])) % 100
        вузли[V, H] = tuple(map(float, xyY[:2]))
    if len(вузли) != 559:
        raise ValueError("Неповний нижній овоїд renotation")
    return вузли


def нижній_овоід(V):
    """Інтерполює C=2 по ASTM-люмінансі між двома табличними рівнями V."""
    munsell = бібліотека().notation.munsell
    рівні = (.2, .4, .6, .8, *map(float, range(1, 11)))
    if not .2 <= V <= 10:
        raise ValueError(f"Таблична renotation не визначена для V={V}")
    низ, верх = next((a, b) for a, b in zip(рівні, рівні[1:]) if a <= V <= b)
    Y = lambda v: float(munsell.luminance_ASTMD1535(v))
    вага = (Y(V) - Y(низ)) / (Y(верх) - Y(низ))
    вузли = нижні_вузли()
    return [(H, tuple((1 - вага) * a + вага * b for a, b in
                     zip(вузли[низ, H], вузли[верх, H]))
             if (низ, H) in вузли and (верх, H) in вузли else None)
            for H in (i * 2.5 for i in range(40))]


def низький_свотч(xyY, V):
    """Обертає трикутну табличну інтерполяцію всередині C=2.

    Трикутники: біла точка C та сусідні вузли овоїда C=2. Це явне
    лабораторне доповнення для V<1 й незбіжних білих V>9, а не прихована
    можливість основного модуля.
    Числова похибка координат не стає допуском меж блоків.
    """
    x, y, _ = xyY
    білий = tuple(map(float, бібліотека().notation.munsell.CCS_ILLUMINANT_MUNSELL))
    px, py = x - білий[0], y - білий[1]
    овоїд = нижній_овоід(V)
    for i, (H, a) in enumerate(овоїд):
        b = овоїд[(i + 1) % len(овоїд)][1]
        if a is None or b is None:
            continue
        ax, ay = a[0] - білий[0], a[1] - білий[1]
        bx, by = b[0] - білий[0], b[1] - білий[1]
        det = ax * by - ay * bx
        u, v = (px * by - py * bx) / det, (ax * py - ay * px) / det
        if u >= 0 and v >= 0 and u + v <= 1:
            C = 2 * (u + v)
            return (H + 2.5 * v / (u + v)) % 100 if C else 30., V, C
    raise ValueError(f"Свотч поза нижнім овоїдом C=2: {xyY}")


def спільна_грань(ліва, права):
    """Визначає сусідство по двовимірній грані, включно зі швом H=1/101.

    Дотик лише ребром або точкою не є сусіднім блоком у цій лічбі.
    """
    for вісь in range(3):
        a, b = ліва[вісь], права[вісь]
        стик = a[1] == b[0] or b[1] == a[0]
        if вісь == 0:
            стик |= a[0] == 1 and b[1] == 101 or b[0] == 1 and a[1] == 101
        if стик and all(min(ліва[j][1], права[j][1]) > max(ліва[j][0], права[j][0])
                        for j in range(3) if j != вісь):
            return True
    return False


@lru_cache(maxsize=1)
def сусіди():
    """Будує симетричне сусідство блоків за їхніми елементарними ділянками."""
    результат = {код: set() for код in range(1, 268)}
    for (a, ліва), (b, права) in itertools.combinations(клітинки(), 2):
        if a != b and b not in результат[a] and спільна_грань(ліва, права):
            результат[a].add(b)
            результат[b].add(a)
    return результат


def зіставити(еталони, коди, із_сусідами=False):
    """Знаходить взаємно однозначну відповідність кольорів незалежно від порядку."""
    if len(коди) < len(еталони):
        return False
    for вибрані in itertools.permutations(коди, len(еталони)):
        if all(код in правдиві or із_сусідами and any(
                код in сусіди().get(правдивий, ()) for правдивий in правдиві)
               for правдиві, код in zip(еталони, вибрані)):
            return True
    return False


def оновити_словник():
    """Перераховує Lab центрів без sRGB-обрізання й звіряє їх із межами блоків.

    Поля назв і центральної Munsell-точки — вхідні дані таблиці. ISCC має
    необмежені блоки, тому «центроїд» тут означає центральний зразок ISCC,
    а не геометричний центр об'єму нескінченної ділянки.
    """
    шлях = ТЕКА / "словник_iscc_267.tsv"
    with шлях.open(encoding="utf-8") as файл:
        рядки = list(csv.DictReader(файл, delimiter="\t"))
    _, родини = МЕЖІ.прочитати_сім_ї(МЕЖІ.ТАБЛИЦЯ.read_text(encoding="utf-8"))
    colour = бібліотека()
    пряме = ПЕРЕНОС.зробити_перетворення(colour)
    назви = {
        18: "світлий сірувато-червоний", 45: "світлий сіруватий червонувато-коричневий",
        60: "світлий сірувато-коричневий", 79: "світлий сіруватий жовтувато-коричневий",
        109: "світлий сірувато-оливковий", 148: "дуже блідий зелений",
        184: "дуже блідий синій", 202: "дуже блідий пурпурно-синій",
        213: "дуже блідий фіолетовий", 226: "дуже блідий пурпуровий",
        261: "світлий сіруватий пурпурно-червоний",
    }
    for рядок in рядки:
        код = int(рядок["код"])
        джерело = рядок.get("munsell_джерело", рядок["munsell"])
        запис = colour.notation.munsell.munsell_colour_to_munsell_specification(джерело)
        тон, V, C, сектор = map(float, запис)
        метод = "центральний зразок джерела"
        if math.isnan(C):
            H, C = 30., 0.
            позначення = джерело
            xyz = colour.xyY_to_XYZ(colour.notation.munsell_colour_to_xyY(джерело))
            lab = простір.адаптувати_освітлювач(colour.XYZ_to_Lab(
                xyz, illuminant=colour.XYZ_to_xy(простір.БІЛІ["C"])))
        else:
            H = float(colour.notation.munsell.hue_to_ASTM_hue([тон, сектор]))
            H = (H - 1) % 100 + 1
            позначення = джерело
            try:
                lab, _ = пряме(H, V, C)
            except (AssertionError, ValueError):
                H, V, C, lab = визначений_зразок(код, (H, V, C), пряме)
                позначення = ПЕРЕНОС.позначення(H, V, C)
                метод = "внутрішня визначена точка блоку; вихідний зразок поза областю перетворення"
        if код not in коди_точки((H, V, C)):
            raise ValueError(f"Центральний зразок {код}: {рядок['munsell']} поза своїм блоком")
        рядок.update(назва_uk=назви.get(код, рядок["назва_uk"]), родина=родини[код],
                     munsell=позначення, munsell_джерело=джерело, центроїд_метод=метод,
                     hex_центроїд=простір.hex_з_lab(lab),
                     L=f"{lab[0]:.8f}", a=f"{lab[1]:.8f}", b=f"{lab[2]:.8f}")
        if any(c.isascii() and c.isalpha() for c in рядок["назва_uk"]):
            raise ValueError(f"Латина в назві {код}")
    if {int(р["код"]) for р in рядки} != set(range(1, 268)):
        raise ValueError("Словник має містити рівно 267 блоків")
    with шлях.open("w", encoding="utf-8", newline="") as файл:
        писач = csv.DictWriter(файл, fieldnames=рядки[0].keys(), delimiter="\t", lineterminator="\n")
        писач.writeheader()
        писач.writerows(рядки)
    return рядки


def визначений_зразок(код, вихідний, пряме):
    """Обирає відтворювану внутрішню точку того самого блоку без заглушки Lab.

    Спершу перевіряє вихідний зразок з V у визначеній області [1,9].
    Якщо його XYZ непридатний, перевіряє внутрішні чверті власних клітинок.
    Цей вибір лише для показу словника; межі й лічба не залежать від нього.
    """
    H, V, C = вихідний
    кандидати = [(H, min(9., max(1., V)), C)]
    for номер, межі in клітинки():
        if номер != код:
            continue
        осі = []
        for вісь, (низ, верх) in enumerate(межі):
            if вісь == 1:
                низ, верх = max(1., низ), min(9., верх)
            if math.isinf(верх):
                верх = низ + 2
            осі.append([низ + (верх - низ) * частка for частка in (.25, .5, .75)])
        кандидати.extend(itertools.product(*осі))
    for H, V, C in кандидати:
        if код not in коди_точки((H, V, C)):
            continue
        try:
            lab, _ = пряме(H, V, C)
            return H, V, C, lab
        except (AssertionError, ValueError):
            continue
    raise ValueError(f"Немає визначеного центрального зразка блоку {код}")
