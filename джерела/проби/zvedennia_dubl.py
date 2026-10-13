# -*- coding: utf-8 -*-
"""Лічба вердиктів у `аудит/ЗВЕДЕННЯ.md` і перелік тих, хто лишився «нема в коді».

ЧОМУ ЧИТАЄ ПОРОДЖЕНИЙ ФАЙЛ, А НЕ МІРЯЄ САМ: вимір коштує 21 хв (батарея моста) і
робить його `зведення.py`. Проба питає РЕЗУЛЬТАТ: чи черга «нема в коді» справді
скоротилась до тих правил, які зараз роблять паралельні сесії, і скільки знято
посиланням на чинний механізм. Факт, а не переказ: ID друкуються поіменно.
Прогін:  python3 проби/zvedennia_dubl.py [ШЛЯХ_ДО_ЗВЕДЕННЯ.md]
"""
import sys, os, collections

ТУТ = os.path.dirname(os.path.abspath(__file__))
ШЛЯХ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ТУТ, "..", "аудит", "ЗВЕДЕННЯ.md")
У_РОБОТІ = {"R-COL-16", "K-PER-00", "K-IO-01", "K-SIZ-02", "R-FEED-07",
            "R-FP-07", "K-COND-04", "R-MUN-07", "R-PC-10"}

вердикти = {}
for р in open(ШЛЯХ, encoding="utf-8").read().split("\n"):
    к = [x.strip() for x in р.split("|")]
    if len(к) == 12 and к[1].startswith("`"):          # рядок повної таблиці
        вердикти[к[1].strip("`")] = к[10].strip("*")
c = collections.Counter(в.split(" → ")[0] for в in вердикти.values())
print("ЗВЕДЕННЯ: %d правил — %s" % (len(вердикти), os.path.abspath(ШЛЯХ)))
for в, n in c.most_common():
    print("   %-16s %4d" % (в, n))

нема = {і for і, в in вердикти.items() if в == "нема в коді"}
print("\n«нема в коді»: %d" % len(нема))
print("   у роботі (claude/pravylo-*): %d — %s"
      % (len(нема & У_РОБОТІ), ", ".join(sorted(нема & У_РОБОТІ)) or "—"))
print("   поза роботою:                %d — %s"
      % (len(нема - У_РОБОТІ), ", ".join(sorted(нема - У_РОБОТІ)) or "—"))
print("   не дійшли до черги (у роботі, та вже не «нема в коді»): %s"
      % (", ".join(sorted(У_РОБОТІ - нема)) or "—"))

дуб = sorted(і for і, в in вердикти.items() if в.startswith("дубль"))
print("\nдубль: %d" % len(дуб))
for і in дуб:
    print("   %-11s %s" % (і, вердикти[і]))
