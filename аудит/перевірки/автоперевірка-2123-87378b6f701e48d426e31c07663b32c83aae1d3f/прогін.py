"""Послідовне відтворення перевірки точної голови PR 2123 без живих моделей."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ДОКАЗИ = Path(__file__).resolve().parent
КОРІНЬ = ДОКАЗИ.parents[2]
ДЕРЕВО = КОРІНЬ.parent / 'review-2123'
ДЖЕРЕЛА = ДЕРЕВО / 'джерела'
АРТЕФАКТИ = Path('C:/Users/gemini/gemini-runs/20261029-015546-26adefb51188/review2123-artifacts')
ОТОЧЕННЯ = dict(os.environ, PYTHONUTF8='1', NODE_PATH=str(КОРІНЬ / 'джерела/node_modules'),
                 LYUSTERKO_CATALOG='повний',
                 LYUSTERKO_PYC_PYTHON='C:/Users/gemini/tools/python-3.12.1/python.exe')
for ключ in ('MODEL', 'MODEL_MOVA', 'ZHYVA', 'REPLAY_EXCHANGE', 'REPLAY_RECORDINGS'):
    ОТОЧЕННЯ.pop(ключ, None)


def виконати(назва, команда, тека=ДЖЕРЕЛА):
    """Чекає завершення команди, зберігає весь вивід та її код."""
    print('ПОЧАТОК ' + назва, flush=True)
    початок = time.monotonic()
    процес = subprocess.run(команда, cwd=тека, env=ОТОЧЕННЯ,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf8', errors='replace', timeout=3600)
    (ДОКАЗИ / (назва + '.txt')).write_text(процес.stdout, encoding='utf8')
    запис = dict(назва=назва, команда=команда, тека=str(тека), код=процес.returncode,
                 секунд=round(time.monotonic() - початок, 2),
                 підсумок=[р for р in процес.stdout.splitlines() if
                           р.startswith(('ВИКОНАНО', 'ВПАЛО', 'ПОКАЗ:', 'ДОКАЗ ', 'ПРОЙДЕНО', '8/8'))
                           or р.lstrip().startswith('✗')])
    print(json.dumps(запис, ensure_ascii=False), flush=True)
    return запис


def головна():
    """Вибирає завершену групу перевірок; чужі журнали не перезаписує."""
    голова = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ДЕРЕВО, text=True).strip()
    assert голова == '87378b6f701e48d426e31c07663b32c83aae1d3f', голова
    група = sys.argv[1]
    журнал = ДОКАЗИ / (група + '.json')
    записи = []
    if група == 'короткі':
        прилад = ДЕРЕВО / 'аудит/перевірка/доробка-Е2-схема-2/ноти_суворість.js'
        for режим in ('штатний', 'мутація'):
            for затримка in (0, 60, 120):
                записи.append(виконати('ноти-' + режим + '-' + str(затримка),
                                      ['node', str(прилад), режим, str(затримка)], ДЕРЕВО))
        for назва in ('ремонт_понад_просили', 'ремонт_порядок_5511', 'повнота_до_вибору_ходи',
                      'повнота_після_вибору_ходи', 'повнота_вибір_прийняття'):
            записи.append(виконати(назва, [sys.executable, '-X', 'utf8', 'проби/' + назва + '.py']))
        проба = ДЕРЕВО / 'аудит/перевірка/Е2-схема-3/власна_проба.py'
        for режим in ('записи', 'випадки'):
            записи.append(виконати(режим, [sys.executable, '-X', 'utf8', str(проба), режим], ДЕРЕВО))
    elif група == 'батарея':
        команди = [(назва, [sys.executable, '-X', 'utf8', назва + '.py', *арг]) for назва, арг in (
            ('стенд_знімок', ['--дим']), ('тест_живого_шляху', []), ('тест_протоколу', []),
            ('прилади/розділи_гейтів', []), ('audit_contracts', []))]
        команди.append(('тест_показу', ['node', 'тест_показу.js']))
        for назва, команда in команди:
            записи.append(виконати(назва.replace('/', '-'), команда))
            журнал.write_text(json.dumps(записи, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif група == 'збірка':
        АРТЕФАКТИ.mkdir(exist_ok=True)
        записи.append(виконати('збірка', [sys.executable, '-X', 'utf8', 'build_артефакт.py', '.',
                                         str(АРТЕФАКТИ / 'index.html'), 'показ-повний']))
    elif група == 'стенд':
        ОТОЧЕННЯ['CHROMIUM'] = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
        ОТОЧЕННЯ['ZNIMKY'] = str(АРТЕФАКТИ / 'знімки')
        ОТОЧЕННЯ['FOTO'] = '1'
        записи.append(виконати('стенд', ['node', 'аудит/проби/рв6_стенд.js',
            'http://127.0.0.1:8765', str(АРТЕФАКТИ), 'C:/Users/gemini/pyodide', '3'], ДЕРЕВО))
    elif група == 'дошка':
        записи.append(виконати('дошка', [sys.executable, '-X', 'utf8',
                              'джерела/прилади/згорнути_дошку.py', '--лише-перевірити'], ДЕРЕВО))
    else:
        raise ValueError(група)
    журнал.write_text(json.dumps(записи, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    if група == 'короткі':
        assert [з['код'] for з in записи[:6]] == [0, 0, 0, 1, 1, 1]
        assert all(з['код'] == 0 for з in записи[6:])
    elif група != 'стенд':
        assert all(з['код'] == 0 for з in записи)


if __name__ == '__main__':
    головна()
