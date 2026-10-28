"""Мірило металу на всіх записах каталогу, без фото й моделей.

Запуск: python каталог_металу.py <дерево> <знімок-каталогу.json>.
"""
import collections
import json
from pathlib import Path
import sys


def головна():
    """Порівняти спільний API палітри та суд для відомих кольорів прикрас."""
    дерево, знімок = map(Path, sys.argv[1:3])
    sys.path.insert(0, str(дерево / "джерела"))
    import колір_річ as К
    import palettes as П
    from суд_від_моделі import _метал_точки
    записи = json.loads(знімок.read_text(encoding="utf-8"))["каталог"]
    типи = collections.Counter(К.тип_кольору(р) for р in записи)
    розбіжності, металів = [], collections.Counter()
    for р in записи:
        if not р.get("метал") or К.межі_кольору(р) is None:
            continue
        if not П.слот_металу(р.get("слот"), р.get("тип")):
            continue
        суд = bool(_метал_точки((р, р["слот"], None, None, None)))
        палітра = П.колір_металу(р)
        металів[К.тип_кольору(р)] += 1
        if суд != палітра:
            розбіжності.append(dict(id=р["id"], тип=К.тип_кольору(р), метал=р["метал"],
                                     палітра=палітра, суд=суд))
    print(json.dumps(dict(записів=len(записи), типи=типи, прикрас_з_металом=металів,
                          невимір_з_lab=sum(bool(р.get("lab")) for р in записи if К.тип_кольору(р) != "вимір"),
                          розбіжностей=len(розбіжності), приклади=розбіжності[:10]), ensure_ascii=False, indent=2))
    return int(bool(розбіжності))


if __name__ == "__main__":
    raise SystemExit(головна())
