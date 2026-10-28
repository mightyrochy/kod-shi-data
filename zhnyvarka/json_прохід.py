"""Підтвердження кінця пагінації JSON-сімейств без SQLite-черги."""
import json
import hashlib
import os
from pathlib import Path
from журнал_карток import прочитати

МЕЖА_СТОРІНОК = 120


def прочитати_стан(журнал, домен):
    """Читає збережену позицію; старий чи пошкоджений стан починається з першої сторінки."""
    файл = Path(журнал) / "проходи" / домен / "json_стан.json"
    try:
        стан = json.loads(файл.read_bytes())
        if not isinstance(стан, dict) or type(стан.get("сторінка", 1)) is not int or стан.get("сторінка", 1) < 1:
            return {}
        return стан
    except (OSError, ValueError):
        return {}


def сторінка(журнал, домен, номер, запис=None, підпис=""):
    """Зберігає повну відповідь сторінки до карток; повтор читає її без мережі."""
    файл = Path(журнал) / "проходи" / домен / "json_сторінки" / f"{номер}.json"
    if запис is not None:
        запис["підпис"] = підпис
        записати(файл, запис)
        return запис
    try:
        дані = json.loads(файл.read_bytes())
        if (isinstance(дані, dict) and дані.get("підпис", "") == підпис and isinstance(дані.get("префікс"), str)
                and isinstance(дані.get("речі"), list) and all(isinstance(р, dict) for р in дані["речі"])):
            return дані
    except (OSError, ValueError):
        pass
    return None


def записати(файл, дані):
    """Атомарно замінює JSON після синхронізації та закриття тимчасового файлу."""
    файл.parent.mkdir(parents=True, exist_ok=True)
    тимчасовий = файл.with_suffix(".tmp")
    with тимчасовий.open("w", encoding="utf-8") as ф:
        json.dump(дані, ф, ensure_ascii=False)
        ф.flush()
        os.fsync(ф.fileno())
    os.replace(тимчасовий, файл)


def завершено(журнал, домен):
    """Читає явний кінець пагінації; відсутній або обірваний запис залишає прохід незавершеним."""
    стан = прочитати_стан(журнал, домен)
    if стан.get("завершено") is not True:
        return False
    файл = Path(журнал) / "сирі" / (домен + ".jsonl")
    if "журнал_sha256" in стан:
        дані = файл.read_bytes() if файл.is_file() else b""
        return hashlib.sha256(дані).hexdigest() == стан["журнал_sha256"]
    return not прочитати(файл)[1]


def позначити(журнал, домен, кінець, номер=None, префікс="", підпис=""):
    """Атомарно зберігає початок проходу або доведений кінець пагінації."""
    файл = Path(журнал) / "проходи" / домен / "json_стан.json"
    if not кінець and номер is None:
        # Явний новий прохід не використовує відповіді попереднього джерела.
        for кеш in (файл.parent / "json_сторінки").glob("*.json"):
            кеш.unlink()
    стан = {"завершено": кінець, "сторінка": номер or 1, "префікс": префікс, "підпис": підпис}
    if кінець:
        картки = Path(журнал) / "сирі" / (домен + ".jsonl")
        стан["журнал_sha256"] = hashlib.sha256(картки.read_bytes() if картки.is_file() else b"").hexdigest()
    записати(файл, стан)
