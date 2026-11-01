# -*- coding: utf-8 -*-
"""Приховані вади, частина (д), Д8: прогін усієї черги `лічба_проб.py` пачками й розбір червоних.

Наряд `аудит/наряди/Приховані-розвідка.md`. Черга — проби `лічба_проб.знайти_проби()` поза реєстром «окремо».
Прогін відновлюваний: зміряне читається з `ТЕКА/п_*.jsonl`, наступна пачка (40 проб) — з решти; вбитий процес
продовжують тим самим викликом. Проби, що пишуть у дерево (Д11), видно `git status` після прогону.

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_d_прогін.py гнати ТЕКА        # NYTOK, STELYA — як у лічба_проб.py
  python3 джерела/прилади/приховані_d_прогін.py звести ТЕКА ВИХІД  # ВИХІД.jsonl: останній вимір кожної проби
  python3 джерела/прилади/приховані_d_прогін.py розбір ЗВІТ.jsonl [--дошка]  # червоні за причиною; × дошка
Повтор незелених — `лічба_проб.py --лише …` із ZVIT у ту саму ТЕКУ під іменем `п_9NN.jsonl`: «звести» бере
останній за іменем файлу.
"""
import collections
import glob
import json
import os
import re
import subprocess
import sys

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")
sys.path.insert(0, os.path.join(ДЖ, "прилади"))
ПАЧКА = 40

ПРИЧИНИ = (  # перша, що збіглась, — за останнім рядком stderr
    ("assert", r"AssertionError"),
    ("імпорт", r"ModuleNotFoundError|ImportError"),
    ("аргумент", r"IndexError: list index|usage:|arguments are required|error: потрібн|Потрібні"),
    ("git", r"CalledProcessError: Command '\['git"),
    ("стеля", r"СТЕЛЯ"),
    ("контракт", r"KeyError|AttributeError|TypeError|NameError|ValueError"),
)


def причина(з):
    if з["rc"] == 124:
        return "стеля"
    for ім, р in ПРИЧИНИ:
        if re.search(р, з.get("причина", "")):
            return ім
    return "інше"


def зміряні(тека):
    з = {}
    for ф in sorted(glob.glob(os.path.join(тека, "п_*.jsonl"))):
        for р in open(ф, encoding="utf-8"):
            try:
                д = json.loads(р)
            except ValueError:
                continue
            з[д["проба"]] = д
    return з


def гнати(тека):
    import лічба_проб as Л
    os.makedirs(тека, exist_ok=True)
    реєстр = Л.читати_реєстр()
    черга = [п for п in Л.знайти_проби() if п not in реєстр]
    while True:
        лишок = [п for п in черга if п not in зміряні(тека)]
        print("зміряно", len(черга) - len(лишок), "лишок", len(лишок), flush=True)
        if not лишок:
            return
        н = 1 + max([int(os.path.basename(ф)[2:5]) for ф in glob.glob(os.path.join(тека, "п_[0-8]*.jsonl"))] or [0])
        subprocess.run([sys.executable, "прилади/лічба_проб.py", "--лише", *лишок[:ПАЧКА]], cwd=ДЖ,
                       env=dict(os.environ, ZVIT=os.path.join(тека, "п_%03d.jsonl" % н)),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def розбір(звіт, дошка):
    з = {json.loads(р)["проба"]: json.loads(р) for р in open(звіт, encoding="utf-8")}
    черв = {п: д for п, д in з.items() if д["rc"] != 0}
    print(f"проб {len(з)} · зелених {len(з) - len(черв)} · незелених {len(черв)}")
    for ім, н in collections.Counter(причина(д) for д in черв.values()).most_common():
        print(f"  {ім:9} {н}")
    if not дошка:
        return
    import приховані_d_мірила as П
    імена = {os.path.basename(п): д for п, д in черв.items()}
    н = 0
    for р in П.рядки_дошки():
        тут = sorted(і for і in set(re.findall(r"[\w\-]+\.py", р["текст"])) if і in імена)
        if тут:
            н += 1
            print(f"аудит/БЕКЛОГ.md:{р['рядок']} №{р['номер']} {р['статус']} доказ={р['доказ']} рід={р['рід']}\t"
                  + "; ".join(f"{т} ({причина(імена[т])})" for т in тут))
    print(f"рядків дошки з червоною пробою: {н}")


if __name__ == "__main__":
    а = sys.argv[1:]
    if а[:1] == ["гнати"]:
        гнати(а[1])
    elif а[:1] == ["звести"]:
        з = зміряні(а[1])
        with open(а[2], "w", encoding="utf-8") as ф:
            for к in sorted(з):
                ф.write(json.dumps(з[к], ensure_ascii=False) + "\n")
        print(len(з))
    elif а[:1] == ["розбір"]:
        розбір(а[1], "--дошка" in а)
    else:
        print(__doc__)
