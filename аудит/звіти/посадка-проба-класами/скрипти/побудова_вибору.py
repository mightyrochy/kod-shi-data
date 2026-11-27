"""Крок 4: завдання складання руки 1 на 10 сценах. ДО — запит ядра як є (двічі: ДО і ДО-повтор — шум самої моделі).
ПІСЛЯ — той самий запит, де в рядках одягу `cut` і `length` — клас крою й краю з нового запису (джерело в `sources`),
у `person.body` — її обхвати, у `case.goal` — її мета словами (половина профілів), а в `style_rules` замість
«missing_input: крій / мета» — текст правил K-BOD-02, K-SIL-01, R-CHEV-08 і знання силуету класами (`знання_силуету.json`).
Запуск: python3 побудова_вибору.py → завдання_вибір.jsonl"""
import glob, json, sys
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import запис_речі
П = "/tmp/пс"
записи = {}
for л in open(f"{П}/запис.jsonl", encoding="utf-8"):
    з = json.loads(л)
    if з.get("статус") == "ok": записи[з["ід"]] = запис_речі.розібрати(з["текст"])["мітки"]
знання = json.load(open(f"{П}/знання_силуету.json", encoding="utf-8"))["правила"]
правила = json.load(open("/home/user/kod-shi-data/джерела/ядро/дані/правила.json"))
МЕТА = {"ж1.json": "хочу підкреслити талію", "с8_юлія": "хочу, щоб ноги здавались довшими",
        "с5_оксана": "не хочу привертати увагу до стегон"}
ОДЯГ = {"top", "bottom", "dress", "set", "outerwear"}
вихід = open(f"{П}/завдання_вибір.jsonl", "w", encoding="utf-8"); звіт = {}
for ф in sorted(glob.glob(f"{П}/вибір_до/*.json")):
    д = json.load(open(ф)); н = ф[-7:-5]; текст = д["запит"]["модель"]["messages"][0]["content"]
    for к in ("ДО", "ДО-повтор"):
        вихід.write(json.dumps({"ключ": f"в{н}:{к}", "текст": текст, "фото": []}, ensure_ascii=False) + "\n")
    т = json.loads(текст); cols = т["pool"]["cols"]; і = {c: cols.index(c) for c in cols}
    змінено = без = 0
    for r in т["pool"]["rows"]:
        if r[і["kind"]] not in ОДЯГ: continue
        м = записи.get(д["ід"][r[0]])
        if not м: без += 1; continue
        дж = r[і["sources"]] if isinstance(r[і["sources"]], dict) else {}
        for поле, col in (("крій", "cut"), ("довжина", "length")):
            if поле in м and м[поле].get("значення") not in (None, "", "unknown"):
                r[і[col]] = м[поле]["значення"]; дж[col] = {"source": "photo" if м[поле].get("джерело") == "фото" else "shop", "record": "new"}
                змінено += 1
        r[і["sources"]] = дж
    т["person"]["body"]["girths_cm"] = {к: в for к, в in д["профіль_мірки"]["обхвати"].items()}
    мета = МЕТА.get(д["жінка"])
    if мета: т["case"]["goal"] = {"value": мета, "source": "її_слова"}
    нові = []
    for с in т["style_rules"]:
        if с["id"] in ("K-BOD-02", "K-SIL-01") or (с["id"] == "R-CHEV-08" and мета):
            с = {"id": с["id"], "rule": правила[с["id"]]["опис"]}
        нові.append(с)
    нові.append({"id": "silhouette_by_class", "rule": знання})
    т["style_rules"] = нові
    вихід.write(json.dumps({"ключ": f"в{н}:ПІСЛЯ", "текст": json.dumps(т, ensure_ascii=False, separators=(",", ":")), "фото": []}, ensure_ascii=False) + "\n")
    звіт[н] = {"сцена": д["сцена"], "жінка": д["жінка"], "мета": мета, "клітинок_класу": змінено, "одягу_без_запису": без}
json.dump(звіт, open(f"{П}/карта_вибору.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(звіт, ensure_ascii=False))
