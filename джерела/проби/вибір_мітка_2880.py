# -*- coding: utf-8 -*-
"""Рядок 2880 · чи мітка образу («o1…o5» — порядок відповіді ремонту) зсуває вибір окремо від позиції в промпті
вибору (після 2770 образи перемішано сідом запиту). Записані запити ВЕРДИКТ_V1 → ВИБІР_V1 живих 11–14 і пачки 2
(гілки `claude/zhyvi-13`, `-14` і поточна): скільки разів обрано кожну мітку і кожну позицію, і як часто мітка
обраного збігається з його позицією. Запуск: cd джерела && python3 проби/вибір_мітка_2880.py"""
import collections, hashlib, json, re, subprocess
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
бачено, мітка, поз, збіг = set(), collections.Counter(), collections.Counter(), collections.Counter()
for г in ("HEAD", "origin/claude/zhyvi-13", "origin/claude/zhyvi-14"):
    for ф in git("ls-tree", "-r", "--name-only", г, "--", "../аудит/").split("\n"):
        if not re.search(r"/VIDPOVIDI/.*ВЕРДИКТ_V1_ВИБІР_V1.*\.txt$", ф):
            continue
        пр, _, в = git("show", "%s:%s" % (г, ф)).partition("\n── ВІДПОВІДЬ")
        м = re.search(r'"chosen"\s*:\s*"\s*(o\d+)\s*"', в)
        if not м or hashlib.md5((пр + в).encode()).digest() in бачено:
            continue
        бачено.add(hashlib.md5((пр + в).encode()).digest())
        ід = [о["your_outfit"]["id"] for о in json.loads(пр.partition("\n")[2]).get("verdict") or []]
        if м.group(1) in ід and len(ід) == 5:
            мітка[м.group(1)] += 1; поз[ід.index(м.group(1)) + 1] += 1
            збіг[ід.index(м.group(1)) + 1 == int(м.group(1)[1:])] += 1
print("виборів із 5 образів: %d · за міткою o1…o5: %s · за позицією 1…5: %s · мітка = позиції: %d" % (
    sum(мітка.values()), [мітка["o%d" % і] for і in range(1, 6)], [поз[і] for і in range(1, 6)], збіг[True]))
