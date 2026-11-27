"""Збір складів: з кожної теки записів — образи складання/ремонту руки з пулом запиту."""
import json, gzip, glob, os, sys
К = "/home/user/kod-shi-data/"
ТЕКИ = sorted(glob.glob(К+"аудит/звіти/ядро-образу-наново/приймання/хмара-sonnet/*/ядро/1/*")) + \
       sorted(glob.glob(К+"аудит/проби/н2-доробка-90ded3b/с*"))
def обміни(т):
    ф = т+"/обміни.jsonl"
    рядки = open(ф) if os.path.exists(ф) else gzip.open(ф+".gz","rt")
    for л in рядки:
        о = json.loads(л); з = о["запит"]
        в = о["відповідь"]
        if isinstance(в, str):
            try: в = json.loads(в)
            except Exception: pass
        yield о, з, в
def текст(в):
    if isinstance(в, dict) and "content" in в:
        return "".join(б.get("text","") for б in в["content"] if б.get("type")=="text")
    return в if isinstance(в,str) else json.dumps(в)
вихід = []
for т in ТЕКИ:
    for і,(о,з,в) in enumerate(обміни(т)):
        if isinstance(з, str): t = з
        else:
            бл = з["messages"][0]["content"]
            t = next((б["text"] for б in бл if б.get("type")=="text" and б["text"].startswith("{")), "")
        if 'Build outfits' not in t[:300] and 'Improve the outfits' not in t[:300]: continue
        тіло = json.loads(t)
        пул = тіло.get("pool") or тіло.get("candidates")
        cols = пул["cols"]; рядки = {р[0]: dict(zip(cols, р)) for р in пул["rows"]}
        try:
            відп = json.JSONDecoder().raw_decode(текст(в).strip().lstrip("`").removeprefix("json").strip())[0]
        except Exception as e:
            print("збій розбору", т, і, e, file=sys.stderr); continue
        for об in відп.get("outfits", []):
            items = об.get("items") or []
            items = [x if isinstance(x,str) else x.get("n") for x in items]
            вихід.append({"тека": т.replace(К,""), "обмін": і, "вид": "ремонт" if "Improve" in t[:300] else "складання",
                          "образ": об.get("id"), "склад": items, "рядки": {н: рядки.get(н) for н in items}})
json.dump(вихід, open("/tmp/пс/склади_сирі.json","w"), ensure_ascii=False)
from collections import Counter
print(len(вихід), Counter(в["тека"].split("/")[-1]+":"+в["вид"] for в in вихід))
print("без рядка:", sum(1 for в in вихід for н,р in в["рядки"].items() if р is None))
