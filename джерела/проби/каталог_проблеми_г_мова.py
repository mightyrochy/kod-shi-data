# -*- coding: utf-8 -*-
"""Рядок 5626 (реєстр 5616, клас Г7): мова сторінки, з якої знято річ. Факт: назви з російськими ознаками
(ы/э/ъ/ё, закінчення -ое/-ая/-ые/-ой, «платье/юбка/женск…»; міра проби, не правило продукту), назви без жодної кирилиці (англомовна версія сайту) по крамницях і причини карантину останнього прогону.
Запуск: python3 джерела/проби/каталог_проблеми_г_мова.py"""
import collections, gzip, os, re                                               # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
офери = [(re.search(r"<name>([^<]*)<", о).group(1), re.search(r'<param name="магазин">([^<]*)<', о).group(1))
         for о in re.findall(r"<offer\b.*?</offer>", xml, re.S)]
Р = re.compile(r"[ыэъё]|\b[а-яё]+(ое|ая|ые|ой)\b|\b(платье|юбка|женск\w*)\b", re.I)
рос = [(н, м) for н, м in офери if Р.search(н)]
лат = [(н, м) for н, м in офери if not re.search(r"[а-яіїєґ]", н.lower())]
print("речей %d · назва з російськими ознаками %d · %s · приклади %s" % (len(офери), len(рос),
      collections.Counter(м for _, м in рос).most_common(6), [н[:28] for н, _ in рос[:2]]))
print("назва без кирилиці %d · %s · приклади %s" % (len(лат), collections.Counter(м for _, м in лат).most_common(5),
      [н[:30] for н, _ in лат[:3]]))
Ф = os.path.join(К, "zhnyvarka", "жнива_2026-09-18", "карантин.xml.gz")
if os.path.exists(Ф):
    к = gzip.open(Ф, "rt", encoding="utf-8").read()
    пр = collections.Counter(re.sub(r"\s*\(.*", "", п) for п in re.findall(r'<param name="(?:причина|карантин)[^"]*">([^<]*)<', к))
    print("карантин прогону 18.09: %d записів · %s" % (sum(пр.values()), пр.most_common(6)))
