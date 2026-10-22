# -*- coding: utf-8 -*-
"""3.1-В (рядки 8662, 8663): скелет ОБРАЗИ_V1 — листки-переліки «a|b» і «one of:»; записані відповіді живих — полюс
поза переліком (склеєний «a|b» чи вигаданий); ремонт понад стелю — за вибором, названа типова (`за_порядком`) чи
мовчки перші N; «chosen» рядками — ще й над стелею на 1 нижче. ДО/ПІСЛЯ — база й правка.
Запуск: cd джерела && python3 проби/скелет_58_replay.py origin/claude/zhyvi-58:аудит/живі_58"""
import collections, io, json, os, re, subprocess, sys, tarfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import протокол as П, збирач_промптів as З, пакет_моделі as ПМ, вердикт_моделі as ВМ, схема_відповіді as СВ
листки = lambda с: ([л for v in (с.values() if isinstance(с, dict) else с) for л in листки(v)]
                    if isinstance(с, (dict, list)) else [с])
for о in (ПМ.СКЛАДАННЯ, ВМ.РЕМОНТ):
    с = З.скелет(о); лл = [л for л in листки(с) if isinstance(л, str)]
    print("скелет %s: «a|b» %d · «one of:» %d · %d байт" % (
        о.задача, sum(bool(re.match(r"[\w\-]+\|", л)) for л in лл), sum("one of: " in л for л in лл),
        len(json.dumps(с, ensure_ascii=False).encode())))
гілка, тека = sys.argv[1].split(":", 1)
корінь = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
архів = tarfile.open(fileobj=io.BytesIO(subprocess.run(["git", "-C", корінь, "archive", гілка, тека],
                                                         capture_output=True).stdout))
полюс, надлишок, рядками = collections.Counter(), collections.Counter(), []
for ч in архів:
    if not ч.isfile() or "ОБРАЗИ_V1" not in ч.name or not ч.name.endswith(".txt"): continue
    т = архів.extractfile(ч).read().decode("utf-8", "replace"); з = "ремонт" if "ВЕРДИКТ_V1" in ч.name else "складання"
    об = П.розбір_за_схемою(т.split("── ВІДПОВІДЬ", 1)[-1].split("\n", 1)[-1], "ОБРАЗИ_V1")[0]
    if not isinstance(об, dict) or not isinstance(об.get("образи"), list): continue
    образи, м = [о for о in об["образи"] if isinstance(о, dict)], re.search(r'"outfits_wanted":\s*(\d+)', т)
    полюс.update((з, "склеєний" if "|" in str(о["полюс"]) else "вигаданий") for о in образи
                 if "полюс" in о and о["полюс"] not in П.ПОЛЮСИ)
    розбір = [dict(ід=о.get("речі") or ["?"], ід_відповіді=str(о.get("ід")), підпис=о.get("підпис")) for о in образи]
    р = any(not isinstance(х, dict) for х in об.get("обрано") or [])
    рядками += [(ч.name.split("/")[-3], len(образи), м and м.group(1))] * р
    for стеля, вид in [(м and int(м.group(1)), "дані")] + [(len(образи) - 1, "рядками, на 1 нижче")] * р:
        if з == "ремонт" and стеля and len(образи) > стеля:
            с = СВ.понад_просили(розбір, об.get("обрано"), стеля)[1] if hasattr(СВ, "понад_просили") else None
            надлишок[(вид, "сліду типової нема (база)" if с is None else "за вибором" if с.get("за_обраним") == стеля
                      else "названо типову" if с.get("за_порядком") else "мовчки перші N")] += 1
for з in ("складання", "ремонт"):
    print("полюс поза переліком, %s: склеєний %d · вигаданий %d" % (з, полюс[(з, "склеєний")], полюс[(з, "вигаданий")]))
print("«chosen» рядками: %s" % (рядками or "—"))
print("ремонт понад стелю: %s" % (" · ".join("%s, %s %d" % (*к, н) for к, н in sorted(надлишок.items())) or "—"))
