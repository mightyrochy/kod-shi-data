"""Запускає ту саму пробу на точному ДО та робочому ПІСЛЯ; журнали лежать поза git."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def main():
    """Зберігає повний вивід і код завершення обох вимірів."""
    корінь = Path(__file__).resolve().parents[3]
    проба = корінь / "джерела/проби/каталог_зависла_крамниця_жнива.py"
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    архів = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=корінь)
    with tempfile.TemporaryDirectory(prefix="dorobka-2069-do-") as тимчасова:
        with tarfile.open(fileobj=io.BytesIO(архів)) as потік:
            потік.extractall(тимчасова, filter="data")
        for назва, дерево, очікуваний in (("ДО", тимчасова, 1), ("ПІСЛЯ", str(корінь), 0)):
            команда = [sys.executable, str(проба), дерево]
            результат = subprocess.run(команда, cwd=корінь, env=середовище, capture_output=True)
            текст = "\n".join(р.rstrip() for р in (результат.stdout + результат.stderr).decode("utf-8").splitlines()) + "\n"
            текст += f"\nКод завершення: {результат.returncode}\n"
            Path(__file__).with_name(назва + ".txt").write_text(текст, encoding="utf-8", newline="\n")
            print(назва, "код", результат.returncode)
            for рядок in текст.splitlines():
                if "HTTP=" in рядок:
                    print(рядок)
            if результат.returncode != очікуваний:
                raise SystemExit(1)


if __name__ == "__main__":
    main()
