import glob, json, os, sys, copy
дер = sys.argv[1]; вих = sys.argv[2]
os.chdir(дер); sys.path.insert(0, os.path.abspath("джерела"))
import feed
import міст_відповіді
feed.каталог_на_диску("каталог_brief.xml")
кат = os.path.abspath("джерела/каталог_brief.xml")
res = []
for ф in sorted(glob.glob("аудит/корпус_3_1_а/*.json")):
    вх0 = json.load(open(ф, encoding="utf-8")); вх0["каталог"] = кат
    варіанти = {"як є": вх0}
    for назва, зміна in (("без відповідь", {"відповідь": None}), ("відповідь=ХЗ", {"відповідь": "ХЗ_V9"}),
                         ("відп=ОЦІНКИ_V1", {"відповідь": "ОЦІНКИ_V1"})):
        v = copy.deepcopy(вх0); v.update(зміна); варіанти[назва] = v
    for н, v in варіанти.items():
        try:
            o = міст_відповіді.від_моделі(copy.deepcopy(v))
        except Exception as e:
            o = "ВИНЯТОК %s: %s" % (type(e).__name__, str(e)[:200])
        res.append([os.path.basename(ф), н, o])
json.dump(res, open(вих, "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
print(len(res), "викликів")
