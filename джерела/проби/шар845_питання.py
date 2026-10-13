# -*- coding: utf-8 -*-
"""ШАР-845: скільки питань «код не знає» картки не дійшло до шару і чи був повтор.
Запуск: python джерела/проби/шар845_питання.py <лог.txt.gz> (на збереженому прогоні стенда)."""
import gzip, re, sys
рядки = gzip.open(sys.argv[1], "rt", encoding="utf-8").read().splitlines()
виклики = [р for р in рядки if re.search(r"\.code_unknowns · layer · dir=out_messages", р)]
def поле(р, к):
    м = re.search(к + r"=(\d+)", р)
    return int(м.group(1)) if м else 0
усього = sum(поле(р, "messages") for р in виклики)
сказано = sum(поле(р, "said") for р in виклики)
повторів = sum(1 for р in рядки if re.search(r"code_unknowns\.retry · layer", р))
обєкт = sum(р.count("[object Object]") for р in рядки if "вхідними лишились" in р)
print("викликів шару на «код не знає»:", len(виклики), "· питань у них:", усього, "· мають текст:", сказано)
print("повторів (.code_unknowns.retry):", повторів, "· «[object Object]» у діагнозі стенда:", обєкт)
