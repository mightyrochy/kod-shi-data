"""Виконує команди мірила послідовно й записує повний вивід із кодами завершення."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """Запускає названу групу без тла, продовжуючи журнал після кожної команди."""
    тека = Path(__file__).resolve().parent
    корінь = Path(os.environ.get('LYUSTERKO_TEST_ROOT', тека.parents[2]))
    джерела = корінь / 'джерела'
    оточення = dict(os.environ, PYTHONUTF8='1', NODE_PATH=str(джерела / 'node_modules'))
    група = sys.argv[1]
    if група in ('суворість-до', 'суворість-після'):
        режими = ['штатний'] if група.endswith('-до') else ['штатний', 'мутація']
        команди = [(['node', str(тека / 'ноти_суворість.js'), режим, str(затримка)], корінь)
                   for режим in режими for затримка in (0, 60, 120)]
    elif група == 'батарея':
        команди = [([sys.executable, ім, *арг], джерела) for ім, арг in (
            ('стенд_знімок.py', ['--дим']), ('тест_живого_шляху.py', []),
            ('тест_протоколу.py', []), ('прилади/розділи_гейтів.py', []),
            ('audit_contracts.py', []))]
        команди.append((['node', 'тест_показу.js'], джерела))
    elif група == 'збірка':
        оточення['LYUSTERKO_CATALOG'] = 'повний'
        команди = [([sys.executable, 'build_артефакт.py', '.', sys.argv[2], 'показ-повний'], джерела)]
    else:
        raise ValueError('Невідома група ' + група)
    результати = []
    вихід = тека / (група + '.json')
    for команда, місце in команди:
        print('Початок: ' + ' '.join(команда), flush=True)
        початок = time.monotonic()
        процес = subprocess.run(команда, cwd=місце, env=оточення, capture_output=True,
                                text=True, encoding='utf-8', timeout=3600)
        запис = {'команда': команда, 'тека': str(місце), 'код': процес.returncode,
                 'секунд': round(time.monotonic() - початок, 2),
                 'вивід': процес.stdout + процес.stderr}
        результати.append(запис)
        вихід.write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'Код {процес.returncode}; {запис["секунд"]} с', flush=True)
        if група == 'батарея' and процес.returncode:
            break
    if група.startswith('суворість-') and not all('ДОКАЗ ' in з['вивід'] for з in результати):
        return 1
    if група == 'суворість-до':
        return int([з['код'] for з in результати] != [0, 1, 1])
    if група == 'суворість-після':
        return int([з['код'] for з in результати] != [0, 0, 0, 1, 1, 1])
    return int(any(з['код'] != 0 for з in результати))


if __name__ == '__main__':
    sys.exit(main())
