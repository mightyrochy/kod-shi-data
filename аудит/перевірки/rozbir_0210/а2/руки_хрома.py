"""А2: скільки кольору в образі кожної руки — кольорових речей (palettes._хроматична), середня C* і L* речей образу.
Руки 3–4 — hex, які модель сама написала (вигадані речі); руки 1–2 — виміряний hex речей каталогу. Запуск із джерела/."""
import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
МЕТ = ("намисто", "сережки", "кольє", "браслет", "каблучка", "прикраси", "брошка")
Σ = K.defaultdict(lambda: [0, 0, 0, 0.0])   # рука → [образів, з кольором, кольорових речей, сума C]
for d in sorted(glob.glob(Т + "/ж*_*/")):
    if not os.path.getsize(d + "вердикти.txt.gz"): continue   # ж8_робота_плиткою: стенд кінчає сценарій плитки до карток, вердиктів нема
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt")); ряд = []
    for в in D["прогони"][0]["вердикти"]:
        р = в["рука"]
        if р in "34":
            hh = [(x.get("hex"), x.get("слот")) for x in (в["етапи"].get("довідник_речей") or {}).values()]
        else:
            кл = {c["крок"]: c for c in в["етапи"]["виклики"]}
            if "assembly" not in кл: continue
            pool = {i["n"]: i for i in json.loads(кл["assembly"]["запит"]["текст"])["pool"]}
            вб = ((кл.get("choice") or {}).get("образи_кроку") or [{}])[0]
            hh = [(pool[n].get("hex"), (вб.get("слоти_н") or {}).get(n)) for n in вб.get("речі_н") or [] if n in pool]
        hh = [(h, с) for h, с in hh if h and с not in МЕТ]
        кол = [h for h, с in hh if P._хроматична(cs.hx(h))]
        C = [cs.lch(cs.hx(h))[1] for h, с in hh]
        s = Σ[р]; s[0] += 1; s[1] += bool(кол); s[2] += len(кол); s[3] += sum(C) / max(1, len(C))
        ряд.append("р%s %d/%d C%.0f" % (р, len(кол), len(hh), sum(C) / max(1, len(C))))
    print("%-28s %s" % (os.path.basename(d.rstrip("/")), " · ".join(ряд)))
for р in sorted(Σ):
    s = Σ[р]; print("рука %s: образів %d, з кольоровою річчю %d, кольорових речей на образ %.1f, середня C* речей %.0f" % (р, s[0], s[1], s[2] / max(1, s[0]), s[3] / max(1, s[0])))
