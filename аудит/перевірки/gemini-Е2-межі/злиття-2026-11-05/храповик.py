"""Виконати повний незмінений храповик на Python 3.11 із виміряним ресурсом."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch


def main():
    """Обмежити лише кількість працівників за записаним виміром вільної пам'яті."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[3]
    if "--дитина" in sys.argv:
        sys.path.insert(0, str(корінь / "джерела/прилади"))
        import храповик_кореня as х
        sys.argv.remove("--дитина")
        # Вимір ресурсу записаний батьківським процесом у храповик.json.
        with patch.object(х.os, "cpu_count", return_value=2):
            return х.main()
    ресурс = subprocess.check_output([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_OperatingSystem | "
        "Select-Object FreePhysicalMemory,TotalVisibleMemorySize | ConvertTo-Json -Compress",
    ], text=True)
    команда = [sys.executable, str(Path(__file__).resolve()), "--дитина", *sys.argv[1:]]
    запис = dict(команда=команда, версія=sys.version, ресурс=json.loads(ресурс), працівників=2)
    os.environ.update(PYTHONUTF8="0", PYTHONIOENCODING="utf-8")
    початок = time.monotonic()
    print("ПОЧАТО повний храповик; працівників 2; Python", sys.version.split()[0], flush=True)
    with (тека / "храповик.txt").open("wb") as журнал:
        р = subprocess.run(команда, cwd=корінь, stdout=журнал, stderr=subprocess.STDOUT)
    запис.update(код=р.returncode, секунд=round(time.monotonic() - початок, 2))
    (тека / "храповик.json").write_text(
        json.dumps(запис, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ЗАВЕРШЕНО повний храповик:", р.returncode, flush=True)
    print((тека / "храповик.txt").read_text(encoding="utf-8", errors="replace"), flush=True)
    return р.returncode


if __name__ == "__main__":
    sys.exit(main())
