"""Рядки 3740–3742 (ЖИВІ-14 проти ЖИВІ-13): перший хід розмови. Записані відповіді MamayLM (VIDPOVIDI гілок живих) —
тим самим кодом: `прийняти_розмову` → `паспорт_з_шару` (суд частин, перший хід — паспорт порожній). Друкує по живих:
К7 — поля, які код записав; речення `text`, що дійшли до неї; запрошення, які суд прийняв; ходи без читаної відповіді.
Далі — промпт ходу К7: розмір і чи стоять вказівки правки. Слова тут читає ПРОБА, не код.
Запуск: cd джерела && python3 проби/мова_перший_хід.py"""
import json, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
ГІЛКИ = {"живі_13": "origin/claude/zhyvi-13", "живі_14": "origin/claude/zhyvi-14"}
К7 = ("occasion", "open_zones", "temperature_c", "precipitation", "movement")
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for ж, г in ГІЛКИ.items():
    л = dict(ходів=0, к7=0, **{к: 0 for к in К7}, текст=0, запрошень=0, теми_моделі=0, без_відповіді=0)
    for ф in git("ls-tree", "-r", "--name-only", г, "../аудит/%s/А" % ж).split():
        if "хід_розмови" not in ф or not ("_01_" in ф or "оціни" in ф and "_13_" not in ф): continue
        с = git("show", "%s:%s" % (г, ф)); нове = json.loads(с.split("\n", 1)[1].split("── ВІДПОВІДЬ")[0])["her_new_message"]
        р = М.прийняти_розмову(с.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]); л["ходів"] += 1
        л["теми_моделі"] += bool(р["частини"].get("invite_topics"))
        if р.get("причина"): л["без_відповіді"] += 1; continue
        ш = М.паспорт_з_шару(р["внутрішня"], {}, слова_ходу=[нове], частини=р["частини"], не_взято=р.get("не_взято"))
        л["текст"] += bool(ш.get("текст")); л["запрошень"] += bool(ш.get("теми_поради"))
        if "мінус п'ятнадцять" in нове:
            л["к7"] += 1
            for к in К7: л[к] += (ш.get("записано") or {}).get(к) not in (None, "", "unknown")
    print(ж, " · ".join("%s %s" % кv for кv in л.items()))
п = json.dumps(json.loads(М.промпт_розмови({"розмова": {"нове": "йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, "
                                                          "відкритого не хочу", "історія": []}})), ensure_ascii=False)
print("промпт К7, симв.:", len(п))
for у in ("the outing itself", "never goal_zones", "never in \\\"text\\\"", "whenever \\\"advice_topics\\\" has codes",
          "invites her to tell nothing", "Whatever you want her to tell", "\\\"invite\\\" is optional"):
    print("  «%s»: %d" % (у.replace("\\\"", '"'), п.count(у)))
