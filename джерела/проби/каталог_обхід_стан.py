# -*- coding: utf-8 -*-
"""Мірило 5.3 ПІСЛЯ: з обхід_стан.tsv журналу обходу друкує адреси (всього/готово/лишилось) і крамниці без каталогу.
Запуск: python3 джерела/проби/каталог_обхід_стан.py <корінь журналу обходу>"""
import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from обхід import прочитати_стан
ряди = list(прочитати_стан(sys.argv[1]).values())
с = lambda к: sum(int(р[к]) for р in ряди)                                      # noqa: E731
print("крамниць %d · адрес %d · готово %d · лишилось %d (%.0f %%)" % (len(ряди), с("адрес"), с("готово"), с("лишилось"),
      100 * с("лишилось") / max(с("адрес"), 1)))
print("стани:", dict(collections.Counter(р["стан_код"] for р in ряди)))
for р in ряди:
    if р["стан_код"] == "WAIT":
        print("  чекає %-24s %-14s %s" % (р["домен"], р["причина_код"], р["підстава"][:80]))
