"""Відтворює розбіжність кодувань ізольованого дочірнього Python у тесті документа."""
from pathlib import Path
import subprocess
import sys


def main():
    """Запускає незмінений тест main; повертає його справжній код завершення."""
    корінь = Path(__file__).resolve().parents[3]
    команда = [sys.executable, '-X', 'utf8',
               str(корінь / 'джерела' / 'прилади' / 'тест_документ_без_коду.py'),
               'Самоперевірка.test_самоперевірка_в_розрідженому_дереві_workflow']
    print(sys.version, flush=True)
    print('КОМАНДА: ' + ' '.join(команда), flush=True)
    вихід = subprocess.run(команда, cwd=корінь)
    print('КОД: %d' % вихід.returncode, flush=True)
    return вихід.returncode


if __name__ == '__main__':
    sys.exit(main())
