# -*- coding: utf-8 -*-
"""Гірший рівень рідший, але доступний; розмір відриву ключа не додає штрафу."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import семплер as С
from добір_вагою import рівні

ранги = рівні([(0, 0), (2, 0), (2, 1)])
речі = [{"id": str(і), С.ПОЛЕ_РАНГУ: (0, 0)} for і in range(100)]
речі.append({"id": "гірша", С.ПОЛЕ_РАНГУ: (1, 1)})
частоти = Counter(р["id"] for сід in range(1, 1001) for р in С.вибрати_зі_слота(речі, 20, сід))
гірша = частоти.pop("гірша")
мінімум = min(частоти.values())
print(f"рівні ключів: {ранги}; гірша: {гірша}, найрідша з кращих: {мінімум}")
sys.exit(int(ранги != [0, 1, 2] or not 0 < гірша < мінімум or sum(частоти.values()) + гірша != 20000))
