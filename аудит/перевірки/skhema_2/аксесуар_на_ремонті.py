import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
АКС = ("bag", "jewel", "scarf", "belt", "headband", "shoes", "pumps", "loafers", "boots", "sandals", "sneakers", "mules", "flats", "clutch", "tote", "ring", "kerchief", "hat", "bracelet", "earring", "necklace", "brooch", "bow", "hair", "stole", "twilly", "shawl", "snood", "slingback")
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
акс = lambda i: any(a in (i.get("type") or "") for a in АКС)
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
кл_ = lambda s: s if isinstance(s, str) else next(iter(s))
for тека in sys.argv[1:]:
    Σ = K.Counter(); ЗН = K.Counter(); ЗНр = K.Counter(); ЗАМ = K.Counter()
    for f in sorted(glob.glob(тека + "/*/вердикти.txt*")):
        D = json.load(gzip.open(f, "rt") if f.endswith("gz") else open(f))
        for в in D["прогони"][0]["вердикти"]:
            if str(в["рука"]) not in "12": continue
            кл = {}
            for c in в["етапи"]["виклики"]: кл.setdefault(c["крок"], c)
            if "repair" not in кл: continue
            rp = json.loads(кл["repair"]["запит"]["текст"]); ra = дж(кл["repair"].get("відповідь_сира") or "")
            відп = {o["id"]: set(o["items"]) for o in ra.get("outfits", [])}
            for o in rp["verdict"]:
                yo = o["your_outfit"]; ca = [i for i in yo["items"] if акс(i) and хр(i)]
                if not ca: continue
                Σ["вердикт: образ із кольоровим аксесуаром"] += 1
                st = {кл_(s) for f_ in o.get("findings", []) for s in f_.get("statements", [])}
                if yo["id"] not in відп: Σ["… відсіяний ремонтом (не в 5)"] += 1; [ЗНр.update([s]) for s in st]; continue
                Σ["… дійшов до 5"] += 1
                втрачено = [i for i in ca if i["n"] not in відп[yo["id"]]]
                if втрачено:
                    Σ["… у 5, кольоровий аксесуар знято/замінено"] += 1; ЗН.update(st)
                    pool = {i["n"]: i for i in yo["items"]}
                    ЗАМ["замінено на кольорове"] += any(хр(i) for i in []) 
                else: Σ["… у 5, аксесуар лишився"] += 1
    print("==", тека); [print("  ", к, v) for к, v in Σ.items()]
    print("   знахідки на образах, де ремонт ЗНЯВ кольоровий аксесуар (частка):", [(к, "%d" % v) for к, v in ЗН.most_common(12)])
