"""Відтворення збірки ДО з її власного стиснутого каталогу."""
import gzip
import os
from pathlib import Path
import shutil
import subprocess
import sys

out = Path(__file__).resolve().parent
root = out.parents[2]
tree = root.parent / 'tmp' / 'до'
if (out / 'ДО_підготовка.txt').exists():
    (out / 'ДО_підготовка.txt').rename(out / 'ДО_підготовка_1.txt')
with (out / 'ДО_підготовка.txt').open('w', encoding='utf-8') as log:
    command = ['git', '-C', str(tree), 'sparse-checkout', 'add', '/каталог_повний.xml.gz']
    print(command, file=log, flush=True)
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    with gzip.open(tree / 'каталог_повний.xml.gz', 'rb') as source:
        with (tree / 'джерела/каталог_повний.xml').open('wb') as target:
            shutil.copyfileobj(source, target)
    command = [sys.executable, 'build_артефакт.py', '.', '../index.html', 'показ-повний']
    print(command, file=log, flush=True)
    result = subprocess.run(command, cwd=tree / 'джерела', env=dict(os.environ,
        PYTHONUTF8='1', PYTHONIOENCODING='utf-8', LYUSTERKO_CATALOG='повний',
        LYUSTERKO_PYC_PYTHON=r'C:\Users\gemini\tools\python-3.12.1\python.exe'),
        stdout=log, stderr=subprocess.STDOUT)
    print('rc=' + str(result.returncode), file=log, flush=True)
    print('Підготовка ДО rc=' + str(result.returncode), flush=True)
raise SystemExit(result.returncode)
