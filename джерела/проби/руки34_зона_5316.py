"""Рядок 5316: `goal_zones` у `case` рук 3–4. Запис живого Г (`claude/zhyvi-1510-g`, код 42d185b2): мовний шар Г3 і Г4 →
паспорт (`паспорт_з_шару`, ходи по черзі) → `випадок_кодами` → промпт руки. ДО — `case` рук 3–4 із запису (того самого
прогону), ПІСЛЯ — з цього коду; рукам 1–2 зона йде в `case.goal_zones` (`пакет_моделі`). Кращим: ПІСЛЯ є `goal_zones`.
Запуск: cd джерела && python3 проби/руки34_зона_5316.py (потрібна гілка `claude/zhyvi-1510-g`)."""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М, руки_без_коду as Р, пакет_моделі as П, дріт_моделі as Д
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/zhyvi-1510-g:refs/remotes/origin/claude/zhyvi-1510-g")
ГІЛКА, ТЕКА = "origin/claude/zhyvi-1510-g", "аудит/живі_1510_Г/"
запис = lambda сц: [l for l in git("ls-tree", "--full-tree", "--name-only", ГІЛКА, ТЕКА + сц + "/VIDPOVIDI/").split("\n") if l]
for сцена in ("03_ж4_клуб_дивились_живіт_танці", "04_ж4_робота_живіт"):
    файли = sorted(l for l in запис(сцена) if "хід_розмови" in l)
    п, слова = None, []
    for ф in файли:
        пр, _, вд = git("show", ГІЛКА + ":" + ф).partition("── ВІДПОВІДЬ")
        сл = (re.search(r'"her_new_message": "([^"]*)"', пр) or [0, ""])[1]
        слова += [сл] if сл not in ("", "unknown") else []
        п = М.паспорт_з_шару(М.прийняти_розмову(вд.split("──", 1)[1])["внутрішня"], {}, паспорт_досі=п and п["паспорт"],
                             слова_ходу=слова)
    паспорт = п["паспорт"]
    проза = git("show", ГІЛКА + ":" + next(l for l in запис(сцена) if "проза_рука_3_4" in l))
    до = json.loads(re.search(r'"case": (\{.*?\})(?:, "person"|\})', проза).group(1))
    print("── %s | мета_зони паспорта: %s" % (сцена, паспорт.get("мета_зони")))
    print("   ДО (запис), рука 3–4 case.goal_zones:", до.get("goal_zones", "—"))
    for рука in ("3", "4"):
        вхід = json.loads(Р.промпт_руки(рука, Р.випадок_кодами(паспорт, паспорт.get("подія") or "")))
        print("   ПІСЛЯ, рука %s case.goal_zones:" % рука, вхід["case"].get("goal_zones", "—"),
              "| у перелік входу:", any("goal_zones" in x for x in вхід["task"]["input"]))
    print("   рукам 1–2 (пакет_моделі):", Д.випадок(П.випадок_для_пакета(паспорт, паспорт.get("подія") or "")).get("goal_zones", "—"))
