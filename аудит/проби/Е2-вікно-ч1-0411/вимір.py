"""Міряє незміненим приладом початковий код і поточне дерево на тих самих записах."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[3]
ДО = 'b694ac2d2469b4191978e4e716ac2a912715dd58'


def main():
    """Розпаковує лише код бази в TEMP, копіює входи вимірника й порівнює числа."""
    звіт = Path(__file__).resolve().parent
    прилад = КОРІНЬ / 'джерела/прилади/корінь_е2_вікно.py'
    with tempfile.TemporaryDirectory(dir=os.environ['TEMP']) as тека:
        база = Path(тека)
        архів = subprocess.run(['git', 'archive', '--format=tar', ДО, 'джерела', 'zhnyvarka'],
                              cwd=КОРІНЬ, check=True, stdout=subprocess.PIPE).stdout
        with tarfile.open(fileobj=io.BytesIO(архів)) as вхід:
            вхід.extractall(база, filter='data')
        записи = КОРІНЬ / 'аудит/проби/б1'
        for ім in ('ДО-2710', 'ПІСЛЯ-Е3'):
            джерело = записи / (ім + '.md')
            адреса = база / джерело.relative_to(КОРІНЬ)
            адреса.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(джерело, адреса)
            for джерело in (записи / ім).glob('*/знімки/модель_виклики.json'):
                адреса = база / джерело.relative_to(КОРІНЬ)
                адреса.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(джерело, адреса)
        результати = []
        for назва, дерево in [('ДО', база), ('ПІСЛЯ', КОРІНЬ)]:
            for формат in ('txt', 'json'):
                команда = [sys.executable, '-X', 'utf8', '-I', str(прилад), '--корінь', str(дерево)]
                if формат == 'json':
                    команда.append('--json')
                з = subprocess.run(команда, cwd=КОРІНЬ, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (звіт / (назва + '.' + формат)).write_bytes(з.stdout)
                if з.returncode:
                    sys.stderr.buffer.write(з.stderr)
                    return з.returncode
            текст = (звіт / (назва + '.txt')).read_text(encoding='utf-8')
            число = int(текст.strip().rsplit('місць: ', 1)[1])
            результати.append(число)
            print(назва + ': ' + str(число), flush=True)
        assert результати == [15, 7], результати
        print('Храповик кореня Е2-вікно: 15 → 7, зростання немає; прилад, база й храповик не змінені.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
