# -*- coding: utf-8 -*-
"""Зберігає коди виходу та вивід перевірок приладу без залежності від кодування оболонки."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def виконати():
    звіт = Path(__file__).resolve().parent
    корінь = звіт.parents[2]
    середовище = dict(os.environ, NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules',
                      PYTHONIOENCODING='utf-8')
    до = Path(os.environ['TEMP']) / 'base-time-measure' / 'test-before.cjs'
    до.write_text("""const fs = require('fs'), Module = require('module'), path = require('path');
const [root, source] = process.argv.slice(2);
const original = path.join(root, 'аудит/проби/нова_база.js');
const read = Module._extensions['.js'];
Module._extensions['.js'] = (m, filename) => filename === original
  ? m._compile(fs.readFileSync(source, 'utf8'), filename) : read(m, filename);
require(path.join(root, 'аудит/проби/перевірити_нову_базу.js'));
""", encoding='utf-8')
    команди = [
        ['node', '--check', 'аудит/проби/нова_база.js'],
        ['node', 'аудит/проби/перевірити_нову_базу.js'],
        [sys.executable, 'джерела/прилади/згорнути_дошку.py', '--лише-перевірити'],
        ['git', 'diff', '--check'],
        ['node', str(до), str(корінь), str(до.parent / 'before.js')],
    ]
    записи = []
    for і, команда in enumerate(команди):
        початок = time.perf_counter()
        р = subprocess.run(команда, cwd=корінь, env=середовище,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        (звіт / f'перевірка-{і + 1}.log').write_bytes(р.stdout)
        запис = {'команда': команда, 'rc': р.returncode, 'секунд': time.perf_counter() - початок}
        записи.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
    (звіт / 'перевірки.json').write_text(json.dumps(записи, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    виконати()
