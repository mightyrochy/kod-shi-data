"""Крок 24а кореня Річ-колір-межі: знімок дерева для ДО → ПІСЛЯ.

    python3 -W ignore аудит/перевірка/річ_колір_межі_крок24а/знімок.py <дерево> <вихід.json.gz>

Записи — 9 535 точок каталогу (`річ_колір_межі_тон_20261105/каталог_точки.json.gz` цього репозиторію) і 56 вікон
слів `verify.ЛЕКСИКОН`. Пари: точка i з i+1, кожне вікно з кожним, кожне вікно з кожною 10-ю точкою. Для пари —
`колір_річ.відношення` (вердикти всіх класів) і `колір_відношення.сила(…, "warm_cool")` з певністю й без; для запису —
`колір_відношення.акцент` і `певність_тону`; для точки — `bases.відхил_тону_ΔE` при поз ±1; жінки ж1–ж9 —
`міст_основи.палітри` цілком."""
import gzip, json, sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
ДЕРЕВО = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ДЕРЕВО / "джерела"))
import колір_відношення as ВІД, колір_річ as КР, verify as V, bases as Б, міст_основи as МО  # noqa: E402


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
речі = [("т:%s" % р[0], {"lab": [float(x) for x in р[1]]}) for р in точки]
вікна = [("с:%s" % к, {"колір_не_вимір": {"вікно": list(в)}}) for к, в in sorted(V.ЛЕКСИКОН.items())]
n = len(речі)
пари = [(i, (i + 1) % n) for i in range(n)]
всі = речі + вікна
пари += [(n + a, n + b) for a in range(len(вікна)) for b in range(len(вікна))]
пари += [(n + a, b) for a in range(len(вікна)) for b in range(0, n, 10)]
записи = [КР.запис_кольору(x) for _, x in всі]
вих = dict(записи={}, пари={}, відхил={}, жінки={})
for (ім, _), р in zip(всі, записи):
    вих["записи"][ім] = ч([ВІД.акцент(р), ВІД.певність_тону(р)])
for a, b in пари:
    к = "%s|%s" % (всі[a][0], всі[b][0])
    вих["пари"][к] = ч([КР.відношення(всі[a][1], всі[b][1]),
                        ВІД.сила(записи[a], записи[b], "warm_cool"),
                        ВІД.сила(записи[a], записи[b], "warm_cool", певність=False)])
for ім, x in речі:
    вих["відхил"][ім] = ч([Б.відхил_тону_ΔE(tuple(x["lab"]), 1.0), Б.відхил_тону_ΔE(tuple(x["lab"]), -1.0)])
for н in range(1, 10):
    d = json.load(open(КОРІНЬ / ("аудит/проби/жінки/ж%d.json" % н), encoding="utf-8"))
    try:
        вх = dict(шкіра=d["skin"], волосся=d["hair"], очі=d["eyes"], обхвати={}, зріст=168)
        вих["жінки"]["ж%d" % н] = ч(json.loads(МО.палітри(вх)))
    except Exception as е:  # noqa: BLE001 — падіння теж факт знімка
        вих["жінки"]["ж%d" % н] = "ПАДІННЯ %s: %s" % (type(е).__name__, е)
json.dump(вих, gzip.open(sys.argv[2], "wt"), ensure_ascii=False)
print("записів", len(записи), "пар", len(пари), "жінок", sum(isinstance(в, dict) for в in вих["жінки"].values()))
