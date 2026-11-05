"""Послідовний запис решти призначених сцен без зміни продукту чи стенда."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT.parent / 'tmp' / 'збірка'
CACHE = Path(r'C:\Users\gemini\gemini-runs\pyodide-0.26.4')
TASK = (OUT / 'НАРЯД.md').read_text(encoding='utf-8')
PLAN = json.loads(TASK.split('ПЛАН ЖИВОГО — ДАНІ (JSON):\n', 1)[1].split('\n', 1)[0])
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')


def main():
    for scene in PLAN['scenes']:
        target = OUT / scene
        if (target / 'результат.json').exists():
            print('Вже записано: ' + scene, flush=True)
            continue
        command = [sys.executable, str(BUILD / 'аудит/проби/записати_сцену.py'),
                   str(BUILD), str(CACHE), str(target), '--сцена', scene]
        print('Запис: ' + scene, flush=True)
        with (OUT / 'команди.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                                  'команда': command}, ensure_ascii=False) + '\n')
        env = dict(ENV)
        if scene == 'ж7_збій_правил_без_підборів':
            env['NODE_OPTIONS'] = env.get('NODE_OPTIONS', '') + ' --require "' + (OUT / 'збій_каталогу.cjs').as_posix() + '"'
        process = subprocess.Popen(command, cwd=ROOT, env=env)
        while process.poll() is None:
            try:
                process.wait(timeout=45)
            except subprocess.TimeoutExpired:
                logfile = target / 'лог.txt'
                lines = logfile.read_text(encoding='utf-8').splitlines() if logfile.exists() else []
                print(scene + ': ' + (lines[-1][:220] if lines else 'запуск'), flush=True)
        with (OUT / 'done.txt').open('a', encoding='utf-8') as log:
            log.write(datetime.now(timezone.utc).isoformat() + ' ' + scene + ' rc=' + str(process.returncode) + '\n')
        subprocess.run(['git', 'add', '--', str(OUT.relative_to(ROOT))], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '--quiet', '-m', 'Записати сцену ' + scene + ' на збірці ac752f5c'], cwd=ROOT, check=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
