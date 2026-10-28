"""Колір hex, ґратка й каталог ДО/ПІСЛЯ на одному корпусі: із джерела/ python проби/колір_hex_вікна.py [база] [корпус]."""
import collections as К, json, os, re, subprocess, sys, tempfile, warnings
warnings.filterwarnings("ignore"); sys.path.insert(0, ".")
if sys.argv[1:2] == ["--знімок"]:
    import feed, мовний_шар as МШ, міст_основи as МО, palettes as PS, фід_каталог as FK, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as cs
    корпус = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.abspath("..")
    шл = subprocess.run(["git", "ls-files", "-z", "--", "аудит"], cwd=корпус, capture_output=True).stdout.decode().split("\0")
    hx = sorted({"#" + х.upper() for ф in шл if "VIDPOVIDI" in ф for х in re.findall(r"#([0-9a-fA-F]{6})\b", open(os.path.join(корпус, ф), encoding="utf-8", errors="ignore").read())} | {"#D3D3D3", "#E6DCCD", "#FFD700"})
    зб, кр = feed.читати_збагачення(), {}
    for o in FR.читати_yml("каталог_повний.xml")[0]:
        z, п = зб.get(o["id"]) or {}, " ".join(str(o.get("колір_сирий") or "").lower().split())
        if п and len(FK._СЕП_КОЛЬОРУ.split(п)) == 1 and V.слово_крамниці(п) and (z.get("колір_основний") or {}).get("hex") \
                and (z.get("версія") or 1) >= 2 and FZ.колір_збагачення(z)[2].startswith("hex"):
            кр[o["id"]] = (V.слово_крамниці(п)["ім"], PS.назва(cs.hx(z["колір_основний"]["hex"]))[0])
    кат = {r["id"]: r for r in FK.прочитати_каталог("каталог_повний.xml", 0)["каталог"]}
    json.dump(dict(коди={х: МШ._код_кольору(х[1:]) for х in hx}, ґратка=МО.ґратка_основ()[0], крамниці=кр, каталог=кат),
              open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, default=str)
    sys.exit()
база, т = (sys.argv[1:] or ["origin/main"])[0], tempfile.mkdtemp(); корпус = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.abspath("..")
subprocess.run(["git", "worktree", "add", "-q", "--detach", т + "/б", база], check=True)
try:
    import shutil
    shutil.copyfile(os.path.abspath("каталог_повний.xml"), т + "/б/джерела/каталог_повний.xml")
    for д, ф in ((т + "/б/джерела", т + "/до.json"), (".", т + "/після.json")):
        subprocess.run([sys.executable, os.path.abspath(__file__), "--знімок", ф, корпус], cwd=д, check=True)
    до, піс = (json.load(open(т + ф, encoding="utf-8")) for ф in ("/до.json", "/після.json"))
finally:
    assert os.path.commonpath((os.path.realpath(т), os.path.realpath(т + "/б"))) == os.path.realpath(т)
    subprocess.run(["git", "worktree", "remove", "--force", т + "/б"])
print("ФАКТ · коди hex знахідки до → після:", {х: (до["коди"].get(х), піс["коди"].get(х)) for х in ("#D3D3D3", "#E6DCCD", "#FFD700")})
зм = [х for х in піс["коди"] if до["коди"].get(х) != піс["коди"][х]]
print("ФАКТ · hex з відповідей моделі: %d, код змінився в %d — %s" % (len(піс["коди"]), len(зм), dict(К.Counter((до["коди"][х], піс["коди"][х]) for х in зм))))
print("ФАКТ · ґратка основ: %s" % ("ПОБАЙТОВО ТА САМА" if до["ґратка"] == піс["ґратка"] else "ЗМІНИЛАСЬ: %s" % sorted(set(до["ґратка"]) ^ set(піс["ґратка"]))))
кз = [і for і in піс["крамниці"] if до["крамниці"][і][1] != піс["крамниці"][і][1]]
print("ФАКТ · точок крамниць з виміром %d: підпис змінився в %d %s; збіг підпису зі словом крамниці %d → %d" % (len(піс["крамниці"]), len(кз),
      dict(К.Counter((до["крамниці"][і][1], піс["крамниці"][і][1]) for і in кз)), *(sum(с == п for с, п in x["крамниці"].values()) for x in (до, піс))))
кк = [і for і in піс["каталог"] if до["каталог"].get(і) != піс["каталог"][і]]
print("ФАКТ · каталог: речей %d → %d; запис змінився в %d, поля %s" % (len(до["каталог"]), len(піс["каталог"]), len(кк),
      dict(К.Counter(п for і in кк for п in set(до["каталог"].get(і, {})) | set(піс["каталог"][і]) if до["каталог"].get(і, {}).get(п) != піс["каталог"][і].get(п)))))
json.dump({і: [до["каталог"].get(і), піс["каталог"][і]] for і in кк}, open(т + "/каталог_зміни.json", "w", encoding="utf-8"), ensure_ascii=False); print("ФАКТ · змінені записи — %s/каталог_зміни.json; додано %d, втрачено %d" % (т, len(піс["каталог"].keys() - до["каталог"].keys()), len(до["каталог"].keys() - піс["каталог"].keys())))
