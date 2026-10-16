"""Рядок 5910: K-MAT-03 із градусами на образі без верхнього шару. Сцена 1551 (файл власника 14.10) із градусами
з її слів: +5 °C і +18 °C: судить `від_моделі` руки 1–2 файла, лляну сукню з
босоніжками й топ на бретелях. Друкує кожну знахідку погоди (K-MAT-03, K-WEA-*) з регістром і силою — ДО/ПІСЛЯ
порівнюються двома прогонами. Запуск: cd джерела && python3 проби/погода_без_пальта_5910.py"""
import datetime, json, subprocess, sys
sys.path.insert(0, "."); import bridge as B, feed as Ф, сценарій as СЦ
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/vlasnyk-1410-1551:refs/remotes/origin/claude/vlasnyk-1410-1551")
ф = json.loads(git("show", "origin/claude/vlasnyk-1410-1551:аудит/тести/власник_2026-10-14/"
                   "verdykty-0phxvk-2026-10-14-1551.json"))
с, руки = ф["спільне"], {в["рука"]: в["склад"].split("+") for в in ф["прогони"][0]["вердикти"]}
СЦ.сьогодні = lambda: datetime.date(2026, 10, 14)
for темп in (5, 18):
    сц = dict(с["вхід_прогону"]["сценарій"], темп_c=темп, типові_поля=["година"])
    па = dict(с["паспорт"], темп_c=темп, джерело_полів=dict(с["паспорт"]["джерело_полів"], темп_c="розмова"),
              виміри=dict(с["паспорт"]["виміри"], temperature_c=темп))
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=сц, паспорт=па,
              випадок=с["випадок_моделі"], гілка=0, каталог=Ф.каталог_на_диску("каталог_повний.xml"))
    json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    кат = B.каталог_останнього_пакета()
    н = lambda c: str(c.get("назва") or "").lower()
    сукня = next(c for c in кат if c.get("слот") == "сукня" and ("льон" in н(c) or "льн" in н(c)))
    бос = next(c for c in кат if c.get("слот") == "взуття" and c.get("тип") == "босоніжки")
    топ = next(c for c in кат if c.get("слот") == "верх" and "бретел" in н(c) and "льон" not in н(c))
    низ = next(c for c in кат if c.get("слот") == "низ")
    образи = [("рука 1", руки["1"]), ("рука 2", руки["2"]), ("лляна сукня + босоніжки", [сукня["id"], бос["id"]]),
              ("топ на бретелях + низ + босоніжки", [топ["id"], низ["id"], бос["id"]])]
    for підпис, ід in образи:
        в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
        зн = set()
        def обійти(x):
            if isinstance(x, dict):
                if str(x.get("правило", "")).startswith(("K-MAT-03", "K-WEA-")) and x.get("заяви"):
                    зн.add((x["правило"], x.get("сила"), x.get("сила_нп"), x["заяви"][0].get("code")))
                for v in x.values(): обійти(v)
            elif isinstance(x, list):
                for v in x: обійти(v)
        обійти(в)
        print("%+d °C · %s · верхній шар %s" % (темп, підпис, "є" if any(c.get("слот") == "верхній_шар"
              for c in кат if c["id"] in ід) else "нема"), в.get("помилка") or "")
        for z in sorted(зн, key=str): print("   ", z)
