"""Зберігає завершені перевірки Е1 та сусідніх приладів у UTF-8."""
import json
import os
from pathlib import Path
import subprocess
import time

КОРІНЬ = Path(__file__).resolve().parents[3]


def перевірити():
    """Виконує сім'ю приймання та сусідні транспортні проби один раз до кінця."""
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    звіт = []
    for ім in ('аудит/проби/звірки_Е1.js', 'аудит/проби/перевірити_записаний_обмін.js',
               'аудит/проби/перевірити_храповик.js', 'аудит/ноутбук_стенд_2/тест_проксі.js',
               'аудит/ноутбук_стенд_2/тест_проксі_5190.js'):
        команда = ['node', ім]
        початок = time.monotonic()
        результат = subprocess.run(команда, cwd=КОРІНЬ, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        лог = Path(__file__).parent / (Path(ім).stem + '-5.log')
        лог.write_bytes(результат.stdout)
        if 'звірки_Е1' in ім:
            (Path(__file__).parent / 'звірки-5.json').write_bytes(результат.stdout)
        звіт.append({'команда': команда, 'rc': результат.returncode,
                     'секунд': round(time.monotonic() - початок, 1), 'лог': лог.name})
        print(ім + ': rc=' + str(результат.returncode), flush=True)
    (Path(__file__).parent / 'перевірки-5.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    assert all(р['rc'] == 0 for р in звіт), звіт


if __name__ == '__main__':
    перевірити()
