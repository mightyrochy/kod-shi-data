# -*- coding: utf-8 -*-
"""Рядок 4510, було (БАЗА — git worktree, типово origin/main) → стало: назва теплих нейтралей палітри з волосся (L*35.4 і 40.1,
C* 8, h 90 — як `palettes.кольори`) і код hex знахідки; точки крамниць з виміром з фото (усі й C* < 10) — підпис `palettes._назва`
і збіг зі словом крамниці; hex відповідей моделі (VIDPOVIDI), що змінили код; ґратка основ; записи каталогу, що змінились. Запуск: cd джерела && python3 проби/колір_майже_нейтраль.py [база]"""
import collections as К, json, os, re, subprocess, sys, tempfile, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, ".")
if sys.argv[1:2] == ["--знімок"]:
    import feed, мовний_шар as МШ, міст_основи as МО, palettes as PS, фід_каталог as FK, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as cs
    шл = subprocess.run(["git", "ls-files", "-z", "--", "../аудит"], capture_output=True).stdout.decode().split("\0")
    hx = sorted({"#" + х.upper() for ф in шл if "VIDPOVIDI" in ф for х in re.findall(r"#([0-9a-fA-F]{6})\b", open(ф, encoding="utf-8", errors="ignore").read())} | {"#585346", "#645e52"})
    зб, кр = feed.читати_збагачення(), {}
    for o in FR.читати_yml("каталог_повний.xml")[0]:
        z, п = зб.get(o["id"]) or {}, " ".join(str(o.get("колір_сирий") or "").lower().split())
        if п and len(FK._СЕП_КОЛЬОРУ.split(п)) == 1 and V.слово_крамниці(п) and (z.get("колір_основний") or {}).get("hex") \
                and (z.get("версія") or 1) >= 2 and FZ.колір_збагачення(z)[2].startswith("hex"):
            кр[o["id"]] = (V.слово_крамниці(п)["ім"], PS._назва(cs.hx(z["колір_основний"]["hex"]))[0], cs.lch(cs.hx(z["колір_основний"]["hex"]))[1])
    кат = {r["id"]: r for r in FK._прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
    json.dump(dict(нт={L: (PS._назва(PS._lab(L, 8.0, 90))[0], PS._hex(PS._lab(L, 8.0, 90))) for L in (35.4, 40.1)}, коди={х: МШ._код_кольору(х[1:]) for х in hx}, ґратка=МО._ґратка_основ()[0], крамниці=кр, каталог=кат),
              open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, default=str)
    sys.exit()
база, т = (sys.argv[1:] or ["origin/main"])[0], tempfile.mkdtemp(); subprocess.run(["git", "worktree", "add", "-q", "--detach", т + "/б", база], check=True)
try:
    os.symlink(os.path.abspath("каталог_повний.xml"), т + "/б/джерела/каталог_повний.xml")
    for д, ф in ((т + "/б/джерела", т + "/до.json"), (".", т + "/після.json")):
        subprocess.run([sys.executable, os.path.abspath(__file__), "--знімок", ф], cwd=д, check=True)
    до, піс = (json.load(open(т + ф, encoding="utf-8")) for ф in ("/до.json", "/після.json"))
finally: subprocess.run(["git", "worktree", "remove", "--force", т + "/б"])
print("ФАКТ · теплі нейтралі палітри (L*: назва, hex):", до["нт"], "→", піс["нт"], "; коди hex знахідки:", {х: (до["коди"].get(х), піс["коди"].get(х)) for х in ("#585346", "#645E52")})
АХ = {"чорний", "білий", "сірий", "графіт", "срібний"}
print("ФАКТ · точки крамниць з C* < 10 (усього, підпис хроматичний, у крамниці хроматичне, збіг) до → після:", [(len(м), sum(в[1] not in АХ for в in м),
      sum(в[0] not in АХ for в in м), sum(в[0] == в[1] for в in м)) for м in ([в for в in x["крамниці"].values() if в[2] < 10] for x in (до, піс))])
зм = [х for х in піс["коди"] if до["коди"].get(х) != піс["коди"][х]]
print("ФАКТ · hex з відповідей моделі: %d, код змінився в %d — %s" % (len(піс["коди"]), len(зм), dict(К.Counter((до["коди"][х], піс["коди"][х]) for х in зм))))
print("ФАКТ · ґратка основ: %s" % ("ПОБАЙТОВО ТА САМА" if до["ґратка"] == піс["ґратка"] else "ЗМІНИЛАСЬ: %s" % sorted(set(до["ґратка"]) ^ set(піс["ґратка"]))))
кз = [і for і in піс["крамниці"] if до["крамниці"][і][1] != піс["крамниці"][і][1]]
print("ФАКТ · точок крамниць з виміром %d: підпис змінився в %d %s; збіг підпису зі словом крамниці %d → %d" % (len(піс["крамниці"]), len(кз),
      dict(К.Counter((до["крамниці"][і][1], піс["крамниці"][і][1]) for і in кз)), *(sum(в[0] == в[1] for в in x["крамниці"].values()) for x in (до, піс))))
кк = [і for і in піс["каталог"] if до["каталог"].get(і) != піс["каталог"][і]]
print("ФАКТ · каталог: речей %d → %d; запис змінився в %d, поля %s" % (len(до["каталог"]), len(піс["каталог"]), len(кк),
      dict(К.Counter(п for і in кк for п in set(до["каталог"][і]) | set(піс["каталог"][і]) if до["каталог"][і].get(п) != піс["каталог"][і].get(п)))))
