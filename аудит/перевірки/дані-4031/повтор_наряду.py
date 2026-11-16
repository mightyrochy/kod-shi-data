"""Запускає саме пробу наряду з голови PR для двох версій продуктових джерел."""
import json
from pathlib import Path
import subprocess
import sys

база, голова, вихід = map(Path, sys.argv[1:])
проба = голова / "аудит/проби/Прогін-слово-жінки/коментар_межа_слота.py"
дані = {}
for назва, дерево in (("ДО", база), ("ПІСЛЯ", голова)):
    for н in (2, 3):
        файли = sorted((голова / f"аудит/проби/живий-як-людина-{н}/стенд/службове").glob("*/обміни.jsonl.gz"))
        р = subprocess.run([sys.executable, str(проба.resolve()), str((дерево / "джерела").resolve()),
                            *(str(ф.resolve()) for ф in файли)], capture_output=True, encoding="utf8")
        if р.returncode:
            raise RuntimeError(р.stderr)
        дані[f"{назва}-{н}"] = {"код": р.returncode, "файлів": len(файли), "підсумок": р.stdout.splitlines()[-1]}
Path(вихід).write_text(json.dumps(дані, ensure_ascii=False, indent=2), encoding="utf8")
print(json.dumps(дані, ensure_ascii=False))
