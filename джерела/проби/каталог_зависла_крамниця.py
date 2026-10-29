# -*- coding: utf-8 -*-
"""5.3-Б: зависання крамниці (контекст, жнива, закриття, синхрон) дає WAIT/TIMEOUT, решта доходить."""
import csv, os, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід  # noqa: E402


def перевірити(місце):
    with tempfile.TemporaryDirectory(prefix=f"обхід-{місце}-") as ж:
        обхід.main(["--журнал", ж, "--магазини", "ok.com,hang.com",
                    "--секунд-на-магазин", "1", "--секунд-на-цикл", "2",
                    "--циклів", "1", "--паралельно", "2", "--заглушка", місце])
        рядки = {р["домен"]: р for р in csv.DictReader(open(Path(ж) / "обхід_стан.tsv", encoding="utf-8"), delimiter="\t")}
        assert рядки["hang.com"]["стан_код"] == "WAIT" and рядки["hang.com"]["причина_код"] == "TIMEOUT"
        assert рядки["ok.com"]["стан_код"] == "CATALOG"
        cmd = [sys.executable, str(Path(__file__).parent / "каталог_обхід_стан.py"), ж]
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        вивід = subprocess.check_output(cmd, text=True, encoding="utf-8", env=env)
        assert "крамниць 2" in вивід and "hang.com" in вивід
        if місце == "контекст":
            обхід.main(["--журнал", ж, "--магазини", "hang.com", "--секунд-на-магазин", "1",
                        "--секунд-на-цикл", "2", "--циклів", "1", "--заглушка", "успіх"])
            повтор = {р["домен"]: р for р in csv.DictReader(open(Path(ж) / "обхід_стан.tsv", encoding="utf-8"), delimiter="\t")}
            assert повтор["hang.com"]["стан_код"] == "CATALOG"
        return f"{місце}: hang.com=WAIT/{рядки['hang.com']['причина_код']}, ok.com=CATALOG"


def main():
    місця = ("контекст", "жнива", "закриття", "синхронний_блок")
    факти = [перевірити(м) for м in місця]
    for ф in факти:
        print("  ✓", ф)
    print("5.3-Б ПІСЛЯ: усі 4 місця зависання знято, кожна крамниця має код")


if __name__ == "__main__":
    main()
