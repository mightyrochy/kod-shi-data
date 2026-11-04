"""Послідовний запис призначених сцен; не змінює продукт або реєстр."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TREE = ROOT.parent / 'tmp/live'
CACHE = Path('C:/Users/gemini/pyodide')
PLAN = json.loads((OUT / 'план.json').read_text(encoding='utf-8'))
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH='C:/Users/gemini/kod-shi-test-node/node_modules')

def note(text):
    line = datetime.now(timezone.utc).isoformat() + ' ' + text
    with (OUT / 'done.txt').open('a', encoding='utf-8') as stream:
        stream.write(line + '\n')
    print(line, flush=True)

def commit(scene):
    subprocess.run(['git', 'add', '--', str(OUT.relative_to(ROOT))], cwd=ROOT, check=True)
    subprocess.run(['git', 'commit', '-m', 'Зберегти запис сцени ' + scene], cwd=ROOT, check=True)

def main():
    for scene in PLAN['scenes']:
        if scene == 'ж7_збій_правил_без_підборів':
            note(scene + ': окремий крок із внесенням пошкоджених полів; звичайний запис його не доводить')
            continue
        dest = OUT / scene
        result = dest / 'результат.json'
        if dest.exists():
            if not result.exists():
                # Перша сцена вже виконується переднім процесом записувача.
                note(scene + ': чекаю завершення вже запущеного записувача')
                while not result.exists():
                    time.sleep(5)
            data = json.loads(result.read_text(encoding='utf-8'))
            rc = data.get('rc', 2)
            note(scene + ': завершений наявний запис, rc=' + str(rc))
        else:
            cmd = [sys.executable, str(ROOT/'аудит/проби/записати_сцену.py'),
                   str(TREE), str(CACHE), str(dest), '--сцена', scene]
            note('КОМАНДА: ' + subprocess.list2cmdline(cmd))
            with (OUT / (scene + '_запуск.txt')).open('w',encoding='utf-8') as stream:
                rc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT).returncode
            note(scene + ': код записувача=' + str(rc))
        commit(scene)
        if rc not in (0,1):
            note('ЗАБЛОКОВАНО: записувач не завершив сцену ' + scene + '; див. журнал і відповідь сервера')
            return rc
    note('Завершено звичайні записи; перевірити питання плану й окрему сцену пошкоджених полів')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
