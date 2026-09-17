# -*- coding: utf-8 -*-
"""K-CRA-10 (камера ≠ життя) на живому шляху: `python3 проби/cra_K-CRA-10.py`.

ЧОМУ СЛІДУ НЕ БУЛО: правило жило в коді ЛИШЕ як коментар — `accessory` двічі
посилається на нього («це системне зміщення нашого каналу, як K-CRA-10»), а
емітента не було. Корпус каже прямо: наш рендер приміряння І Є фотографія, тож
фактурний інтерес у ньому систематично занижений — і це зміщення ВЛАСНОГО каналу,
а не вада образу. Тому сила `hint` і умова однобічна: рядок виходить лише тоді,
коли ВЕСЬ інтерес образу фактурний (ні хроми, ні принту)."""
import sys, pathlib, json, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import bridge as B
import colorspace as КС

вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
ФАКТ = ("knit-chunky", "tweed-boucle", "smooth-shine", "satin", "patent")
print("текстури каталогу пакета:",
      collections.Counter(c.get("текстура") for c in кат.values()).most_common(6))


def тиха(c):
    try:
        return КС.lch(c["lab"])[1] < 18 and c.get("візерунок") in (None, "solid")
    except Exception:
        return False


# річ береться з КАТАЛОГУ пакета: потрібна НЕЙТРАЛЬНА річ із фактурою, і
# `перевірити_від_моделі` законно судить річ поза кандидатами.
ц = next(c for c in кат.values() if c.get("текстура") in ФАКТ and тиха(c))
дод = [next(c for c in кат.values() if c["слот"] == сл and тиха(c)
            and c.get("текстура") not in ФАКТ)
       for сл in ("взуття", "пояс") if сл != ц["слот"]]
ід = [c["id"] for c in [ц] + дод]
print("образ:", [(кат[i]["слот"], кат[i].get("текстура")) for i in ід])
вд = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
о = ((вд.get("вердикт") or {}).get("образи") or [{}])[0]
з = next((z for z in (о.get("знахідки") or []) if z["правило"] == "K-CRA-10"), None)
print("K-CRA-10 у вердикті:", "НЕМА" if not з else
      "%s %.2f · %s" % (з["сила"], з["сила_нп"], з["суть"][:62]))
print("  речі рядка:", (з or {}).get("речі"), "· регістр", (з or {}).get("регістр"))
assert з, о.get("знахідки")
