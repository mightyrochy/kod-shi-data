"""Рядки жінці для знімків ДО/ПІСЛЯ: пункт картки → один рядок. Слова — живої моделі з записаного прогону
(`укр.json`, ключ код+значення без речей); свідки кольору й крій без назви — за взірцем її речення з видом і кольором САМЕ цієї
речі (записаний словник річ не розрізняв, і два різні вироби читались одним «шарфом «молочний»»).
Однаковий словник на обидва боки: різниться лише те, які пункти й заяви лишились."""
import json, sys
м = json.load(open(sys.argv[1])); код, сиг = м["code"], м["sig"]
РІД = {"cap": "кепки", "collar_necklace": "намиста-коміра", "bracelet": "браслета", "jacket": "жакета",
       "brooch": "брошки", "beanie": "шапки", "loafers": "лоферів", "cardigan": "кардигана", "coat": "пальта",
       "heeled_sandals": "босоніжок", "scarf": "шарфа", "bag_generic": "сумки", "boots": "чобіт", "dress": "сукні"}
СЛОВО = {"white": "білий", "powder_pink": "пудровий", "black": "чорний", "green": "зелений", "turquoise": "бірюзовий"}
def вид(в): return ", ".join(РІД.get(х.get("kind"), "речі") for х in в.get("items") or []) or "речі"
def с(x): return СЛОВО.get(x, x)
def sig(z):
    def n(x):
        if isinstance(x, dict): return {k: n(w) for k, w in sorted(x.items()) if k not in ("item_id", "items", "item_ids")}
        if isinstance(x, list): return [n(w) for w in x]
        return x
    return json.dumps(n(z.get("values") or {}), ensure_ascii=False, sort_keys=True)
def речення(з):
    к, в = з["code"], з.get("values") or {}
    х = (в.get("items") or [{}])[0]
    if к in ("colour_word_shop", "colour_word_model", "colour_word_not_photo"):
        джерело = "крамниці" if к == "colour_word_shop" else "опису"
        return "Колір %s я знаю лише зі слова %s — «%s», а не з виміру по фото." % (вид(в), джерело, с(х.get("colour", "")))
    if к in ("colour_word_shop_photo_other", "photo_shows_other_colour"):
        return ("Крамниця називає колір %s «%s», а на фото картки він %s, тож напевно я його не знаю — поглянь на річ сама."
                % (вид(в), с(х.get("colour", "")), с(х.get("photo", ""))))
    if к == "cut_not_declared_assumed_regular":
        return ("У картці %s не названо крій, тому я порахувала його як звичайний прямий; усе далі правильне, лише "
                "якщо крій справді такий." % вид(в))
    return сиг.get(к + "|" + sig(з)) or код.get(к)
def картка(шлях, сцена):
    рядки = []
    for п in json.load(open(шлях))[сцена]["пункти"]:
        if п.get("для_всіх"): continue
        ч = []
        for з in (п.get("повідомлення") or {}).get("statements") or []:
            if з.get("recipient") == "journal": continue
            т = речення(з)
            if т and т not in ч: ч.append(т)
        if ч: рядки.append(" ".join(ч))
    return рядки
до, після = sys.argv[2], sys.argv[3]
вих = {с_: {"before": картка(до, с_), "after": картка(після, с_)} for с_ in ("весілля_літо", "мороз_ожеледь_офіс")}
json.dump(вих, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)
for с_, в in вих.items(): print(с_, len(в["before"]), "→", len(в["after"]))
