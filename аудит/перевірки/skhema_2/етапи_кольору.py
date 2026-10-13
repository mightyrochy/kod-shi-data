import json, glob, os, sys
sys.path.insert(0, "."); import colorspace as cs, palettes as P
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
for s in ("ДО", "ПІСЛЯ"):
    Σ = {"10": [0, 0], "5": [0, 0], "1": [0, 0]}
    for d in sorted(glob.glob(f"/tmp/s2/runs/{s}/*/")):
        D = json.load(open(d + "вердикти.txt")); ряд = []
        for в in D["прогони"][0]["вердикти"]:
            if str(в["рука"]) not in "12": continue
            кл = {c["крок"]: c for c in в["етапи"]["виклики"]}
            pool = {i["n"]: i for i in json.loads(кл["assembly"]["запит"]["текст"])["pool"]}
            ет = {"10": дж(кл["assembly"].get("відповідь_сира") or "").get("outfits", []),
                  "5": дж((кл.get("repair") or {}).get("відповідь_сира") or "").get("outfits", [])}
            ch = дж((кл.get("choice") or {}).get("відповідь_сира") or "").get("chosen")
            ет["1"] = [o for o in ет["5"] if o["id"] == ch]
            р = []
            for к, оо in ет.items():
                n = sum(any(хр(pool[x]) for x in o["items"] if x in pool) for o in оо); Σ[к][0] += n; Σ[к][1] += len(оо); р.append("%d/%d" % (n, len(оо)))
            ряд.append("р%s %s | суд: %s" % (в["рука"], "→".join(р), в.get("схема_вийшла")))
        print(s, os.path.basename(d.rstrip("/")), " · ".join(ряд))
    print(s, "РАЗОМ образів із кольоровою річчю (palettes._хроматична): " + " → ".join("%s: %d/%d" % (к, *v) for к, v in Σ.items()))
