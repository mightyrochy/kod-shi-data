"""Рядок 3653 і наряд МОВА-ПЕРШИЙ-ХІД (3740–3742): replay перших ходів розмови ЖИВІ-14 (ПІСЛЯ пачок 19–21,
`claude/zhyvi-14`) тим самим кодом (`прийняти_розмову` → `суд_частин`), без моделі. На кожен хід друкує: що код
записав, причину повтору, теми запрошення, бульбашку після суду і відкинуті частини з «чужими» кодами `about`.
Кращим: речення про записане не знімається через код, який код сам переклав (`weather_feel` → `precipitation`) чи не
взяв (`goal_zones`); при `need` look/app хід не падає в `no_text_field`.
Запуск: cd джерела && python3 проби/живі14_перший_хід.py"""
import subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
Г, Т = "origin/claude/zhyvi-14", "../аудит/живі_14/А"
subprocess.run(["git", "fetch", "-q", "origin", "claude/zhyvi-14"], capture_output=True)
файли = [ф for ф in subprocess.run(["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", Г, Т],
         capture_output=True, text=True).stdout.split() if "хід_розмови" in ф and ("_01_" in ф or "оціни" in ф)]
порожніх = знято = без_тексту_оцінки = без_кодів_оцінки = 0
for ф in файли:
    т = subprocess.run(["git", "show", "%s:%s" % (Г, ф)], capture_output=True, text=True).stdout
    р = М.прийняти_розмову(т.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1])
    ч = р["частини"]
    б, _, відк, *_ = М.суд_частин(ч, ч.get("invite_topics") or [], [], записано=р["внутрішня"])
    чуже = [x.get("чуже") for x in відк if x["чому"] == "not_about_recorded" and x.get("чуже")]
    if not б and ч.get("need") == "look":
        без_тексту_оцінки += not ч.get("text")
        без_кодів_оцінки += bool(ч.get("text")) and any(
            x["чому"] == "not_about_recorded" and not x.get("про") for x in відк)
    порожніх += not б; знято += bool(чуже)
    print(ф.split("/")[-3][:26], ф.split("/")[-1][:8], "| записано:", sorted(к for к in р["внутрішня"] if к != "quotes"),
          "| причина:", р["причина"], "| теми:", ч.get("invite_topics"), "| чуже:", чуже, "| бульбашка:", (б or "—")[:70])
print("ходів:", len(файли), "| бульбашка порожня:", порожніх, "| речення знято через «чужий» код:", знято)
print("порожні need=look: без says:", без_тексту_оцінки, "| says без about:", без_кодів_оцінки)
