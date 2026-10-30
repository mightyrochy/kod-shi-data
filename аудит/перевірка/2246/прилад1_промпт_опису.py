# Мій прилад перевірки (не виконавця): ті самі 6 прогонів живого шляху, але лічу ВЕСЬ промпт опису
# незалежно від речей образу: будь-яка назва каталогу, будь-який id з "@", ключі shop/free_text/item_ids.
import json, os, re, sys, tempfile
ТУТ = os.getcwd(); sys.path.insert(0, ТУТ)
import тест_живого_шляху as Т, bridge as B, feed as Ф
пійм = []
_в = B.виклик
def об(ім, вх):
    в = _в(ім, вх)
    if ім == "опис": пійм.append((json.loads(вх), json.loads(в)))
    return в
B.виклик = об
вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["каталог"] = Ф.каталог_на_диску(Т.КАТАЛОГ)
вх["кеш_кольорів"] = os.path.join(tempfile.gettempdir(), "кеш_живого_шляху.json")
if not os.path.exists(вх["кеш_кольорів"]): json.dump({}, open(вх["кеш_кольорів"], "w"))
каталог = Ф.база_прогону(вх["каталог"], 0, вх["кеш_кольорів"])["каталог"]
назви = {re.sub(r"\s+", " ", str(з.get("назва") or "")).strip() for з in каталог}
назви = {н for н in назви if len(н) > 6}
ід_ре = re.compile(r"[\wа-яіїєґ.\-]+@[\w.\-]+")
sumс = dict(назва=0, id_з_пошти=0, shop=0, free_text=0, item_ids=0)
for г in Т.ГІЛКИ:
    for н in Т.НАМІРИ:
        пійм.clear(); Т.прогін(вх, г, н)
        for _, о in [x for x in пійм if True]:
            п = о["промпт"]
            sumс["назва"] += sum(п.count(x) for x in назви)
            sumс["id_з_пошти"] += len(ід_ре.findall(п))
            sumс["shop"] += п.count('"shop') + п.count("shop_color")
            sumс["free_text"] += п.count("free_text"); sumс["item_ids"] += п.count("item_ids")
print("МІЙ ПРИЛАД, промпт опису, 6 прогонів:", sumс)
