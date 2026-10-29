"""Рядки 6615, 6618: replay записів ЖИВІ-1016-2 (`claude/zhyvi-1016-2`) тим самим кодом, без моделі. Ремонти поради
(усі сцени): записана відповідь → `прийняти_пораду` — скільки знято `too_many_sentences` (ДО, відповідь записана);
промпт ремонту збирається наново — чи стоїть у ньому «may skip it» і заборона другого речення (ПІСЛЯ — у правилі).
Репліки ж2_новорічна_мороз (Ж:01–03): записаний вхід → `промпт_репліки` — чисел у вході перекладача (шкала рівня).
Запуск: cd джерела && python3 проби/мова_порада_репліка_6615.py"""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
Г, Т = "origin/claude/zhyvi-1016-2", "../аудит/живі_1016_2"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", Г.split("/", 1)[1])
вади, ремонтів, двома, новий = {v: k for k, v in М.ВАДИ_ПОРАДИ_EN.items()}, 0, 0, ""
файли = [ф for ф in git("ls-tree", "-r", "--name-only", Г, Т).split("\n") if "VIDPOVIDI" in ф]
for ф in sorted(ф for ф in файли if "_ремонт_поради" in ф):
    промпт, відповідь = git("show", "%s:%s" % (Г, ф)).split("── ПРОМПТ", 1)[1].split("──", 1)[1].split("── ВІДПОВІДЬ", 1)
    вх = json.loads(промпт.strip())
    рем = dict(вада=вади.get(вх.get("defect")), дозволені=list(вх.get("advice_topics") or {}),
               запрошення=вх.get("your_invitation") or "")
    новий = М.промпт_поради(рем, вх.get("her_new_message") or "")
    р = М.прийняти_пораду(відповідь.split("──", 1)[1], рем)
    д = [в["чому"] for в in р["відкинуто"]]
    ремонтів, двома = ремонтів + 1, двома + ("too_many_sentences" in д)
    print("  %s %s | знято: %s | показано: %s" % (ф.split("/")[-3][:24], ф.split("/")[-1][:8], д, р["теми_поради"]))
print("ремонтів %d · знято too_many_sentences %d (ДО, записані відповіді)" % (ремонтів, двома))
print("промпт ремонту: «may skip it» %d · «no second sentence» %d" % (
    len(re.findall(r"saying she may skip", новий)), новий.count("no second sentence")))
for ф in sorted(ф for ф in файли if "ж2_новорічна_мороз" in ф and ф.endswith("_мовний_шар_репліка.txt")):
    вх = json.loads(git("show", "%s:%s" % (Г, ф)).split("РЕПЛІКА:\n", 1)[1].split("\n", 1)[0])
    дані = М.промпт_репліки(вх).split("РЕПЛІКА:\n", 1)[1]
    print("  репліка %s · formality запису %s → у вході перекладача: %r · чисел: %d" % (
        ф.split("/")[-3][:2], (вх.get("recorded") or {}).get("formality"),
        json.loads(дані).get("recorded", {}).get("formality"), len(re.findall(r"\d", дані))))
