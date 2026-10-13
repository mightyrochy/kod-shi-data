"""РЕМОНТ-1 (рядки 4290, 4291), без моделі: промпт ремонту чинного коду проти записаного заміром ГГ-1 на тих самих
входах — розмір, «case», порядок і форма відповіді — і чи міст прийняв відповідь із «chosen» (заглушка).
  cd джерела && BOKY=з_гг1 VYVID=<т> python3 ../аудит/проби/гг1_повтор_ремонту.py --заглушка
  python3 ../аудит/проби/ремонт1_промпт.py <т> ../аудит/гг1_замір"""
import gzip, json, glob, os, sys, collections as K

нові = {os.path.basename(ф)[:12]: json.load(gzip.open(ф, "rt"))["з_гг1"] for ф in glob.glob(sys.argv[1] + "/сирі/*.json.gz")}
Л = K.Counter(); Д = K.defaultdict(lambda: [0, 0]); розмір = []


def два(ім, записаний, чинний):
    Д[ім + ": записаний / чинний"][0] += записаний; Д[ім + ": записаний / чинний"][1] += чинний


for к, н in sorted(нові.items()):
    з = json.load(gzip.open("%s/сирі/%s.json.gz" % (sys.argv[2], к), "rt"))["з_гг1"]
    if н.get("збій") or not н.get("промпт"):
        Л["збій: %s" % н.get("збій")] += 1; continue
    п, с = json.loads(н["промпт"]), json.loads(з["промпт"]); т, тс = п["task"], с["task"]
    розмір.append((len(з["промпт"]), len(н["промпт"])))
    Л["входів"] += 1
    два("case з intent", "intent" in с["case"], "intent" in п["case"])
    два("case з goal", "goal" in с["case"], "goal" in п["case"])
    два("set.bold", "bold" in (с.get("set") or {}), "bold" in (п.get("set") or {}))
    Л["скелет: " + " → ".join(т["answer_schema"])] += 1
    Л["done у скелеті: " + т["answer_schema"]["outfits"][0]["done"][0]["finding"]] += 1
    два("правил", len(тс["rules"]), len(т["rules"]))
    два("вітрина", len(с.get("showcase") or []), len(п.get("showcase") or []))
    Л["образів у вердикті"] += len(п["verdict"])
    Л["міст прийняв відповідь із chosen (образів після)"] += len(н.get("образи_після") or [])
for к in sorted(Л):
    print("  %-62s %s" % (к, Л[к]))
for к in sorted(Д):
    print("  %-62s %d / %d" % (к, *Д[к]))
if розмір:
    print("  символів промпту, сума: записаний %d · чинний %d (%+.1f %%)" % (
        sum(а for а, _ in розмір), sum(б for _, б in розмір), 100 * (sum(б for _, б in розмір) / sum(а for а, _ in розмір) - 1)))
