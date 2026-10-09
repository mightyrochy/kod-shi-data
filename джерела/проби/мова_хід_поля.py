# -*- coding: utf-8 -*-
"""Рядки 3451, 3453, 3454, 3456 (живі 13): скільки полів перший хід розмови дає з її листа. Записані відповіді
MamayLM (`мова_хід_поля_записи.json`: перші ходи живих 12 і 13) — тим самим кодом (`прийняти_розмову`): поле є,
коли код його взяв. Далі — промпт ходу: живі 12 → тепер, частинами, і чи стоять нові вказівки.
Запуск: python3 проби/мова_хід_поля.py"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М
ТУТ = pathlib.Path(__file__).resolve().parent
записи = json.load(open(ТУТ / "мова_хід_поля_записи.json", encoding="utf-8"))
# що її лист називає (читає проба, не код): поле → уривки листа, що його несуть
ЧЕКАЄ = {"temperature_c": "мінус п'ятнадцять", "precipitation": ("сніг", "дощ"), "movement": "пішки",
         "place": "ресторані", "wants|own_items": ("замшеві чоботи", "своє взуття"), "part_of_day": ("ввечері", "зранку")}
лічба = {}
for з in записи:
    р = М.прийняти_розмову(з["відповідь"])
    в = р["внутрішня"]
    for поле, уривки in ЧЕКАЄ.items():
        if any(у in з["нове"] for у in ((уривки,) if isinstance(уривки, str) else уривки)):
            к = лічба.setdefault((поле, з["живі"]), [0, 0])
            к[0] += any(в.get(п) for п in поле.split("|"))
            к[1] += 1
    if "ввечері" in з["нове"]:
        лічба.setdefault(("hour без годинника (вада)", з["живі"]), [0, 0])[0] += в.get("hour") is not None
        лічба[("hour без годинника (вада)", з["живі"])][1] += 1
print("поле першого ходу            живі 12   живі 13")
for поле in list(ЧЕКАЄ) + ["hour без годинника (вада)"]:
    print("  %-26s %s" % (поле, "   ".join("%d з %d" % tuple(лічба.get((поле, ж), [0, 0])) for ж in ("живі_12", "живі_13"))))
старий = (ТУТ.parent.parent / "аудит/живі_12/А/02_ж7_мороз_без_відкритого/VIDPOVIDI/"
          "seed4_01_мовний_шар_хід_розмови.txt").read_text(encoding="utf-8")
п12 = json.loads(старий.split("\n", 1)[1].split("── ВІДПОВІДЬ")[0])
п = json.loads(М.промпт_розмови({"розмова": {"нове": п12["her_new_message"], "історія": []}}))
print("промпт К7р, симв.: живі 12 %d · живі 13 %d · тепер %d" % (len(json.dumps(п12, ensure_ascii=False)),
      next(з["симв"] for з in записи if з["живі"] == "живі_13" and з["нове"] == п12["her_new_message"]), len(json.dumps(п, ensure_ascii=False))))
for ч in ("input", "rules", "codes", "answer_schema"):
    print("  task.%-14s %6d → %6d" % (ч, len(json.dumps(п12["task"][ч], ensure_ascii=False)),
                                      len(json.dumps(п["task"][ч], ensure_ascii=False))))
for уривок in ("Go through her message part by part", "never an hour", "only when she names a clock time",
               "one phrase may fill several"):
    print("  вказівка «%s»: %d" % (уривок, json.dumps(п, ensure_ascii=False).count(уривок)))
