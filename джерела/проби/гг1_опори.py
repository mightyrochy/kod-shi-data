"""ГГ-1 (рядки 1121, 1290): скільки похвал і відлунь ішло ремонту ЗНАХІДКАМИ ДО і скільки ПІСЛЯ — на збережених живих
вердиктах (руки 1–2, промпт ремонту): ДО — заяви похвал у findings промпта; ПІСЛЯ — K-ACC-01 чинним кодом на тих самих
речах (hex вердикта): знахідки / опори; рука 2 з вимкненим K-ACC-01 — опор нема. Плюс K-COL-01 «колона» на мірі мети «вище».
Запуск із джерела/: python3 проби/гг1_опори.py [тека з ж*_*, типово ../аудит/перевірки/fokus_2/ПІСЛЯ]"""
import json, gzip, glob, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, внутрішня_мова as ВМ, аксесуари_структура as АС, реєстр_правил as РП
import правило_руки2 as Р2, колір_світлота as КС
ПОХВАЛИ = ("accessory_spends_chroma_budget", "column_one_tone_is_her_goal", "border_colour_held_by_companions")
кл = lambda s: s if isinstance(s, str) else next(iter(s))
СЛ = (("bag", "сумка"), ("clutch", "сумка"), ("tote", "сумка"), ("belt", "пояс"), ("scarf", "шарф"), ("kerchief", "шарф"), ("jewel", "прикраси"))
сл = lambda i: ВМ.ключ("slot", ВМ.СЛОТ_ТИПУ.get(i.get("type"))) or next((с for к, с in СЛ if к in (i.get("type") or "")), None)  # тип без слота — не аксесуар
Л = K.Counter()
for f in sorted(glob.glob((sys.argv[1] if len(sys.argv) > 1 else "../аудит/перевірки/fokus_2/ПІСЛЯ") + "/ж*_*/вердикти.txt.gz")):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        cc = {c["крок"]: c for c in в["етапи"]["виклики"]}
        if str(в["рука"]) not in "12" or "repair" not in cc: continue
        for o in json.loads(cc["repair"]["запит"]["текст"])["verdict"]:
            Л["ідей у ремонті"] += 1
            речі = [dict(id=i["n"], назва=i["n"], слот=сл(i), lab=list(cs.hx(i["hex"]))) for i in o["your_outfit"]["items"]
                    if i.get("hex") and i.get("color") not in ("golden", "silvery", "pearly")]
            зн, оп = РП.розділити_опори(АС.аксесуар_як_структура(речі))
            луна = {у["річ"] for z in оп for у in z["учасники"]}   # номери речей відлуння
            for fd in o.get("findings", []):
                for s in fd.get("statements", []):
                    if кл(s) == ПОХВАЛИ[0]: Л["ДО знахідками: відлуння аксесуара" if луна & set(fd.get("items") or ()) else "ДО знахідками: витрата без відлуння"] += 1
                    elif кл(s) in ПОХВАЛИ: Л["ДО знахідками: " + кл(s)] += 1
            Л["ПІСЛЯ знахідками: витрата без відлуння"] += len(зн); Л["ПІСЛЯ опорами: відлуння аксесуара"] += len(оп)
            with Р2.вимкнено(["K-ACC-01"]):
                Л["рука 2 без K-ACC-01: опор"] += len(РП.розділити_опори(АС.аксесуар_як_структура(речі))[1])
E = [dict(річ=r, слот=с, L=40.0, C=5.0, h=60.0, lab=(40.0, 2.0, 4.0), площа=0.4, сім_я="нейтраль", текстура=None) for r, с in (("a", "верх"), ("b", "низ"))]
кол = [z for z in КС.перевірка_value(E, мета="вище") if z.get("правило") == "K-COL-01"]
Л["K-COL-01 «колона» за мети «вище»: знахідок / опор"] = "%d / %d" % (sum(not РП.опора(z) for z in кол), sum(РП.опора(z) for z in кол))
for к, v in Л.items(): print("  %-58s %s" % (к, v))
