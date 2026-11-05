# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, а:157.2): зайве в показі.

Лічить у `показ/*.js` і `показ.html` означення функцій (`function ім(`, `const ім = (…) =>`) і для кожного — скільки
разів ім'я трапляється в показі та в `build_*.py` (збірка вставляє JS); ім'я, що трапляється лише в своєму означенні,
— функція без жодного вжитку. Окремо — імена верхнього рівня (означення з першої колонки), означені кілька разів:
у скриптах без модулів пізніше означення мовчки підміняє раннє. Разовий вимір, не прилад кореня.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g2_мертві_js.py "$PWD/джерела"
"""
import collections
import glob
import os
import re
import sys

ІМ = r"[\wЀ-ӿʼ$]+"


def main(корінь):
    os.chdir(корінь)
    файли = [ф for ф in sorted(glob.glob("показ/*.js")) + ["показ.html"] if os.path.exists(ф)]
    текст = {ф: open(ф, encoding="utf-8").read() for ф in файли}
    збірка = "\n".join(open(ф, encoding="utf-8").read() for ф in glob.glob("build_*.py"))
    озн, верх = [], collections.defaultdict(list)
    for ф in файли:
        for н, р in enumerate(текст[ф].split("\n"), 1):
            for м in re.finditer(r"(?:async\s+)?function\s+(" + ІМ + r")\s*\(", р):
                озн.append((м.group(1), ф, н))
            м = re.match(r"\s*(?:const|let|var)\s+(" + ІМ + r")\s*=\s*(?:async\s*)?(?:\([^)]*\)|" + ІМ + r")\s*=>", р)
            if м:
                озн.append((м.group(1), ф, н))
            м = (re.match(r"(?:async\s+)?function\s+(" + ІМ + r")\s*\(", р)
                 or re.match(r"(?:const|let|var)\s+(" + ІМ + r")\s*=", р))
            if м:
                верх[м.group(1)].append("%s:%d" % (ф, н))
    усе = "\n".join(текст.values()) + "\n" + збірка
    мертві = [(ім, ф, н) for ім, ф, н in озн
              if len(re.findall(r"(?<![\wЀ-ӿʼ$])" + re.escape(ім) + r"(?![\wЀ-ӿʼ$])", усе)) <= 1]
    print("означень функцій: %d; без жодного вжитку: %d" % (len(озн), len(мертві)))
    for ім, ф, н in мертві:
        print("  %s:%d %s" % (ф, н, ім))
    двічі = {ім: м for ім, м in верх.items() if len(м) > 1}
    print("імен верхнього рівня: %d; означених кілька разів: %d" % (len(верх), len(двічі)))
    for ім, м in sorted(двічі.items()):
        print("  %s %s" % (ім, " ".join(м)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "джерела"))
