"""Послідовний запуск приладу запису; продукт і прилад не змінює."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BUILD = ROOT.parent / 'tmp' / 'збірка'
PLAN = json.loads((OUT / 'план.json').read_text(encoding='utf-8'))
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')


def main():
    for scene in PLAN['scenes']:
        if (OUT / scene / 'результат.json').exists():
            continue
        command = [sys.executable, str(BUILD / 'аудит/проби/записати_сцену.py'),
                   str(BUILD), r'C:\Users\gemini\pyodide', str(OUT / scene), '--сцена', scene]
        print(datetime.now(timezone.utc).isoformat(), scene, flush=True)
        with (OUT / 'команди.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps({'час': datetime.now(timezone.utc).isoformat(),
                                  'команда': command}, ensure_ascii=False) + '\n')
        with (OUT / (scene + '_запуск.txt')).open('w', encoding='utf-8') as log:
            result = subprocess.run(command, cwd=ROOT, env=ENV, stdout=log, stderr=subprocess.STDOUT)
        with (OUT / 'done.txt').open('a', encoding='utf-8') as log:
            log.write(f'{datetime.now(timezone.utc).isoformat()} {scene} rc={result.returncode}\n')
        print(scene, 'rc=' + str(result.returncode), flush=True)
        subprocess.run(['git', 'add', '--', str(OUT.relative_to(ROOT))], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['git', 'commit', '-m', 'проба: записати ' + scene], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        if result.returncode >= 2 or not (OUT / scene / 'результат.json').exists():
            print('Зупинка: збій середовища, потрібен огляд журналу.', flush=True)
            return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
