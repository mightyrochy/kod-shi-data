import glob, json, os, sys
дер = sys.argv[1]; os.chdir(дер); sys.path.insert(0, os.path.abspath("джерела"))
import feed, міст_відповіді, pipeline as PL, вердикт_моделі as ВМ
feed.каталог_на_диску("каталог_brief.xml"); кат = os.path.abspath("джерела/каталог_brief.xml")
зап = []
orig = PL.мова_повтор
def обгортка(*a, **k):
    зап.append(k.get("відповідь")); return orig(*a, **k)
PL.мова_повтор = обгортка
for ф in sorted(glob.glob("аудит/корпус_3_1_а/*.json")):
    d = json.load(open(ф, encoding="utf-8")); d["каталог"] = кат; зап.clear()
    міст_відповіді.від_моделі(d)
    print(os.path.basename(ф)[:38].ljust(40), зап)
# прямий вплив на текст запиту мови
вердикт = {"можна_видавати": False}
for н in ("ОБРАЗИ_V1", "ДОПОВНЕННЯ_V1"):
    try:
        o = ВМ.мова_повтор(dict(можна_видавати=False, порушення=[]), спроба=1, відповідь=н)
        print(н, "→", None if o is None else o.get("формат"))
    except Exception as e: print(н, "виняток", e)
