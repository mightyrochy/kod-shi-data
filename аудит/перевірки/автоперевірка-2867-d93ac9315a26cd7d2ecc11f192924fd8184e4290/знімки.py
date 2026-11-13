"""Витягує джерела показу бази PR та знімає базу й голову окремо."""
from pathlib import Path
import subprocess
import sys

дерево = Path(sys.argv[1]).resolve()
база = Path(sys.argv[2]).resolve()
sha = 'dcb3c59d67238a3f86181cade35e0cd7089fb482'
файли = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', sha,
    'джерела/показ', 'джерела/показ.html', 'джерела/показ.css'], cwd=дерево).decode('utf-8').splitlines()
for файл in файли:
    шлях = база / файл
    шлях.parent.mkdir(parents=True, exist_ok=True)
    шлях.write_bytes(subprocess.check_output(['git', 'show', f'{sha}:{файл}'], cwd=дерево))
тека = Path(__file__).resolve().parent
subprocess.run(['node', str(тека / 'знімок.cjs'), str(дерево), str(тека), str(база)], check=True)
