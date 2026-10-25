"""ПРОБА ГРАМАТИКИ 5.4 (5.4-Г) на теці нового прогону: обрізаних серед 50 обрізаних частини 1 (мірило ≤1 %), чи
ті самі коди в 50 розібраних (проти `каталог_розбір_коди.json.gz`, без evidence і features), с/річ стіною.
python3 проби/проба_граматики_54г.py <тека> аудит/виконання_5.4/проба_граматики_розібрані50.txt <обрізані50.txt>"""
import collections, gzip, json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import каталог_розбір_прогін as П
тека, розібрані, обрізані = sys.argv[1], П.ід_еталону(sys.argv[2]), П.ід_еталону(sys.argv[3])
речі = {р["id"]: р for р in json.load(open(Path(тека) / "прогін.json", encoding="utf-8"))["речі"]}
нові = json.load(open(П.зібрати(тека), encoding="utf-8"))
старі = json.load(gzip.open(Path(__file__).resolve().parents[1] / "каталог_розбір_коди.json.gz", "rt"))
нема = [і for і in розібрані + обрізані if і not in речі]
assert not нема, "у теці нема речей: %s" % нема[:5]
не_json = lambda і: str(речі[і].get("впало") or "").startswith("invalid_json")
коди = lambda п: {к: з for к, з in (п or {}).items() if к not in ("evidence", П.КР.ОСОБЛИВОСТІ)}
інші = collections.Counter(к for і in розібрані for к in set(коди(старі[і])) | set(коди(нові.get(і)))
                           if коди(старі[і]).get(к) != коди(нові.get(і)).get(к))
те_саме = sum(коди(старі[і]) == коди(нові.get(і)) for і in розібрані)
с = [речі[і]["секунд"] for і in розібрані + обрізані]
print("обрізаних (invalid_json) серед %d обрізаних частини 1: %d; серед %d розібраних: %d" % (
    len(обрізані), sum(map(не_json, обрізані)), len(розібрані), sum(map(не_json, розібрані))))
print("розібраних з тими самими кодами: %d з %d; поля, що розійшлись: %s" % (те_саме, len(розібрані), інші.most_common(10)))
print("с/річ (виклик із повтором): медіана %.1f, середнє %.1f, найбільше %.1f; повторів %d" % (
    statistics.median(с), statistics.mean(с), max(с), sum(речі[і].get("повторів", 0) for і in розібрані + обрізані)))
