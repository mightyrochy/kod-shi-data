"""Витягає незмінений запис сцени та його index.html з указаного нарядом коміту."""
import argparse
from pathlib import Path
import subprocess

КОМІТ = '6c44a6c5edac74caeb499ebee919bc71a763d181'
СЦЕНА = 'аудит/проби/автоживий-c71cc075fdaca37a3df5b1419fc035acd0035024/ж4_робота_стримано'


def витягти(тека, доповнення=False):
    """Зберігає байти Git без перекодування оболонкою."""
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', КОМІТ, '--', СЦЕНА])
    paths = ['index.html'] + [p.decode('utf-8') for p in names.split(b'\0') if p]
    for name in paths:
        target = тека / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', КОМІТ+':'+name]))
    print('Витягнуто:', len(paths), 'файлів із', КОМІТ)
    if доповнення:
        # Для ізольованого мірила кешу — прийнята відповідь третьої проби №33.
        # Дві відхилені проби зберігаються окремо й не підмінюють первинні 31 обмін.
        for назва, номер in (('доповнення-32', 32), ('доповнення-33-спроба-3', 33)):
            ім = f'{номер:05}.json'
            джерело = Path(__file__).parent / назва / 'обмін' / ім
            ціль = тека / СЦЕНА / 'VIDPOVIDI' / 'обмін' / ім
            with ціль.open('xb') as файл:
                файл.write(джерело.read_bytes())
        print('Додано 2 точні живі обміни; усіх живих проб у наряді — 4')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('тека', type=Path)
    p.add_argument('--доповнити', action='store_true', help='Додати прийняту фікстуру заміни руки 2')
    a = p.parse_args()
    витягти(a.тека, a.доповнити)
