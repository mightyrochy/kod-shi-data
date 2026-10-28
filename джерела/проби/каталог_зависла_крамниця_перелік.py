"""Друкує відновлення невідомого переліку після таймауту, збою й обриву без зведення."""
import csv, sys, tempfile
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід
from журнал_проходу import ЖурналПроходу


def main():
    """Відрізняє незавершений пошук від завершеної черги й перевіряє наступний запуск."""
    помилки = []
    for відомо, усього, нотатка in ((0, 0, "бюджет 1 с вичерпано (таймаут)"),
            (0, 0, "збій"), (0, 0, None), (0, 1, None), (0, 0, "давній TIMEOUT"), (1, 1, "успіх")):
        with tempfile.TemporaryDirectory(prefix="обхід-перелік-") as ж:
            п = ЖурналПроходу(Path(ж) / "проходи", "test.com", "проба")
            with п.база:
                п.база.execute("UPDATE мета SET значення=? WHERE ключ='відомо'", (str(відомо),))
                if усього:
                    п.база.execute("INSERT INTO черга VALUES ('/p1','PENDING',NULL)")
                    п.завершити(dict(url="/p1", стан="картка", відповідь=п.відповідь("/p1", 200, b"CARD")))
            п.закрити()
            if нотатка == "давній TIMEOUT":
                обхід.записати(ж, {"test.com": dict(домен="test.com", стан_код="WAIT", причина_код="TIMEOUT", адрес=0, готово=0, лишилось=0, цикл=1, підстава=нотатка)})
            ряд = dict(нотатка=нотатка, карток="0", адрес_знайдено="0", відкрито="0")
            (Path(ж) / "зведення_жнив.tsv").write_text("домен\n", encoding="utf-8")
            with patch.object(обхід, "останні_рядки", return_value=({"test.com": ряд} if нотатка else {}, 0)), patch.object(
                    обхід.subprocess, "Popen", return_value=Mock(wait=Mock(return_value=0))) as запуск:
                for _ in range(2):
                    обхід.main(["--журнал", ж, "--магазини", "test.com", "--циклів", "1"])
                with open(Path(ж) / "обхід_стан.tsv", encoding="utf-8") as ф:
                    стан = next(csv.DictReader(ф, delimiter="\t"))
            оч = 0 if відомо else 2
            print(f"відомо={відомо}, адрес={усього}, {нотатка}: лишилось={стан['лишилось']}, запусків={запуск.call_count}/{оч}")
            помилки.append(запуск.call_count != оч or bool(int(стан["лишилось"])) == bool(відомо))
    return int(any(помилки))


if __name__ == "__main__":
    sys.exit(main())
