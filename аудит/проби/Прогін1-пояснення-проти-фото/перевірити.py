"""Один запуск батареї й наявних проб опису; усі команди закінчуються, повний вивід зберігається."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def make_fixture(here):
    """Викладає сім справжніх записаних відповідей для діагностики, що потребує теку та сід."""
    folder = tempfile.TemporaryDirectory(prefix='опис-проба-', dir=os.environ.get('TEMP') or os.environ.get('TMP'))
    for index, row in enumerate(json.loads((here / 'джерела.json').read_text(encoding='utf8'))['образи'], 1):
        path = Path(folder.name) / f'seed0_{index}_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1.txt'
        path.write_text('── ПРОМПТ ──\n' + json.dumps(row['вхід'], ensure_ascii=False)
            + '\n\n── ВІДПОВІДЬ ──\n' + json.dumps(row['вихід'], ensure_ascii=False) + '\n', encoding='utf8')
    return folder


def main():
    """Виконує батарею до кінця, включно з командами після невдачі."""
    here = Path(__file__).resolve().parent
    source = here.parents[2] / 'джерела'
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', NODE_PATH=str(source / 'node_modules'))
    commands = [[sys.executable, 'стенд_знімок.py', '--дим'],
                *[[sys.executable, name] for name in ['тест_живого_шляху.py', 'тест_протоколу.py',
                    'прилади/розділи_гейтів.py', 'audit_contracts.py']], ['node', 'тест_показу.js']]
    probes = sorted((source / 'проби').glob('опис_*.py'))
    probes += [source / 'проби' / name for name in ['вибір_опис_v1.py', 'мова_картки_рук34.py']]
    commands += [[sys.executable, str(path.relative_to(source))] for path in probes]
    fixture = make_fixture(here)
    for command in commands:
        if Path(command[1]).name == 'опис_екран_у_рядку.py':
            command.extend([fixture.name, '0'])
    results = []
    with (here / 'батарея.log').open('w', encoding='utf8') as log:
        for command in commands:
            print('ВИКОНУЄТЬСЯ', command[1], flush=True)
            result = subprocess.run(command, cwd=source, env=env, capture_output=True)
            log.write('\nКОМАНДА ' + ' '.join(command) + '\n')
            log.write(result.stdout.decode('utf8', errors='replace'))
            log.write(result.stderr.decode('utf8', errors='replace'))
            log.write('\nКОД ' + str(result.returncode) + '\n')
            log.flush()
            results.append({'команда': command[1:], 'код': result.returncode})
            print('КОД', result.returncode, flush=True)
    (here / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('команд:', len(results), 'невдалих:', sum(r['код'] != 0 for r in results))
    fixture.cleanup()
    return int(any(r['код'] != 0 for r in results))


if __name__ == '__main__':
    sys.exit(main())
