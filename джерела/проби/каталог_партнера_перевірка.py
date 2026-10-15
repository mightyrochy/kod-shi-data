# -*- coding: utf-8 -*-
"""Читає фід крамниці-партнера (YML, можна .gz) і друкує, яких обов'язкових полів бракує.

Чому так: поля — ключі специфікації `аудит/дослідження_research/каталог_партнерів_2026-10-15.md`, не слова речі;
значень проба не читає, лише є поле чи нема (п.12). Запуск: `python3 проби/каталог_партнера_перевірка.py [фід]`."""
import sys, gzip, pathlib, collections
from xml.etree import ElementTree as ET

_ПРИКЛАД = pathlib.Path(__file__).resolve().parents[2] / "аудит/дослідження_research/каталог_партнерів_приклад.xml"
_АТРИБУТИ = ("id", "available", "group_id")
_ТЕГИ = (("url",), ("name", "name_ua"), ("categoryId",), ("picture",), ("price",))   # кортеж — рівноцінні імена
_ПАРАМИ = (("Колір",), ("Склад", "Матеріал"))
_БАЖАНІ = ("Ролі фото", "Візерунок", "Силует", "Довжина", "Зріст моделі", "Розмір на моделі", "Сезон", "Догляд")

def параметри(офер):
    """Повертає {name: текст} непорожніх `param`; текст і з вкладених `<value lang>` Rozetka, і після `<br/>`."""
    return {п.get("name"): т for п in офер.findall("param") if (т := "".join(п.itertext()).strip())}

def бракує(офер, розмірна):
    """Повертає (обов'язкові, бажані) назви полів, яких нема; `Розмір` — лише коли колір моделі має кілька оферів."""
    п = параметри(офер)
    нема = [а for а in _АТРИБУТИ if not офер.get(а)]
    нема += ["/".join(т) for т in _ТЕГИ if not any((офер.findtext(і) or "").strip() for і in т)]
    нема += ["/".join(і) for і in _ПАРАМИ + ((("Розмір",),) if розмірна else ()) if not п.keys() & set(і)]
    return нема, [б for б in _БАЖАНІ if б not in п]

if __name__ == "__main__":
    шлях = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else _ПРИКЛАД
    офери = list(ET.parse(gzip.open(шлях) if шлях.suffix == ".gz" else шлях).getroot().iter("offer"))
    варіант = lambda о: (о.get("group_id"), параметри(о).get("Колір"))
    групи = collections.Counter(map(варіант, офери))
    підсумки = [(о.get("id"), *бракує(о, bool(о.get("group_id")) and групи[варіант(о)] > 1)) for о in офери]
    for ід, н, _ in підсумки:
        if н and len(підсумки) <= 50:
            print("offer %s: бракує %s" % (ід, ", ".join(н)))
    обов = collections.Counter(х for _, н, _ in підсумки for х in н)
    print("оферів %d · без обов'язкових полів %d" % (len(підсумки), sum(bool(н) for _, н, _ in підсумки)))
    print("обов'язкові (бракує): %s" % (dict(обов.most_common()) or "усі є"))
    print("бажані (бракує): %s" % dict(collections.Counter(х for *_, б in підсумки for х in б).most_common()))
