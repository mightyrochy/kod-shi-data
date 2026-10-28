"""Відтворює прилад сумісності та навмисну втрату на кожному боці порівняння."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
ПРИЛАД = ТЕКА.parent / 'перевірити_сумісність.py'


def дитина(втрата):
    """Виконує справжній прилад; мутація вилучає одну прийняту заяву з відповіді продукту."""
    опис = importlib.util.spec_from_file_location('прилад', ПРИЛАД)
    прилад = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(прилад)
    прийняти = прилад.сумісність.шар.прийняти_повідомлення
    викликів = 0

    def з_втратою(*аргументи):
        """Псує лише першу пару викликів, не змінюючи архів чи вихідний код."""
        nonlocal викликів
        результат = прийняти(*аргументи)
        викликів += 1
        if викликів in {'до': (1,), 'після': (2,), 'обидва': (1, 2)}.get(втрата, ()):
            результат['заяви'] = результат['заяви'][1:]
        return результат

    прилад.сумісність.шар.прийняти_повідомлення = з_втратою
    try:
        print(json.dumps(прилад.перевірити(), ensure_ascii=False))
    except AssertionError as помилка:
        слід = помилка.__traceback__
        while слід:
            if 'підсумок' in слід.tb_frame.f_locals:
                print(json.dumps(слід.tb_frame.f_locals['підсумок'], ensure_ascii=False), flush=True)
                break
            слід = слід.tb_next
        raise


def виміряти(назва):
    """Зберігає коди завершення та журнали однакових команд ДО й ПІСЛЯ."""
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    звіт = []
    for втрата in ('нема', 'до', 'після', 'обидва'):
        команда = [sys.executable, str(Path(__file__).resolve()), '--дитина', втрата]
        результат = subprocess.run(команда, env=середовище, capture_output=True, text=True, encoding='utf-8', timeout=60)
        лог = f'{назва}-{втрата}.log'
        (ТЕКА / лог).write_text(результат.stdout + результат.stderr, encoding='utf-8', newline='\n')
        звіт.append({'втрата': втрата, 'rc': результат.returncode, 'лог': лог,
                     'підсумок': json.loads(результат.stdout)})
    (ТЕКА / f'{назва}.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(звіт, ensure_ascii=False, indent=1))
    assert [р['rc'] for р in звіт] == ([1, 1, 1, 1] if назва == 'ДО' else [0, 1, 1, 1])


if __name__ == '__main__':
    if sys.argv[1] == '--дитина':
        дитина(sys.argv[2])
    else:
        виміряти(sys.argv[1])
