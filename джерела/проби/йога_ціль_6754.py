"""Рядок 6754 · replay суду записаних образів йоги (рук 1–2, `образи_кроку` збирання й ремонту, id каталогу) чинним
`bridge.від_моделі` з профілем і сценарієм прогону: K-KOH-05 (напрям, рівень, ціль) і текст ремонту. ДО — нагода «спорт» без
ошатності міряна широким дефолтом [3, 6]: спортивний образ «нижче», ремонт «зсунути на 0 кроків»; ПІСЛЯ — ціль рядка «спорт».
Запуск із джерела/: python3 проби/йога_ціль_6754.py <тека з 01_ж2_йога_зранку/вердикти.txt>"""
import json, gzip, glob, sys, collections as K
sys.path.insert(0, "."); import bridge as B
ВХ0 = json.load(open("стенд_вх.json", encoding="utf-8"))
for f in sorted(glob.glob(sys.argv[1] + "/*йога*/вердикти.txt*")):
    д = json.load(gzip.open(f, "rt") if f.endswith(".gz") else open(f, encoding="utf-8")); вп = д["спільне"]["вхід_прогону"]; к = вп["колір"]
    п = д["спільне"].get("паспорт", {})
    вх = dict(ВХ0, зріст=вп["мірки"]["зріст"], обхвати=вп["мірки"]["обхвати"], шкіра=к["шкіра"][0], волосся=к["волосся"], очі=к["очі"],
              сценарій=dict(вп["сценарій"], **{x: п[x] for x in ("мета", "намір") if п.get(x) not in (None, "невідомо")}), випадок=п.get("подія") or "")
    B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    Л = K.Counter()
    for в in (в for пр in д["прогони"] for в in пр["вердикти"] if str(в["рука"]) in "12"):
        for c in в["етапи"]["виклики"]:
            for о in (c.get("образи_кроку") or []) if c.get("крок") in ("assembly", "repair") else []:
                вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=о["ід"]), ensure_ascii=False)))
                for z in ((вм.get("вердикт") or {}).get("образи") or [{}])[0].get("знахідки") or []:
                    if z.get("правило") != "K-KOH-05": continue
                    зв = next((з.get("values") for з in z.get("заяви") or [] if isinstance(з, dict) and з.get("code") == "outfit_level_off_occasion"), None)
                    if зв is None: continue
                    Л["рука %s %s: %s" % (в["рука"], c["крок"], зв.get("direction"))] += 1
                    print("рука %s %-6s %-4s %-34s %s · ремонт: %s" % (в["рука"], c["крок"], о.get("номер"), (о.get("підпис") or "")[:34],
                          json.dumps(зв, ensure_ascii=False), "; ".join(z.get("ремонт") or [])[:70] if isinstance(z.get("ремонт"), list) else str(z.get("ремонт"))[:70]))
    print(f.split("/")[-2], "· K-KOH-05 outfit_level_off_occasion:", dict(Л) or "0")
