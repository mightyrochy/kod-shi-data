"""Друкує чотири незалежні офлайн-відтворення на призначеному дереві обходу.

Запуск: python <цей файл> <тимчасове дерево голови PR>.
Це одноразовий доказ перевірки, не частина батареї продукту.
"""
import contextlib
import csv
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch


def стани(тека):
    """Читає збережений стан усіх крамниць."""
    with open(Path(тека) / "обхід_стан.tsv", encoding="utf-8") as потік:
        return {рядок["домен"]: рядок for рядок in csv.DictReader(потік, delimiter="\t")}


def прогін(обхід, тека, крамниці, режим, паралельно=2):
    """Виконує справжній керівник обходу з його штатною заглушкою без мережі."""
    with contextlib.redirect_stdout(io.StringIO()):
        обхід.main(["--журнал", тека, "--магазини", крамниці, "--заглушка", режим,
                    "--секунд-на-магазин", "1", "--секунд-на-цикл", "3",
                    "--циклів", "1", "--паралельно", str(паралельно)])


def main():
    """Звіряє SHA дерева та друкує факти відновлення, ізоляції й кодів стану."""
    корінь = Path(sys.argv[1]).resolve()
    голова = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip()
    if len(sys.argv) > 2 and голова != sys.argv[2]:
        raise ValueError("Потрібна саме призначена голова PR #1768: " + голова)
    sys.path.insert(0, str(корінь / "zhnyvarka"))
    import обхід

    with tempfile.TemporaryDirectory(prefix="review1768-resume-") as тека:
        прогін(обхід, тека, "hang.com", "закриття")
        до = стани(тека)["hang.com"]
        зведення = Path(тека) / "зведення_жнив.tsv"
        рядків_до = len(зведення.read_text(encoding="utf-8").splitlines()) - 1
        прогін(обхід, тека, "hang.com", "успіх")
        після = стани(тека)["hang.com"]
        рядків_після = len(зведення.read_text(encoding="utf-8").splitlines()) - 1
        print(f"В1: ДО {до['стан_код']}/{до['причина_код']}, лишилось={до['лишилось']}; "
              f"ПІСЛЯ успішного режиму {після['стан_код']}/{після['причина_код']}; "
              f"рядків зведення {рядків_до}->{рядків_після}")

    with tempfile.TemporaryDirectory(prefix="review1768-isolation-") as тека:
        for спроба in (1, 2):
            прогін(обхід, тека, "hang.com,ok.com", "синхронний_блок", паралельно=1)
            ряди = стани(тека)
            сирі = Path(тека) / "сирі" / "ok.com.jsonl"
            print(f"В2: спроба {спроба}, " + ", ".join(
                f"{домен}={ряд['стан_код']}/{ряд['причина_код']}" for домен, ряд in ряди.items())
                + f"; журнал ok.com існує={сирі.exists()}")

    with tempfile.TemporaryDirectory(prefix="review1768-threshold-") as тека:
        сирі = Path(тека) / "сирі"
        сирі.mkdir()
        (сирі / "low.com.jsonl").write_text(json.dumps(
            {"url": "https://low.com/p1", "стан": "нижче_порогу"}, ensure_ascii=False) + "\n", encoding="utf-8")
        ряд = обхід.стан_рядка("low.com", dict(нотатка="", карток="0", адрес_знайдено="1", відкрито="1"), 1, тека)
        print(f"В3: лише нижче_порогу -> {ряд['стан_код']}, причина={ряд['причина_код']!r}")

    with tempfile.TemporaryDirectory(prefix="review1768-no-progress-") as тека:
        черга = Path(тека) / "проходи" / "ok.com"
        черга.mkdir(parents=True)
        with contextlib.closing(sqlite3.connect(черга / "черга.sqlite3")) as база:
            with база:
                база.execute("CREATE TABLE черга (url TEXT, стан TEXT)")
                база.executemany("INSERT INTO черга VALUES (?,?)", [("p1", "DONE"), ("p2", "PENDING")])
        (Path(тека) / "сирі").mkdir()
        (Path(тека) / "сирі" / "ok.com.jsonl").write_text(json.dumps(
            {"url": "p1", "стан": "картка"}, ensure_ascii=False) + "\n", encoding="utf-8")
        обхід.записати(тека, {"ok.com": dict(домен="ok.com", стан_код="CATALOG", причина_код="",
            адрес=2, готово=1, лишилось=1, цикл=1, підстава="картку збережено")})

        class Виконавець:
            """Повертає один рядок зведення із заслоном і незмінною чергою."""
            def __init__(self, *args, **kwargs):
                """Приймає аргументи Popen; процес для цієї проби не запускає."""
                self.pid = -1

            def wait(self, **kwargs):
                """Пише зведення завершеного циклу без нових виконаних адрес."""
                with open(Path(тека) / "зведення_жнив.tsv", "w", encoding="utf-8", newline="") as потік:
                    запис = csv.DictWriter(потік, ["домен", "нотатка", "карток", "адрес_знайдено", "відкрито"], delimiter="\t")
                    запис.writeheader()
                    запис.writerow(dict(домен="ok.com", нотатка="заслон Cloudflare", карток=0, адрес_знайдено=2, відкрито=1))
                return 0

        with patch.object(обхід.subprocess, "Popen", Виконавець), contextlib.redirect_stdout(io.StringIO()) as вивід:
            обхід.main(["--журнал", тека, "--магазини", "ok.com", "--циклів", "2"])
        ряд = стани(тека)["ok.com"]
        print(f"В4: без прогресу, лишилось={ряд['лишилось']}, {ряд['стан_код']}, "
              f"причина={ряд['причина_код']!r}; підстава={ряд['підстава']!r}")
        print("В4: " + вивід.getvalue().strip())


if __name__ == "__main__":
    main()
