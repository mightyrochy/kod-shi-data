"""Повторює повний лічильник Річ-запис-речі на двох деревах із Python версії CI."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела' / 'прилади'))
from храповик_кореня import ЧАС_ПРИЛАДУ


def лічити(інтерпретатор, дерево, назва):
    """Виконує всі входи лічильника зі штатною межею часу й зберігає справжній код."""
    тека = Path(__file__).resolve().parent
    префікс = тека / ('річ-311-' + назва)
    команда = [str(інтерпретатор), '-X', 'utf8',
               str(дерево / 'джерела' / 'прилади' / 'корінь_річ_запис_речі.py'), '--поступ']
    початок = time.monotonic()
    межа = False
    with префікс.with_suffix('.txt').open('wb') as вихід, префікс.with_suffix('.поступ.txt').open('wb') as журнал:
        процес = subprocess.Popen(команда, cwd=дерево, stdout=вихід, stderr=журнал)
        try:
            код = процес.wait(timeout=ЧАС_ПРИЛАДУ)
        except subprocess.TimeoutExpired:
            межа = True
            subprocess.run(['taskkill', '/PID', str(процес.pid), '/T', '/F'], capture_output=True)
            процес.wait()
            код = 124
    stdout = префікс.with_suffix('.txt').read_bytes()
    stderr = префікс.with_suffix('.поступ.txt').read_text(encoding='utf-8', errors='replace')
    числа = re.findall(r'(?m)^місць:\s*(\d+)\s*$', stdout.decode('utf-8', errors='replace'))
    сторінки = re.findall(r'(?m)^(\d+)/144 ', stderr)
    результат = dict(дерево=str(дерево), команда=команда, код=код, межа_секунд=ЧАС_ПРИЛАДУ,
                     тайм_аут=межа, секунд=time.monotonic() - початок,
                     місць=int(числа[-1]) if числа else None,
                     сторінок_почато=len(сторінки),
                     stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                     час_завершення=datetime.now(timezone.utc).isoformat())
    префікс.with_suffix('.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(результат, ensure_ascii=False), flush=True)
    return результат


def main():
    """Звіряє два повні повтори; часткова вибірка або тайм-аут не дають успіху."""
    інтерпретатор, база = (Path(значення).resolve() for значення in sys.argv[1:3])
    версія = subprocess.run([str(інтерпретатор), '--version'], capture_output=True, check=True).stdout.decode('utf-8').strip()
    assert версія.startswith('Python 3.11.'), версія
    print(версія, flush=True)
    дерева = ((КОРІНЬ, 'голова'), (база, 'база'))
    if len(sys.argv) > 3:
        assert sys.argv[3] in ('голова', 'база')
        дерева = tuple(пара for пара in дерева if пара[1] == sys.argv[3])
    with ThreadPoolExecutor(max_workers=len(дерева)) as пул:
        завдання = [пул.submit(лічити, інтерпретатор, дерево, назва)
                    for дерево, назва in дерева]
        результати = [завдання.result() for завдання in завдання]
    успіх = all(р['код'] == 0 and р['сторінок_почато'] == 144 and р['місць'] is not None for р in результати)
    if len(результати) == 2:
        успіх = успіх and результати[0]['місць'] == результати[1]['місць']
    print('Повні 144 сторінки та нічні записи на вибраних деревах: ' + ('так' if успіх else 'НЕ ПІДТВЕРДЖЕНО'), flush=True)
    return 0 if успіх else 1


if __name__ == '__main__':
    sys.exit(main())
