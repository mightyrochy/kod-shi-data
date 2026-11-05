"""Виконати батарею та проби доробки, записати завершення кожної команди."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    """Зберегти журнали й коди всіх перевірок без зупинки на першій червоній."""
    тека = Path(__file__).resolve().parent
    репо = тека.parents[3]
    джерела = репо / 'джерела'
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    батарея = [
        ['python', 'стенд_знімок.py', '--дим'], ['python', 'тест_живого_шляху.py'],
        ['python', 'тест_протоколу.py'], ['python', 'прилади/розділи_гейтів.py'],
        ['python', 'audit_contracts.py'], ['node', 'тест_показу.js'],
    ]
    проби = [['node', 'проби/шар_спільні_питання.js']]
    проби += [['python', str(п.relative_to(джерела))] for п in sorted((джерела / 'проби').glob('е2_*.py'))]
    результати = []
    for н, команда in enumerate(батарея + проби, 1):
        print('Запуск:', ' '.join(команда), flush=True)
        журнал = тека / f'перевірка-{н:02}.txt'
        with журнал.open('w', encoding='utf-8') as вихід:
            р = subprocess.run(команда, cwd=джерела, env=середовище,
                               stdout=вихід, stderr=subprocess.STDOUT)
        результати.append(dict(команда=команда, код=р.returncode, журнал=журнал.name))
        (тека / 'перевірки.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Код:', р.returncode, flush=True)
    sys.exit(int(any(р['код'] for р in результати)))


if __name__ == '__main__':
    main()
