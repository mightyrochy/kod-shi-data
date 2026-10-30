"""Міряє незміненим приладом код початкового SHA в тимчасовій теці задачі."""
from pathlib import Path
import os
import subprocess
import sys
import tarfile


if __name__ == "__main__":
    база = "1641412fe533cadb57943b26b12316e008fd35b2"
    тека = Path(os.environ["TEMP"]) / "е2-текст-до"
    тека.mkdir(parents=True, exist_ok=True)
    процес = subprocess.Popen(["git", "archive", база, "джерела"], stdout=subprocess.PIPE)
    файлів = 0
    with tarfile.open(fileobj=процес.stdout, mode="r|") as архів:
        for запис in архів:
            if not запис.isfile() or Path(запис.name).suffix not in {".py", ".js", ".html"}:
                continue
            ціль = (тека / запис.name).resolve()
            assert ціль.is_relative_to(тека.resolve())
            ціль.parent.mkdir(parents=True, exist_ok=True)
            ціль.write_bytes(архів.extractfile(запис).read())
            файлів += 1
    assert процес.wait() == 0
    with (Path(__file__).parent / "прилад-до.txt").open("wb") as вихід:
        результат = subprocess.run([sys.executable, "джерела/прилади/корінь_е2_текст_жінці.py",
                                    str(тека / "джерела")], stdout=вихід, stderr=subprocess.STDOUT)
    print(f"База {база}, файлів коду {файлів}, код приладу {результат.returncode}")
    sys.exit(результат.returncode)
