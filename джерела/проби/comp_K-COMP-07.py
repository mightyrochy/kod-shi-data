# -*- coding: utf-8 -*-
"""K-COMP-07 (формула — стартова точка, не вирок): `python3 проби/comp_K-COMP-07.py`.

ЧОМУ БУЛО «НЕМА В КОДІ»: жоден модуль не читав твердження правила. А воно рівно
одне й перевірне: «formulas seed generation; they never validate output. A
formula-shaped outfit still has to pass the blandness checklist». Обидва входи на
живому шляху вже лежали поруч — назва колірної формули, за якою складали пул
(`спец_слоти["_схема"]`), і чекліст прісності K-SYS-09.
ЩО ПОКАЗУЄ ПРОБА: образ, зібраний за обраною схемою, дає рядок K-COMP-07 із
лічбою провалених пунктів прісності, і ці пункти видно поруч у чеклісті."""
import sys, pathlib, json
_К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_К))
import feed as Ф, bridge as B

вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = B.каталог_останнього_пакета()
сук = next(c for c in кат if c.get("слот") == "сукня")
вз = next(c for c in кат if c.get("слот") == "взуття")
вм = json.loads(B.виклик("від_моделі", json.dumps(
    dict(вх, ід=[сук["id"], вз["id"]]), ensure_ascii=False)))
о = ((вм.get("вердикт") or {}).get("образи") or [{}])[0]
прс = (вм.get("чеклісти") or {}).get("прісність") or []
print("чекліст прісності:", [(p["пункт"], p["стан"]) for p in прс])
з = next((z for z in (о.get("знахідки") or []) if z["правило"] == "K-COMP-07"), None)
print("K-COMP-07:", "НЕМА" if not з else
      "%s %.2f · %s" % (з["сила"], з["сила_нп"], з["суть"][:70]))
print("ремонт:", str((з or {}).get("ремонт"))[:96])
assert з and sum(1 for p in прс if p["стан"] == "провал") >= 1, (з, прс)
