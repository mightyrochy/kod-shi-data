# -*- coding: utf-8 -*-
"""Річ-запис-речі, п.7, крок 2 (16.11.2026): той самий повтор записаних входів, що крок 1
(`аудит/проби/річ-запис-речі-п7-взуття/повтор_входів.py`), з ключами кроку 2 — `heel_shape`, `heel_height`, `heel_cm`,
`sole`, `wear_season`, `lining` — і легендою `дріт_моделі.легенда_ключів`. Продукт — з `--джерела` (ДО — тека `main`,
ПІСЛЯ — ця гілка), тож різниця двох запусків — ціна кроку 2 у вході моделі.

Моделей не кличе. Кожну пару взуття записаного пулу зіставляє з записом каталогу (ціна, код крамниці номера, колір, hex,
вид, світлота, `heel` і матеріал рядка ДО) і будує її осі тим самим викликом, що `пакет_моделі.py`
(`композитор_річ.у_річ` → `graph.зона` → `дріт_моделі.осі`). Нові ключі (`heel_cm`, `sole`) дописує в хвіст того самого
рядка записаного пулу, їхні пояснення — у `pool_keys`; розмір входу — компактний JSON пакета ДО і ПІСЛЯ. Пара, яку зіставлено неоднозначно і в кандидатів
різні нові поля, лишається як була (друкується).

Запуск з кореня: python3 аудит/проби/річ-запис-речі-п7-картка/повтор_входів.py <тека джерела> [кеш.pkl]"""
import gzip, json, os, pickle, sys, warnings

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
warnings.simplefilter("ignore")
ДЖЕРЕЛА = os.path.abspath(sys.argv[1]); sys.argv[1:2] = []
sys.path.insert(0, ДЖЕРЕЛА); os.chdir(ДЖЕРЕЛА)
import фід_каталог as ФК, дріт_моделі as Д, graph as ГР, каблук as КБ, композитор_річ as КПР, колір_річ as КР  # noqa: E402

кеш = sys.argv[1] if len(sys.argv) > 1 else None
if кеш and os.path.exists(кеш):
    каталог = pickle.load(open(кеш, "rb"))
else:
    каталог = ФК.прочитати_каталог(ФК.каталог_на_диску(), ліміт_фото=0)["каталог"]
    if кеш:
        pickle.dump(каталог, open(кеш, "wb"))
взуття = [r for r in каталог if r.get("слот") == "взуття"]
БАЗА = os.path.join(КОРІНЬ, "аудит/проби/живий-як-людина-3/стенд/службове")


def осі(r):
    кб = КБ.каблук(r["назва"], None, r.get("url"))
    рч = КПР.у_річ(dict(r), "взуття", {})
    return Д.осі(ГР.зона(рч), dict(рч, слот="взуття", каблук_є=кб["є"], каблук=r.get("каблук"), каблук_форма=кб["форма"],
                                    каблук_висота=кб["висота"], каблук_словами=КБ.словами(кб)))


def кандидати(о, хв, крамниця=None):
    к = [r for r in взуття if r.get("ціна") == о.get("price")]
    if крамниця:
        к = [r for r in к if r["id"].split("@")[-1] == крамниця] or к
    for умова in (lambda r: Д.колір_код(r.get("колір_назва"))[0] == о.get("color"),
                  lambda r: bool(о.get("hex")) and (КР.hex_кольору(r) or "").lower() == о["hex"].lower(),
                  lambda r: Д.код("item_type", r.get("тип")) == о.get("type"),
                  lambda r: о.get("L") is not None and осі(r).get("L") == (о["L"] if isinstance(о["L"], list) else [о["L"]] * 2),
                  lambda r: осі(r).get("heel") == хв.get("heel")):
        if len(к) > 1:
            к = [r for r in к if умова(r)] or к
    return к


КЛЮЧІ = ("heel_shape", "heel_height", "heel_cm", "sole", "wear_season", "lining")
for сцена, н, ціль in (("с8_мінус_десять_сніг", 34, "#404·11"), ("с5_весілля_сестри", 10, "#1·35")):
    обміни = [json.loads(л) for л in gzip.open(os.path.join(БАЗА, сцена, "обміни.jsonl.gz"), "rt", encoding="utf-8")]
    пакет = json.loads(json.loads(обміни[н]["запит"])["messages"][0]["content"][0]["text"])
    cols, рядки = пакет["pool"]["cols"], пакет["pool"]["rows"]
    до = len(json.dumps(пакет, ensure_ascii=False, separators=(",", ":")))
    пари = [(dict(zip(cols, row)), row[-1]) for row in рядки
            if len(row) > len(cols) and isinstance(row[-1], dict) and "heel" in row[-1]]
    # код крамниці номера («#404·11» → 11) — один у межах пакета (`пакет_моделі.номери_речей`)
    крамниці = {}
    for о, хв in пари:
        к = кандидати(о, хв)
        if len(к) == 1:
            крамниці[о["n"].split("·")[1]] = к[0]["id"].split("@")[-1]
    зіставлено, підсумок = 0, {"heel_cm число": 0, "heel_cm смуга": 0, "heel_cm unknown": 0, "sole кодом": 0, "sole unknown": 0}
    print("== %s, обмін №%d: пар взуття в пулі %d" % (сцена, н, len(пари)))
    for о, хв in пари:
        к = кандидати(о, dict(хв), крамниці.get(о["n"].split("·")[1]))
        нові = {json.dumps({ключ: осі(r).get(ключ) for ключ in КЛЮЧІ}) for r in к}
        if len(нові) != 1:
            print("   %s — не зіставлено: %d кандидатів із різними новими полями %s" % (о["n"], len(к), sorted(нові)))
            continue
        зіставлено += 1
        нов = осі(к[0])
        for ключ in КЛЮЧІ:
            хв.pop(ключ, None)
            if ключ in нов:
                хв[ключ] = нов[ключ]
        h, s = хв.get("heel_cm"), хв.get("sole")
        підсумок["heel_cm число"] += isinstance(h, (int, float))
        підсумок["heel_cm смуга"] += isinstance(h, list)
        підсумок["heel_cm unknown"] += h == "unknown"
        підсумок["sole кодом"] += s not in (None, "unknown")
        підсумок["sole unknown"] += s == "unknown"
        if о["n"] == ціль:
            print("   ЦІЛЬ %s = %s «%s»: рядок ПІСЛЯ %s" % (о["n"], к[0]["id"], к[0]["назва"], json.dumps(хв, ensure_ascii=False)))
    # пояснення нових ключів — легенда пакета `pool_keys` (`дріт_моделі.легенда_ключів`), раз на пакет
    легенда = пакет.setdefault("pool_keys", {})
    легенда.update({к: т for к, т in Д.легенда_ключів([хв for _, хв in пари]).items() if к not in легенда})
    після = len(json.dumps(пакет, ensure_ascii=False, separators=(",", ":")))
    print("   зіставлено %d з %d · %s" % (зіставлено, len(пари), json.dumps(підсумок, ensure_ascii=False)))
    print("   розмір входу (компактний JSON пакета): ДО %d → ПІСЛЯ %d (+%d, +%.2f %%)" % (до, після, після - до, 100.0 * (після - до) / до))
