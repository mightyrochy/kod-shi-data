"""Повторює прилад голови на повному обсязі Python/JS указаного коміту.

Запуск із кореня: python <цей файл> <тека tmp цієї задачі>.
Тимчасове дерево містить усі .py/.js/.mjs з джерела/; решта типів не є
входами приладу Річ-колір-межі. Прилад і його помічник беруться з голови.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def головна(тека):
    """Вивантажує обсяг бази в теку задачі й записує число та код завершення."""
    корінь = Path.cwd().resolve()
    тека = Path(тека).resolve()
    assert тека == корінь.parent / "tmp", "Потрібна tmp цієї задачі"
    дерево = Path(tempfile.mkdtemp(prefix="тон-база-", dir=тека))
    база = "5fc912a01fe93e5c180422131ce6a6798c2b3c27"
    кількість = 0
    with subprocess.Popen(["git", "archive", база, "джерела"], stdout=subprocess.PIPE) as процес:
        with tarfile.open(fileobj=процес.stdout, mode="r|") as архів:
            for файл in архів:
                if файл.isfile() and файл.name.endswith((".py", ".js", ".mjs")):
                    assert (дерево / файл.name).resolve().is_relative_to(дерево)
                    архів.extract(файл, дерево, filter="data")
                    кількість += 1
        assert процес.wait() == 0, "git archive не завершився успішно"
    середовище = dict(os.environ, PYTHONIOENCODING="utf-8")
    середовище.pop("PYTHONUTF8", None)
    вихід = Path(__file__).with_name("до.txt")
    with вихід.open("w", encoding="utf-8") as журнал:
        результат = subprocess.run([sys.executable, "джерела/прилади/корінь_річ_колір_межі.py",
                                    str(дерево)], env=середовище, stdout=журнал, stderr=subprocess.STDOUT)
    Path(__file__).with_name("база.json").write_text(json.dumps(
        {"база": база, "файлів": кількість, "код": результат.returncode,
         "python": sys.version}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"база: {база}; файлів Python/JS: {кількість}; код: {результат.returncode}")
    print("\n".join(вихід.read_text(encoding="utf-8").splitlines()[-8:]))
    return результат.returncode


if __name__ == "__main__":
    sys.exit(головна(sys.argv[1]))
