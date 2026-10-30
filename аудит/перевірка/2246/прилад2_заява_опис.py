# Синтетичний хід: оголошений хід проти знахідки (`свідомі`) з заявою, як її пишуть виробники (вільний(назва) + item_id).
import json, os, re, sys, tempfile
sys.path.insert(0, os.getcwd())
import тест_живого_шляху as Т, bridge as B, feed as Ф, statements as З, внутрішня_мова as ВМ
пійм = []; _в = B.виклик
def об(ім, вх):
    в = _в(ім, вх)
    if ім == "опис": пійм.append((json.loads(вх), json.loads(в)))
    return в
B.виклик = об
вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["каталог"] = Ф.каталог_на_диску(Т.КАТАЛОГ)
вх["кеш_кольорів"] = os.path.join(tempfile.gettempdir(), "кеш_живого_шляху.json")
Т.прогін(вх, None, "conventional")
вх_оп, _ = пійм[-1]
р = вх_оп["речі"][0]
назва = next(з["назва"] for з in Ф.база_прогону(вх["каталог"], 0, вх["кеш_кольорів"])["каталог"] if str(з["id"]) == str(р["id"]))
заява = ВМ.заява("scarf_size_unknown", item=ВМ.вільний(назва), item_id=р["id"])
вх2 = dict(вх_оп, свідомі=[{"ід": [р["id"]], "заяви": [заява]}])
о = json.loads(_в("опис", json.dumps(вх2, ensure_ascii=False)))
п = о["промпт"]
print("id:", р["id"], "| назва:", назва)
print("повний id у промпті опису:", п.count(str(р["id"])), "| назва:", п.count(назва), "| shop-хвіст:", п.count("@"))
i = п.find("your_declared"); print(п[i-20:i+450] if i >= 0 else "your_declared не знайдено")
