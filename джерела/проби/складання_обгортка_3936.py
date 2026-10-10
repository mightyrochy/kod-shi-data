# -*- coding: utf-8 -*-
"""Рядок 3936 · replay записаних відповідей складання, ремонту, вибору й опису: ЖИВІ-15 №11 рука 1 ({"answer": {образи},
"needed": […]}) і №12 рука 2 ({"answer_schema": {образи}}, образ закрито передчасно, бракує останньої «}»). ДО — протокол
бази @ 9ad76ee2, ПІСЛЯ — поточний; у дужках (образів | обрано | непорожніх полів опису, потрібно, обрізано).
Запуск: git archive origin/claude/zhyvi-15 аудит/живі_15 | tar -x -C /tmp/z15 && cd джерела &&
  python3 проби/складання_обгортка_3936.py /tmp/z15 ../аудит"""
import glob, gzip, json, subprocess, sys, types
sys.path.insert(0, "."); import протокол as ПІСЛЯ
ДО = types.ModuleType("протокол_до"); ДО.__file__ = "протокол.py"; exec(compile(subprocess.run(["git", "show", "9ad76ee2712d0ddf1a24d7afcbdaccc403356960:джерела/протокол.py"],
                            capture_output=True, text=True).stdout, "протокол_до", "exec"), ДО.__dict__)
СХ = dict(assembly="ОБРАЗИ_V1", repair="ОБРАЗИ_V1", completeness_repair="ОБРАЗИ_V1", choice="ВИБІР_V1", description="ОПИС_ВІДПОВІДЬ_V1")
def знак(П, в, сх):
    об, _, н = П.розбір_за_схемою(в, сх)
    об = об if isinstance(об, dict) else {}
    if сх == "ВИБІР_V1":
        return (int(bool(об.get("обрано"))), 0, 0)
    if сх == "ОПИС_ВІДПОВІДЬ_V1":
        return (sum(1 for v in об.values() if v not in (None, "", [], {})), 0, 0)
    return (len([о for о in об.get("образи") or [] if isinstance(о, dict)]), len(об.get("потрібно") or []), int(н["обрізано"]))
відп = {}   # (відповідь, схема) → звідки
for тека in sys.argv[1:]:
    for ф in glob.glob(тека + "/**/VIDPOVIDI/*_ОБРАЗИ_V1.txt", recursive=True):
        відп[(open(ф, encoding="utf-8").read().split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1].strip(), "ОБРАЗИ_V1")] = "/".join(ф.split("/")[-3:])[:60]
    for ф in glob.glob(тека + "/**/вердикти.txt*", recursive=True):
        try:
            д = json.load(gzip.open(ф, "rt") if ф.endswith(".gz") else open(ф))
        except ValueError:
            continue
        for пр in д.get("прогони") or []:
            for v in пр.get("вердикти") or []:
                for к in (v.get("етапи") or {}).get("виклики") or []:
                    if СХ.get(к.get("крок")) and "{" in (к.get("відповідь_сира") or ""):
                        відп[(к["відповідь_сира"].strip(), СХ[к["крок"]])] = "%s · рука %s · %s" % ("/".join(ф.split("/")[-3:-1])[:34], v.get("рука"), к["крок"])
зміни = [(з, сх, знак(ДО, в, сх), знак(ПІСЛЯ, в, сх)) for (в, сх), з in відп.items()]
for з, сх, а, б in зміни:
    if а != б:
        print("  %-60s %-12s ДО %s → ПІСЛЯ %s" % (з, сх[:12], а, б))
print("різних відповідей %d · змінилось %d · зменшень %d · без образів (вибору) ДО %d → ПІСЛЯ %d" % (
    len(зміни), sum(а != б for _, _, а, б in зміни), sum(б[0] < а[0] for _, _, а, б in зміни),
    sum(а[0] == 0 for _, _, а, _ in зміни), sum(б[0] == 0 for _, _, _, б in зміни)))
