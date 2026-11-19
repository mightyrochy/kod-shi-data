"""Лічба «неперевіреного» по РЯДКАХ картки (пункт без `для_всіх` = рядок, який бачить жінка).
Факт рядка — (клас заяви, річ): колір речі — один клас, хоч яким кодом сказано (`міст_відповіді._ФАКТ_ЗАЯВИ`).
Повтор — рядок, усі факти якого вже стояли в рядках вище; «факт удруге» — скільки разів факт про річ
стоїть у другому й далі рядку; заяви журналу (`recipient=journal`) жінці не показують і тут не лічать."""
import json, sys, collections
КОЛІР = {"colour_word_shop", "colour_word_shop_photo_other", "colour_word_model", "colour_word_not_photo",
         "colour_partly_measured", "photo_shows_other_colour"}
def факти(з):
    к = "колір_речі" if з.get("code") in КОЛІР else з.get("code")
    в = з.get("values") or {}
    р = [х.get("item_id") for х in в.get("items") or [] if isinstance(х, dict) and х.get("item_id")]
    р += [і for і in [в.get("item_id"), (в.get("item") or {}).get("item_id") if isinstance(в.get("item"), dict) else None] if і]
    return {(к, і) for і in р} if р else {(к, json.dumps(в, sort_keys=True, ensure_ascii=False))}
д = json.load(open(sys.argv[1])); разом = collections.Counter()
for ім, вм in д.items():
    рядки = [п for п in вм.get("пункти") or [] if not п.get("для_всіх") and п.get("повідомлення")]
    бачено, повт, удруге, заяв = set(), 0, 0, 0
    for п in рядки:
        зз = [з for з in п["повідомлення"]["statements"] if з.get("recipient") != "journal"]
        заяв += len(зз)
        ф = set().union(*[факти(з) for з in зз]) if зз else set()
        повт += bool(ф) and ф <= бачено
        удруге += len(ф & бачено)
        бачено |= ф
    print("%-22s рядків %2d, рядків-повторів %2d, факт про річ удруге %2d, заяв жінці %3d" % (ім, len(рядки), повт, удруге, заяв))
    разом.update(рядків=len(рядки), повторів=повт, факт_удруге=удруге, заяв=заяв)
print("РАЗОМ", dict(разом))
