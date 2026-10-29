"""Рядки 5260, 5232, 5230: факти дня — у всіх споживачів. Сцена 1551 (тест власника 14.10: побачення ввечері, дощ)
— `case` рук 3–4 і запит палітри (`occasion` + `day`) проти `day` рук 1–2; replay ЖИВІ-15 №12 (новорічний
корпоратив, хід 10.10) — записана відповідь і та сама з `month: december` на «новорічний» (поле після 5260).
Кращим: руки 3–4 і палітра мають `part_of_day`, `precipitation`, `season`; №12 з місяцем — `winter` усюди.
Запуск: cd джерела && python3 проби/сезон_5260.py (гілки `claude/vlasnyk-1410-1551`, `claude/zhyvi-15`)."""
import datetime, json, subprocess, sys
sys.path.insert(0, "."); import сценарій as СЦ, руки_без_коду as Р, мовний_шар as М, вибір_палітри as ВП
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for г in ("claude/vlasnyk-1410-1551", "claude/zhyvi-15"):
    git("fetch", "-q", "origin", "%s:refs/remotes/origin/%s" % (г, г))
с = json.loads(git("show", "origin/claude/vlasnyk-1410-1551:аудит/тести/власник_2026-10-14/"
                   "verdykty-0phxvk-2026-10-14-1551.json"))["спільне"]
т12 = git("show", "origin/claude/zhyvi-15:аудит/живі_15/А/12_ж2_корпоратив_виділитися/VIDPOVIDI/"
          "seed3_01_мовний_шар_хід_розмови.txt").split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]
сц12 = {"година": 11, "темп_c": 18, "типові_поля": ["година", "темп_c"]}
def паспорт12(т):
    п = М.паспорт_з_шару(М.прийняти_розмову(т)["внутрішня"], сц12,
                         слова_ходу=["новорічний корпоратив у ресторані, дрес-код коктейльний"])["паспорт"]
    return п
з_місяцем = т12.replace('"update": {', '"update": {"month": {"quote": "новорічний", "value": "december"},', 1)
СЦЕНИ = [("1551", с["паспорт"], с["вхід_прогону"]["сценарій"], с["випадок_моделі"], "2026-10-14"),
         ("№12 запис", паспорт12(т12), сц12, "новорічний корпоратив", "2026-10-10"),
         ("№12 month", паспорт12(з_місяцем), сц12, "новорічний корпоратив", "2026-10-10")]
ФАКТИ = ("season", "part_of_day", "precipitation", "temperature_c", "dress_code", "formality", "goal")
for ім, п, сц, рядок, дата in СЦЕНИ:
    СЦ.сьогодні = lambda д=дата: datetime.date.fromisoformat(д)
    print("── %s, дата %s, паспорт місяць=%s" % (ім, дата, п.get("місяць")))
    print("   руки 1–2 day:", {к: v for к, v in СЦ.день_кодами(СЦ.з_показу(сц, п)[0]).items() if к in ФАКТИ})
    case = Р.випадок_кодами(п, рядок, сценарій=сц)
    print("   руки 3–4 case:", {к: v for к, v in case.items() if к in ФАКТИ})
    пал = ВП._випадок(dict(паспорт=п, сценарій=сц, випадок=рядок))
    о, д = пал if isinstance(пал, tuple) else (пал, None)
    print("   палітра occasion:", {к: v for к, v in о.items() if к in ФАКТИ}, "| day:",
          {к: v for к, v in (д or {}).items() if к in ФАКТИ} or "—")
