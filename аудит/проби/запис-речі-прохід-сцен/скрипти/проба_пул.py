#!/usr/bin/env python3
"""Мірило (б) наряду Запис-речі-колір-мітка: записаний запит складання с5_весілля_сестри/1/7 зі звіту
`аудит/звіти/стилістка-вибір-з-пулу`, де колір речей, проведених через запис нового виду (журнал Sonnet), узято з
мітки «колір» через читача ядра (`запис_речі.розібрати` → `ядро.відтінки.факт`), — 20 запитів складання з різним сідом
порядку, той самий транспорт, що `проба.py` звіту (`claude -p --model sonnet`, 4 паралельно).

Рядок пулу з кодом: color — код відтінку, hex/family/L — ділянка коду, L_from — `photo_model`, у додатку рядка —
`color_source: photo_model`, `shades`, `print`, `shop_color` (слово крамниці лишається словом). «Не певний» — color
`uncertain`, hex порожній, межа світлості зі слова крамниці лишається, `shades_between`. Відповіді нема — рядок як був.
Настанов стилістки не змінено (наряд: «не просиш стилістку брати речі з невідомим кольором»).

Запуск з кореня: python3 аудит/проби/запис-речі-колір-с5/скрипти/проба_пул.py --усі | <сід> | --розбір"""
import importlib.util, json, os, random, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[4]
ПРОБА = КОРІНЬ / "аудит/проби/запис-речі-прохід-сцен"
os.environ["ПРОБА_ЗАПИТ"] = "с5_весілля_сестри/1/7"
os.environ["ПРОБА_ТЕКА"] = "../../проби/запис-речі-прохід-сцен/проба"
sys.path.insert(0, str(КОРІНЬ / "джерела"))
сп = importlib.util.spec_from_file_location("проба", КОРІНЬ / "аудит/звіти/стилістка-вибір-з-пулу/проба.py")
ПР = importlib.util.module_from_spec(сп); sys.modules["проба"] = ПР; сп.loader.exec_module(ПР)
import запис_речі
from ядро import відтінки
from ядро.поняття import НЕ_ПЕВНИЙ

ЗАПИТ_ЗАПИСУ = ПР.запит_із_запису


def мітки_за_n():
    """Усі рядки пулу запиту з записом проходу: n → (мітка кольору, слово крамниці). Записи проходу — `дані/записи_речі.json.gz`."""
    import csv, gzip
    записи = {к.split("@")[0]: в for к, в in json.load(gzip.open(ПРОБА / "дані/записи_речі.json.gz", "rt", encoding="utf-8")).items()}
    вихід = {}
    for р in csv.DictReader(gzip.open(КОРІНЬ / "аудит/звіти/стилістка-вибір-з-пулу/рядки.csv.gz", "rt", encoding="utf-8")):
        if р["запит"] != os.environ["ПРОБА_ЗАПИТ"] or not р["ід"]:
            continue
        к = записи.get(р["ід"].split("@")[0], {}).get("мітки", {}).get("колір")
        if к:
            вихід[р["n"]] = (к, р["колір_укр"])
    return вихід


def пакет_після():
    пакет = ЗАПИТ_ЗАПИСУ()
    cols = пакет["pool"]["cols"]
    і = {к: cols.index(к) for к in cols}
    мітки = мітки_за_n()
    for r in пакет["pool"]["rows"]:
        if r[0] not in мітки:
            continue
        мітка, слово = мітки[r[0]]
        ф = відтінки.факт(мітка, слово)
        дод = r[len(cols)] if len(r) > len(cols) else {}
        if ф.значення == НЕ_ПЕВНИЙ:
            r[і["color"]], r[і["hex"]], r[і["family"]] = "uncertain", None, None
            дод = dict(дод, color_source="photo_model", shades_between=list(ф.межі["відтінки"]))
        else:
            в = ф.значення
            r[і["color"]], r[і["hex"]], r[і["family"]], r[і["L"]], r[і["L_from"]] = в["color"], в["hex"], в["family"], в["L"], "photo_model"
            дод = dict(дод, color_source="photo_model", shades=[list(x) for x in в["відтінки"]])
            if "принт" in в:
                дод["print"] = в["принт"]
        if слово:
            дод["shop_color"] = слово
        if len(r) > len(cols):
            r[len(cols)] = дод
        else:
            r.append(дод)
    пакет["pool_keys"]["color_source"] = ("photo_model — `color` is a colour code a vision model named from the item's "
                                         "own photo gallery; `hex`, `family` and `L` are that code's centre")
    пакет["pool_keys"]["shades"] = "the item's colours as [code, share of the visible item], main first"
    пакет["pool_keys"]["shades_between"] = "`color` uncertain: the vision model hesitated between these two codes"
    пакет["pool_keys"]["print"] = "true — the item carries a printed or woven pattern"
    return пакет


ПР.запит_із_запису = lambda ключ=None: пакет_після()

if __name__ == "__main__":
    if sys.argv[1] == "--розбір":
        # Розбір звіту без змін, лише групи — як ДО: «колір був невідомий» = hex порожній у записаному запиті. Розбір
        # пише підсумок у теку звіту під назвою теки відповідей («проба») — його переносимо сюди, а файл звіту
        # повертаємо, щоб не переписати ДО.
        до = ЗАПИТ_ЗАПИСУ()
        ihex = до["pool"]["cols"].index("hex")
        невідомий_до = {r[0] for r in до["pool"]["rows"] if r[ihex] is None}

        def пакет_з_групами_до(ключ=None):
            п = пакет_після()
            for r in п["pool"]["rows"]:
                r[ihex] = None if r[0] in невідомий_до else (r[ihex] or "known")
            return п

        ПР.запит_із_запису = пакет_з_групами_до
        звіт = КОРІНЬ / "аудит/звіти/стилістка-вибір-з-пулу"
        файл_звіту = звіт / "проба-підсумок.json"
        збережено = файл_звіту.read_bytes()
        сп2 = importlib.util.spec_from_file_location("розбір", звіт / "розбір_проби.py")
        Р = importlib.util.module_from_spec(сп2)
        сп2.loader.exec_module(Р)
        Р.ПР = ПР
        try:
            Р.розібрати()
            (ПРОБА / "проба-підсумок.json").write_bytes(файл_звіту.read_bytes())
        finally:
            файл_звіту.write_bytes(збережено)
    else:
        сіди = range(1, 21) if sys.argv[1] == "--усі" else [int(sys.argv[1])]
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(ПР.виклик, сіди))
