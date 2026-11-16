"""Повний повтор на кеші з обчисленням і лічбою виміру 14.11, без HTTP-транспорту."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "кадр_варіант_кв1_канал_1411"))
import вимір


def одна(старий, сховище, дерево, голова):
    """Читає збережену відповідь і викликає незмінений розрахунок попереднього виміру."""
    шлях = сховище / "відповіді" / (старий["ід"] + ".json.gz")
    with gzip.open(шлях, "rt", encoding="utf-8") as потік:
        збережене = json.load(потік)
    assert збережене["адреса"] == старий["адреса"]
    відповідь = збережене["відповідь"]
    результат = dict(ід=старий["ід"], адреса=старий["адреса"], знято=збережене["знято"],
                     код=відповідь["код"], кінцева_адреса=відповідь["url"],
                     помилка=відповідь.get("помилка"), причина_код=відповідь.get("причина_код"),
                     файл=str(шлях.resolve()), голова=голова)
    if відповідь["код"] != 200 or not відповідь.get("тіло") or відповідь.get("заслон"):
        результат.update(стан="без_відповіді")
    else:
        try:
            результат.update(вимір.оцінити_окремо(старий, відповідь, дерево))
        except Exception as збій:
            результат.update(стан="збій_розбору", збій=type(збій).__name__ + ": " + str(збій))
    return результат


def голова_дерева(дерево):
    """Читає SHA коду, яким міряємо всі записи."""
    return subprocess.check_output(["git", "-C", str(дерево), "rev-parse", "HEAD"], text=True).strip()


def main():
    """Виконує всі записи й пише повний звіт один раз після завершення черги."""
    парсер = argparse.ArgumentParser(description=__doc__)
    for поле in ("дерево", "знімок", "сховище", "вихід"):
        парсер.add_argument("--" + поле, type=Path, required=True)
    парсер.add_argument("--без-мережі", action="store_true", required=True)
    парсер.add_argument("--процесів", type=int, default=3)
    парсер.add_argument("--продовжити", type=Path, help="проміжний архів тільки цього самого SHA")
    а = парсер.parse_args()
    assert 1 <= а.процесів <= (os.cpu_count() or 1)
    дерево = а.дерево.resolve()
    голова = голова_дерева(дерево)
    assert hashlib.sha256(а.знімок.read_bytes()).hexdigest() == вимір.ВІДБИТОК
    sys.path[:0] = [str(дерево / "zhnyvarka"), str(дерево / "джерела")]
    import жниварка as ж
    assert ж._curl is not None and ж.ПАРСЕР_HTML == "lxml", "Потрібні curl_cffi та lxml"
    записи = [dict(ід=з["ід"], адреса=з["адреса"]) for з in вимір.читати(а.знімок) if
              {п[0]: п[1] for п in з.get("параметри", [])}.get("канал") == "картка"]
    адреси = {з["ід"]: з["адреса"] for з in записи}
    assert len(записи) == len(адреси) == 13882
    бракує = [з["ід"] for з in записи if not (а.сховище / "відповіді" / (з["ід"] + ".json.gz")).is_file()]
    if бракує:
        raise SystemExit("Неповний кеш: " + repr(бракує))
    результати = {}
    if а.продовжити:
        for р in вимір.читати(а.продовжити):
            assert р["голова"] == голова and адреси[р["ід"]] == р["адреса"]
            assert р["ід"] not in результати
            результати[р["ід"]] = р
    продовжено = len(результати)
    print("Збережено на тому самому SHA:", продовжено, "голова:", голова, flush=True)
    with ProcessPoolExecutor(max_workers=а.процесів) as пул:
        завдання = [пул.submit(одна, з, а.сховище.resolve(), дерево, голова)
                    for з in записи if з["ід"] not in результати]
        for готове in as_completed(завдання):
            р = готове.result()
            результати[р["ід"]] = р
            if len(результати) % 100 == 0:
                print(вимір.зараз(), len(результати), р["стан"], flush=True)
    assert len(результати) == 13882 and голова_дерева(дерево) == голова
    вимір.підсумок(записи, результати, а.вихід)
    маніфест = dict(голова=голова, знімок_sha256=вимір.ВІДБИТОК,
                   знято=вимір.зараз(), записів=13882, оброблено=len(результати),
                   процесів=а.процесів, продовжено=продовжено,
                   продовження_sha256=hashlib.sha256(а.продовжити.read_bytes()).hexdigest() if а.продовжити else None)
    (а.вихід / "маніфест.json.gz").write_bytes(gzip.compress(
        json.dumps(маніфест, ensure_ascii=False).encode("utf-8"), mtime=0))


if __name__ == "__main__":
    main()
