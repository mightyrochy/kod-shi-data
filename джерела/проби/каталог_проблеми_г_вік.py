# -*- coding: utf-8 -*-
"""Рядок 5620 (реєстр 5616, клас Г1): скільки днів тому знято кожну річ каталогу і чи є в жнив розклад.
Факт: вік `знято` по крамницях і тригери трьох workflow жнив. Мережі не треба.
Запуск: python3 джерела/проби/каталог_проблеми_г_вік.py [РРРР-ММ-ДД — «сьогодні», типово дата машини]"""
import collections, datetime, gzip, os, re, sys                                # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
сьогодні = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
офери = re.findall(r"<offer\b.*?</offer>", xml, re.S)
def поле(о, ім):
    м = re.search(r'<param name="%s">([^<]*)<' % ім, о)
    return м.group(1) if м else None
дати = collections.Counter(поле(о, "знято") for о in офери)
print("речей %d · знято:" % len(офери))
for д, ч in sorted(дати.items()):
    print("  %s — %5d речей (%4.1f %%), %d днів тому" % (д, ч, 100 * ч / len(офери), (сьогодні - datetime.date.fromisoformat(д)).days))
кр = collections.defaultdict(set)
for о in офери:
    кр[поле(о, "знято")].add(поле(о, "магазин"))
print("крамниць за датою: %s" % {д: len(м) for д, м in sorted(кр.items())})
for wf in ("zhnyva.yml", "zhnyvarka.yml", "rozvidka.yml"):
    т = open(os.path.join(К, ".github", "workflows", wf), encoding="utf-8").read()
    print("%-14s розклад (schedule): %s · лише ручний запуск: %s" % (wf, "так" if re.search(r"^\s*schedule:", т, re.M) else "НІ",
          "так" if "workflow_dispatch" in т else "ні"))
