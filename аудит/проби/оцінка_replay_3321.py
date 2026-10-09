"""Рядок 3321: replay записаних відповідей `OUTFIT_REVIEW_V1` через `оцінка_образу.прийняти_оцінку`.
Суд відновлено з вхідного промпта запису (ід, образ, запасні, зміни, знахідки, палітра речей). На відповідь друкує:
записів works/change; скільки з них називають за ід річ ПОЗА образом (для change запасні — не поза) і скільки
таких дійшло до картки; окремо, лише для звіту, — у скількох записах на картці ТЕКСТ називає тип речі, якого нема
ні в її речах, ні в крамничній заміні (словник — міра проби; у продукті слів код не читає, п.12).
Запуск: python3 аудит/проби/оцінка_replay_3321.py <тека `джерела`> <відповідь.txt>…"""
import sys, json, re
sys.path.insert(0, sys.argv[1]); import оцінка_образу as О
ТИПИ = {"top": "блуз сорочк футболк светр джемпер лонгслів shirt blouse sweater tee", "bottom": "штан спідниц джинс шорт trouser pant skirt jean",
        "dress": "сукн плать dress", "scarf": "шарф хуст scarf", "shoes": "взутт туфл кросівк черевик ботильйон чобіт shoe boot sneaker",
        "outerwear": "курт пальт піджак жакет блейзер jacket coat blazer", "bag": "сумк bag"}
типи = lambda т: {к for к, в in ТИПИ.items() if any(re.search(r"\b" + с, т.lower()) for с in в.split())}
рядок = lambda т: " ".join(str(т).split())
for ф in sys.argv[2:]:
    т = open(ф, encoding="utf-8").read(); пр, відп = т.split("── ВІДПОВІДЬ", 1); відп = відп.split("\n", 1)[1]; д = json.loads(пр[пр.index("{"):])
    з = О.ід_з_дроту; речі = {з(x["id"]): x for x in д["items"]}; образ = [з(i) for i in д["outfit"]]; зап = [з(i) for i in д.get("alternatives", [])]
    суд = {"образ": образ, "запасні": зап, "зміни": [{"ід": з(c["id"])} for c in д.get("changes", [])],
           "речі": [{"ід": і, "палітра": {"стан": {"in": "у палітрі", "edge": "на межі", "out": "поза палітрою"}.get(x.get("palette"))}} for і, x in речі.items()],
           "суд": {"findings": [{"ід": з(f["id"]), "правило": f["rule"], "регістр": {"remark": "репліка", "gate": "гейт"}.get(f["register"]), "сила_нп": f.get("sila_np"),
                                 "речі": [з(i) for i in f["items"]], "ремонт_заяви": f.get("fix")} for f in д["check"]["findings"]]}}
    в = О._ПР.розбір_останній(відп, ("answer", "verdict"))[0]; р = О.прийняти_оцінку(відп, суд); к = р["картка"] or {}
    if not isinstance(в, dict): print("%s: відповідь не розібрана: %s" % (ф.split("/")[-1][:8], р["причина"])); continue
    шоп = {з(c["id"]): (c.get("with_shop") or {}).get("slot") for c in д.get("changes", [])}
    записи = [("works", x, образ, None) for x in в.get("works", [])] + [("change", x, образ + зап, з(str(x.get("id")))) for x in в.get("change", [])]
    поза = [x for _, x, доп, _ in записи if any(з(str(i)) not in доп for i in x.get("items") or [])]
    на_картці = {рядок(x["текст"]) for x in к["вдало"] + к["змінити"]}
    слова = [(тип, рядок(x.get("text", ""))[:48]) for тип, x, _, ід in записи if рядок(x.get("text", "")) in на_картці and (тип == "works" or ід in шоп)
             and типи(x.get("text", "")) - ({ти for i in образ + зап if i in речі for ти in {речі[i]["slot"]} | типи(речі[i].get("name") or "")} | {шоп.get(ід)})]
    print("%s: записів %d · на картці %d · ід поза образом %d (з них на картці %d) · сторож %s · тип поза речами й заміною: %d %s" % (
          ф.split("/")[-1][:8], len(записи), len(на_картці), len(поза), sum(рядок(x.get("text", "")) in на_картці for x in поза),
          [c["чому"] for c in р["сторож"]] or "—", len(слова), слова))
