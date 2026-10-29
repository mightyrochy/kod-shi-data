"""Чи пул похорону знімає речі кодом: `траурний_регістр.траурне_відсічення`.

Запуск: python -I -X utf8 пул.py <дерево> <знімок каталогу JSON> <id> [<id> …].
"""
import json
import os
from pathlib import Path
import sys

дерево = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(дерево / "джерела"))
os.chdir(дерево / "джерела")
import композитор_річ as КП
import траурний_регістр as ТР

за_id = {р["id"]: р for р in json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["каталог"]}
тр = ТР.траур_випадку(нагода="похорон", місце="похорон")
for і in sys.argv[3:]:
    р = за_id[і]
    print(і, "відсічення пулу:", ТР.траурне_відсічення(КП.у_річ(р, р["слот"], {}), тр))
