"""Примусово обриває процес запису TSV у чотирьох фазах атомарної заміни."""
import os, subprocess, sys, tempfile
from pathlib import Path
from каталог_зависла_крамниця_json_проба import обхід


def main():
    """До заміни зберігає давній файл; після заміни залишає лише цілий новий."""
    код = '''
import os, sys
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
import обхід
фаза = sys.argv[3]
замінити = обхід.os.replace
def обірвати(*арг):
    if фаза == "після": замінити(*арг)
    os._exit(7)
обєкт, імя = (обхід.csv.DictWriter, "writerows") if фаза == "рядки" else (обхід.os, "fsync" if фаза == "fsync" else "replace")
with patch.object(обєкт, імя, обірвати):
    обхід.записати(sys.argv[2], {})
'''
    with tempfile.TemporaryDirectory(prefix="обрив-заміна-") as ж:
        файл = Path(ж) / "обхід_стан.tsv"
        for фаза in ("рядки", "fsync", "перед", "після"):
            обхід.записати(ж, {"test.com": dict(домен="test.com", стан_код="WAIT", причина_код="TIMEOUT",
                             адрес=0, готово=0, лишилось=1, цикл=1, підстава="обрив")})
            давній = файл.read_bytes()
            п = subprocess.run([sys.executable, "-c", код, str(обхід.ТЕКА), ж, фаза],
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=10)
            оч = ("\t".join(обхід.ШАПКА) + "\r\n").encode() if фаза == "після" else давній
            assert п.returncode == 7 and файл.read_bytes() == оч, фаза
            print(f"Б/обрив={фаза}: файл цілий, код={п.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
