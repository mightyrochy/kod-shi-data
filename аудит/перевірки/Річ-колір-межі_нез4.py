"""Незалежна звірка #2518 (ребра зшивання на області renotation): прямий виклик Colour, без лінійної моделі методу.

Запуск із кореня: python3 аудит/перевірки/Річ-колір-межі_нез4.py  (colour-science 0.4.6, numpy 2.2.6, scipy 1.15.3)
Друкує: стани вершин, класи ребер, випадкові проби й межі областей, замкненість контурів після згортання C=0,
метод тону Colour на відкладених H-ребрах, незаокруглений θ свідка 11678.
"""
import importlib.util, json, math, random, warnings
from collections import Counter
from pathlib import Path
warnings.filterwarnings("ignore")
К = Path(__file__).resolve().parents[2]
Л = К / "джерела/лабораторія"


def модуль(назва, файл):
    с = importlib.util.spec_from_file_location(назва, Л / файл)
    м = importlib.util.module_from_spec(с)
    с.loader.exec_module(м)
    return м


З = модуль("зшивання", "колір_сім_ї_зшивання.py")
ОС = модуль("контури", "колір_сім_ї_контури.py")
import colour
from colour.notation import munsell as M

комп = json.loads((Л / "колір_сім_ї_зшивання.json").read_text("utf-8"))
арт = json.loads((Л / "колір_сім_ї_ребра.json").read_text("utf-8"))


def прямо(H, V, C):
    """Сама бібліотека: позначення → xyY → XYZ ≥ 0; будь-яка відмова — немає образу."""
    try:
        xyY = M.munsell_colour_to_xyY(ОС.позначення(H, V, C))
    except (AssertionError, ValueError):
        return False
    xyz = colour.xyY_to_XYZ(xyY)
    return all(math.isfinite(float(x)) for x in xyz) and min(xyz) >= 0


def у(обл, t):
    return any(x["від"] < t < x["до"] or (t == x["від"] and x["замкнено"][0])
               or (t == x["до"] and x["замкнено"][1]) for x in обл)


def пт(вісь, ф, t):
    p = list(ф)
    p.insert("HVC".index(вісь), t)
    return p


def вершини():
    лік, розб = Counter(), 0
    for v, а in zip(комп["вершини"], арт["вершини"]):
        H, V, C = v
        ст = "нейтраль" if C == 0 else "невизначено" if V in (0, 10) else (
            "визначено" if прямо(H, V, C) else "невизначено")
        лік[ст] += 1
        розб += ст != а["стан"]
    print("вершини", dict(лік), "розбіжностей", розб,
          "нейтральних V", len({v[1] for v in комп["вершини"] if v[2] == 0}))
    for s in ("5R 10/4", "5R 0/4", "5R 9.9995/4", "5R 0.5/4"):
        try:
            M.munsell_colour_to_xyY(s)
            print(s, "образ є")
        except AssertionError:
            print(s, "відмова Colour")


def ребра():
    random.seed(2518)
    проб = розб = межпроб = 0
    класи, межі = Counter(), Counter()
    for е, а in zip(комп["ребра"], арт["ребра"]):
        вісь, ф = е["вісь"], е["фіксовані"]
        lo, hi = З.число(е["інтервал"][0]), З.число(е["інтервал"][1])
        кл = а["клас"]
        класи[кл] += 1
        if вісь == "H":
            очік = "нейтральна точка" if ф[1] == 0 else "кінець V" if ф[0] in (0, 10) else "відкладено"
        elif вісь == "V":
            очік = "нейтральний відрізок" if ф[1] == 0 else "V"
        else:
            очік = "кінець V" if ф[1] in (0, 10) else "C"
        розб += кл != очік
        if кл not in ("C", "V"):
            continue
        обл = а["область"]
        top = min(hi, 60.0)
        for _ in range(40):
            t = lo + (top - lo) * random.random()
            if t <= 0:
                continue
            проб += 1
            розб += прямо(*пт(вісь, ф, t)) != у(обл, t)
        for x in обл:
            for бік, (e, зам) in enumerate(((x["від"], x["замкнено"][0]), (x["до"], x["замкнено"][1]))):
                тип = x["межі"][бік]
                межі[тип] += 1
                назовні = -math.inf if бік == 0 else math.inf
                if тип == "дані renotation":
                    ок = (прямо(*пт(вісь, ф, e)) == зам
                          and not прямо(*пт(вісь, ф, math.nextafter(e, назовні)))
                          and прямо(*пт(вісь, ф, math.nextafter(e, -назовні))))
                elif тип == "XYZ":
                    d, s = 1e-9 * max(1, abs(e)), (-1 if бік == 0 else 1)
                    ок = not прямо(*пт(вісь, ф, e + s * d)) and прямо(*пт(вісь, ф, e - s * d))
                else:
                    continue
                межпроб += 1
                розб += not ок
    print("класи", dict(класи), "випадкових проб", проб, "меж", межпроб, dict(межі), "розбіжностей", розб)


def контури():
    в, р = комп["вершини"], комп["ребра"]
    образ = lambda x: ("∞",) if x is None else ("н", в[x][1]) if в[x][2] == 0 else ("х", x)
    розімк, нуль = [], []
    for n, кон in enumerate(комп["контури"]):
        гр, ланц = Counter(), Counter()
        for п in кон:
            i, z = З.розпакувати(п)
            a, b = (образ(x) for x in р[i]["вершини"])
            if a == b and a[0] == "н":
                continue
            ланц[("н", a, b) if a[0] == b[0] == "н" else ("р", i)] += z
            if a[0] != "∞":
                гр[a] -= z
            if b[0] != "∞":
                гр[b] += z
        if any(гр.values()):
            розімк.append(n)
        if not any(ланц.values()):
            нуль.append(n)
    print("контурів", len(комп["контури"]), "розімкнених", розімк, "нульових", нуль)


def тон():
    лік = Counter()
    for е, а in zip(комп["ребра"], арт["ребра"]):
        if а["клас"] != "відкладено":
            continue
        V, C = е["фіксовані"]
        lo, hi = З.число(е["інтервал"][0]), З.число(е["інтервал"][1])
        Vs = [round(V)] if abs(V - round(V)) <= 1e-3 else [math.floor(V), math.floor(V) + 1]
        Cs = [C] if C % 2 == 0 else [2 * math.floor(C / 2), 2 * math.floor(C / 2) + 2]
        методи = set()
        for k in range(401):
            H = lo + (hi - lo) * k / 400
            for v in (v for v in Vs if 1 <= v <= 9):
                for c in (c for c in Cs if c >= 2):
                    sp = M.munsell_colour_to_munsell_specification(ОС.позначення(min(max(H, 1), 101), v, c))
                    if sp[0] % 2.5:
                        методи.add(M.interpolation_method_from_renotation_ovoid(sp))
        лік["Radial" if "Radial" in методи else "Linear" if "Linear" in методи else "без інтерполяції"] += 1
    print("відкладені H-ребра за методом тону Colour:", dict(лік))


def свідок():
    б = ОС.залежності()
    _, θ = ОС.зробити_перетворення(б)(17, 9.9985, 6)
    print("свідок 11678 H=17 V=9.9985 C=6: θ", repr(θ[0]), "→", round(θ[0], 9),
          "до межі половини", abs(θ[0] * 1e9 % 1 - 0.5) * 1e-9)


if __name__ == "__main__":
    вершини(); ребра(); контури(); тон(); свідок()
