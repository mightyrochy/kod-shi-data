"""Виконує передбачену аудит/КОД.md батарею до кінця й зберігає коди та журнал."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

КОРІНЬ = Path(__file__).resolve().parents[3]
ДОКАЗИ = Path(__file__).parent


def main():
    """Чекає кожну команду на передньому плані; жодного живого виклику моделі не додає."""
    команди = [
        ('дим', [sys.executable, 'стенд_знімок.py', '--дим']),
        ('живий_шлях', [sys.executable, 'тест_живого_шляху.py']),
        ('протокол', [sys.executable, 'тест_протоколу.py']),
        ('гейти', [sys.executable, 'прилади/розділи_гейтів.py']),
        ('контракти', [sys.executable, 'audit_contracts.py']),
        ('показ', ['node', 'тест_показу.js']),
    ]
    оточення = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', NODE_PATH=str(КОРІНЬ / 'джерела/node_modules'))
    звіт = []
    for назва, команда in команди:
        початок = time.monotonic()
        print('Початок:', назва, flush=True)
        with (ДОКАЗИ / ('батарея-' + назва + '.txt')).open('wb') as вихід:
            пр = subprocess.run(команда, cwd=КОРІНЬ / 'джерела', env=оточення, stdout=вихід, stderr=subprocess.STDOUT)
        запис = dict(назва=назва, команда=команда, код=пр.returncode, секунд=round(time.monotonic() - початок, 1))
        звіт.append(запис)
        (ДОКАЗИ / 'батарея.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Кінець:', назва, 'код', пр.returncode, запис['секунд'], flush=True)
    sys.exit(any(з['код'] != 0 for з in звіт))


if __name__ == '__main__':
    main()
