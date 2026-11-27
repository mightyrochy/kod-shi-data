"""Номер пулу запису → ід каталогу: рядок пулу проти рядка, який ядро дає з таблиці каталогу (ціна, рід, тип, слово кольору крамниці, тканина, крій, довжина)."""
import json, pickle, sys
from collections import defaultdict
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
from ядро import річ as ч2, запит
рядки = pickle.load(open("/tmp/каталог_рядки.pkl","rb"))
def слово(р):
    c = (р.get("sources") or {}).get("color") or {}
    v = c.get("value")
    if isinstance(v, dict) and "слово_крамниці" in v: return v["слово_крамниці"]
    r = c.get("range")
    if isinstance(r, dict): return r.get("слово_крамниці")
    return None
ПОЛЯ = ("kind","type","fabric","cut","length","pattern","sole","heel","sleeve","neckline")
def ключ(р): return (float(р["price"]) if р.get("price") not in (None,"unknown") else None, р.get("type"), слово(р))
індекс = defaultdict(list); повні = {}
for ряд in рядки:
    try:
        р = ч2.читати(ряд); пр = запит._рядок("#0", р, {"за": None})
    except Exception as e:
        continue
    пр = {к: (в.значення if hasattr(в,"значення") else в) for к,в in пр.items()}
    індекс[ключ(пр)].append((ряд["id"], пр))
сирі = json.load(open("/tmp/пс/склади_сирі.json"))
нема = однозн = багато = 0; карта = {}
for с in сирі:
    for н, р in с["рядки"].items():
        к = (с["тека"], с["обмін"], н)
        if к in карта: continue
        канд = індекс.get(ключ(р), [])
        if len(канд) > 1:
            def збіг(пр): return sum(1 for п in ПОЛЯ if json.dumps(пр.get(п),ensure_ascii=False,default=str)==json.dumps(р.get(п),ensure_ascii=False,default=str))
            найб = max(збіг(пр) for _,пр in канд)
            канд = [(і,пр) for і,пр in канд if збіг(пр)==найб]
        ід = sorted({і for і,_ in канд})
        карта["|".join(map(str,к))] = ід
        if not ід: нема += 1
        elif len(ід)==1: однозн += 1
        else: багато += 1
json.dump(карта, open("/tmp/пс/карта.json","w"), ensure_ascii=False)
print("однозначно", однозн, "кілька", багато, "нема", нема)
