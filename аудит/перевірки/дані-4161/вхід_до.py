"""Відтворення ДО: python вхід_до.py <дерево призначеної голови PR #4161>."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

дерево = Path(sys.argv[1]).resolve()
база = '2fa468d20ee49091590e929f3b6d58f7e270a8c1'
with tempfile.TemporaryDirectory(prefix='перевірка-4161-до-') as тимчасова:
    модулі = Path(тимчасова)
    for імя in ('знання_речі.py', 'дріт_моделі.py', 'розбір_відповідей.py'):
        (модулі / імя).write_bytes(subprocess.check_output(
            ['git', 'show', база + ':джерела/' + імя], cwd=дерево))
    os.chdir(дерево)
    файл = дерево / 'аудит/проби/Е2-опора-пояснення-без-опису-речі/вхід_пояснення.py'
    код = файл.read_text(encoding='utf-8').replace(
        'sys.path.insert(0, "джерела")',
        'sys.path[:0] = ' + repr([str(модулі), str(дерево / 'джерела')]))
    exec(compile(код, str(файл), 'exec'))
