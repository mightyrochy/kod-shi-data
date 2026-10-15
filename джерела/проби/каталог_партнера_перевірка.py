# -*- coding: utf-8 -*-
"""Читає фід крамниці-партнера (YML, можна .gz) і друкує, яких обов'язкових полів бракує.

Чому так: перелік полів — ключі специфікації `аудит/дослідження_research/каталог_партнерів_2026-10-15.md`
(назви тегів і `param name`), а не слова речі; значень проба не читає, лише є поле чи нема (п.12).
Запуск: `python3 проби/каталог_партнера_перевірка.py [фід.xml|.xml.gz]` — без аргументу бере приклад."""
import sys, gzip, pathlib, collections
from xml.etree import ElementTree as ET

_ПРИКЛАД = pathlib.Path(__file__).resolve().parents[2] / "аудит/дослідження_research/каталог_партнерів_приклад.xml"
_АТРИБУТИ = ("id", "available", "group_id")
_ТЕГИ = ("url", "name", "categoryId", "picture", "price")
_ПАРАМИ = (("Колір",), ("Склад", "Матеріал"), ("Розмір",))   # кортеж — рівноцінні імена
_БАЖАНІ = ("Ролі фото", "Візерунок", "Силует", "Довжина", "Зріст моделі", "Розмір на моделі", "Сезон", "Догляд")


def бракує(офер):
    """Повертає (обов'язкові, бажані) назви полів, яких нема в одному `offer`."""
    парами = {п.get("name") for п in офер.findall("param") if (п.text or "").strip()}
    нема = [а for а in _АТРИБУТИ if not офер.get(а)]
    нема += [т for т in _ТЕГИ if not (офер.findtext(т) or "").strip()]
    нема += ["/".join(п) for п in _ПАРАМИ if not парами & set(п)]
    return нема, [б for б in _БАЖАНІ if б not in парами]


if __name__ == "__main__":
    шлях = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else _ПРИКЛАД
    корінь = ET.parse(gzip.open(шлях) if шлях.suffix == ".gz" else шлях).getroot()
    обов, баж, офери, неповних = collections.Counter(), collections.Counter(), list(корінь.iter("offer")), 0
    for о in офери:
        н, б = бракує(о)
        обов.update(н), баж.update(б)
        неповних += bool(н)
        if н and len(офери) <= 50:
            print("offer %s: бракує %s" % (о.get("id"), ", ".join(н)))
    print("оферів %d · без обов'язкових полів %d" % (len(офери), неповних))
    print("обов'язкові (бракує): %s" % (dict(обов.most_common()) or "усі є"))
    print("бажані (бракує): %s" % dict(баж.most_common()))
