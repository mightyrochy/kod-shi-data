"""А2 (рядок 1292): картки, де код каже «образ вийшов нейтральним», а в образі є річ, яку крамниця зве кольором.
Запуск із джерела/."""
import json, gzip, glob, os, sys
sys.path.insert(0, "."); import colorspace as cs, palettes as P
Т = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
НЕЙТР = {"black", "white", "grey", "graphite", "beige", "cream", "milky", "sand", "taupe", "camel", "latte", "cocoa", "brown",
         "chocolate", "silvery", "golden", "pearly", "creamy", "ivory", "nude", "unknown", None, "multi"}
всього = суперечних = 0
for d in sorted(glob.glob(Т + "/ж*_*/")):
    if not os.path.getsize(d + "вердикти.txt.gz"): continue   # ж8_робота_плиткою: стенд кінчає сценарій плитки до карток, вердиктів нема
    D = json.load(gzip.open(d + "вердикти.txt.gz", "rt"))
    for в in D["прогони"][0]["вердикти"]:
        sj = в["етапи"]["суд"].get("схема_жінці") or {}
        коди = [s["code"] for s in ((sj.get("повідомлення") or {}).get("statements") or [])]
        if not ({"look_came_out_all_neutral", "big_items_all_neutral"} & set(коди)): continue
        всього += 1
        кл = {c["крок"]: c for c in в["етапи"]["виклики"]}
        pool = {i["n"]: i for i in json.loads(кл["assembly"]["запит"]["текст"])["pool"]}
        вб = ((кл.get("choice") or {}).get("образи_кроку") or [{}])[0]
        сл = [pool[n] for n in вб.get("речі_н") or [] if n in pool and pool[n].get("color") not in НЕЙТР]
        if сл:
            суперечних += 1
            print(os.path.basename(d.rstrip("/")), "р" + в["рука"], [(i["name"][:45], i["color"], i["hex"], "C%.0f" % cs.lch(cs.hx(i["hex"]))[1]) for i in сл])
print("карток «вийшло нейтрально»: %d, з них з річчю кольорового слова крамниці: %d" % (всього, суперечних))
