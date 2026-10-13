# -*- coding: utf-8 -*-
"""Рядок 3462 · відповіді без схеми (`протокол.розбір_останній`: оцінка образу, допит, речі з фото, перелік речей
рук 3–4, стилістка, вибір палітри) розбором ДО (протокол бази 085023dd) і ПІСЛЯ: ЖИВІ-11 Н4 `seed3_40` — оцінка
з ключем без лапок `{text: "…"}` в «unknown» — крізь `оцінка_образу.прийняти_оцінку` (картка чи причина відмови),
і replay усіх записаних відповідей `VIDPOVIDI/*` (гілки `claude/zhyvi-13`, `-14` і поточна) з полями кожного
викликача: скільки розборів змінилось і чи є серед змін хоч один, що ДО читався. Запуск: cd джерела && python3
проби/ключ_без_лапок_3462.py"""
import hashlib, json, re, subprocess, sys, types
sys.path.insert(0, "."); import протокол as ПІСЛЯ, оцінка_образу as О
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ДО = types.ModuleType("протокол_до"); ДО.__file__ = "протокол.py"
exec(compile(git("show", "085023ddd882c67b5a6b3ed7b7f815674a8b177b:джерела/протокол.py"), "протокол_до", "exec"), ДО.__dict__)
в = open("../аудит/живі_11/Н4/VIDPOVIDI/seed3_40_ОЦІНКА_відповідь.txt").read().partition("\n── ВІДПОВІДЬ")[2]
в = в.partition("\n")[2].strip()
for назва, П in (("ДО", ДО), ("ПІСЛЯ", ПІСЛЯ)):
    О._ПР = П
    р = О.прийняти_оцінку(в, {})
    к = р.get("картка") or {}
    print("seed3_40 %-5s → %s · не_знаю: %s · нотатки: %s" % (назва, "картка, вердикт %s" % к.get("вердикт") if к
                                                             else "без картки: %s" % р.get("причина"),
                                                             к.get("не_знаю"), р.get("нотатки")))
О._ПР = ПІСЛЯ
ПОЛЯ = (("items",), ("answer",), ("scheme",), ("answer", "verdict"))
бачено, усього, зміни = set(), 0, []
for г in ("HEAD", "origin/claude/zhyvi-13", "origin/claude/zhyvi-14"):
    for ф in git("ls-tree", "-r", "--name-only", г, "--", "../аудит/").split("\n"):
        т = git("show", "%s:%s" % (г, ф)).partition("\n── ВІДПОВІДЬ")[2] if re.search(r"/VIDPOVIDI/.*\.txt$", ф) else ""
        т = т.partition("\n")[2].strip()
        if "{" not in т or hashlib.md5(т.encode()).digest() in бачено:
            continue
        бачено.add(hashlib.md5(т.encode()).digest()); усього += 1
        for п in ПОЛЯ:
            а, б = ДО.розбір_останній(т, п)[0], ПІСЛЯ.розбір_останній(т, п)[0]
            if json.dumps(а, ensure_ascii=False, sort_keys=True) != json.dumps(б, ensure_ascii=False, sort_keys=True):
                зміни.append((ф.split("аудит/")[1][:60], п, а is not None))
print("replay: відповідей %d × %d наборів полів · розбір змінився у %d, з них ДО читався — %d" % (
    усього, len(ПОЛЯ), len(зміни), sum(з[2] for з in зміни)))
for з in зміни:
    print("  %s · поля %s · ДО %s" % (з[0], "+".join(з[1]), "читався" if з[2] else "не читався"))
