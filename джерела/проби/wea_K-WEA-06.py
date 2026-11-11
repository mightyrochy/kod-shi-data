# -*- coding: utf-8 -*-
"""K-WEA-06: гладка підошва в мороз дає знахідку, у прохолодну смугу — ні.
Без ознаки підошви в мороз питання потрапляє в чергу на вхід."""
import sys, pathlib, json
_К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_К))
import feed as Ф, bridge as B, accessory as АК
вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
вх["сценарій"].update(смуга_погоди='frost', опади="сніг")
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = B.каталог_останнього_пакета()
гладкі = [c for c in кат if c.get("слот") == "взуття"
          and any(g in (c.get("підошва") or "").lower() for g in АК.ГЛАДКА_ПІДОШВА)]
без = [c for c in кат if c.get("слот") == "взуття" and not c.get("підошва")]
print("пар із гладкою підошвою:", len(гладкі), "· без слова про підошву:", len(без))
сукня = next(c["id"] for c in кат if c.get("слот") == "сукня")
def прогін(взуття, t):
    """Судить те саме взуття у явно заданій смузі погоди."""
    вх["сценарій"]["смуга_погоди"] = t
    вм = json.loads(B.виклик("від_моделі", json.dumps(
        dict(вх, ід=[взуття["id"], сукня]), ensure_ascii=False)))
    о = ((вм.get("вердикт") or {}).get("образи") or [{}])[0]
    return next((z for z in (о.get("знахідки") or []) if z.get("правило") == "K-WEA-06"), None)
print("гладка:", гладкі[0]["назва"][:44], "· підошва «%s»" % гладкі[0]["підошва"])
for t in ("frost", "cool"):
    з = прогін(гладкі[0], t)
    assert bool(з) == (t == "frost"), (t, з)
    print("  %s K-WEA-06:" % t, "НЕМА" if not з else
          "%s %.2f · %s" % (з["сила"], з["сила_нп"], з["суть"][:44]))
з = прогін(без[0], "frost")
assert з is None, з
print("без поля підошви у frost: НЕ серед знахідок")
import pipeline as PL, паспорт_нагоди as ПН
F, T, _зр, _kw = B._збірка(вх)
сц, _ = ПН.з_показу(вх["сценарій"], None)
ч = PL.перевірити_від_моделі([без[0]["id"], сукня], F, кат, T, сц).get("черга_на_вхід") or []
к = next((z for z in ч if z.get("правило") == "K-WEA-06"), None)
assert к is not None, ч
print("  у черзі на вхід:", "НЕМА" if not к else "«%s»" % к["суть"][:56])
