"""Повтор кв3 на тому самому кеші: писач → канонічний запис → читач кожного кадру."""
import importlib.util
import collections
import csv
import gzip
import json
from pathlib import Path
import sys

ПРОБИ = Path(__file__).resolve().parent.parent
спец = importlib.util.spec_from_file_location("кв2_повтор", ПРОБИ / "кадр_варіант_кв2_один_колір_1611/повтор.py")
кв2 = importlib.util.module_from_spec(спец)
спец.loader.exec_module(кв2)
вимір = кв2.вимір
старі_причини = вимір.причини


def причини(факти, ж):
    """Лічить ті самі перешкоди, виключаючи кольори окремих сестринських сторінок."""
    вихід = [п for п in старі_причини(факти, ж) if п not in
             ("кілька_кольорів_JSON_LD", "кілька_свотчів", "кілька_значень_вибору", "нема_свідчення_одного_кольору")]
    переліки = ж.переліки_кольору(факти)
    кольорові = [ім for ім, п in zip(("кілька_кольорів_JSON_LD", "кілька_свотчів", "кілька_значень_вибору",
                                    "кілька_значень_вибору"), переліки) if len(п) > 1]
    if not ж.свідчення_одного_кольору(факти, факти["url"]):
        вихід.append("нема_свідчення_одного_кольору")
    return list(dict.fromkeys(кольорові + вихід))


вимір.причини = причини


def підсумок(записи, результати, вихід):
    """Зберігає всі результати та лічбу за фактичним джерелом доказу, включно з офертами."""
    лічби = collections.defaultdict(collections.Counter)
    for р in результати.values():
        д = вимір.urlsplit(р["адреса"]).netloc
        ключ = ("доведено:" + р["джерело"] if р["стан"] == "доведено" else
                "невідомо:" + р["причина"] if р["стан"] == "невідомо" else р["стан"])
        лічби[д][ключ] += 1
        лічби[д]["записів"] += 1
    разом = sum(лічби.values(), collections.Counter())
    assert разом["записів"] == len(результати) == len(записи) == 13882
    поля = ["крамниця", "записів"] + sorted(set(разом) - {"записів"})
    вихід.mkdir(parents=True, exist_ok=True)
    with (вихід / "лічба.tsv").open("w", encoding="utf-8", newline="") as потік:
        писач = csv.DictWriter(потік, поля, delimiter="\t", lineterminator="\n")
        писач.writeheader()
        for д, л in [*sorted(лічби.items()), ("РАЗОМ", разом)]:
            писач.writerow(dict(крамниця=д, **{п: л[п] for п in поля[1:]}))
    with gzip.open(вихід / "результати.jsonl.gz", "wt", encoding="utf-8") as потік:
        for р in sorted(результати.values(), key=lambda р: р["ід"]):
            потік.write(json.dumps(р, ensure_ascii=False) + "\n")
    print(json.dumps(разом, ensure_ascii=False), flush=True)


вимір.підсумок = підсумок

if __name__ == "__main__":
    кв2.база.main()
