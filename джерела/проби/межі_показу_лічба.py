# -*- coding: utf-8 -*-
"""Е2-межі-показу, мірило: скільки місць у `показ/*.js` розбирають ВІДПОВІДЬ МОДЕЛІ поза реєстром форм
(`схема_відповіді.py`), ДО (база) і ПІСЛЯ (робоче дерево). Місце — ознака власного читача: ремонт/розбір
кольорів, фільтр міток прози, JSON.parse над прозою картки, запобіжник обіцянки (регекс над сирим текстом).
Решта `JSON.parse(` у `показ/` — копія обʼєкта, ключ localStorage, потік моста, відповідь моста, промпт або
стовпець журналу для звіту власника (`звіти.js:розібратиПоле`) — друкуються поштучно, щоб звірити.
Запуск з `джерела`: python3 проби/межі_показу_лічба.py [база=origin/main]"""
import glob, os, re, subprocess, sys
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
корінь = os.path.join(К, "..")
база = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
ОЗНАКИ = [("кольори: власний читач (розібратиКолір/_jsonКольоруП/_hexКольоруП)", r"(function|const)\s+(розібратиКолір|_jsonКольоруП|_hexКольоруП)\b"),
          ("прози картки: JSON.parse(безОгорож) у людською()", r"JSON\.parse\(безОгорож\)"),
          ("прози картки: фільтр міток ОБРАЗ/ПІДПИС/ФОТО НЕ ТЕ", r"\(ОБРАЗ\|ПІДПИС\|ФОТО НЕ ТЕ\)"),
          ("прози картки: рядки «СВІДОМО:» з тексту", r"СВІДОМО\|Свідомо\|свідомо\|НАВМИСНО"),
          ("помічниці: запобіжник обіцянки (const ОБІЦЯНКА_П)", r"const\s+ОБІЦЯНКА_П\b")]
def дерево(реф):
    if реф is None:
        return {os.path.basename(ф): open(ф, encoding="utf-8").read() for ф in glob.glob(os.path.join(К, "показ", "*.js"))}
    ф = subprocess.run(["git", "ls-tree", "-r", "--name-only", "-z", реф, "джерела/показ/"], capture_output=True, text=True, cwd=корінь, check=True).stdout.split("\0")
    return {os.path.basename(п): subprocess.run(["git", "show", реф + ":" + п], capture_output=True, text=True, cwd=корінь, check=True).stdout
            for п in ф if п.endswith(".js")}
рез = {}
for мітка, реф in (("ДО  (" + база + ")", база), ("ПІСЛЯ (дерево)", None)):
    д = дерево(реф); рез[мітка] = [sum(len(re.findall(р, т)) for т in д.values()) for _, р in ОЗНАКИ]
    інші = [(ф, i + 1, л.strip()[:70]) for ф, т in sorted(д.items()) for i, л in enumerate(т.split("\n"))
            if "JSON.parse(" in л and "JSON.parse(JSON.stringify(" not in л and "безОгорож" not in л]
    print("%s: ознак власного читача відповіді моделі — %d; решта JSON.parse (не відповідь моделі) — %d" % (мітка, sum(рез[мітка]), len(інші)))
    for ф, i, л in інші: print("    %s:%d  %s" % (ф, i, л))
for (н, _), а, б in zip(ОЗНАКИ, *рез.values()): print("  %-62s ДО %d → ПІСЛЯ %d" % (н, а, б))
