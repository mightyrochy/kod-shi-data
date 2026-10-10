# -*- coding: utf-8 -*-
"""Рядок 4371: вжиток слова «лимонний» — крамниці (вимір з фото речей з одним словом кольору) і модель (речення
ВІДПОВІДІ записаних прогонів VIDPOVIDI з hex і словом кольору), та код hex знахідки. Лише друкує факти.
Запуск: cd джерела && python3 проби/лимонний_вжиток.py   (потрібен розпакований каталог_повний.xml)"""
import collections as К, re, subprocess, sys, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, ".")
import feed, palettes as PS, фід_каталог as FK, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as cs
зб, кр = feed.читати_збагачення(), []
for o in FR.читати_yml("каталог_повний.xml")[0]:
    z, п = зб.get(o["id"]) or {}, " ".join(str(o.get("колір_сирий") or "").lower().split())
    if п and len(FK._СЕП_КОЛЬОРУ.split(п)) == 1 and V.слово_крамниці(п) and (z.get("колір_основний") or {}).get("hex") \
            and (z.get("версія") or 1) >= 2 and FZ.колір_збагачення(z)[2].startswith("hex"):
        кр.append((V.слово_крамниці(п)["ім"], z["колір_основний"]["hex"], *cs.lch(cs.hx(z["колір_основний"]["hex"]))))
лим = [к for к in кр if к[0] == "лимонний" and к[3] >= V.ДРІЖ_AB]
print("ФАКТ · крамниці «лимонний» з тоном (C* ≥ %g): %d, C* %.0f–%.0f, тон %.0f–%.0f, L* %.0f–%.0f" % (V.ДРІЖ_AB, len(лим),
      min(к[3] for к in лим), max(к[3] for к in лим), min(к[4] for к in лим), max(к[4] for к in лим), min(к[2] for к in лим), max(к[2] for к in лим)))
for мін, макс in ((45, 54), (54, 58), (58, 66), (66, 101)):
    зона = [к for к in кр if мін <= к[3] < макс and 94 <= к[4] <= 115 and к[2] >= 75]
    print("ФАКТ · крамниці, L* ≥ 75, тон 94–115°, C* %d–%d: %s · підпис коду: %s" % (мін, макс, dict(К.Counter(к[0] for к in зона)),
          dict(К.Counter((к[0], PS._назва(cs.hx(к[1]))[0]) for к in зона))))
шл = [ф for ф in subprocess.run(["git", "ls-files", "-z", "--", "../аудит"], capture_output=True).stdout.decode().split("\0") if "VIDPOVIDI" in ф]
сл, речень = К.Counter(), 0
for ф in шл:
    т = open(ф, encoding="utf-8", errors="ignore").read()
    for р in re.split(r"\n|(?<=[.;!?])\s", т.split("── ВІДПОВІДЬ", 1)[1] if "── ВІДПОВІДЬ" in т else ""):
        hx = {х.upper() for х in re.findall(r"#([0-9a-fA-F]{6})\b", р)}
        if len(hx) == 1:
            речень += 1
            for к, рег in (("лимонний", r"лимонн|\blemon"), ("жовтий", r"жовт|\byellow"), ("золотий", r"золот|\bgold")):
                if re.search(рег, р, re.I): сл[(к, next(iter(hx)))] += 1
print("ФАКТ · модель: файлів %d, речень відповіді з одним hex %d; слово моделі → hex: %s" % (len(шл), речень,
      {к: sorted({h for (кк, h) in сл if кк == к}) for к in ("лимонний", "жовтий", "золотий")}))
print("ФАКТ · код hex знахідки:", {h: PS._назва(cs.hx(h))[0] for h in ("#FFF44F", "#FAFA33", "#ECDA6E", "#DFDC8E", "#F4E87C", "#FFD700")})
