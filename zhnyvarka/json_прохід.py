"""Підтвердження кінця пагінації JSON-сімейств без SQLite-черги."""
import json
import os
from pathlib import Path


def завершено(журнал, домен):
    """Читає явний кінець пагінації; відсутній або обірваний запис залишає прохід незавершеним."""
    файл = Path(журнал) / "проходи" / домен / "json_стан.json"
    try:
        with файл.open(encoding="utf-8") as ф:
            стан = json.load(ф)
        return isinstance(стан, dict) and стан.get("завершено") is True
    except (OSError, ValueError):
        return False


def позначити(журнал, домен, кінець):
    """Атомарно зберігає початок проходу або доведений кінець пагінації."""
    файл = Path(журнал) / "проходи" / домен / "json_стан.json"
    файл.parent.mkdir(parents=True, exist_ok=True)
    тимчасовий = файл.with_suffix(".tmp")
    with тимчасовий.open("w", encoding="utf-8") as ф:
        json.dump({"завершено": кінець}, ф, ensure_ascii=False)
        ф.flush()
        os.fsync(ф.fileno())
    os.replace(тимчасовий, файл)
