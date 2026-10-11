# -*- coding: utf-8 -*-
"""Рядок 4710: рамка «на око» — одним текстом (`річ_з_фото.РАМКА_НА_ОКО`) в обох промптах речей.
ДО — записи ЖИВІ-24 (`origin/claude/zhyvi-24`, VIDPOVIDI `*речі_з_фото*` сцен «ж3_свято_др_взуття_фото»):
скільки рамок мають сторону, що дорівнює ширині чи висоті фото (пікселі, а не тисячні).
`python3 проби/рамка_на_око_4710.py` (з теки `джерела`)."""
import json, re, subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import річ_з_фото as РФ, оцінка_образу as О

фото = [{"ід": "ф1", "ширина": 500, "висота": 700}]
for назва, промпт in (("розмова (річ_з_фото.промпт_фото)", РФ.промпт_фото(фото)),
                      ("оцінка (оцінка_образу.промпт_речей)", О.промпт_речей(фото))):
    правило = next(п for п in json.loads(промпт)["task"]["rules"] if п.startswith('"frame"'))
    print("%s: інструкція %s\n  %s" % (назва, "є" if РФ.РАМКА_НА_ОКО in правило else "НЕМА", правило))

ГІЛКА, СЦЕНА = "origin/claude/zhyvi-24", "ж3_свято_др_взуття_фото/VIDPOVIDI/"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=off", *а], capture_output=True, text=True, encoding="utf-8")
файли = [ф for ф in git("ls-tree", "-r", "--full-tree", "--name-only", ГІЛКА).stdout.split()
         if ф.startswith("аудит/живі_24/") and СЦЕНА in ф and "речі_з_фото" in ф]
if not файли:
    sys.exit("ДО: БЕЗ ВХОДУ — нема %s (git fetch origin claude/zhyvi-24)" % ГІЛКА)
усього = пікс = 0
for ф in файли:
    текст = git("show", "%s:%s" % (ГІЛКА, ф)).stdout
    промпт, відповідь = текст.split("── ВІДПОВІДЬ", 1)
    сторони = {int(ч) for ш, в in re.findall(r'"width": *(\d+), *"height": *(\d+)', промпт) for ч in (ш, в)}
    обʼєкт = json.loads(відповідь[відповідь.index("{"):])
    речі = (обʼєкт.get("answer") or обʼєкт).get("items") or []
    for р in речі:
        рамка = р.get("frame") or {}
        у_пікселях = any(рамка.get(к) in сторони for к in ("left", "top", "right", "bottom"))
        усього += 1; пікс += у_пікселях
        print("%s  сторони фото %s  frame %s%s" % (ф.split("/")[3][:2] + "/" + ф.split("/")[-1], sorted(сторони),
              [рамка.get(к) for к in ("left", "top", "right", "bottom")], "  ← у пікселях" if у_пікселях else ""))
print("ДО (ЖИВІ-24): рамок зі стороною = ширині чи висоті фото — %d з %d" % (пікс, усього))
