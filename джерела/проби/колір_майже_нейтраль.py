"""Теплі нейтралі, hex, ґратка й каталог на одному корпусі: із джерела/ python проби/колір_майже_нейтраль.py [база] [корпус]."""
import collections as К, json, os, re, subprocess, sys, tempfile, warnings; warnings.filterwarnings("ignore"); sys.path.insert(0, "."); import colorspace as cs
if sys.argv[1:2] == ["--знімок"]:
    import feed, мовний_шар as МШ, міст_основи as МО, palettes as PS, фід_каталог as FK, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as cs
    корпус = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.abspath(".."); шл = subprocess.run(["git", "ls-files", "-z", "--", "аудит"], cwd=корпус, capture_output=True).stdout.decode().split("\0")
    hx = sorted({"#" + х.upper() for ф in шл if "VIDPOVIDI" in ф for х in re.findall(r"#([0-9a-fA-F]{6})\b", open(os.path.join(корпус, ф), encoding="utf-8", errors="ignore").read())} | {"#585346", "#645e52"})
    зб, кр = feed.читати_збагачення(), {}
    for o in FR.читати_yml("каталог_повний.xml")[0]:
        z, п = зб.get(o["id"]) or {}, " ".join(str(o.get("колір_сирий") or "").lower().split())
        if п and len(FK._СЕП_КОЛЬОРУ.split(п)) == 1 and V.слово_крамниці(п) and (z.get("колір_основний") or {}).get("hex") \
                and (z.get("версія") or 1) >= 2 and FZ.колір_збагачення(z)[2].startswith("hex"):
            кр[o["id"]] = (V.слово_крамниці(п)["ім"], PS.назва(cs.hx(z["колір_основний"]["hex"]))[0], cs.lch(cs.hx(z["колір_основний"]["hex"]))[1], *cs.lch(cs.hx(z["колір_основний"]["hex"]))[::2])
    кат = {r["id"]: r for r in FK.прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
    json.dump(dict(нт={L: (PS.назва(PS.lab_з_lch(L, 8.0, 90))[0], PS.hex_з_lab(PS.lab_з_lch(L, 8.0, 90))) for L in (35.4, 40.1)}, коди={х: МШ._код_кольору(х[1:]) for х in hx}, ґратка=МО.ґратка_основ()[0], центри={ім: PS.назва(PS.центр(в))[0] for ім, в in V.ЛЕКСИКОН.items()}, крамниці=кр, каталог=кат),
              open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, default=str); sys.exit()
база, т = (sys.argv[1:] or ["origin/main"])[0], tempfile.mkdtemp(); корпус = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.abspath(".."); subprocess.run(["git", "worktree", "add", "-q", "--detach", т + "/б", база], check=True)
try:
    import shutil
    shutil.copyfile(os.path.abspath("каталог_повний.xml"), т + "/б/джерела/каталог_повний.xml")
    for д, ф in ((т + "/б/джерела", т + "/до.json"), (".", т + "/після.json")):
        subprocess.run([sys.executable, os.path.abspath(__file__), "--знімок", ф, корпус], cwd=д, check=True)
    до, піс = (json.load(open(т + ф, encoding="utf-8")) for ф in ("/до.json", "/після.json"))
finally: assert os.path.commonpath((os.path.realpath(т), os.path.realpath(т + "/б"))) == os.path.realpath(т); subprocess.run(["git", "worktree", "remove", "--force", т + "/б"])
print("ФАКТ · теплі нейтралі палітри (L*: назва, hex):", до["нт"], "→", піс["нт"], "; коди hex знахідки:", {х: (до["коди"].get(х), піс["коди"].get(х)) for х in ("#585346", "#645E52")})
АХ = {"чорний", "білий", "сірий", "графіт", "срібний"}
print("ФАКТ · точки крамниць з C* < 10 (усього, підпис хроматичний, у крамниці хроматичне, збіг) до → після:", [(len(м), sum(в[1] not in АХ for в in м),
      sum(в[0] not in АХ for в in м), sum(в[0] == в[1] for в in м)) for м in ([в for в in x["крамниці"].values() if в[2] < 10] for x in (до, піс))])
зм = [х for х in піс["коди"] if до["коди"].get(х) != піс["коди"][х]]
print("ФАКТ · hex з відповідей моделі: %d, код змінився в %d — %s" % (len(піс["коди"]), len(зм), dict(К.Counter((до["коди"][х], піс["коди"][х]) for х in зм))))
см = {і: в for і, в in піс["крамниці"].items() if 15 <= в[3] <= 50 and 6 <= в[2] <= 12 and (в[4] >= 330 or в[4] <= 30)}
print("ФАКТ · смуга h 330–30, L*15–50, C*6–12: точок %d, підпис до → після %s → %s; слово крамниці %s" % (len(см), dict(К.Counter(до["крамниці"][і][1] for і in см).most_common()), dict(К.Counter(піс["крамниці"][і][1] for і in см).most_common()), dict(К.Counter(в[0] for в in см.values()).most_common(6))))
кл = [к for к, (х, _) in піс["ґратка"].items() if 6 <= cs.lch(cs.hx(х))[1] <= 12]
print("ФАКТ · центри вікон лексикону, що змінили підпис: %s; клітинок ґратки з C* 6–12: %d, підпис змінився в %d" % ({ім: (до["центри"][ім], п) for ім, п in піс["центри"].items() if до["центри"][ім] != п}, len(кл), sum(до["ґратка"][к][1] != піс["ґратка"][к][1] for к in кл)))
print("ФАКТ · ґратка основ: %s" % ("ПОБАЙТОВО ТА САМА" if до["ґратка"] == піс["ґратка"] else "ЗМІНИЛАСЬ: %s" % sorted(set(до["ґратка"]) ^ set(піс["ґратка"]))))
кз = [і for і in піс["крамниці"] if до["крамниці"][і][1] != піс["крамниці"][і][1]]
print("ФАКТ · точок крамниць з виміром %d: підпис змінився в %d %s; збіг підпису зі словом крамниці %d → %d" % (len(піс["крамниці"]), len(кз),
      dict(К.Counter((до["крамниці"][і][1], піс["крамниці"][і][1]) for і in кз)), *(sum(в[0] == в[1] for в in x["крамниці"].values()) for x in (до, піс))))
кк = [і for і in піс["каталог"] if до["каталог"].get(і) != піс["каталог"][і]]
print("ФАКТ · каталог: речей %d → %d; запис змінився в %d, поля %s" % (len(до["каталог"]), len(піс["каталог"]), len(кк),
      dict(К.Counter(п for і in кк for п in set(до["каталог"].get(і, {})) | set(піс["каталог"][і]) if до["каталог"].get(і, {}).get(п) != піс["каталог"][і].get(п)))))
