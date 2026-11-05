"""Повторює відмови записаних запитів вибору через читачів спільного дроту без моделі.
Запуск: cd джерела; python проби/межі_записаний_дріт.py
"""
import json
from pathlib import Path
import sys
import tarfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import дріт_моделі as Д
import уважний_вибір as У

if __name__ == "__main__":
    архів = Path(__file__).resolve().parents[2] / "аудит/перевірки/rozbir_0210/ж5_співбесіда_без/відповіді.tar.gz"
    записів = вад = 0
    with tarfile.open(архів) as записи:
        for файл in записи.getmembers():
            if not файл.isfile() or "ВЕРДИКТ_V1_ВИБІР_V1" not in файл.name:
                continue
            текст = записи.extractfile(файл).read().decode("utf-8").split("── ВІДПОВІДЬ")[0]
            об, _ = json.JSONDecoder().raw_decode(текст[текст.index("{"):])
            межі = об["she_refuses"]
            очікувані = [код for коди in об["case"]["refusals"].values() for код in коди]
            пакет = {"обмеження": {"жорстке_ні": межі}}
            дроти = [Д.пакет(пакет), Д.вердикт({}, межі=межі),
                     Д.вердикт({}, межі=межі, вибір=True), Д.вердикт({}, межі=межі, ремонти=False),
                     У._контекст(пакет, межі), Д.опис({"образ": {}, "межі": межі})]
            розбіжностей = sum(дріт.get("she_refuses") != очікувані for дріт in дроти)
            записів += 1
            вад += розбіжностей
            print("%s: %r → %r; розбіжностей %d/6" % (файл.name, межі, очікувані, розбіжностей))
    print("записів: %d; розбіжностей: %d" % (записів, вад))
    sys.exit(bool(вад or not записів))
