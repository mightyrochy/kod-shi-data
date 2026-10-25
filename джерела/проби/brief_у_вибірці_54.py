"""Фікстура brief проти повного каталогу на шляху 5.4: наявність, вибірка розбору, збіг записів, коди."""
import gzip, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed as ФР, фід_каталог as ФК, каталог_коди as КК, каталог_розбір_прогін as П
def brief():
    with tempfile.TemporaryDirectory() as т:
        ш = os.path.join(т, "brief.xml")
        with gzip.open(Path(__file__).resolve().parents[1] / "каталог_brief.xml.gz", "rb") as ф, open(ш, "wb") as в: в.write(ф.read())
        return ФР.читати_yml(ш, показ=False)[0]
б = {о["id"]: о for о in brief()}
повні = {о["id"]: о for о in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]}
у_вибірці = {о["id"] for _, о in П.вибірка(list(повні.values()), len(повні))}
нема = sorted(k for k in б if k not in повні)
поза = sorted(k for k in б if k in повні and k not in у_вибірці)
різні = sorted(k for k in б if k in повні and б[k] != повні[k])
кат = {}
for о in б.values(): кат[о['категорія']] = кат.get(о['категорія'], 0) + 1
print("brief %d · у повному %d · у вибірці розбору %d (з %d) · різних записів %d · з кодами частини 1 %d"
      % (len(б), len(б) - len(нема), len(б) - len(нема) - len(поза), len(у_вибірці), len(різні), sum(1 for k in б if КК.поля(k))))
print("поза вибіркою:", поза); print("різні:", різні[:20]); print("за категорією:", dict(sorted(кат.items())))
sys.exit(1 if нема or поза or різні else 0)
