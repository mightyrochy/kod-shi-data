# -*- coding: utf-8 -*-
"""Порівнює обох читачів зон на всьому каталозі з однаковими записами покриття."""
import collections
import subprocess
import sys
import types
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import feed
import фід_каталог as Ф
import місце_речі as М
import outfit as О


def main():
    """Друкує лічбу відкритих зон ДО / ПІСЛЯ для кожного стану й читача."""
    до = types.ModuleType("outfit_до")
    джерело = subprocess.check_output(["git", "show", "3cb6a98b49b:джерела/outfit.py"], cwd=КОРІНЬ)
    exec(compile(джерело, "outfit_до.py", "exec"), до.__dict__)
    каталог = Ф.прочитати_каталог(feed.каталог_на_диску(), ліміт_фото=0)["каталог"]
    print("речей каталогу:", len(каталог), flush=True)
    шар = dict(id="шар", слот="верхній_шар")
    for назва, покриття, видно in (("без шару", None, None), ("під невідомим шаром", шар, None),
                                   ("не видно під шаром", шар, "ні")):
        лічба = collections.Counter()
        for річ in каталог:
            р = dict(річ)
            if видно:
                р["місце_стилістки"] = dict(видно=видно)
            р["місце_речі"] = М.записати(р, покриття)
            for ім in ("зони_речі", "зони_вето_з_кодів"):
                старі, нові = getattr(до, ім)(р)[0], getattr(О, ім)(р)[0]
                лічба[ім + " ДО"] += bool(старі)
                лічба[ім + " ПІСЛЯ"] += bool(нові)
                лічба[ім + " відмінностей"] += старі != нові
        print(назва, dict(лічба), flush=True)


if __name__ == "__main__":
    main()
