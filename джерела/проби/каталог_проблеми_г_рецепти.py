# -*- coding: utf-8 -*-
"""Рядок 5624 (реєстр 5616, клас Г11): скільки різних збирачів і чи доведені рецепти. Факт: стани й транспорт рецептів
(`zhnyvarka/рецепти.tsv`), рядки коду трьох збирачів (жниварка, виконавець, розвідка) і жнив ноутбука (`джерела/жнива_*`),
і тихі `except` у збирачах. Запуск: python3 джерела/проби/каталог_проблеми_г_рецепти.py"""
import collections, glob, os, re                                               # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
Ж = os.path.join(К, "zhnyvarka")
р = [л.rstrip("\n").split("\t") for л in open(os.path.join(Ж, "рецепти.tsv"), encoding="utf-8")]
ш = р[0]; р = [х for х in р[1:] if len(х) > ш.index("стан")]                    # noqa: E702
print("рецептів %d · стан %s · транспорт %s · сімейство %s" % (len(р), dict(collections.Counter(х[ш.index("стан")] for х in р)),
      dict(collections.Counter(х[ш.index("транспорт")] for х in р)), dict(collections.Counter(х[ш.index("сімейство")] for х in р))))
def лічба(ф):
    т = open(ф, encoding="utf-8").read()
    return т.count("\n"), len(re.findall(r"except\s*(Exception)?\s*:\s*\n?\s*(pass|continue|return None)\b", т))
for ф in ("жниварка.py", "виконавець.py", "розвідка.py", "влиття_в_каталог.py") + tuple(
        os.path.basename(x) for x in sorted(glob.glob(os.path.join(Ж, "перезняти_*.py")))):
    print("  zhnyvarka/%-28s рядків %5d · тихих except %d" % ((ф,) + лічба(os.path.join(Ж, ф))))
жн = sorted(glob.glob(os.path.join(К, "джерела", "жнива_*.py")))
print("  джерела/жнива_*.py: файлів %d, рядків %d, тихих except %d" % (len(жн), sum(лічба(ф)[0] for ф in жн),
      sum(лічба(ф)[1] for ф in жн)))
т = open(os.path.join(Ж, "жниварка.py"), encoding="utf-8").read()
print("жниварка тримає власну копію словників слотів на випадок збою `import feed`: %s" % ("так" if re.search(r"except\s+ImportError", т) else "не знайдено"))
