# -*- coding: utf-8 -*-
"""Рядок 2362: фактична повнота змішаних значень на штатному повному каталозі.
Запуск: cd джерела && python3 проби/fid2a_2362.py.
ДО на main 65dd727: 16169 оферів, 22 змішані (19 G/F, 3 G/H), усі невідомі.
"""
import collections
import os
import re
import sys

def main():
    """Друкує лічбу змішаних полів, результат consumer і одиничні контролі."""
    тут = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, тут)
    os.chdir(тут)
    import feed
    import фід_взуття as взуття  # Фасад не реекспортує повнота_з_параметрів.
    офери = feed.читати_yml(feed.каталог_на_диску())[0]
    змішані, контролі = [], collections.Counter()
    for офер in офери:
        for ім, зн in (офер.get("параметри") or {}).items():
            if not взуття._ІМ_ПОВНОТИ.match(str(ім).lstrip("~ ").strip()):
                continue
            пряме = взуття.повнота_з_параметрів(офер["параметри"])
            if len(set(re.findall(r"\b[A-Z]\b", str(зн)))) > 1:
                змішані.append((офер["id"], зн, пряме, взуття.взуттєві_поля(офер).get("повнота")))
            else:
                контролі[(зн, пряме)] += 1
    print("ФАКТ · оферів:", len(офери), "· змішаних:", len(змішані))
    print("ФАКТ · змішані значення:", dict(collections.Counter(x[1] for x in змішані)))
    print("ФАКТ · пряме / consumer:", dict(collections.Counter((x[2], x[3]) for x in змішані)))
    print("ФАКТ · одиничні контролі:", dict(контролі))
    print("ФАКТ · id змішаних:", [x[0] for x in змішані])
    return int(any(x[2] is not None or x[3] is not None for x in змішані))

if __name__ == "__main__":
    raise SystemExit(main())
