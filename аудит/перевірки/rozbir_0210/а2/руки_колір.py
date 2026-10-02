"""А2: руки 1–2 — колір на етапах (ідеї→ремонт→вибір), «схема вийшла», ΔE обраних речей до цілі слота, слово крамниці проти виміру.
Запуск із джерела/: python3 ../аудит/перевірки/rozbir_0210/а2/руки_колір.py [тека]"""
import json, gzip, glob, os, sys, math, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
Т = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-v" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
МЕТ = ("golden", "silvery", "pearly")
хр = lambda i: bool(i.get("hex")) and i.get("color") not in МЕТ and P._хроматична(cs.hx(i["hex"]))
КІНД = {"сукня": "top", "комплект": "top", "верх": "top", "низ": "bottom", "взуття": "shoes", "сумка": "bag", "верхній_шар": "outerwear"}
def дж(t):
    try: return json.JSONDecoder().raw_decode(t[t.index("{"):])[0]
    except Exception: return {}
Σ = K.Counter(); ΔE = []; СЛ = []
for d in sorted(glob.glob(Т + "/ж*_*/")):
    if not os.path.getsize(d + "вердикти.txt.gz"): continue   # ж8_робота_плиткою: стенд кінчає сценарій плитки до карток, вердиктів нема
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt")); ряд = []
    for в in D["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        кл = {}
        for c in в["етапи"]["виклики"]: кл.setdefault(c["крок"], c)
        if "assembly" not in кл: ряд.append("р%s без складання" % в["рука"]); continue
        q = json.loads(кл["assembly"]["запит"]["текст"]); pool = {i["n"]: i for i in q["pool"]}
        pal = q["person"].get("palette") or {}; kc = pal.get("kind_colours") or {}
        ет = {"10": дж(кл["assembly"].get("відповідь_сира") or "").get("outfits", []),
              "5": дж((кл.get("repair") or {}).get("відповідь_сира") or "").get("outfits", [])}
        ch = дж((кл.get("choice") or {}).get("відповідь_сира") or "").get("chosen")
        вб = ((кл.get("choice") or {}).get("образи_кроку") or [{}])[0]
        ет["1"] = [{"items": вб.get("речі_н") or []}] if вб else []
        р = []
        for к, оо in ет.items():
            n = sum(any(хр(pool[x]) for x in o["items"] if x in pool) for o in оо); Σ["ет" + к] += n; Σ["ет" + к + "_з"] += len(оо); р.append("%d/%d" % (n, len(оо)))
        фін = [pool[x] for o in ет["1"] for x in o["items"] if x in pool]
        кол = [i for i in фін if хр(i)]
        de = []
        for n in вб.get("речі_н") or []:
            оп = (вб.get("описи_н") or {}).get(n) or {}; t = kc.get(КІНД.get((вб.get("слоти_н") or {}).get(n), ""))
            if t and pool.get(n, {}).get("hex"):
                x = math.dist(cs.hx(pool[n]["hex"]), cs.hx(t["hex"])); de.append(x); ΔE.append(x)
                СЛ.append((os.path.basename(d.rstrip("/")), в["рука"], (вб.get("слоти_н") or {}).get(n), оп.get("колір"), pool[n]["hex"], pool[n].get("color"), t["hex"], round(x)))
        sj = (в["етапи"]["суд"].get("схема_жінці") or {}); пов = sj.get("повідомлення") or {}
        коди = [s["code"] for s in пов.get("statements", [])]
        Σ["вийшла_" + str(в.get("схема_вийшла"))] += 1
        ряд.append("р%s %s %s ΔE[%s] ет=%s вийшла=%s кольорових у фіналі=%s ціль_слотів=%s у_пулі=%s великі=%s повід=%s" % (
            в["рука"], в.get("пал_схема_руки"), "ітер%s" % в.get("ітерацій"), ",".join("%.0f" % x for x in de), "→".join(р), в.get("схема_вийшла"),
            ["%s:%s/%s" % (i.get("type"), i.get("color"), i.get("hex")) for i in кол], sorted(kc)[:9] if isinstance(kc, dict) else kc,
            sj.get("у_пулі"), sj.get("великі"), ",".join(коди)))
    print(os.path.basename(d.rstrip("/"))); [print("   " + x) for x in ряд]
print("РАЗОМ", dict(Σ))
print("ΔE обраних речей до цілі слота: %d речей, ≤20: %d, медіана %.0f" % (len(ΔE), sum(x <= 20 for x in ΔE), sorted(ΔE)[len(ΔE)//2] if ΔE else 0))
if "-v" in sys.argv: [print("  ", *x) for x in СЛ]
