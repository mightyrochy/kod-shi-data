import json, glob, os, math, sys
sys.path.insert(0, ".")
import feed as F; F.каталог_на_диску('каталог_повний.xml')
import фід_каталог as ФК, colorspace as cs
кат = {r["id"]: r for r in ФК._прочитати_каталог('каталог_повний.xml', 0)['каталог']}
КІНД = {"сукня": "dress", "верх": "top", "низ": "bottom", "взуття": "shoes", "сумка": "bag", "верхній_шар": "outerwear", "комплект": "set"}
def цілі(cell):
    D = json.load(open(f"/tmp/s2/runs/ПІСЛЯ/{cell}/вердикти.txt"))
    for в in D["прогони"][0]["вердикти"]:
        for c in в["етапи"]["виклики"]:
            if c["крок"] == "assembly":
                kc = ((json.loads(c["запит"]["текст"]).get("person") or {}).get("palette") or {}).get("kind_colours")
                if kc: return kc
    return {}
for s in ("ДО", "ПІСЛЯ"):
    сум = [0, 0, 0.0]
    for d in sorted(glob.glob(f"/tmp/s2/runs/{s}/*/")):
        cell = os.path.basename(d.rstrip("/")); kc = цілі(cell); ряд = []
        D = json.load(open(d + "вердикти.txt"))
        for в in D["прогони"][0]["вердикти"]:
            if str(в["рука"]) not in "12": continue
            de = []
            for r in в.get("речі_образу") or []:
                к = КІНД.get(r.get("слот")); t = kc.get("top" if к in ("dress", "set") else к) if к else None; л = (кат.get(r["id"]) or {}).get("lab")
                if t and л: de.append(math.dist(л, cs.hx(t["hex"])))
            ряд.append("р%s %d/%d≤20 сер%.0f" % (в["рука"], sum(x <= 20 for x in de), len(de), sum(de) / max(1, len(de))))
            сум[0] += sum(x <= 20 for x in de); сум[1] += len(de); сум[2] += sum(de)
        print(s, cell, " · ".join(ряд))
    print("%s РАЗОМ: ΔE≤20 до цілі слота %d з %d (%.0f%%), середнє ΔE %.1f" % (s, сум[0], сум[1], 100 * сум[0] / сум[1], сум[2] / сум[1]))
