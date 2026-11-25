"""Локально везе відмову JS через штатний протокол Python."""
import json
import sys
from unittest.mock import patch

from ядро import запит, протокол
from ядро.тести import обвязка
from ядро.тести.тест_н2 import _запис

відповідь = json.load(sys.stdin)
каталог = [_запис("dress", "сукня"), _запис("boots", "взуття")]
with patch.object(запит, "запит", wraps=запит.запит) as будівник:
    почато = обвязка.почати(протокол, обвязка.вхід_с5(каталог=каталог))
    фінал, журнал = обвязка.довезти(протокол, почато, lambda _: відповідь)
assert фінал["кінець"]
збій = фінал.get("збій") or next(к["збій"] for к in фінал["картки"] if к["рука"] == 1)
видачі = len(журнал["запити"])
assert будівник.call_count == видачі, (будівник.call_count, видачі, [х.get("кінець") for х in журнал["відповіді"]], збій)
print(json.dumps({"issued": видачі, "retries": видачі - 1, "terminal": збій,
                  "successful_cards": sum(not к["збій"] for к in фінал["картки"]),
                  "report": [р["збій"] for р in фінал["звіт"] if р.get("крок") == "складання" and р.get("збій")]},
                 ensure_ascii=False))
