"""Рядок 5261: пора року в суді без градусів. Сцена 1551 (тест власника 14.10: побачення ввечері, дощ, градусів
нема) — пул каталогу її входу, судить `від_моделі`: лляна сукня з босоніжками, топ на бретелях. Друкує знахідки
K-MAT-03 / K-WEA-07 / K-WEA-01 і скільки лляних, на бретелях і босоніжок лишилось у пулі (пул не відсіює, п.17).
Кращим: знахідки є (осінь — hint), пул той самий. Запуск: cd джерела && python3 проби/сезон_5261.py"""
import datetime, json, subprocess, sys
sys.path.insert(0, "."); import bridge as B, feed as Ф, сценарій as СЦ
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/vlasnyk-1410-1551:refs/remotes/origin/claude/vlasnyk-1410-1551")
с = json.loads(git("show", "origin/claude/vlasnyk-1410-1551:аудит/тести/власник_2026-10-14/"
                   "verdykty-0phxvk-2026-10-14-1551.json"))["спільне"]
СЦ.сьогодні = lambda: datetime.date(2026, 10, 14)
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=с["вхід_прогону"]["сценарій"],
          паспорт=с["паспорт"], випадок=с["випадок_моделі"], гілка=0)
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml")
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = B.каталог_останнього_пакета()
назва = lambda c: str(c.get("назва") or "").lower()
льон = [c for c in кат if c.get("слот") in ("сукня", "верх") and ("льон" in назва(c) or "льн" in назва(c))]
бретелі = [c for c in кат if c.get("слот") == "верх" and "бретел" in назва(c) and "льон" not in назва(c)]
босоніжки = [c for c in кат if c.get("слот") == "взуття" and c.get("тип") == "босоніжки"]
низ = next(c for c in кат if c.get("слот") == "низ")
print("пул: лляних %d · на бретелях %d · босоніжок %d" % (len(льон), len(бретелі), len(босоніжки)))
def знахідки(x):
    if isinstance(x, dict):
        yield from ([x] if x.get("правило") in ("K-MAT-03", "K-WEA-07", "K-WEA-01") and x.get("заяви") else [])
        for v in x.values(): yield from знахідки(v)
    elif isinstance(x, list):
        for v in x: yield from знахідки(v)
def суди(ід):
    в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
    return sorted({(z["правило"], z.get("сила"), z.get("регістр"), z.get("сила_нп"), (z.get("заяви") or [{}])[0].get("code"))
                   for z in знахідки(в)}, key=str)
сукня = next((c for c in льон if c.get("слот") == "сукня"), льон[0])
for підпис, ід in (("лляна %s + босоніжки" % сукня["слот"], [сукня["id"], босоніжки[0]["id"]]),
                   ("топ на бретелях + низ + босоніжки", [бретелі[0]["id"], низ["id"], босоніжки[0]["id"]])):
    print("%s:" % підпис, [c["назва"][:40] for c in кат if c["id"] in ід])
    for z in суди(ід):
        print("   ", z)
