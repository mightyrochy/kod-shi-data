"""5.4-Г: 148 речей частини 1 зі slot=unknown — бракує типу в переліку чи модель змовчала?

Назву речі звіряє зі словником типу фіда (`фід_слот.ТИП_КЛЮЧІ`) і з родовими словами переліку
item_type (сукня, шапка…). Друкує, скільки назв має тип, уже наявний у переліку.
Запуск: python3 проби/типи_unknown_54г.py"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import каталог_розбір_прогін as П, фід_слот as ФС
РОДОВІ = {"dress_generic": ("сукн",), "hat": ("шапк",), "belt": ("ремін", "пояс"), "earrings": ("сереж",),
          "sneakers": ("sneaker", "кросів"), "bracelet": ("брасл",), "ring": ("кільц", "каблучк"),
          "fur_coat": ("шуб",), "t_shirt": ("поло",), "poncho": ("кейп",)}
к = json.load(gzip.open(os.path.join(os.path.dirname(П.__file__), "каталог_розбір_коди.json.gz"), "rt"))
оф, _ = П.ФР.читати_yml(П.ФК.каталог_на_диску(), показ=False)
назва = {о["id"]: (о.get("name") or о.get("назва") or "").lower() for о in оф}
лік, без = collections.Counter(), []
for і, р in к.items():
    if р.get("slot") != "unknown":
        continue
    н = назва.get(і, "")
    if any(any(х in н for х in кл) for _, кл in ФС.ТИП_КЛЮЧІ):
        лік[(р.get("item_type"), "словник фіда")] += 1
    elif any(any(х in н for х in кл) for кл in РОДОВІ.values()):
        лік[(р.get("item_type"), "родове слово переліку")] += 1
    else:
        лік[(р.get("item_type"), "типу нема")] += 1; без.append(н[:50])
print("slot=unknown:", sum(лік.values()))
for (т, д), n in sorted(лік.items()):
    print("  модель item_type=%s, тип за назвою — %s: %d" % (т, д, n))
print("без типу за назвою:", без)
