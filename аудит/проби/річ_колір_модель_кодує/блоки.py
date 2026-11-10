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
    специфікація = colour.notation.munsell.xyY_to_munsell_specification(colour.XYZ_to_xyY(xyz))
    тон, V, C, сектор = map(float, специфікація)
    if math.isnan(C):
        H, C = 30., 0.
    else:
        H = float(colour.notation.munsell.hue_to_ASTM_hue([тон, сектор]))
    точка = ((H - 1) % 100 + 1, V, C)
    if not all(math.isfinite(x) for x in точка) or not коди_точки(точка):
        raise ValueError(f"Свотч {hex}: немає визначеного блоку для {точка}")
    return точка


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
