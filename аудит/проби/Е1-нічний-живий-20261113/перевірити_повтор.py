"""Окремий точний replay завершених записів для питання PR 3536; без LM Studio.

Запуск після завершення GPU-черги, до обробки баз:
python аудит/проби/Е1-нічний-живий-20261113/перевірити_повтор.py <збірка> <кеш>
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import subprocess
import sys

out = Path(__file__).resolve().parent
repo = out.parents[2]
plan = json.loads((out / 'ПЛАН.json').read_text(encoding='utf-8'))
build, cache = map(lambda value: str(Path(value).resolve()), sys.argv[1:3])
root = out / 'повтор_обміну'
root.mkdir(exist_ok=True)
rows = []
for scene, questions in plan['scenes'].items():
    if not any(question['pr'] == 3536 for question in questions):
        continue
    source = out / scene
    result = json.loads((source / 'результат.json').read_text(encoding='utf-8'))
    if result.get('rc') not in (0, 1):
        rows.append({'сцена': scene, 'стан': 'не завершений первинний запис; повний replay не доводиться', 'rc_запису': result.get('rc')})
        continue
    target = root / scene
    target.mkdir(exist_ok=False)
    passport = json.loads((source / 'повтор.json').read_text(encoding='utf-8'))
    environment = dict(os.environ)
    code = (repo / 'аудит/проби/рв6_стенд.js').read_text(encoding='utf-8')
    for key in re.findall(r'process\.env\.([A-Z_][A-Z\d_]*)', code):
        if key not in ('CHROMIUM', 'NODE_PATH', 'HTTPS_PROXY', 'NODE_OPTIONS', 'PYTHONPATH'):
            environment.pop(key, None)
    environment.update(passport['змінні'])
    woman = target / 'жінка.json'
    woman.write_text(json.dumps(passport['жінка'], ensure_ascii=False), encoding='utf-8')
    environment.update(ZHINKA=str(woman), REPLAY_EXCHANGE=str(source / 'VIDPOVIDI/обмін'),
                       ZNIMKY=str(target / 'знімки'))
    command = ['node', str(repo / 'аудит/проби/рв6_стенд.js'), 'http://127.0.0.1:8765', build, cache, str(passport['сід'])]
    row = {'сцена': scene, 'PR': 3536, 'команда': command, 'запис': str(source),
           'початок': datetime.now(timezone.utc).isoformat(), 'моделі_не_викликаються': True}
    with (target / 'лог.txt').open('w', encoding='utf-8') as stream:
        try:
            run = subprocess.run(command, env=environment, cwd=repo, stdout=stream, stderr=subprocess.STDOUT, timeout=600)
            row['rc'] = run.returncode
        except subprocess.TimeoutExpired:
            row['rc'] = 2
            row['помилка'] = 'TimeoutExpired 600 с'
    row['кінець'] = datetime.now(timezone.utc).isoformat()
    (target / 'результат.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    rows.append(row)
    print(scene, 'replay rc=', row['rc'], flush=True)
(root / 'підсумок.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
