"""Порівняти записані ходи на трьох модулях ДО та ПІСЛЯ зміни опису підвидів."""
import json
import subprocess
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[4]
КОД = КОРІНЬ / "джерела"
sys.path.insert(0, str(КОД))
sys.path.insert(0, str(КОД / "прилади"))
if sys.argv[1] == "до":
    ТЕКА = КОРІНЬ.parent / "tmp" / "підвиди-до"
    ТЕКА.mkdir(parents=True, exist_ok=True)
    for ім in ("мовний_шар.py", "паспорт_нагоди.py", "паспорт_поля.py"):
        дані = subprocess.check_output(["git", "show", "7a66c78e9:джерела/" + ім], cwd=КОРІНЬ)
        (ТЕКА / ім).write_bytes(дані)
else:
    ТЕКА = КОД
from replay_картки import виміряти
print(json.dumps(виміряти(КОД / "проби/дані/картка_запиту.json", ТЕКА), ensure_ascii=False))
