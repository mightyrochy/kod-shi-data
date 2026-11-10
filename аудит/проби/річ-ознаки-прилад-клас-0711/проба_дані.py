import asyncio, json, sys, collections, traceback
from pathlib import Path
К = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(К / "джерела/прилади"))
import знімок_мосту as З
З.підготувати(str(К / "джерела"))
import feed
feed.каталог_на_диску("каталог_brief.xml")
import personal_palette as PP, face_features as ФФ
лік = collections.Counter()
ор = PP.дані
def дані(F):
    лік["усі"] += 1
    д = ор(F)
    if д:
        стек = tuple(f"{fr.name}:{fr.lineno}" for fr in traceback.extract_stack()[-6:-1])
        лік[(ФФ.джерело_виміру(F), (F.get("_meta") or {}).get("protocol"), стек)] += 1
    return д
PP.дані = дані
for сцена in sys.argv[2].split(","):
    запис = З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz")))
    знімок, час = asyncio.run(З.прогнати(запис))
    print(сцена, flush=True)
for к, н in лік.most_common(15):
    print(н, к)
