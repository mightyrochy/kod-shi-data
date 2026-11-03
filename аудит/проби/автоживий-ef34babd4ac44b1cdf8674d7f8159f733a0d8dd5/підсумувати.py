"""Зіставляє записані вердикти, запускає штатний прилад бази та зберігає його результат."""
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

ТЕКА = Path(__file__).resolve().parent
РЕПО = ТЕКА.parents[2]
assert ТЕКА.is_relative_to(РЕПО)
assert (РЕПО / 'аудит/проби/нічні').resolve().is_relative_to(РЕПО)
дані = json.loads((ТЕКА / 'ДОКАЗИ_ПИТАНЬ.json').read_text(encoding='utf-8'))
план = json.loads(next(x for x in (ТЕКА / 'НАРЯД.md').read_text(encoding='utf-8').splitlines()
                       if x.startswith('{"since":')))
assert set(дані) == set(план['scenes'])
правила = []
for рука in дані['б1_концерт_стримано']['руки']:
    if рука['рука'] not in ['1', '2']:
        continue
    в = {'рука': рука['рука']}
    for правило in ['K-CRA-04', 'K-OUT-06']:
        в[правило] = {
            'слід': [x for x in рука['слід'] if x['правило'] == правило],
            'знахідки': [x for x in рука['знахідки'] or [] if x.get('правило') == правило]}
    правила.append(в)
(ТЕКА / 'КРОК_РЕДАГУВАННЯ.json').write_text(json.dumps(правила, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
main = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=РЕПО, text=True).strip()
команда = ['node', 'аудит/проби/нова_база.js', ТЕКА.relative_to(РЕПО).as_posix()]
р = subprocess.run(команда, cwd=РЕПО, env=os.environ, capture_output=True, text=True, encoding='utf-8')
база = {'час_utc': datetime.now(timezone.utc).isoformat(), 'команда': команда, 'origin_main': main,
        'rc': р.returncode, 'stdout': р.stdout, 'stderr': р.stderr}
(ТЕКА / 'НОВА_БАЗА_ЗАПУСК.json').write_text(json.dumps(база, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
звіт = ТЕКА / 'ЗВІТ.md'
текст = звіт.read_text(encoding='utf-8')
маркер = '\n## Результат штатного приладу бази\n'
текст = текст.split(маркер)[0]
текст += маркер + '\nКоманда: `' + ' '.join(команда) + '`; код виходу `' + str(р.returncode) + \
         '`. Фактичний `origin/main`: `' + main + '`.\n\n'
файл = ТЕКА / 'НОВА_БАЗА.md'
if файл.exists():
    текст += '\n'.join(файл.read_text(encoding='utf-8').splitlines()[2:]) + '\n'
else:
    текст += 'Файл НОВА_БАЗА.md не створено.\n'
if р.returncode == 2:
    текст += '\nЗбій приладу:\n\n```text\n' + р.stdout + р.stderr + '\n```\n'
звіт.write_text(текст, encoding='utf-8')
підсумок = {
    'призначений_sha': '4ee2f284af6282ce68bb7451da4c3e182083949b',
    'штамп_джерел': 'ef34babd4ac44b1cdf8674d7f8159f733a0d8dd5',
    'сцен': len(дані), 'питань': sum(map(len, план['scenes'].values())),
    'коди': dict(Counter(x['rc'] for x in дані.values())),
    'доведено_завершення': sum(bool(x.get('завершення', {}).get('вердикт', {}).get('доведено')) for x in дані.values()),
    'червоних_звірок': sum(len(x['червоні']) for x in дані.values()),
    'база_rc': р.returncode, 'повторів_сцен': 0,
    'незавершені': [с for с, x in дані.items() if not x.get('завершення', {}).get('вердикт', {}).get('доведено')]}
(ТЕКА / 'ПІДСУМОК.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(json.dumps(підсумок, ensure_ascii=False))
print(р.stdout)
if р.stderr:
    print(р.stderr)
