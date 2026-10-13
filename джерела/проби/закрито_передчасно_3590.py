# -*- coding: utf-8 -*-
"""Рядок 3590 · replay усіх записаних відповідей ОБРАЗИ_V1 / ВИБІР_V1 / ОПИС_ВІДПОВІДЬ_V1 (`відповідь_сира` кроків
складання, ремонту, ремонту повноти, вибору й опису у `аудит/**/вердикти.txt[.gz]`) розбором ДО (протокол бази
`claude/pachka-1009-22` @ 085023dd) і ПІСЛЯ (поточний): образів, речей і ходів з ід знахідки; вибір — обрано й
прийнято; опис — непорожні поля. Друкує відповіді, де розбір змінився, і скільки з них — зменшень.
Запуск: cd джерела && python3 проби/закрито_передчасно_3590.py"""
import glob, gzip, json, subprocess, sys, types
sys.path.insert(0, "."); import протокол as ПІСЛЯ
ДО = types.ModuleType("протокол_до"); ДО.__file__ = "протокол.py"
exec(compile(subprocess.run(["git", "show", "085023ddd882c67b5a6b3ed7b7f815674a8b177b:джерела/протокол.py"],
                            capture_output=True, text=True).stdout, "протокол_до", "exec"), ДО.__dict__)
СХ = {"assembly": "ОБРАЗИ_V1", "repair": "ОБРАЗИ_V1", "completeness_repair": "ОБРАЗИ_V1", "choice": "ВИБІР_V1",
      "description": "ОПИС_ВІДПОВІДЬ_V1"}
def знак(П, в, сх):
    об = П.розбір_за_схемою(в, сх)[0] or {}
    if сх == "ВИБІР_V1":
        return (bool(об.get("обрано")), len(об.get("прийнято") or []))
    if сх == "ОПИС_ВІДПОВІДЬ_V1":
        return (sum(1 for v in об.values() if v not in (None, "", [], {})),)
    о = [x for x in об.get("образи") or [] if isinstance(x, dict)]
    return (len(о), sum(len(x.get("речі") or []) for x in о),
            sum(1 for x in о for с in x.get("свідомо") or [] if isinstance(с, dict) and с.get("знахідка")))
усього, зміни = 0, []
for ф in sorted(glob.glob("../аудит/**/вердикти.txt*", recursive=True)):
    try:
        д = json.load(gzip.open(ф, "rt") if ф.endswith(".gz") else open(ф))
    except Exception:
        continue
    for пр in д.get("прогони") or []:
        for v in пр.get("вердикти") or []:
            for к in (v.get("етапи") or {}).get("виклики") or []:
                в, сх = к.get("відповідь_сира"), СХ.get(к.get("крок"))
                if not (в and сх and "{" in в):
                    continue
                усього, а, б = усього + 1, знак(ДО, в, сх), знак(ПІСЛЯ, в, сх)
                if а != б:
                    зміни.append((ф[9:70], v.get("рука"), к.get("крок"), а, б))
print("відповідей %d · розбір змінився у %d · зменшень %d" % (усього, len(зміни), sum(б < а for *_, а, б in зміни)))
for з in зміни:
    print("  %s · рука %s · %s: ДО %s → ПІСЛЯ %s" % з)
