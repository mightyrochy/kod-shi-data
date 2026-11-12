"""Виконує батарею та проби сім'ї послідовно, зберігає команди, коди й повні журнали."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys


def виконати():
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / 'джерела'
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    команди = [
        ('фікстура', джерела, [sys.executable, '-c', "import feed; print(feed.каталог_на_диску('каталог_brief.xml'))"]),
        ('стенд_знімок', джерела, [sys.executable, 'стенд_знімок.py', '--дим']),
        ('живий_шлях', джерела, [sys.executable, 'тест_живого_шляху.py']),
        ('протокол', джерела, [sys.executable, 'тест_протоколу.py']),
        ('гейти', джерела, [sys.executable, 'прилади/розділи_гейтів.py']),
        ('контракти', джерела, [sys.executable, 'audit_contracts.py']),
        ('показ', джерела, ['node', 'тест_показу.js']),
        ('записаний_обмін', корінь, ['node', 'аудит/проби/перевірити_записаний_обмін.js']),
        ('храповик', корінь, ['node', 'аудит/проби/перевірити_храповик.js']),
        ('нова_звірка', корінь, ['node', 'аудит/проби/перевірити_храповик_нову.js']),
        ('погодження_push', корінь, ['node', 'аудит/проби/перевірити_доробку_2041.js']),
        ('дошка', корінь, [sys.executable, 'джерела/прилади/згорнути_дошку.py', '--лише-перевірити']),
        ('дифф', корінь, ['git', 'diff', '--check']),
    ]
    результати = []
    for назва, де, команда in команди:
        р = subprocess.run(команда, cwd=де, env=середовище, capture_output=True)
        (тека / (назва + '.txt.gz')).write_bytes(gzip.compress(р.stdout + b'\n' + р.stderr))
        результати.append({'перевірка': назва, 'код': р.returncode, 'команда': команда, 'тека': str(де)})
        (тека / 'перевірки.json').write_text(json.dumps(результати, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'{назва}: {р.returncode}', flush=True)
    return int(any(р['код'] for р in результати))


if __name__ == '__main__':
    sys.exit(виконати())
