"""А2: як код прочитав кожну жінку — осі (value/chroma), «найдальші» (K-PAL-14), вікно L/C палітри, рівень контрасту.
І лічба по прогонах: схема рангу 1, гама, основа. Запуск із джерела/."""
import json, gzip, glob, os, sys, collections as K
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
бачила = set(); Σ = K.Counter()
for d in sorted(glob.glob(Т + "/ж*_*/")):
    if not os.path.getsize(d + "вердикти.txt.gz"): continue
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt")); w = os.path.basename(d.rstrip("/")).split("_")[0]
    e = D["прогони"][0]["спільне"]["етапи"]["прогін"]["вибір_палітри"]
    q = json.loads(e["виклик"]["запит"]["текст"]); a = json.loads(e["виклик"]["відповідь_сира"])
    Σ["прогонів"] += 1; Σ["схема рангу 1"] += a["scheme"] == q["schemes"][0]["scheme"]
    Σ["гама " + a.get("saturation", "?")] += 1
    b = {x["id"]: x for x in q["bases"]}[a["base"]]; Σ["основа " + b["colour"]] += 1
    Σ["why_her_eyes при основі не з сім'ї очей"] += "why_her_eyes" in a["base_reasons"] and b["family"] != q["person"]["eyes"]["family"]
    if w in бачила: continue
    бачила.add(w)
    for в in D["прогони"][0]["вердикти"]:
        c = [c for c in в["етапи"]["виклики"] if c["крок"] == "assembly"]
        if not c: continue
        p = json.loads(c[0]["запит"]["текст"]).get("person") or {}
        if "palette" not in p: continue   # рука 3–4: палітри не бачить
        pal = p["palette"]; ax = pal["axes"]
        print("%s контраст=%s поз(value=%+.2f %s, chroma=%+.2f %s) найдальші=%s вікно L%s C%s" % (w, p.get("contrast"), ax["positions"]["value"], ax["sides"]["value"],
              ax["positions"]["chroma"], ax["sides"]["chroma"], pal.get("farthest"), pal["window"]["lightness"], pal["window"]["chroma"]))
        break
for к, v in sorted(Σ.items()): print("  %-45s %d" % (к, v))
