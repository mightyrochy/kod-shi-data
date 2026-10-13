import json, glob, os, math, sys
sys.path.insert(0, "."); import colorspace as cs
def хр(i):
    return i.get("hex") and i.get("color") not in ("golden", "silvery", "pearly") and cs.lch(cs.hx(i["hex"]))[1] >= 15
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
for s in ("ДО", "ПІСЛЯ"):
    Σ = [0, 0, 0, 0]
    for d in sorted(glob.glob(f"/tmp/s2/runs/{s}/*/")):
        D = json.load(open(d + "вердикти.txt")); ряд = []
        for в in D["прогони"][0]["вердикти"]:
            if str(в["рука"]) not in "12": continue
            for c in в["етапи"]["виклики"]:
                if c["крок"] == "assembly":
                    p = json.loads(c["запит"]["текст"]); a = дж(c.get("відповідь_сира") or ""); break
            pool = {i["n"]: i for i in p["pool"]}; ід = a.get("outfits", [])
            k = sum(any(хр(pool[n]) for n in o["items"] if n in pool) for o in ід)
            ряд.append("р%s %d/%d" % (в["рука"], k, len(ід))); Σ[0] += k; Σ[1] += len(ід)
        print(s, os.path.basename(d.rstrip("/")), " · ".join(ряд))
    print("%s РАЗОМ: ідей складання з кольоровою річчю (C*≥15, без металу) %d з %d (%.0f%%)" % (s, Σ[0], Σ[1], 100 * Σ[0] / Σ[1]))
