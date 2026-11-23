"""Підтверджує, які задуми складання несе видимий стилістці пул."""
from collections import defaultdict
import json
from pathlib import Path

from .знання import старий_запис
from .поняття import НЕВІДОМО, НЕ_ПЕВНИЙ

with Path(__file__).with_name("дані").joinpath("задуми.json").open(encoding="utf-8") as _файл:
    _ЗАДУМИ = json.load(_файл)


def доступні(речі, скільки):
    """Повертає названі й вільні задуми та ідентифікатори недоступних."""
    from колір_річ import межі_кольору
    from реєстр_константи import C

    слоти = defaultdict(list)
    виразна = False
    for річ in речі:
        межі = межі_кольору(старий_запис(річ))
        принт = річ.поля["візерунок"].значення
        виразна |= (isinstance(принт, str) and принт not in (НЕВІДОМО, НЕ_ПЕВНИЙ, "", "solid", "однотон")
                    or межі is not None and межі[2] > 0)
        слоти[річ.слот].append(межі)
    # Верх і низ можуть бути в одному складі; різні базові слоти не завжди сумісні.
    колона = any(max(abs(а[0] - б[1]), abs(а[1] - б[0])) < C["step_min"]
                 for а in слоти.get("верх", ()) if а is not None
                 for б in слоти.get("низ", ()) if б is not None)
    входи = {
        "filter_and_rank": bool(слоти),
        "anchor_first": виразна,
        "tonal_column": колона,
        "ease_the_knot": any(len(ряд) >= 2 for ряд in слоти.values()),
        # Пул Н2 ще не засвідчує гілку поза вікном палітри для окремої речі.
        "break": False,
    }
    вибрані = [{"id": код, "idea": _ЗАДУМИ[код]["idea"]} for код, є in входи.items() if є][:скільки]
    if len(вибрані) < скільки:
        вибрані.append({"id": "free", "idea": _ЗАДУМИ["free"]["idea"], "outfits": скільки - len(вибрані)})
    return вибрані, [код for код, є in входи.items() if not є]
