"""Вимірює кінцеві кольори схем на 315 входах через справжній міст.

python аудит/проби/кольори_2028_2.py <дерево> <вихід> [--усі-гами]
Одна команда для ДО й ПІСЛЯ; це вимір наряду, не гейт CI.
"""
import gzip
import importlib.util
import itertools
import json
import pathlib
import subprocess
import sys
from collections import Counter


def головна():
    """Зберігає чипи, джерело й сили кожної пари серіалізованих кольорів."""
    корінь, вихід = map(lambda п: pathlib.Path(п).resolve(), sys.argv[1:3])
    вихід.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(корінь / "джерела"))
    мод = importlib.util.spec_from_file_location("вимір_9858", корінь / "аудит/проби/кольори_9858.py")
    в = importlib.util.module_from_spec(мод)
    мод.loader.exec_module(в)
    import колір_відношення as КВ
    класи = {"тріада": "triadic", "аналогова": "analogous", "приглушена_комплементарна": "complementary"}
    архів = json.loads(gzip.decompress((корінь / "аудит/перевірка/кольори_9858/персони.json.gz").read_bytes()))
    результати = []
    for гама in ([None, "приглушені", "насичені"] if "--усі-гами" in sys.argv else [None]):
        персони, вади, пари = [], [], Counter()
        тріад_із_вадою, зміни_брифу = set(), Counter()
        for і, до in enumerate(архів):
            вхід = dict(до["вхід"])
            if гама:
                вхід["вибір_кольору"] = dict(насиченість=гама)
            після = в.зняти(вхід)
            for г, поєднання in zip(після["екран"]["гілки"], після["поєднання"]):
                for п in поєднання:
                    клас = класи.get(п["прийом"])
                    if not клас:
                        continue
                    кольори = п["кольори"] if клас == "triadic" else [к for к in п["кольори"] if к["роль"] == "колір"]
                    for а, б in itertools.combinations(кольори, 2):
                        а, б = (dict(lab=в.КС.hx(к["hex"])) for к in (а, б))
                        сила = КВ.сила(в.КР.запис_кольору(а), в.КР.запис_кольору(б), клас)[0]
                        сім = в.КР.та_сама_сім_я(а, б)
                        пари[п["прийом"]] += 1
                        if сила < 0.5 or сім != "ні":
                            вади.append(dict(персона=і, гілка=г["схема"], прийом=п["прийом"], сила=сила,
                                             сім=сім, hex=[к["hex"] for к in п["кольори"]]))
                            if г["схема"] == п["прийом"] == "тріада":
                                тріад_із_вадою.add(і)
            без = not any(п["прийом"] == "аналогова" for п in до["поєднання"][0])
            зміни_брифу[("без_аналогової" if без else "з_аналоговою") + ("_змінено" if після["поєднання"] != до["поєднання"] else "_незмінно")] += 1
            персони.append(після)
            if (і + 1) % 35 == 0:
                print(f"{гама or 'середні'}: {і+1}/315", flush=True)
        назва = гама or "середні"
        (вихід / f"{назва}-персони.json.gz").write_bytes(gzip.compress(json.dumps(персони, ensure_ascii=False).encode(), mtime=0))
        тріади = [з for з in вади if з["гілка"] == з["прийом"] == "тріада"]
        р = dict(гама=назва, **в.підсумок(персони), пар=dict(пари), вади=вади,
                 тріади_поганих_пар=len(тріади), тріади_поганих_персон=len(тріад_із_вадою),
                 поєднання_проти_першої_спроби=dict(зміни_брифу))
        результати.append(р)
        print(json.dumps({к: з for к, з in р.items() if к != "вади"}, ensure_ascii=False), flush=True)
    підсумок = dict(sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip(), гами=результати)
    (вихід / "вимір.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    головна()
