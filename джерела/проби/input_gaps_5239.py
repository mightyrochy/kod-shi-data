"""5239 Н3а: лічба записаних пар ремонту без виклику моделі."""
import gzip
import json
import pathlib
import sys


def лічба(тека):
    """Друкує історичний розмір промптів вибраних пар; це не замір чинного коду."""
    пари = []
    for файл in sorted(pathlib.Path(тека).glob("сирі/*.json.gz")):
        запис = json.load(gzip.open(файл, "rt", encoding="utf-8"))["з_гг1"]
        if not запис.get("збій") and запис.get("виклики"):
            промпт = json.loads(запис["промпт"])
            пари.append(len(json.dumps(промпт, ensure_ascii=False, separators=(",", ":"))))
    print(json.dumps(dict(історичних_пар=len(пари), історичних_символів=sum(пари)), ensure_ascii=False))


if __name__ == "__main__":
    лічба(sys.argv[1])
