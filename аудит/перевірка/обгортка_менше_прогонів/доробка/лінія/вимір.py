"""Міряє цілісність часової лінії восьми одночасних заглушок."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def писати(тека, старий, слаг):
    """Виконує 500 пар подій старим або спільним писачем без запуску рушія."""
    if старий:
        файл = тека / 'fake_cli.py'
        вузол = next(в for в in ast.parse(файл.read_text(encoding='utf-8')).body
                     if isinstance(в, ast.FunctionDef) and в.name == 'hold')
        простір = dict(os=os, time=time)
        exec(compile(ast.Module(body=[вузол], type_ignores=[]), str(файл), 'exec'), простір)
        тримати = простір['hold']
    else:
        sys.path.insert(0, str(тека))
        sys.dont_write_bytecode = True
        from fake_timeline import тримати
    for номер in range(500):
        тримати(слаг + '-' + str(номер))


def виконати():
    """Приймає стару й нову теки перевірки та окрему нову теку журналів."""
    if sys.argv[1] == '--писач':
        писати(Path(sys.argv[2]), sys.argv[3] == 'ДО', sys.argv[4])
        return
    до, після, журнали = map(Path, sys.argv[1:])
    журнали.mkdir(parents=True, exist_ok=False)
    результати = []
    for фаза, тека in (('ДО', до), ('ПІСЛЯ', після)):
        файл = журнали.resolve() / (фаза + '.txt')
        середовище = dict(os.environ, FAKE_HOLD='0', FAKE_TIMELINE=str(файл), PYTHONUTF8='1')
        процеси = [subprocess.Popen([sys.executable, '-X', 'utf8', __file__, '--писач', str(тека.resolve()), фаза, str(номер)],
                                    env=середовище) for номер in range(8)]
        assert [процес.wait() for процес in процеси] == [0] * 8
        рядки = файл.read_text(encoding='utf-8').splitlines()
        події = [рядок.split() for рядок in рядки]
        коректні = [подія for подія in події if len(подія) == 3 and подія[0] in ('start', 'end')]
        ключі = {(подія[0], подія[1]) for подія in коректні}
        запис = dict(фаза=фаза, очікувано=8000, рядків=len(рядки), пошкоджених=len(рядки)-len(коректні),
                     унікальних=len(ключі), втрачено=8000-len(ключі))
        результати.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
    (журнали / 'результат.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert результати[1]['унікальних'] == результати[1]['рядків'] == 8000


if __name__ == '__main__':
    виконати()
