"""Спільне читання JSONL: пошкоджений запис не знищує сусідні картки."""
import json
import gzip
from pathlib import Path
import sys


def прочитати(шлях, ключ="url"):
    """Повертає цілі записи та ознаку пошкодження, декодуючи кожен рядок окремо."""
    записи, пошкоджено = [], False
    файл = Path(шлях)
    if файл.is_file():
        відкрити = gzip.open if файл.suffix == ".gz" else open
        with відкрити(файл, "rb") as потік:
            for номер, рядок in enumerate(потік, 1):
                try:
                    запис = json.loads(рядок.decode("utf-8"))
                    if not isinstance(запис, dict) or (ключ is not None and not isinstance(запис.get(ключ), str)):
                        raise ValueError("запис без адреси")
                    записи.append(запис)
                except (UnicodeError, ValueError):
                    пошкоджено = True
                    print(f"JOURNAL_CORRUPT: {файл}:{номер}", file=sys.stderr)
    return записи, пошкоджено
