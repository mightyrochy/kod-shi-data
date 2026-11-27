"""Таблиця огляду наосліп: кожне речення-кандидат (кандидати.jsonl) ДО і ПІСЛЯ, перемішане сталим зерном; у рядку —
речення, частина відповіді (text/advice — певне, unknown — «не знаю»), фото речей, про які воно (адреси крамниці й локальні
кадри), профіль жінки (зріст, обхвати, мета її словами, коли вона її назвала) і назви речей словами крамниці. Ключ
ДО/ПІСЛЯ — окремим файлом. Запуск: python3 наосліп.py <тека виходу>"""
import json, pickle, random, sys, glob, os
П = "/tmp/пс"; ТЕКА = sys.argv[1]; os.makedirs(ТЕКА, exist_ok=True)
р = {r["id"]: r for r in pickle.load(open("/tmp/каталог_рядки.pkl", "rb"))}
СЛОТ = {"top": "верх", "bottom": "низ", "dress": "сукня", "set": "комплект", "outerwear": "верхній_шар", "shoes": "взуття",
        "bag": "сумка", "earrings": "сережки", "scarf": "шарф", "belt": "пояс", "headwear": "головний_убір",
        "bracelet": "браслет", "jewelry": "прикраси"}
карта = json.load(open(f"{П}/карта_опису.json")); склади = json.load(open(f"{П}/склади.json"))
завд = {json.loads(л)["ключ"]: json.loads(л) for л in open(f"{П}/завдання_опис.jsonl", encoding="utf-8")}
def речі_запиту(н, вид):
    з = завд[f"о{н}:{вид}"]; т = json.loads(з["текст"]); фото = {x["n"]: x["url"] for x in з["фото"]}
    ряд = [р[i] for i in склади[int(н)]["речі"]]; вих = {}
    for k, v in т["facts"].items():
        if v.get("state") != "item": continue
        x = [r for r in ряд if r["слот"] == СЛОТ.get(v.get("slot"))]
        if not x: continue
        r = x[0]
        вих[k] = {"річ": r["назва"], "фото": фото.get(k) or (r["фото"] or [None])[0],
                  "кадри": sorted(glob.glob(f"{П}/фото/{r['id'].split('@')[0]}-*.jpg"))[:3], "ід": r["id"]}
    return вих
рядки = []
for з in map(json.loads, open(f"{П}/кандидати.jsonl", encoding="utf-8")):
    н = з["склад"]; к = карта[н]; речі = речі_запиту(н, з["вид"])
    про = [речі[f] for f in (з.get("about") or {}) if f in речі]
    рядки.append({"речення": з["says"], "частина": "певне" if з["де"] in ("text", "advice") else "не знаю",
                  "речі": про or list(речі.values()),
                  "профіль": {"зріст_см": к["профіль"]["зріст"], "обхвати_см": к["профіль"]["обхвати"], "мета_її_словами": к["мета"]},
                  "_ключ": {"склад": н, "вид": з["вид"], "де": з["де"], "і": з["і"]}})
random.Random(4883).shuffle(рядки)
with open(f"{ТЕКА}/наосліп.jsonl", "w", encoding="utf-8") as ф, open(f"{ТЕКА}/наосліп_ключ.jsonl", "w", encoding="utf-8") as ф2:
    for і, x in enumerate(рядки, 1):
        ключ = x.pop("_ключ")
        ф.write(json.dumps({"№": і, **x}, ensure_ascii=False) + "\n")
        ф2.write(json.dumps({"№": і, **ключ}, ensure_ascii=False) + "\n")
print("рядків", len(рядки))
