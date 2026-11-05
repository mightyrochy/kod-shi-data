"""Читання рядкових TSV жнив: пошкодження не забирає сусідні підсумки."""
import csv
import os
from pathlib import Path
import sys
import tempfile


def прочитати(шлях, шапка, числа=(), з_рядка=0):
    """Повертає цілі записи після фізичного курсора й кількість усіх рядків даних.

    Пошкоджені рядки теж рухають курсор, але не підтверджують результат крамниці.
    Шапка задана писачем: її обрив не змінює схему наступних цілих рядків.
    """
    записи, всього = [], 0
    файл = Path(шлях)
    if not файл.is_file():
        return записи, всього
    with файл.open("rb") as потік:
        for номер, сирий in enumerate(потік):
            if номер:
                всього = номер
            try:
                поля = next(csv.reader([сирий.decode("utf-8")], delimiter="\t", strict=True))
                if not сирий.endswith(b"\n") or len(поля) != len(шапка):
                    raise ValueError("ROW_INCOMPLETE")
                if not номер:
                    if tuple(поля) != tuple(шапка):
                        raise ValueError("HEADER_INVALID")
                    continue
                запис = dict(zip(шапка, поля))
                if not запис["домен"]:
                    raise ValueError("DOMAIN_MISSING")
                for ключ in числа:
                    int(запис[ключ])
                if номер > з_рядка:
                    записи.append(запис)
            except (UnicodeError, ValueError, csv.Error) as помилка:
                print(f"JOURNAL_CORRUPT: {файл}:{номер + 1}: {type(помилка).__name__}", file=sys.stderr)
    return записи, всього


def дописати(шлях, рядок):
    """Відокремлює цілий новий запис від обірваного хвоста та синхронізує файл."""
    with open(шлях, "a+b") as потік:
        потік.seek(0, os.SEEK_END)
        префікс = b""
        if потік.tell():
            потік.seek(-1, os.SEEK_END)
            if потік.read(1) != b"\n":
                префікс = b"\n"
        потік.write(префікс + рядок.encode("utf-8") + b"\n")
        потік.flush()
        os.fsync(потік.fileno())


def створити(шлях, шапка):
    """Ініціалізує порожній журнал шапкою через спільний писач рядків."""
    файл = Path(шлях)
    if not файл.exists() or not файл.stat().st_size:
        дописати(файл, "\t".join(шапка))


def замінити(шлях, шапка, рядки):
    """Атомарно замінює знімок TSV після fsync на тому самому диску."""
    файл = Path(шлях)
    тимчасовий = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=файл.parent,
                                         prefix=файл.stem + "-", suffix=".tmp", delete=False) as потік:
            тимчасовий = Path(потік.name)
            писач = csv.DictWriter(потік, шапка, delimiter="\t")
            писач.writeheader()
            писач.writerows(рядки)
            потік.flush()
            os.fsync(потік.fileno())
        os.replace(тимчасовий, файл)
    finally:
        if тимчасовий is not None:
            тимчасовий.unlink(missing_ok=True)
