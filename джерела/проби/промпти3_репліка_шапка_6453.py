"""Рядки 6453, 6454, 6456: replay записів ЖИВІ-1016-1 і ЖИВІ-1016-2 тим самим кодом, без моделі. Репліка — прийнято,
ідів фото й типових 11:00 у бульбашці, смуга ошатності у вході перекладачки (число замість плитки); шапка першого
ходу — шапок, що пройшли `_шапка` з полем, якого хід не записав кодом (лічба на виході, п.12).
Кращим: прийнято — усі, ідів і 11:00 — 0, смуг — 0, шапок зі сміттям — 0. Запуск: cd джерела && python3 проби/<цей файл>"""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for г, т in (("claude/zhyvi-1016-1", "аудит/живі_1016_1"), ("claude/zhyvi-1016-2", "аудит/живі_1016_2")):
    git("fetch", "-q", "origin", г)
    реп = прийн = ід = смуг = шапок = сміття = 0
    for ф in git("ls-tree", "--full-tree", "-r", "--name-only", "origin/" + г, т).split("\n"):
        if not re.search(r"_мовний_шар_(репліка|хід_розмови)\.txt$", ф) or ("_01_" not in ф and "репліка" not in ф):
            continue
        с = git("show", "origin/%s:%s" % (г, ф))
        відп = с.split("── ВІДПОВІДЬ", 1)[1].split("──\n", 1)[1].strip()
        if "репліка" in ф:
            вхід = json.loads(с.split("\nРЕПЛІКА:\n", 1)[1].split("\n", 1)[0])
            р = М.прийняти_репліку(відп, вхід)
            реп += 1; прийн += bool(р["текст"]); ід += len(re.findall(r"ф\d|\b11:00\b", р["текст"]))
            смуг += isinstance(json.loads(М.промпт_репліки(вхід).split("РЕПЛІКА:\n", 1)[1]).get(
                "recorded", {}).get("formality"), dict)
            continue
        об, _ = М._обʼєкт(відп)
        if not (isinstance(об, dict) and об.get("header")):
            continue
        р = М.прийняти_розмову(відп)
        шапок += 1
        к = {"година": "hour", "темп_c": "temperature_c", "опади": "precipitation", "бажання": "wants",
             "вето": "vetoes", "настрій": "mood"}
        сміття += any(к[п] not in р["внутрішня"] for п in р["частини"].get("header") or {})
    print("%s: реплік %d, прийнято %d, ідів і 11:00 у бульбашці %d, смуг у вході %d | шапок %d, зі сміттям %d"
          % (т, реп, прийн, ід, смуг, шапок, сміття))
