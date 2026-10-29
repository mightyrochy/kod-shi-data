"""Спільне читання JSONL: пошкоджений запис не знищує сусідні картки."""
import json
from pathlib import Path


def прочитати(шлях):
    """Повертає цілі записи та ознаку пошкодження, декодуючи кожен рядок окремо."""
    записи, пошкоджено = [], False
    файл = Path(шлях)
    if файл.is_file():
        with файл.open("rb") as потік:
            for рядок in потік:
                try:
                    запис = json.loads(рядок.decode("utf-8"))
                    if not isinstance(запис, dict) or not isinstance(запис.get("url"), str):
                        raise ValueError("запис без адреси")
                    записи.append(запис)
                except (UnicodeError, ValueError):
                    пошкоджено = True
    return записи, пошкоджено
