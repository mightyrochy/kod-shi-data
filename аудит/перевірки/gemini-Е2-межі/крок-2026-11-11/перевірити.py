"""Виконати батарею та повтор записів до кінця; зберегти команди й коди виходу."""
import json, os, subprocess, sys, time
from pathlib import Path

тека = Path(__file__).resolve().parent
корінь = тека.parents[3]
код = корінь / 'джерела'
до = корінь.parent / 'tmp/межі-до-20261111'
до.mkdir(parents=True, exist_ok=True)
for ім in ('мовний_шар.py', 'протокол.py', 'схема_відповіді.py'):
    (до / ім).write_bytes(subprocess.check_output(['git', 'show', '48252dea6b263e8c654299179e0b324dc18364f9:джерела/' + ім], cwd=корінь))
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
                  PYTHONPATH=str(код), NODE_PATH=str(код / 'node_modules'))
перевірки = []
for версія, джерела in (('до', до), ('після', код)):
    перевірки.append(('записи-' + версія, [sys.executable, str(тека / 'вимір.py'), str(джерела),
                                        str(тека / ('записи-' + версія + '.json.gz'))], корінь))
for ім, аргументи in [('дим', ['стенд_знімок.py', '--дим']), ('живий-шлях', ['тест_живого_шляху.py']),
                     ('протокол', ['тест_протоколу.py']), ('гейти', ['прилади/розділи_гейтів.py']),
                     ('контракти', ['audit_contracts.py'])]:
    перевірки.append((ім, [sys.executable] + аргументи, код))
перевірки.append(('показ', ['node', 'тест_показу.js'], код))
for проба in sorted((код / 'проби').glob('*.py')):
    if проба.name.startswith(('межі', 'е2_', 'шлях_шар_', 'поділ_')) and (not проба.name.startswith('поділ_') or проба.name.endswith('_ast.py')):
        перевірки.append((проба.stem, [sys.executable, str(проба)], код))
перевірки.append(('повнота-1886', [sys.executable, 'проби/шар_повнота_1886.py'], код))
звіти = []
for ім, команда, місце in перевірки:
    почато = time.monotonic()
    результат = subprocess.run(команда, cwd=місце, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (тека / (ім + '.txt')).write_bytes(результат.stdout)
    рядок = dict(назва=ім, команда=команда, тека=str(місце), код=результат.returncode,
                 секунди=round(time.monotonic() - почато, 2))
    звіти.append(рядок)
    (тека / 'підсумок.json').write_text(json.dumps(звіти, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(рядок, ensure_ascii=False), flush=True)
sys.exit(int(any(з['код'] for з in звіти)))
