"""Лічба на кеші HTML: скільки сторінок кожної крамниці має елемент вибору кольору (без мережі).

Елемент вибору — будь-який вузол, окрім клітинок таблиць і службових тегів, у якого слово кольору стоїть у `class`,
`id`, `name` або в ключі `data-*` (`swatch`, `color`, `colour`, `tsvet`, `kolir`, `колір`). Лічба не залежить від писача:
вона каже, чи є на сторінці що читати, а не чи прочитав це писач. Вихід — TSV: крамниця, сторінок, з елементом, частка,
три найчастіші елементи.
"""
import argparse
import collections
import gzip
import json
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

СЛОВО = re.compile(r"(?:^|[-_\s\[\]])(?:swatch(?:es)?|colou?rs?|tsvet\w*|cvet\w*|kolir\w*|колір\w*|pa_colou?r)(?:$|[-_\s\[\]])", re.I)
НЕ_ВУЗОЛ = frozenset(("meta", "link", "script", "style", "html", "body", "head", "svg", "path", "th", "td", "tr", "table"))
ТЕКА = Path(__file__).resolve().parent


def елементи(html):
    """Перелік (тег, атрибут, значення) вузлів вибору кольору на сторінці."""
    знайдено = set()
    for вузол in BeautifulSoup(html, "lxml").find_all(True):
        if вузол.name in НЕ_ВУЗОЛ:
            continue
        for атр, знач in вузол.attrs.items():
            знач = " ".join(знач) if isinstance(знач, list) else str(знач)
            if атр in ("class", "id", "name") and len(знач) < 100 and СЛОВО.search(знач):
                знайдено.add((вузол.name, атр, знач))
            elif атр.startswith("data-") and СЛОВО.search(атр):
                знайдено.add((вузол.name, атр, ""))
    return sorted(знайдено)


def одна(аргументи):
    ід, сховище = аргументи
    with gzip.open(Path(сховище) / "відповіді" / (ід + ".json.gz"), "rt", encoding="utf-8") as потік:
        тіло = json.load(потік)["відповідь"].get("тіло") or ""
    return ід, елементи(тіло)


def main():
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument("--результати", type=Path, required=True, help="результати.jsonl.gz виміру каналу")
    п.add_argument("--сховище", type=Path, required=True)
    п.add_argument("--вихід", type=Path, default=ТЕКА / "вибір_кольору.tsv")
    п.add_argument("--процесів", type=int, default=8)
    а = п.parse_args()
    with gzip.open(а.результати, "rt", encoding="utf-8") as потік:
        записи = [json.loads(р) for р in потік]
    придатні = [р for р in записи if р["стан"] != "без_відповіді"]
    домен = {р["ід"]: urlsplit(р["адреса"]).netloc for р in придатні}
    with ProcessPoolExecutor(а.процесів) as пул:
        вихід = list(пул.map(одна, [(р["ід"], str(а.сховище)) for р in придатні], chunksize=20))
    сторінок, з_елементом = collections.Counter(), collections.Counter()
    частоти = collections.defaultdict(collections.Counter)
    for ід, знайдено in вихід:
        д = домен[ід]
        сторінок[д] += 1
        if знайдено:
            з_елементом[д] += 1
        for е in знайдено:
            частоти[д][" ".join(е).strip()] += 1
    рядки = ["крамниця\tсторінок\tз_елементом_вибору\tчастка\tнайчастіші"]
    for д in sorted(сторінок):
        топ = "; ".join("%s ×%d" % (е, н) for е, н in частоти[д].most_common(3))
        рядки.append("\t".join((д, str(сторінок[д]), str(з_елементом[д]), "%.3f" % (з_елементом[д] / сторінок[д]), топ)))
    а.вихід.write_bytes(("\n".join(рядки) + "\n").encode("utf-8"))
    print("\n".join(рядки[:1] + [р.split("\t", 4)[0] + " " + " ".join(р.split("\t")[1:4]) for р in рядки[1:]]))


if __name__ == "__main__":
    main()
