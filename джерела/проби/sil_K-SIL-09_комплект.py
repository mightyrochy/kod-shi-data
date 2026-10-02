# -*- coding: utf-8 -*-
"""СУД-974: `python3 проби/sil_K-SIL-09_комплект.py` — скільки речей каталогу дістає K-SIL-09
як єдина поверхня образу (річ + взуття), по слотах, і чи є серед них комплекти (дві частини)."""
import sys, pathlib, json, collections
_К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_К))
import feed as Ф, bridge as B
from суд_силует import мономісце

вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = B.каталог_останнього_пакета()
вз = next(c for c in кат if c.get("слот") == "взуття")
усього, дає, прикл = collections.Counter(), collections.Counter(), {}
for р in кат:
    сл = р.get("слот")
    if сл not in ("сукня", "комплект", "верх", "низ", "верхній_шар"): continue
    усього[сл] += 1
    з = мономісце([р, вз], [])
    if з:
        дає[сл] += 1
        прикл.setdefault(сл, (р.get("назва") or "")[:44] + " → " + з[0]["суть"][:12])
for сл in усього:
    print("%-12s речей %4d  K-SIL-09 дає %4d  %s" % (сл, усього[сл], дає[сл], прикл.get(сл, "")))
хиб = дає["комплект"]
print("ХИБНІ (комплект = дві частини названий сукнею/однією річчю):", хиб)
