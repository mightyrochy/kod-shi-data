"""Крок 23 кореня Річ-колір-межі: тепле ↔ холодне — одне визначення. Знімок дерева для ДО → ПІСЛЯ.

    python3 -W ignore аудит/перевірка/річ_колір_межі_крок23/тепло.py <дерево> <вихід.json.gz>

Точки — `аудит/перевірка/річ_колір_межі_тон_20261105/каталог_точки.json.gz` цього репозиторію (9 535 з Lab):
`colorspace.тепло(h)` кожної точки, `колір_відношення.сила(…, "warm_cool")` пари (i, i+1), `підтон_риси` точки як
риси; жінки `аудит/проби/жінки/ж1–ж9.json` — `міст_основи.палітри` цілком (схеми, основи, температури центрів,
рис і нейтралей); `palettes.СІМ_Ї` — теплота середин версій сімей."""
import gzip, inspect, json, sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
ДЕРЕВО = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ДЕРЕВО / "джерела"))
import colorspace as КП, колір_відношення as ВІД, колір_річ as КР, колір_простір_риси as РИС, palettes as П  # noqa: E402
import міст_основи as МО, палітра_температура as ПТ  # noqa: E402


def ч(x):
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, (list, tuple)):
        return [ч(y) for y in x]
    if isinstance(x, dict):
        return {str(k): ч(v) for k, v in x.items()}
    return x if x is None or isinstance(x, (str, int, bool)) else repr(x)


точки = [р for р in json.load(gzip.open(КОРІНЬ / "аудит/перевірка/річ_колір_межі_тон_20261105/каталог_точки.json.gz", "rt"))
         if р[1] is not None]
записи = [КР.запис_кольору(dict(lab=list(р[1]))) for р in точки]
нова_сигн = "lab" in inspect.signature(РИС.підтон_риси).parameters
вих = dict(точки=[], пари=[], жінки={}, версії={}, нейтралі={к: ч(в["нейтраль_дуга"]) for к, в in ПТ.ТЕМП_НЕЙТРАЛІ.items()})
for i, р in enumerate(точки):
    lab = tuple(float(x) for x in р[1])
    L, C, h = КП.lch(lab)
    п = РИС.підтон_риси(lab) if нова_сигн else РИС.підтон_риси(lab[1], lab[2], h)
    вих["точки"].append([р[0], ч(КП.тепло(h)), п])
    вих["пари"].append(ч(ВІД.сила(записи[i], записи[(i + 1) % len(точки)], "warm_cool", певність=False)))
for ім, в in П.СІМ_Ї.items():
    вих["версії"][ім] = {т: (None if д is None else ч(КП.тепло(П.середина_дуги(д)))) for т, д in в.items()}
for н in range(1, 10):
    d = json.load(open(КОРІНЬ / ("аудит/проби/жінки/ж%d.json" % н), encoding="utf-8"))
    try:
        вх = dict(шкіра=d["skin"], волосся=d["hair"], очі=d["eyes"], обхвати={}, зріст=168)
        вих["жінки"]["ж%d" % н] = ч(json.loads(МО.палітри(вх)))
    except Exception as е:  # noqa: BLE001 — падіння теж факт знімка
        вих["жінки"]["ж%d" % н] = "ПАДІННЯ %s: %s" % (type(е).__name__, е)
json.dump(вих, gzip.open(sys.argv[2], "wt"), ensure_ascii=False)
print("точок", len(точки), "жінок", sum(isinstance(в, dict) for в in вих["жінки"].values()))
