# -*- coding: utf-8 -*-
"""3.1-Б: записані відповіді живих (рядки 8642, 8646, 8648) крізь читання схемою — без моделі й стенда.
8648 — відповіді ОБРАЗИ_V1 з образами, що розійшлися зі схемою (`usable_but_off_schema`), і помилки за видом;
8642 — відповіді ВИБІР_V1 в обгортці «answer» і скільки з них прочитано з «chosen»;
8646 — ярлики `слід_правил` файлів вердиктів: з кирилицею й фраз (не одне слово-код). ДО/ПІСЛЯ — база й правка.
Запуск: cd джерела && python3 проби/схема_58_replay.py origin/claude/zhyvi-58:аудит/живі_58"""
import collections, io, json, os, re, subprocess, sys, tarfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import протокол as П
гілка, тека = sys.argv[1].split(":", 1)
корінь = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
архів = tarfile.open(fileobj=io.BytesIO(subprocess.run(["git", "-C", корінь, "archive", гілка, тека],
                                                         capture_output=True, check=True).stdout))
поза, видів, обр, обг, обг_так, ярл, кир, фраз, поза_сліду = 0, collections.Counter(), 0, 0, 0, 0, 0, 0, 0
сліди = lambda о: ([о["слід_правил"]] if isinstance(о, dict) and isinstance(о.get("слід_правил"), list) else []) + \
    [с for в in (о.values() if isinstance(о, dict) else о if isinstance(о, list) else []) for с in сліди(в)]
for ч in архів:
    if not ч.isfile() or not (ч.name.endswith(".txt")):
        continue
    т = архів.extractfile(ч).read().decode("utf-8", "replace")
    if ч.name.endswith("вердикти.txt"):
        for сл in сліди(json.loads(т)):
            for з in сл:
                я = str(з.get("ярлик") or ""); ярл += 1; кир += bool(re.search(r"[а-яіїєґ]", я, re.I))
                фраз += not re.fullmatch(r"[\w\-]*", я)
        поза_сліду += sum(not re.fullmatch(r"[\w\-]*", json.loads(я)) for я in re.findall(r'"ярлик":("(?:[^"\\]|\\.)*")', т))
        continue
    відп = т.split("── ВІДПОВІДЬ", 1)[-1].split("\n", 1)[-1].rstrip("\n")
    if "ОБРАЗИ_V1" in ч.name:
        об = П.розбір_за_схемою(відп, "ОБРАЗИ_V1")[0]
        if isinstance(об, dict) and isinstance(об.get("образи"), list) and об["образи"]:
            обр += 1; пом = П.перевірити(П.СХЕМИ["ОБРАЗИ_V1"], об); поза += bool(пом)
            видів.update(re.sub(r"\[\d+\]", "[]", п["де"]) + "=" + п["що"].split("(«")[0] for п in пом)
    elif "ВИБІР_V1" in ч.name and re.match(r'\s*\{\s*("version"\s*:\s*"?1"?\s*,\s*)?"answer"\s*:\s*\{', відп):
        обг += 1; об = П.розбір_за_схемою(відп, "ВИБІР_V1")[0]
        обг_так += bool(isinstance(об, dict) and об.get("обрано"))
print("8648: ОБРАЗИ_V1 з образами %d · поза схемою %d · помилок %d" % (обр, поза, sum(видів.values())))
for в, н in видів.most_common():
    print("   %4d  %s" % (н, в))
print("8642: ВИБІР_V1 в обгортці «answer» %d · прочитано з «chosen» %d" % (обг, обг_так))
print("8646: ярликів сліду %d · з кирилицею %d · фраз (не одне слово-код) %d · фраз у «ярлик» поза слідом %d"
      % (ярл, кир, фраз, поза_сліду - фраз))
