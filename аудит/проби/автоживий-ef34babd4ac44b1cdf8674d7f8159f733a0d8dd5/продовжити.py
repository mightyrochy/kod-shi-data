"""Підтверджує походження відновленого дерева й продовжує незаписані сцени."""
from pathlib import Path
import datetime
import json
import os
import subprocess
import sys
import urllib.request

ТЕКА = Path(__file__).resolve().parent
РЕПО = ТЕКА.parents[2]
ДЕРЕВО = РЕПО.parent / 'tmp/збірка'
старе = json.loads((ТЕКА / 'походження_стенда.json').read_text(encoding='utf-8'))
перевірки = {
    p: subprocess.check_output(['git', 'hash-object', str(ДЕРЕВО / p)], text=True).strip() == h
    for p, h in старе.items() if p in [
        'index.html', 'build.txt', 'аудит/проби/записати_сцену.py',
        'аудит/проби/рв6_стенд.js', 'аудит/ноутбук_стенд_2/проксі_почергове.js']}
assert all(перевірки.values()), перевірки
with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=20) as р:
    моделі = json.load(р)
assert not any(м['loaded_instances'] for м in моделі['models'])
дані = {
    'час_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'призначений_sha': '4ee2f284af6282ce68bb7451da4c3e182083949b',
    'дерево': str(ДЕРЕВО), 'збіг_хешів': перевірки, 'моделі': моделі,
    'NODE_OPTIONS': os.environ.get('NODE_OPTIONS'), 'PYTHONPATH': os.environ.get('PYTHONPATH'),
    'попередніх_сцен': 4, 'залишилось_сцен': 13}
(ТЕКА / 'ПРОДОВЖЕННЯ.json').write_text(json.dumps(дані, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
subprocess.run(['git', 'add', '--', str(ТЕКА)], cwd=РЕПО, check=True)
subprocess.run(['git', 'commit', '-m', 'Підтвердити середовище продовження автоживого'], cwd=РЕПО, check=True)
raise SystemExit(subprocess.run([sys.executable, str(ТЕКА / 'запустити.py')], cwd=РЕПО).returncode)
