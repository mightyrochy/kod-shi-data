# -*- coding: utf-8 -*-
"""Перерахунок записів «рівень» `джерела/похибка_вимірів_тіла.py` з даних обміру й таблиця проти `areas.РІВНІ`.

Прогін (з кореня репозиторію; файли — з openlab.psu.edu/ansur2 і openlab.psu.edu/ansur):
    python3 -I аудит/перевірка/похибка_вимірів_тіла/вимір.py ANSUR_II_FEMALE_Public.csv ansurWomen.csv
Друкує sha256 файлів, для кожного рівня — шаблон, середнє ± SD відношення «висота орієнтира / зріст» і чи
стоїть шаблон у межах розкиду; виходить з кодом 1, якщо перераховане розходиться із записом.
"""
import csv, hashlib, os, statistics, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "джерела"))
import areas, похибка_вимірів_тіла as П  # noqa: E402

ОРІЄНТИРИ = {  # рівень → (файл 2|1, стовпець висоти, стовпець зросту)
    "плечі": (2, "acromialheight", "stature"), "груди": (2, "chestheight", "stature"),
    "талія": (1, "WAIST_HT_NATURAL", "STATURE"), "стегна": (2, "buttockheight", "stature"),
    "пах": (2, "crotchheight", "stature"), "коліно": (2, "kneeheightmidpatella", "stature"),
    "литка": (1, "CALF_HT", "STATURE"),
}
НИЖНІ_МЕЖІ = {"щиколотка": (2, "lateralmalleolusheight", "stature")}  # рівень → поле `нижня_межа` запису
ІНШІ = [(2, "талія (пупок)", "waistheightomphalion", "stature"),
        (2, "коліно (epicondyle)", "lateralfemoralepicondyleheight", "stature")]


def відношення(рядки, висота, зріст):
    """Середнє й SD відношення висоти до зросту по всіх рядках файлу."""
    x = [float(р[висота]) / float(р[зріст]) for р in рядки]
    return len(x), statistics.mean(x), statistics.stdev(x)


def main(шлях2, шлях1):
    файли = {}
    for к, ш in ((2, шлях2), (1, шлях1)):
        print("ANSUR %s: %s sha256 %s" % ("II" if к == 2 else "I", ш, hashlib.sha256(open(ш, "rb").read()).hexdigest()))
        файли[к] = list(csv.DictReader(open(ш, encoding="utf-8")))
    шаблон, збої = dict(areas.РІВНІ), 0
    print("\n| рівень | areas.РІВНІ | середнє ± SD (n) | |шаблон − середнє| / SD | запис |")
    for рів, (к, в, з) in ОРІЄНТИРИ.items():
        n, м, s = відношення(файли[к], в, з)
        зап = П.запис("рівень", рів)
        згода = round(м, 4) == зап["середнє"] and round(s, 4) == зап["val"]
        збої += not згода
        print("| %s | %.3f | %.4f ± %.4f (%d) | %.2f%s | %s |" % (рів, шаблон[рів], м, s, n, abs(шаблон[рів] - м) / s,
              " — ПОНАД РОЗКИД" if abs(шаблон[рів] - м) > s else "", "збігається" if згода else "РОЗХОДИТЬСЯ"))
    for рів, (к, в, з) in НИЖНІ_МЕЖІ.items():
        n, м, s = відношення(файли[к], в, з)
        межа = П.запис("рівень", рів)["нижня_межа"]
        згода = round(м, 4) == межа["середнє"] and round(s, 4) == межа["val"]
        збої += not згода
        print("| %s: нижня межа, %s | %.3f | %.4f ± %.4f (%d) | — | %s |" % (рів, в, шаблон[рів], м, s, n,
              "збігається" if згода else "РОЗХОДИТЬСЯ"))
    print("\nінші орієнтири (не записи):")
    for к, назва, в, з in ІНШІ:
        n, м, s = відношення(файли[к], в, з)
        print("  %s, %s: %.4f ± %.4f (n %d)" % (назва, в, м, s, n))
    print("\nзаписів, що розходяться з перерахунком: %d" % збої)
    return 1 if збої else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
