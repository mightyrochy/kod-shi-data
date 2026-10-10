# -*- coding: utf-8 -*-
"""Рядок 3681 · replay записаних відповідей OUTFITS_V1 (`аудит/живі_*/**/VIDPOVIDI`): скільки відповідей складання
(промпт із «pool») і ремонту дали образів більше, ніж «outfits_wanted», і скільки секунд тривали такі виклики проти
решти. Промпт з правилом кількості (рядок 3681, «end the answer there») — окремим рядком: ДО — живі 11–12, ПІСЛЯ —
наступний живий прогін. Запуск: cd джерела && python3 проби/складання_понад_3681.py [тека, типово ../аудит]"""
import glob, json, re, sys
sys.path.insert(0, "."); import протокол as П
тека = sys.argv[1] if len(sys.argv) > 1 else "../аудит"
з = {}
for ф in sorted(glob.glob(тека + "/живі_*/**/VIDPOVIDI/*.txt", recursive=True)):
    пр, _, в = open(ф, encoding="utf-8").read().partition("\n── ВІДПОВІДЬ")
    шап, _, в = в.partition("──\n")
    try:
        о = json.loads(пр.partition("──\n")[2].strip())
    except ValueError:
        continue
    if not isinstance(о, dict) or (о.get("task") or {}).get("answer") != "OUTFITS_V1" or not о.get("outfits_wanted"):
        continue
    с = re.search(r"симв\., ([\d.]+) с", шап)
    # написано образів — і за розбором, і за ключем «pole» (зламаний JSON розбір не читає, а час виводу той самий)
    хочу = int(о["outfits_wanted"])
    дала = max(len((П.розбір_за_схемою(в.strip(), "ОБРАЗИ_V1")[0] or {}).get("образи") or []), len(re.findall(r'"pole"\s*:', в)))
    правило = any("end the answer there" in р for р in (о["task"].get("rules") or []))
    кл = ("складання" if "pool" in о else "ремонт") + (" · з правилом" if правило else "")
    р = з.setdefault(кл, dict(відп=0, понад=[], с_понад=[], с_решта=[]))
    р["відп"] += 1
    if дала > хочу:
        р["понад"].append("%d із %d · %s" % (дала, хочу, ф.split("живі_", 1)[1].split("/VIDPOVIDI")[0]))
    (р["с_понад"] if дала > хочу else р["с_решта"]).append(float(с.group(1)) if с else 0.0)
мед = lambda x: sorted(x)[len(x) // 2] if x else 0
for кл, р in sorted(з.items()):
    print("%-26s відповідей %3d · понад outfits_wanted %d (%d%%) · медіана виклику: понад %.0f с, решта %.0f с"
          % (кл, р["відп"], len(р["понад"]), 100 * len(р["понад"]) // р["відп"], мед(р["с_понад"]), мед(р["с_решта"])))
    for п in р["понад"]:
        print("    ", п)
