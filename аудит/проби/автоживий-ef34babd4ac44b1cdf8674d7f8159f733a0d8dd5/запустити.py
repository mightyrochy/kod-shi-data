"""Послідовний запис призначених сцен без зміни стенда або продукту."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import urllib.request

ТЕКА = Path(__file__).resolve().parent
РЕПО = ТЕКА.parents[2]
ДЕРЕВО = РЕПО.parent / 'tmp' / 'збірка'
КЕШ = Path('C:/Users/gemini/pyodide')
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH='C:/Users/gemini/kod-shi-test-node/node_modules')
ПЛАН = json.loads(next(x for x in (ТЕКА / 'НАРЯД.md').read_text(encoding='utf-8').splitlines()
                      if x.startswith('{"since":')))


def api(шлях='', тіло=None):
    запит = urllib.request.Request('http://127.0.0.1:1234/api/v1/models' + шлях,
        data=None if тіло is None else json.dumps(тіло).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(запит, timeout=300) as р:
        return json.load(р)


def запис(текст):
    with (ТЕКА / 'done.txt').open('a', encoding='utf-8') as ф:
        ф.write(datetime.now(timezone.utc).isoformat() + ' ' + текст + '\n')
    print(текст, flush=True)


def підготовка():
    результати = {'час_utc': datetime.now(timezone.utc).isoformat(), 'моделі_до': api(),
                  'контексти': [], 'NODE_OPTIONS': os.environ.get('NODE_OPTIONS'),
                  'PYTHONPATH': os.environ.get('PYTHONPATH')}
    if any(м['loaded_instances'] for м in результати['моделі_до']['models']):
        raise RuntimeError('Сервер тримає чужу модель; потрібне звільнення GPU')
    for модель, контекст in [('mamaylm-gemma-3-12b-it-v2.0', 16384), ('qwen/qwen3.5-9b', 57344)]:
        власна = None
        try:
            завантажено = api('/load', {'model': модель, 'context_length': контекст,
                                     'parallel': 1, 'echo_load_config': True})
            власна = завантажено.get('instance_id')
            стан = api()
            результати['контексти'].append({'модель': модель, 'завантажено': завантажено, 'стан': стан})
            екземпляри = [е for м in стан['models'] if м['key'] == модель for е in м['loaded_instances']
                         if е['id'] == власна]
            if not екземпляри or екземпляри[0]['config']['context_length'] != контекст or екземпляри[0]['config']['parallel'] != 1:
                raise RuntimeError('Не підтверджено контекст і parallel=1: ' + модель)
        finally:
            if власна:
                api('/unload', {'instance_id': власна})
            (ТЕКА / 'середовище.json').write_text(json.dumps(результати, ensure_ascii=False, indent=1), encoding='utf-8')
        запис('Підтверджено контекст: ' + модель + ' ' + str(контекст) + ', parallel=1; модель вивантажено')


def виконати():
    if not (ТЕКА / 'середовище.json').exists():
        підготовка()
    for сцена in ПЛАН['scenes']:
        вихід = ТЕКА / сцена
        if (вихід / 'результат.json').exists():
            continue
        env = dict(ENV)
        if сцена == 'ж1_робота':
            env['MODEL_VYBIR'] = 'assess'
        if сцена == 'ж4_робота_стримано':
            env['ZAMINA_RUK'] = '1,2'
        if сцена == 'ж1_побачення_день_червоне':
            env['ROZMOVA'] = str(ТЕКА / 'R_chervone.json')
        команда = [sys.executable, str(ДЕРЕВО / 'аудит/проби/записати_сцену.py'),
                   str(ДЕРЕВО), str(КЕШ), str(вихід), '--сцена', сцена]
        запис('Початок: ' + сцена)
        with (ТЕКА / (сцена + '-запускач.txt')).open('w', encoding='utf-8') as лог:
            лог.write(json.dumps(команда, ensure_ascii=False) + '\n')
            лог.flush()
            р = subprocess.run(команда, cwd=ДЕРЕВО, env=env, stdout=лог, stderr=subprocess.STDOUT)
        запис('Кінець: ' + сцена + ' rc=' + str(р.returncode))
        subprocess.run(['git', 'add', '--', str(ТЕКА)], cwd=РЕПО, check=True)
        subprocess.run(['git', 'commit', '-m', 'Записати живу сцену ' + сцена], cwd=РЕПО, check=True)
        if р.returncode >= 2:
            запис('Незавершена сцена: ' + сцена + '; потрібен розбір середовища перед продовженням')
            return р.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(виконати())
