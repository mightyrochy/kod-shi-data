"""ПАЛІТРА-ХРОМА (рядки 1400, 1401): на теці прогонів стенда (підтеки ж*_* з вердикти.txt.gz і картки.txt)
друкує гаму й основу вибору палітри, цілі C* слотів рук 1–2, кольорові речі фіналу руки 1 і їхню C*,
«найдальші» й вікно L палітри та речення «найдальш/уникай» на картках.
Запуск із джерела/: python3 проби/palitra_khroma.py <тека>"""
import json, gzip, glob, os, re, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
МЕТ = ("golden", "silvery", "pearly"); Т = sys.argv[1]; Σ = K.Counter(); цілі, хроми = [], []
for d in sorted(glob.glob(Т + "/ж*_*/")):
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt")); п = D["прогони"][0]
    e = п["спільне"]["етапи"]["прогін"]["вибір_палітри"]["виклик"]
    q, a = json.loads(e["запит"]["текст"]), json.loads(e["відповідь_сира"])
    б = {x["id"]: x for x in q["bases"]}[a["base"]]; Σ["гама " + a.get("saturation", "?")] += 1
    ряд = ["гама=%s основа=%s/%s" % (a.get("saturation"), б["colour"], б["saturation"])]
    for в in п["вердикти"]:
        if str(в["рука"]) not in "12": continue
        кл = {c["крок"]: c for c in в["етапи"]["виклики"]}
        if "assembly" not in кл: continue
        зп = json.loads(кл["assembly"]["запит"]["текст"]); pal = зп["person"].get("palette") or {}
        пул = {i["n"]: i for i in зп["pool"]}
        кц = [round(cs.lch(cs.hx(t["hex"]))[1]) for t in (pal.get("kind_colours") or {}).values() if t.get("hex")]
        цілі += кц
        if str(в["рука"]) == "1":
            ряд.append("найдальші=%s вікно L%s цілі C*%s" % (pal.get("farthest"), (pal.get("window") or {}).get("lightness"), sorted(кц)))
            вб = ((кл.get("choice") or {}).get("образи_кроку") or [{}])[0]
            кол = [пул[n] for n in вб.get("речі_н") or [] if n in пул and пул[n].get("hex") and пул[n].get("color") not in МЕТ and P._хроматична(cs.hx(пул[n]["hex"]))]
            Σ["р1 образів"] += 1; Σ["р1 з кольоровою річчю"] += bool(кол)
            хроми += [cs.lch(cs.hx(i["hex"]))[1] for i in кол]
            ряд.append("р1 кольорові: %s" % ["%s/C%.0f" % (i.get("color"), cs.lch(cs.hx(i["hex"]))[1]) for i in кол])
    кт = open(d + "картки.txt", encoding="utf-8").read()
    фр = re.findall(r"[^.!?\n]*(?:[Нн]айдальш|[Уу]никай)[^.!?\n]*", кт); Σ["речень найдальш/уникай"] += len(фр)
    print(os.path.basename(d.rstrip("/")), " · ".join(ряд)); [print("     «%s»" % f.strip()[:160]) for f in фр]
с = sorted(цілі)
print("цілі C* слотів рук 1–2: %d, медіана %d, C*<12: %d" % (len(с), с[len(с) // 2] if с else 0, sum(x < 12 for x in с)))
print("р1: середня C* кольорових речей %.0f (%d речей)" % (sum(хроми) / len(хроми) if хроми else 0, len(хроми)))
for к, v in sorted(Σ.items()): print("  %-28s %d" % (к, v))
