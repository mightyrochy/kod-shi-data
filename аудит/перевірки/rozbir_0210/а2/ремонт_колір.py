"""А2: що ремонт робить із кольоровою річчю (руки 1–2): образи з кольоровою річчю у вердикті → у п'ятірці колір лишився / знято;
які знахідки суду стояли на образах, де колір знято. Запуск із джерела/."""
import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
кл_ = lambda s: s if isinstance(s, str) else next(iter(s))
Σ = K.Counter(); ЗН = K.Counter(); ЗЛ = K.Counter(); ВС = K.Counter(); прог = K.Counter()
for f in sorted(glob.glob(Т + "/ж*_*/вердикти.txt.gz")):
    if not os.path.getsize(f): continue   # ж8_робота_плиткою: стенд кінчає сценарій плитки до карток, вердиктів нема
    D = json.load(gzip.open(f, "rt"))
    for в in D["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        кл = {}
        for c in в["етапи"]["виклики"]: кл.setdefault(c["крок"], c)
        if "repair" not in кл: continue
        rp = json.loads(кл["repair"]["запит"]["текст"]); ra = дж(кл["repair"].get("відповідь_сира") or "")
        відп = {o["id"]: set(o["items"]) for o in ra.get("outfits", [])}
        for o in rp["verdict"]:
            yo = o["your_outfit"]; ca = [i for i in yo["items"] if хр(i)]
            st = {кл_(s) for f_ in o.get("findings", []) for s in f_.get("statements", [])}
            ВС.update(st)
            if not ca: continue
            Σ["образ із кольоровою річчю у вердикті"] += 1; ЗЛ.update(st)
            if yo["id"] not in відп: Σ["… не повернувся з ремонту"] += 1; continue
            if [i for i in ca if i["n"] not in відп[yo["id"]]]:
                Σ["… колір знято/замінено"] += 1; ЗН.update(st); прог[os.path.basename(os.path.dirname(f))] += 1
            else: Σ["… колір лишився"] += 1
[print(к, v) for к, v in Σ.items()]
КОЛ = ("accent", "focus", "excess", "chroma", "colour", "color", "scheme", "loud", "palette", "contrast", "hue", "tonal", "neutral", "triad", "complement")
print("колірні знахідки: на образах, де колір ЗНЯТО / на всіх кольорових образах:")
for к, v in ЗЛ.most_common():
    if any(x in к for x in КОЛ): print("   %-40s %3d / %3d" % (к, ЗН[к], v))
print("прогонів, де ремонт знімав колір:", len(прог), dict(прог))
