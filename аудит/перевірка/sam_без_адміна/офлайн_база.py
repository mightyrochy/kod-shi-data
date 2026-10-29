# -*- coding: utf-8 -*-
"""Звіряє падіння історичної проби з модулями початкової голови гілки."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def головна():
    """Підставляє початкові версії всіх змінених модулів, решту бере з незміненого дерева."""
    корінь = Path(__file__).resolve().parents[3]
    база = "156c90a0d7d9fc5781fe7e6ae56aaa6e9e79995b"
    тека = Path(tempfile.mkdtemp(prefix=".sam-baseline-", dir=корінь)).resolve()
    assert тека.is_relative_to(корінь) and тека.name.startswith(".sam-baseline-")
    файли = ["жнива_v2.py", "жнива_реєстр.py", "жнива_фото.py", "жнива_маски.py", "жнива_колір.py",
             "verify.py", "проби/поділ_жнива_офлайн.py", "каталог_збагачення.json.gz"]
    try:
        for ім in файли:
            файл = тека / ім
            файл.parent.mkdir(parents=True, exist_ok=True)
            файл.write_bytes(subprocess.check_output(["git", "show", база + ":джерела/" + ім], cwd=корінь))
        оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONPATH=str(корінь / "джерела"))
        прогін = subprocess.run([sys.executable, str(тека / "проби/поділ_жнива_офлайн.py"), "95b0102",
                                 str(корінь / "джерела/каталог_повний.xml")], cwd=корінь,
                                env=оточення, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        Path(__file__).with_name("офлайн_база.log").write_bytes(прогін.stdout)
        факт = dict(база=база, код=прогін.returncode, початкові_файли=файли,
                    та_сама_помилка=b"module 'verify' has no attribute '_" in прогін.stdout)
        Path(__file__).with_name("офлайн_база.json").write_text(json.dumps(факт, ensure_ascii=False, indent=2), encoding="utf-8")
        print(прогін.stdout.decode("utf-8", errors="replace")[-1500:])
        print(факт)
        assert прогін.returncode == 1 and факт["та_сама_помилка"]
    finally:
        assert тека.is_relative_to(корінь) and тека.name.startswith(".sam-baseline-")
        shutil.rmtree(тека)


if __name__ == "__main__":
    головна()
