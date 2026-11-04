"""Незмінний знімок бази всередині теки задачі для повного приладу кореня."""
import json
import os
import pathlib
import subprocess
import sys
import tarfile
import time


def main():
    """Викладає джерела бази через git archive й чекає повного підсумку приладу."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    база = "805178a37ecddde0dedee5800e512db9c04e3b25"
    знімок = pathlib.Path(os.environ["TEMP"]) / "ознаки-ч4-база"
    знімок.mkdir(exist_ok=True)
    архів = знімок.parent / "ознаки-ч4-база.tar"
    subprocess.run(["git", "archive", "--format=tar", "--output=" + str(архів), база, "джерела"],
                   cwd=корінь, check=True)
    with tarfile.open(архів) as ф:
        ф.extractall(знімок, filter="data")
    команда = [sys.executable, "-W", "ignore", "джерела/прилади/корінь_річ_ознаки_обличчя.py",
               "--корінь", str(знімок)]
    початок = time.monotonic()
    with (тека / "до.txt").open("wb") as ф:
        вихід = subprocess.run(команда, cwd=корінь, stdout=ф, stderr=subprocess.STDOUT)
    (тека / "прилад-до.json").write_text(json.dumps(dict(база=база, команда=команда,
        код=вихід.returncode, секунд=round(time.monotonic() - початок, 2)), ensure_ascii=False, indent=2), "utf-8")
    return вихід.returncode


if __name__ == "__main__":
    sys.exit(main())
