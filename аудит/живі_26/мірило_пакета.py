# Живий ПІСЛЯ: вхід стилістки з записаних пакетів (теки з VIDPOVIDI). З `джерела`: python3 <цей файл> <тека>...
import collections, glob, json, sys
sys.path.insert(0, "."); import колір_річ as К
for т in sys.argv[1:]:
    каб, бурі, кап = collections.Counter(), collections.Counter(), 0
    for ф in glob.glob(т + "/VIDPOVIDI/*ПАКЕТ*.txt"):
        for р in json.loads(open(ф, encoding="utf-8").read().split("\n")[1]).get("pool", []):
            if "heel" in р: каб[р["heel"]] += 1
            кап += р.get("color") == "cappuccino"
            if р.get("hex"):
                L, C, h = К.lch(К._lab(р["hex"]))
                if К._темне_буре(L, C, h): бурі["з family" if р.get("family") else "без family"] += 1
    print(т, "| heel:", dict(каб), "| темні бурі:", dict(бурі), "| cappuccino:", кап)
