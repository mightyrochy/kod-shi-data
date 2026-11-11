"""Виконує батарею до кінця, зберігає виходи й коди кожної команди."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    """Ганяє Python-частину батареї; показ має окремий повний журнал."""
    звіт = Path(__file__).resolve().parent
    джерела = звіт.parents[2] / 'джерела'
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    команди = [
        ('дим', ['стенд_знімок.py', '--дим']),
        ('живий_шлях', ['тест_живого_шляху.py']),
        ('протокол', ['тест_протоколу.py']),
        ('гейти', ['прилади/розділи_гейтів.py']),
        ('контракти', ['audit_contracts.py']),
        ('правила', [str(звіт / 'правила.py')]),
        ('розмова', ['проби/вікно_розмови_164.py']),
        ('самозвіт_палітри', ['проби/try_pytannia_151.py']),
    ]
    коди = []
    for назва, арг in команди:
        with (звіт / (назва + '.txt')).open('w', encoding='utf-8') as вихід:
            процес = subprocess.run([sys.executable, '-X', 'utf8', *арг], cwd=джерела,
                                    env=середовище, stdout=вихід, stderr=subprocess.STDOUT)
        коди.append(f'{назва}: {процес.returncode}')
        print(коди[-1], flush=True)
    (звіт / 'коди.txt').write_text('\n'.join(коди) + '\n', encoding='utf-8')
    return int(any(not р.endswith(': 0') for р in коди))


if __name__ == '__main__':
    sys.exit(main())
