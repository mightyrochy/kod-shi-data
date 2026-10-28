# -*- coding: utf-8 -*-
"""Друкує причину зупинки та кількість циклів на незмінній і рухомій черзі без мережі."""
import csv, sys, tempfile
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід
def main():
    """Порівнює фактичний приріст виконаних адрес, зберігаючи явну причину збою."""
    помилки = []
    for назва, карток, нотатка, готово, оч_причина, оч_циклів in (
        ("без нового стану", 1, "стеля 1", [2, 2, 2], "NO_PROGRESS", 1),
        ("без карток", 0, "стеля 1", [0, 0, 0], "NO_PROGRESS", 1),
        ("явний таймаут", 0, "таймаут", [0, 0, 0], "TIMEOUT", 1),
        ("таймаут із картками", 1, "таймаут", [2, 2, 2], "TIMEOUT", 1),
        ("заслон із картками", 1, "заслон Cloudflare", [2, 2, 2], "BOT_CHALLENGE", 1),
        ("рух без карток", 0, "стеля 1", [0, 1, 2], "", 2),
        ("рух із картками", 1, "стеля 1", [0, 1, 2], "", 2),
        ("черга вичерпана", 1, "успіх", [2, 2, 2], "", 0),
    ):
        with tempfile.TemporaryDirectory(prefix="обхід-прогрес-") as ж:
            номер = [0]
            def завершити(timeout):
                """Імітує виконані адреси чергового циклу."""
                номер[0] += 1
                return 0
            ряд = dict(нотатка=нотатка, карток=str(карток), адрес_знайдено="4", відкрито="0")
            усього = 2 if назва == "черга вичерпана" else 4
            with patch.object(обхід, "черга", side_effect=lambda *а: (усього, готово[номер[0]])), patch.object(
                обхід, "останні_рядки", return_value=({"test.com": ряд}, 1)), patch.object(
                обхід.subprocess, "Popen", return_value=Mock(wait=завершити)):
                (Path(ж) / "зведення_жнив.tsv").write_text("домен\n", encoding="utf-8")
                обхід.main(["--журнал", ж, "--магазини", "test.com", "--циклів", "2"])
            with open(Path(ж) / "обхід_стан.tsv", encoding="utf-8") as ф:
                с = next(csv.DictReader(ф, delimiter="\t"))
            print(f"{назва}: {с['стан_код']}/{с['причина_код']}, циклів={номер[0]}")
            помилки.append(номер[0] != оч_циклів or (с["причина_код"] != оч_причина if оч_причина else с["причина_код"] == "NO_PROGRESS"))
    return int(any(помилки))
if __name__ == "__main__":
    sys.exit(main())
