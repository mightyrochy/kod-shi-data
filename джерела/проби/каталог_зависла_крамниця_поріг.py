# -*- coding: utf-8 -*-
"""Друкує стан крамниці з прийнятими й відхиленими записами, зокрема без нового зведення."""
import json, sys, tempfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід


def main():
    """Перевіряє, що лише прийнята картка доводить наявність каталогу."""
    помилки = []
    with tempfile.TemporaryDirectory(prefix="обхід-поріг-") as ж:
        сирі = Path(ж) / "сирі"
        сирі.mkdir()
        ряд = dict(нотатка="стеля 1", карток="0", адрес_знайдено="2", відкрито="1")
        for назва, записи, очікувано in (
            ("відхилена", ["нижче_порогу"], "WAIT"),
            ("прийнята", ["картка"], "CATALOG"),
            ("перезаписана", ["картка", "нижче_порогу"], "WAIT"),
        ):
            (сирі / "test.com.jsonl").write_text("".join(json.dumps(dict(url="/p1", стан=с)) + "\n"
                                                       for с in записи), encoding="utf-8")
            зі_зведенням = обхід.стан_рядка("test.com", ряд, 1, ж)["стан_код"]
            with patch.object(обхід.subprocess, "Popen", return_value=Mock(wait=Mock(return_value=1))):
                обхід.main(["--журнал", ж, "--магазини", "test.com", "--циклів", "1"])
            import csv
            with open(Path(ж) / "обхід_стан.tsv", encoding="utf-8") as ф:
                без_зведення = next(csv.DictReader(ф, delimiter="\t"))["стан_код"]
            (Path(ж) / "обхід_стан.tsv").unlink()
            print(f"{назва}: зі зведенням={зі_зведенням}, без зведення={без_зведення}; очікувано={очікувано}")
            помилки.append(зі_зведенням != очікувано or без_зведення != очікувано)
    return int(any(помилки))


if __name__ == "__main__":
    sys.exit(main())
