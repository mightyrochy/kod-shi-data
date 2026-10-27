"""Повна батарея наряду й родина заяв одним послідовним запуском."""
import os
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    """Дочекатися кожної команди й надрукувати результат та шлях повного журналу."""
    корінь = Path(__file__).resolve().parents[2]
    джерела = корінь / 'джерела'
    тека = Path(tempfile.mkdtemp(prefix='ремонт-шар-батарея-'))
    середовище = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONUNBUFFERED='1',
                     NODE_PATH=str(джерела / 'node_modules'))
    зразки = []
    for н, джерело in enumerate((
        'origin/claude/zhyvi-15:аудит/живі_15/А/11_ж2_новорічна_мороз/VIDPOVIDI/seed3_31_мовний_шар.txt',
        '6cb247ffa66b6c1e074994d43b06904cb0567130:аудит/живі_1016_2/08_ж4_робота_живіт/VIDPOVIDI/seed3_28_мовний_шар.txt')):
        ф = тека / f'запис-{н}.txt'
        р = subprocess.run(['git', 'show', джерело], cwd=корінь, capture_output=True, encoding='utf-8', check=True)
        ф.write_text(р.stdout, encoding='utf-8')
        зразки.append(str(ф))
    команди = [[sys.executable, '-X', 'utf8', ім] for ім in (
        'стенд_знімок.py', 'тест_живого_шляху.py', 'тест_протоколу.py',
        'прилади/розділи_гейтів.py', 'audit_contracts.py')]
    команди[0].append('--дим')
    команди.append(['node', 'тест_показу.js'])
    if '--лише-родина' in sys.argv:
        команди = []
    for ф in sorted((джерела / 'проби').glob('заяви_*.py')):
        аргументи = зразки if ф.stem == 'заяви_промпт_6870' else ['каталог_повний.xml'] if ф.stem == 'заяви_каталог_35' else []
        команди.append([sys.executable, '-X', 'utf8', str(ф.relative_to(джерела)), *аргументи])
    команди.append([sys.executable, '-X', 'utf8', 'проби/картка_replay.py'])
    помилки, результати = [], []
    for н, команда in enumerate(команди, 1):
        журнал = тека / f'{н:02}.txt'
        with журнал.open('w', encoding='utf-8') as вих:
            р = subprocess.run(команда, cwd=джерела, env=середовище, stdout=вих, stderr=subprocess.STDOUT)
        текст = журнал.read_text(encoding='utf-8')
        результати.append(dict(команда=команда, код=р.returncode, журнал=str(журнал)))
        print(f'код {р.returncode}: {" ".join(команда[2:] if команда[0] == sys.executable else команда)} · {журнал}', flush=True)
        print('\n'.join(текст.splitlines()[-2:]), flush=True)
        if р.returncode:
            помилки.append(str(журнал))
    print(f'Команд {len(команди)}, провалів {len(помилки)}', flush=True)
    (тека / 'підсумок.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
    return bool(помилки)


if __name__ == '__main__':
    sys.exit(main())
