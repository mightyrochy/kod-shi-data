# -*- coding: utf-8 -*-
"""розбір_порядок_наявні.py — доказ наряду 5.4-Н PR-1: `--усі` бере речі в наявності першими.

Без моделі й без мережі. Кличе справжній `прогін(..., усі=True)` ДО (версія з аргументу `--до`, файл
`каталог_розбір_прогін.py` зі старого коміту) і ПІСЛЯ (поточна), на каталозі з git, і перехоплює чергу
`чекають` на вході в `Годинник` — тобто рівно те, що пішло б у модель. Друкує:
  множини пар (ім'я файла, промпт) ДО/ПІСЛЯ — тотожні?  індекси в іменах — ті самі?
  частку `available is True` серед перших N речей черги ДО/ПІСЛЯ.
Запуск: python3 джерела/проби/розбір_порядок_наявні.py <файл_до.py> [N=1350]"""
import importlib.util
import json
import os
import sys
import tempfile

ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ТУТ, ".."))


class _Перехоплено(Exception):
    pass


def черга(шлях):
    спец = importlib.util.spec_from_file_location("розбір_%d" % abs(hash(шлях)), шлях)
    м = importlib.util.module_from_spec(спец)
    спец.loader.exec_module(м)

    class _Г:
        def __init__(self, *а, **к):
            л = sys._getframe(1).f_locals
            raise _Перехоплено(list(л["чекають"]), len(л["пари"]))
    м.Годинник = _Г
    with tempfile.TemporaryDirectory() as т:
        try:
            м.прогін("проба", куди=т, усі=True)
        except _Перехоплено as е:
            return е.args
    raise SystemExit("черга не перехоплена")


def головна(до, n=1350):
    ч0, всього = черга(до)
    ч1, _ = черга(os.path.join(ТУТ, "..", "каталог_розбір_прогін.py"))
    пари = lambda ч: {(р[3], р[4]) for р in ч}
    доля = lambda ч: sum(1 for р in ч[:n] if р[2].get("available") is True)
    print("речей у `--усі`: %d · у черзі ДО %d, ПІСЛЯ %d" % (всього, len(ч0), len(ч1)))
    print("множини пар (ім'я, промпт) тотожні: %s" % (пари(ч0) == пари(ч1)))
    print("індекси в іменах ті самі (ім'я→індекс): %s" % ({р[3]: р[0] for р in ч0} == {р[3]: р[0] for р in ч1}))
    print("порядок змінився: %s" % ([р[3] for р in ч0] != [р[3] for р in ч1]))
    print("available is True у черзі: %d з %d" % (sum(1 for р in ч1 if р[2].get("available") is True), len(ч1)))
    print("серед перших %d: ДО %d (%.1f%%) · ПІСЛЯ %d (%.1f%%)"
          % (n, доля(ч0), 100 * доля(ч0) / n, доля(ч1), 100 * доля(ч1) / n))


if __name__ == "__main__":
    головна(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1350)
