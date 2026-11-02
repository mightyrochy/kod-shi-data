"""Витягає незмінений запис сцени та його index.html з указаного нарядом коміту."""
import argparse
from pathlib import Path
import subprocess

КОМІТ = '6c44a6c5edac74caeb499ebee919bc71a763d181'
СЦЕНА = 'аудит/проби/автоживий-c71cc075fdaca37a3df5b1419fc035acd0035024/ж4_робота_стримано'


def витягти(тека):
    """Зберігає байти Git без перекодування оболонкою."""
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', КОМІТ, '--', СЦЕНА])
    paths = ['index.html'] + [p.decode('utf-8') for p in names.split(b'\0') if p]
    for name in paths:
        target = тека / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', КОМІТ+':'+name]))
    print('Витягнуто:', len(paths), 'файлів із', КОМІТ)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('тека', type=Path)
    витягти(p.parse_args().тека)
