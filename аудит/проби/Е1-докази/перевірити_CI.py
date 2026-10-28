"""Виконує крок CI з накладених латок у Bash зі справжнім Chromium/Pyodide."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

КОРІНЬ = Path(__file__).resolve().parents[3]


def перевірити():
    """Зіставляє код приймання ДО перевірки опису PR та код цілого кроку ПІСЛЯ."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--збірка', type=Path, required=True)
    парсер.add_argument('--кеш', type=Path, required=True)
    парсер.add_argument('--вихід', type=Path, required=True)
    парсер.add_argument('--bash', default='C:/Program Files/Git/bin/bash.exe')
    арг = парсер.parse_args()
    сторінка = (арг.збірка / 'index.html').read_text(encoding='utf-8')
    крок = json.loads((Path(__file__).parent / 'доробка-латки.json').read_text(encoding='utf-8'))['крок_CI']['run']
    крок = крок.replace('${{ matrix.chastyna }}', '0')
    assert крок.count('приймання_записів.js') == крок.count('живий_після_CI.js') == 1
    звіт = {'sha256_збірки': hashlib.sha256((арг.збірка / 'index.html').read_bytes()).hexdigest(),
            'крок_CI': крок, 'проби': []}
    for назва, заміна, опис, до, після in [
        ('точна-база', None, '', 0, 0),
        ('регрес', ("? 'Готово' : 'Далі'", "? 'Далі' : 'Далі'"), '', 1, 1),
        ('застарілий-без-рядка', ('messages:повідомлення', 'messages:[]'), '', 0, 1),
        ('застарілий-з-рядком', ('messages:повідомлення', 'messages:[]'),
         'ЖИВИЙ ПІСЛЯ: б1_концерт_стримано — перезаписати вхід моделі', 0, 0),
    ]:
        тека = арг.вихід.resolve() / назва
        тека.mkdir(parents=True, exist_ok=False)
        (тека / 'pokaz').mkdir()
        текст = сторінка
        if заміна:
            assert текст.count(заміна[0]) == 1
            текст = текст.replace(*заміна)
        (тека / 'pokaz/index.html').write_text(текст, encoding='utf-8', newline='\n')
        (тека / 'подія.json').write_text(json.dumps({'pull_request': {'body': опис}}, ensure_ascii=False), encoding='utf-8')
        середовище = {к: з for к, з in os.environ.items() if not к.startswith('REPLAY_')}
        середовище.update(RUNNER_TEMP=тека.as_posix(), GITHUB_EVENT_PATH=(тека / 'подія.json').as_posix(),
                          E1_ACCEPTANCE_RC=(тека / 'приймання.rc').as_posix())
        # Кеш є передумовою кроку CI; збірка й базова база підготовлені окремо.
        команда = крок.replace('"${RUNNER_TEMP}/pyodide"', json.dumps(арг.кеш.resolve().as_posix()))
        # Обгортка лише записує код першої команди; аргументи й код повернення зберігаються.
        обгортка = '''node() {
  local rc=0
  command node "$@" || rc=$?
  if [[ "$1" == *приймання_записів.js ]]; then printf '%s' "$rc" > "$E1_ACCEPTANCE_RC"; fi
  return "$rc"
}
'''
        print('ПОЧАТОК:', назва, flush=True)
        with (тека / 'CI.log').open('w', encoding='utf-8') as лог:
            результат = subprocess.run([арг.bash, '--noprofile', '--norc', '-e', '-o', 'pipefail', '-c', обгортка + команда],
                                      cwd=КОРІНЬ, env=середовище, stdout=лог, stderr=subprocess.STDOUT, timeout=900)
        rc = int((тека / 'приймання.rc').read_text())
        підсумок = json.loads((тека / 'replay/підсумок.json').read_text(encoding='utf-8'))
        запис = {'проба': назва, 'ДО': rc, 'ПІСЛЯ': результат.returncode, 'підсумок': підсумок}
        звіт['проби'].append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
        (Path(__file__).parent / 'доробка-CI.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        assert (rc, результат.returncode) == (до, після), (тека / 'CI.log').read_text(encoding='utf-8')


if __name__ == '__main__':
    перевірити()
