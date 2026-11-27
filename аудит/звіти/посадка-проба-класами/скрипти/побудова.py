"""ДО/ПІСЛЯ для пояснення 30 складів. ДО — запит картки ядра як є (`опис_до/NN.json`), лише без фактів
`catalogue_slot_shortage` (артефакт малого каталогу проби: каталог = речі складу). ПІСЛЯ — той самий запит, де замість
утриманих фактів посадки: у фактах одягу — клас крою й краю, тканина й опис з нового запису (`запис.jsonl`), довжина
виробу крамниці зі старого запису, коли є; відомі факти — її пропорції, її мета (для половини профілів, її словами) і
знання силуету класами (`знання_силуету.json`, без порогів у см). Правила task — ті самі.
Запуск: python3 побудова.py → завдання_опис.jsonl"""
import glob, json, pickle, sys
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import запис_речі
П = "/tmp/пс"
ряд = {r["id"]: r for r in pickle.load(open("/tmp/каталог_рядки.pkl", "rb"))}
записи = {}
for л in open(f"{П}/запис.jsonl", encoding="utf-8"):
    з = json.loads(л)
    if з.get("статус") == "ok": записи[з["ід"]] = запис_речі.розібрати(з["текст"])
знання = json.load(open(f"{П}/знання_силуету.json", encoding="utf-8"))["правила"]
МЕТА = {"ж1.json": "хочу підкреслити талію", "с8_юлія": "хочу, щоб ноги здавались довшими",
        "с5_оксана": "не хочу привертати увагу до стегон"}
СЛОТ = {"top": "верх", "bottom": "низ", "dress": "сукня", "set": "комплект", "outerwear": "верхній_шар"}
ВИТЯТИ = {"catalogue_slot_shortage"}
ПОСАДКА = {"measured_contour_widths", "vertical_balance_not_judged", "edge_not_judged_error_unknown",
           "measured_waist_ease_and_contour", "hem_class_vs_shop_word_not_judged"}

def перенумерувати(т, геть):
    факти = т["facts"]; нові = {}; мапа = {}
    for k, v in факти.items():
        if k in геть: continue
        мапа[k] = f"f{len(мапа) + 1}"
    def п(x): return [мапа[i] for i in x if i in мапа]
    for k, v in факти.items():
        if k not in мапа: continue
        v = dict(v)
        for поле in ("items", "because"):
            if поле in v: v[поле] = п(v[поле])
        нові[мапа[k]] = v
    т["facts"] = нові; т["photos"] = п(т.get("photos", []))
    т["confirmed_wrong_photos"] = п(т.get("confirmed_wrong_photos", []))
    т["swap_candidates"] = [dict(с, **{кл: мапа.get(с[кл], с[кл]) for кл in ("item", "to") if кл in с}) if isinstance(с, dict) else с
                            for с in т.get("swap_candidates", [])]
    return т, мапа

def зміст(д):
    return json.loads(д["запит"]["модель"]["messages"][0]["content"])

вихід = open(f"{П}/завдання_опис.jsonl", "w", encoding="utf-8"); карта = {}
for ф in sorted(glob.glob(f"{П}/опис_до/*.json")):
    д = json.load(open(ф)); н = ф[-7:-5]; т = зміст(д)
    фото = {x["n"]: x["url"] for x in д["запит"]["фото"]}
    геть = {k for k, v in т["facts"].items() if v.get("code") in ВИТЯТИ}
    до, мапа = перенумерувати(json.loads(json.dumps(т)), геть)
    фото_до = [{"n": мапа[k], "url": u} for k, u in фото.items() if k in мапа]
    вихід.write(json.dumps({"ключ": f"о{н}:ДО", "текст": json.dumps(до, ensure_ascii=False, separators=(",", ":")), "фото": фото_до}, ensure_ascii=False) + "\n")
    # ПІСЛЯ
    т2 = json.loads(json.dumps(т))
    геть2 = геть | {k for k, v in т2["facts"].items() if v.get("state") == "held" and (v.get("code") in ПОСАДКА or v.get("field") == "крій")}
    речі = [ряд[i] for i in д["склад"]["речі"]]; відп = {}
    for k, v in т2["facts"].items():
        if v.get("state") != "item" or v.get("slot") not in СЛОТ: continue
        r = [x for x in речі if x["слот"] == СЛОТ[v["slot"]] or x.get("місце") == СЛОТ[v["slot"]]][0]
        відп[k] = r["id"]; з = записи.get(r["id"])
        if not з: continue
        м = з["мітки"]
        for поле, ключ in (("крій", "cut"), ("довжина", "hem_class"), ("тканина", "fabric")):
            if поле in м and м[поле].get("значення") not in (None, "", "unknown"):
                v[ключ] = м[поле]["значення"]; v[ключ + "_source"] = {"фото": "photo", "крамниця": "shop"}.get(м[поле].get("джерело"), м[поле].get("джерело"))
        if з.get("опис"): v["description"] = з["опис"]
        if r.get("довжина_виробу_см"): v["shop_length_cm"] = r["довжина_виробу_см"]
    профіль = д["профіль_мірки"]
    т2["facts"]["fP"] = {"state": "known", "field": "її_пропорції", "value": {"зріст_см": профіль["зріст"],
                         **{f"{к}_обхват_см": в for к, в in профіль["обхвати"].items()}, "джерело": "профіль"}}
    if д["жінка"] in МЕТА:
        т2["facts"]["fG"] = {"state": "known", "field": "її_мета_силуету", "value": {"значення": МЕТА[д["жінка"]], "джерело": "її_слова", "уривок": МЕТА[д["жінка"]]}}
    т2["facts"]["fK"] = {"state": "known", "field": "знання_силуету", "value": знання}
    після, мапа2 = перенумерувати(т2, геть2)
    фото_п = [{"n": мапа2[k], "url": u} for k, u in фото.items() if k in мапа2]
    вихід.write(json.dumps({"ключ": f"о{н}:ПІСЛЯ", "текст": json.dumps(після, ensure_ascii=False, separators=(",", ":")), "фото": фото_п}, ensure_ascii=False) + "\n")
    карта[н] = {"до": {мапа[k]: i for k, i in відп.items() if k in мапа}, "після": {мапа2[k]: i for k, i in відп.items() if k in мапа2},
                "без_запису": [i for i in відп.values() if i not in записи], "мета": МЕТА.get(д["жінка"]), "жінка": д["жінка"],
                "профіль": профіль, "склад": д["склад"]["ід"], "не_знаю": д["склад"].get("не_знаю", False),
                "геть_до": len(геть), "геть_посадка": len(геть2 - геть)}
json.dump(карта, open(f"{П}/карта_опису.json", "w"), ensure_ascii=False, indent=1)
print("без запису:", sum(len(x["без_запису"]) for x in карта.values()), "посадкових утримань знято:", sum(x["геть_посадка"] for x in карта.values()))
