"""Друкує координати тону й чинні сім'ї всього каталогу для звірки перенесення.

Запуск із джерела/: python проби/колір_тон_каталог.py <знімок.json> [базовий.json].
"""
import collections, gzip, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import colorspace as КП
import колір_річ as КР
import фід_каталог as ФК


def головна(вихід):
    """Записує результати через чинні продуктові фасади без зміни словника сімей."""
    if len(sys.argv) > 2:
        читати = gzip.open if sys.argv[2].endswith(".gz") else open
        with читати(sys.argv[2], "rt", encoding="utf-8") as файл:
            каталог = [{"id": р[0], "точка": р[1]} for р in json.load(файл)]
    else:
        шлях = ФК.каталог_на_диску("каталог_повний.xml")
        каталог = ФК.прочитати_каталог(шлях, 0)["каталог"]
    рядки = []
    for річ in каталог:
        lab = річ["точка"] if "точка" in річ else КР.точка_кольору(річ)
        if lab is None:
            рядки.append([річ["id"], None])
            continue
        h = КП.lch(lab)[2]
        рядки.append([річ["id"], list(lab), КР.сім_я(lab), КП.у_коло_художника(h),
                      КП.доповнення(h), КП.зсув_на_колі(h, 120), КП.дуга_кола(h, 15),
                      КП.тепло(h), {к: КП.центри_відношення(h, к) for к in КП.RELATIONS}])
    Path(вихід).write_text(json.dumps(рядки, ensure_ascii=False), encoding="utf-8")
    print("речей:", len(рядки), "з виміром:", sum(р[1] is not None for р in рядки))
    print("сім'ї:", dict(collections.Counter(р[2] if len(р) > 2 else "невідомо" for р in рядки)))


if __name__ == "__main__":
    головна(sys.argv[1])
