"""Рядок 5740: злиття точних дублів у `речі_з_відповіді` (6б `seed3_11`: 8 рядків → 4, «запасних» 5 → 1).
Аргумент — файл відповіді задачі `РЕЧІ` (типово: власна копія 6б з 4 речей, названих двічі)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import оцінка_образу as О

def річ(фото, слот, колір, назва, у_образі, рамка):
    return dict(photo=фото, slot=слот, color=колір, name=назва, in_outfit=у_образі, frame=рамка)

if len(sys.argv) > 1:
    текст = open(sys.argv[1], encoding="utf-8").read()
    текст = текст.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1] if "── ВІДПОВІДЬ" in текст else текст
else:
    чотири = [річ("ф1", "outerwear", "olive", "Olive jacket", True, [0, 0, 500, 500]),
              річ("ф1", "bottom", "burgundy", "Burgundy skirt", True, [0, 500, 500, 1000]),
              річ("ф2", "top", "beige", "Beige shirt", None, [0, 0, 500, 500]),
              річ("ф2", "top", "black", "Black shirt", False, [500, 0, 1000, 500])]
    текст = json.dumps({"items": чотири + чотири})
для = [{"ід": "ф1"}, {"ід": "ф2"}]
р = О.речі_з_відповіді(текст, для)
дублів = sum(х.startswith(О.ДУБЛЬ_РЕЧІ) for х in р["нотатки"])
образ, запасні, _ = О.скласти(р["речі"])
print("рядків у відповіді: %d → після злиття: %d; «запасних»: %d; нотатки duplicate_item: %d"
      % (len(р["речі"]) + дублів, len(р["речі"]), len(запасні), дублів))
print("ід:", [х["ід"] for х in р["речі"]])
