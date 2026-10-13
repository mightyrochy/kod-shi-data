"""ФОКУС-2: якою знахідкою ремонт (руки 1–2) зняв колір — образ із кольоровою річчю, з якої річ пішла;
знахідки, які модель назвала в «done» (fixed) цього образу, за кодом заяви. Запуск із джерела/:
python3 ../аудит/перевірки/fokus_2/знято_чим.py <тека з ж*_*>"""
import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
кл = lambda s: s if isinstance(s, str) else next(iter(s))
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
ЧОТИРИ = ("accent_surfaces_same_colour_word", "accent_not_from_eyes", "accessory_spends_chroma_budget", "more_than_one_loud_colour")
Н = K.Counter(); С = K.Counter(); З = K.Counter()
for f in sorted(glob.glob(sys.argv[1] + "/ж*_*/вердикти.txt.gz")):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        c = next((c for c in в["етапи"]["виклики"] if c["крок"] == "repair"), None)
        if not c: continue
        q = json.loads(c["запит"]["текст"]); a = {o["id"]: o for o in дж(c.get("відповідь_сира") or "").get("outfits", [])}
        for o in q["verdict"]:
            yo = o["your_outfit"]; ca = [i["n"] for i in yo["items"] if хр(i)]
            st = {fd["id"]: {кл(s) for s in fd.get("statements", [])} for fd in o.get("findings", [])}
            for к in set().union(*st.values()) if st else (): С[к] += bool(ca)
            if not ca or yo["id"] not in a or all(n in a[yo["id"]]["items"] for n in ca): continue
            Н["образів, де ремонт зняв колір"] += 1
            for d in a[yo["id"]].get("done") or []:
                if d.get("action") == "fixed":
                    for к in st.get(d.get("finding"), ()): З[к] += 1
print(dict(Н))
print("чотири знахідки ФОКУС-2 — названа «fixed» на образі, де колір знято / стоїть на кольорових образах:")
for к in ЧОТИРИ: print("   %-36s %3d / %3d" % (к, З[к], С[к]))
print("решта колірних «fixed» на знятті:", ", ".join("%s %d" % kv for kv in З.most_common(10) if kv[0] not in ЧОТИРИ))
