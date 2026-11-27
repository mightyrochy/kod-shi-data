#!/usr/bin/env python3
"""Повторює чотири запити й 200 відкриттів на одному знімку каталогу.

Запуск з кореня: python3 аудит/звіти/крамниці-рівна-черга/до_після.py
Потрібні Python, Git (база гілки) та Node.js.
"""

import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from вимір import ROOT, СИТУАЦІЇ, СІДИ, ТЕКА, вхід, git, знімок, крамниця, розподіл

БАЗА = "71b31e5ed2930651f3aaffd0447c8608bb9d519f"
ДЖЕРЕЛА = ROOT / "джерела"
sys.path.insert(0, str(ДЖЕРЕЛА))

from добір_вагою import рівні
import семплер


def старий_семплер(копія):
    """Вантажить справжній семплер зі свіжого main на старті наряду."""
    шлях = копія / "семплер_до.py"
    шлях.write_bytes(git("show", f"{БАЗА}:джерела/семплер.py"))
    опис = importlib.util.spec_from_file_location("семплер_до", шлях)
    код = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(код)
    return код


def добори(код, речі, бюджет):
    """Рахує покази та пули з одним типом серед слотів, де були різні типи."""
    квоти = код.квоти({слот: len(rs) for слот, rs in речі.items()}, бюджет)
    різні = {слот for слот, ряд in речі.items() if len({r.get("тип") for r in ряд}) > 1}
    показано, один_тип = Counter(), Counter()
    найбільша_частка = 0
    for сід in СІДИ:
        пул = код.вибрати(речі, бюджет, сід=сід)
        assert {слот: len(rs) for слот, rs in пул.items()} == квоти
        іди = [r["id"] for ряд in пул.values() for r in ряд]
        assert len(set(іди)) == len(іди)
        показано.update(іди)
        найбільша_частка = max(найбільша_частка, max(Counter(map(крамниця, іди)).values()) / len(іди))
        for слот in різні:
            один_тип[слот] += len({r.get("тип") for r in пул[слот]}) == 1
    групи = defaultdict(list)
    for слот, ряд in речі.items():
        for річ, рівень in zip(ряд, рівні([r.get("_ранг_пізній", ()) for r in ряд])):
            групи[слот, рівень].append(показано[річ["id"]])
    усі = [x for xs in групи.values() for x in xs]
    return {
        "квоти": квоти, "розподіл": розподіл(усі), "нуль": усі.count(0),
        "частка_однієї_крамниці_макс": round(найбільша_частка, 4),
        "пули_з_одним_типом_у_різних_слотах": dict(sorted(один_тип.items())),
        "рівні": {f"{слот} / {л}": розподіл(xs) for (слот, л), xs in sorted(групи.items())},
    }


def полиця(збірка, копія):
    """Міряє живий JavaScript пошуку на рядках однієї збірки."""
    шлях = "джерела/показ/дзеркало/catalog-index.js"
    до = копія / "полиця_до.js"
    до.write_bytes(git("show", f"{БАЗА}:{шлях}"))
    команда = ["node", str(ТЕКА / "полиця.mjs"), str(до), str(ROOT / шлях)]
    return json.loads(subprocess.check_output(команда, input=json.dumps(збірка, ensure_ascii=False).encode()))


def головна():
    """Записує підсумки порівняння в JSON поруч зі звітом."""
    with TemporaryDirectory(prefix="рівний-шанс-") as тека:
        копія = Path(тека)
        каталог, збірка, _ = знімок(копія, git("show", f"{БАЗА}:index.html"))
        до = старий_семплер(копія)
        дані = {"база": БАЗА, "сідів": len(СІДИ), "полиця": полиця(збірка, копія), "пул": {}}
        for ім, фільтри, смуга, бюджет in СИТУАЦІЇ:
            речі = вхід(каталог, фільтри, смуга)
            дані["пул"][ім] = {"до": добори(до, речі, бюджет), "після": добори(семплер, речі, бюджет)}
            print(ім, file=sys.stderr, flush=True)
    (ТЕКА / "до-після.json").write_text(json.dumps(дані, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    головна()
