"""М.7: звіряє відповіді моделі на ситуації з еталоном; друкує збіг і кожне розходження.

    python3 аудит/правила_ролей/м7/звірити.py <відповіді.json> [<відповіді.json> …]

Файл відповідей — `{"id": "КОД", …}` або `{"модель": …, "відповіді": {"id": "КОД", …}}`.
"""
import json
import sys
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
ЕТАЛОН = json.loads((ТЕКА / "очікувані.json").read_text(encoding="utf-8"))
КОДИ = set(json.loads((ТЕКА / "дії.json").read_text(encoding="utf-8")))

код_виходу = 0
for шлях in sys.argv[1:]:
    дані = json.loads(Path(шлях).read_text(encoding="utf-8"))
    відповіді = дані.get("відповіді", дані)
    розходження = [(і, е, відповіді.get(і)) for і, е in ЕТАЛОН.items() if відповіді.get(і) != е]
    чужі = sorted(к for к in відповіді.values() if к not in КОДИ)
    print(f"{шлях}: {len(ЕТАЛОН) - len(розходження)}/{len(ЕТАЛОН)} збіглось"
          + (f"; коди поза переліком: {', '.join(чужі)}" if чужі else ""))
    for і, е, ф in розходження:
        print(f"  {і}: очікувано {е}, відповідь {ф}")
    код_виходу |= bool(розходження or чужі)
sys.exit(код_виходу)
