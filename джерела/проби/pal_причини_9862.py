# -*- coding: utf-8 -*-
"""9862: суддя `вибір_палітри.прийняти` звіряє КОЖНУ причину з даними (`ЗВІРКА_ПРИЧИН`), а не лише очі.
1) збережена відповідь Д4 (основа 9-го рангу + why_first_advice + чужа схема проти fixed): що приймає суддя;
2) 315 персон (5 шкір × 7 очей × 3 волосся × 3 метали, як у #1592): кожна основа переліку × why_first_advice /
   why_her_eyes → прийнято хибних (ранг>1; без поля eyes). Запуск із `джерела`: python3 проби/pal_причини_9862.py"""
import sys, json, glob, pathlib, itertools
К = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(К))
import вибір_палітри as ВП
Ж = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(str(К.parent / "аудит/проби/жінки/ж*.json")))]
Т = dict(зріст=168, обхвати={"плечі": 98, "груди": 92, "талія": 74, "стегна": 99})
def вхід(ш, о, в, м, **ще):
    return dict(Т, шкіра=ш, волосся=[в], очі=о, **({"драп": {"метал": м}} if м else {}), **ще)
# 1) Д4: ж3, схема fixed «тріада»; модель дала b9 (світло-блакитна тепла L68 приглушена) і схему не з fixed
пер = ВП.перелік(вхід(Ж[2]["skin"][0], Ж[2]["eyes"], Ж[2]["hair"][0], None, схема="тріада"))
б9 = next(o for o in пер["основи"] if (o["назва"], o["L"], o["смуга"], o["темп"]) == ("блакитний", 68, "приглушені", "тепла"))
відп = json.dumps(dict(scheme="neutrals_plus_accent", scheme_reasons=["why_goal_flatter", "why_weather"], base=б9["id"],
                       base_reasons=["why_her_eyes", "why_first_advice"], saturation="muted"))
р = ВП.прийняти(вхід(Ж[2]["skin"][0], Ж[2]["eyes"], Ж[2]["hair"][0], None, схема="тріада"), відп)
print("Д4 основа ранг %d · схема %s (fixed тріада) · причини основи %s · відхилено %s"
      % (б9["ранг"], р["вибір"]["схема"], р["вибір"]["причини"].get("base"), р["відхилено"]))
# 1б) її слова: «вимоги» → випадок.her_words → why_her_words лишається; без слів — знімається; словники узгоджені
assert set(ВП.ПРИЧИНИ) == set(ВП.ЗВІРКА_ПРИЧИН), set(ВП.ПРИЧИНИ) ^ set(ВП.ЗВІРКА_ПРИЧИН)
for вим in ("хочу щось яскраве й червоне", ""):
    d = dict(вхід(Ж[2]["skin"][0], Ж[2]["eyes"], Ж[2]["hair"][0], None), вимоги=вим)
    р = ВП.прийняти(d, json.dumps(dict(base=ВП.перелік(d)["основи"][3]["id"], base_reasons=["why_her_words", "why_first_advice"])))
    print("вимоги «%s» · випадок %s · причини %s · відхилено %s" % (вим, ВП.перелік(d)["випадок"], р["вибір"]["причини"]["base"], р["відхилено"]))
# 2) 315 персон
шк, оч, вол = [list(dict.fromkeys(x[k][0] if k != "eyes" else x[k] for x in Ж))[:n] for k, n in (("skin", 5), ("eyes", 7), ("hair", 3))]
п = {"персон": 0, "перевірок": 0, "прийнято хибних first_advice": 0, "прийнято хибних eyes": 0}
for ш, о, в, м in itertools.product(шк, оч, вол, (None, "теплі", "холодні")):
    d = вхід(ш, о, в, м); пер = ВП.перелік(d); п["персон"] += 1
    for о_ in пер["основи"]:
        р = ВП.прийняти(d, json.dumps(dict(base=о_["id"], base_reasons=["why_first_advice", "why_her_eyes"])))
        пр = (р["вибір"]["причини"] or {}).get("base") or []; п["перевірок"] += 1
        п["прийнято хибних first_advice"] += "why_first_advice" in пр and о_["ранг"] != 1
        п["прийнято хибних eyes"] += "why_her_eyes" in пр and not о_["очі"]
print("ФАКТ ·", п)
