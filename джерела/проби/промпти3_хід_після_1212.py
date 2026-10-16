"""ХІД-ПІСЛЯ-1212 (рядки 6455, 6457, 6290): replay записаних відповідей тим самим кодом читання, без моделі.
1) Перші ходи Ж:16–50 ЖИВІ-1016-1 (`claude/zhyvi-1016-1`): поле `update`, якого нема ні у внутрішній мові (і на своєму
полі після шва), ні в `невідомо` з рядком `не_взято`, — знято мовчки; ДО (main) 11, ПІСЛЯ 0; Ж:34/39 — `place` club/bar;
Ж:36 — нагода списком за `occasion_part`.
2) Ходи плиток ж1 живої пачки 15: formality парою з одним числом, яку код не взяв; ДО 3, ПІСЛЯ 0.
Запуск: cd джерела && python3 проби/промпти3_хід_після_1212.py"""
import re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
відповідь = lambda Г, ф: git("show", "%s:%s" % (Г, ф)).split("── ВІДПОВІДЬ", 1)[-1].split("──", 1)[-1]
ходи = lambda Г, взір: sorted(ф for ф in git("ls-tree", "-r", "--name-only", Г, "../аудит/").split("\n") if re.search(взір, ф))
Г = "origin/claude/zhyvi-1016-1"
git("fetch", "-q", "origin", "claude/zhyvi-1016-1", "claude/zhyvi-pachka-15")
мовчки, місця = [], {}
for ф in ходи(Г, r"живі_1016_1/(1[6-9]|[2-4]\d|50)_[^/]*/VIDPOVIDI/seed\d_01_мовний_шар_хід_розмови"):
    сцена = "Ж:" + ф.split("/")[-3][:2]
    об = М._обʼєкт(відповідь(Г, ф))[0]
    р = М.прийняти_розмову(відповідь(Г, ф))
    куди = dict(x[7:].split("->", 1) for x in р["перенесено"] if x.startswith("update.") and "->" in x)
    for к in ((об or {}).get("update") or {}) if isinstance(об, dict) else ():
        if куди.get(к, к) not in р["внутрішня"] and к not in р["невідомо"] and к != "quotes":
            мовчки.append("%s %s" % (сцена, к))
    if сцена in ("Ж:34", "Ж:39"):
        місця[сцена] = (р["внутрішня"].get("place"), р["внутрішня"].get("occasion"))
    if сцена in ("Ж:36", "Ж:49"):     # рядок 6522: нагода списком — за occasion_part (у Ж:36 його нема)
        місця[сцена] = р["внутрішня"].get("occasion")
print("перших ходів Ж:16–50 — знято мовчки %d %s" % (len(мовчки), мовчки))
print("Ж:34/39 (place, occasion), Ж:36/49 occasion:", місця)
пар = не_взято = 0
for ф in ходи("origin/claude/zhyvi-pachka-15", r"0[1-9]_ж1_оціни_образ_6б/VIDPOVIDI/.*_хід_розмови"):
    об = М._обʼєкт(відповідь("origin/claude/zhyvi-pachka-15", ф))[0]
    ф_ = ((об or {}).get("update") or {}).get("formality") if isinstance(об, dict) else None
    if isinstance(ф_, dict) and "quote" in ф_ and isinstance(ф_.get("value"), (int, float)):
        пар += 1
        не_взято += "formality" not in М.прийняти_хід_плиток(відповідь("origin/claude/zhyvi-pachka-15", ф))["внутрішня"]
print("ходів плиток ж15 з formality парою-числом %d, не взято %d" % (пар, не_взято))
print("R5 межа зон:", "goal_zones holds only" in М.РОЗМОВА_ПРАВИЛА[5], "· скелет просить пару:",
      '"value"' in М.СКЕЛЕТ_РОЗМОВИ["update"]["<field>"])
