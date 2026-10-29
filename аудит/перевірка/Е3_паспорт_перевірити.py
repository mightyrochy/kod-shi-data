"""Один послідовний запуск батареї та проб сім'ї; повні журнали поза репозиторієм."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

корінь = Path(__file__).resolve().parents[2]
дж = корінь / 'джерела'
журнали = Path(tempfile.mkdtemp(prefix='Е3-паспорт-'))
середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf8', NODE_PATH=str(дж / 'node_modules'))
команди = [[sys.executable, ім] for ім in ('стенд_знімок.py', 'тест_живого_шляху.py', 'тест_протоколу.py',
                                          'прилади/розділи_гейтів.py', 'audit_contracts.py')]
команди[0].append('--дим')
команди.append(['node', 'тест_показу.js'])
команди += [[sys.executable, str(ф.relative_to(дж))] for префікс in ('паспорт_', 'картка_')
            for ф in sorted((дж / 'проби').glob(префікс + '*.py'))]
команди += [['node', 'проби/паспорт_факт.js'], [sys.executable, 'проби/поділ_pipeline_ast.py']]
результати = []
print('Журнали:', журнали, flush=True)
for н, команда in enumerate(команди):
    журнал = журнали / f'{н:02d}.log'
    with журнал.open('w', encoding='utf8') as вихід:
        р = subprocess.run(команда, cwd=дж, env=середовище, stdout=вихід, stderr=subprocess.STDOUT)
    результати.append(dict(команда=команда, код=р.returncode, журнал=str(журнал)))
    print(f'{р.returncode}: {" ".join(команда[1:])}', flush=True)
    if р.returncode:
        print(журнал.read_text(encoding='utf8')[-2200:], flush=True)
(корінь / 'аудит/перевірка/Е3_паспорт_перевірки.json').write_text(
    json.dumps(результати, ensure_ascii=False, indent=1) + '\n', encoding='utf8')
sys.exit(any(р['код'] for р in результати))
