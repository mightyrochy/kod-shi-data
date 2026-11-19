# -*- coding: utf-8 -*-
"""Зберігає відсутні виходи двох коротких сцен для звірки рішень; це не повний прохід."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from виміряти import ВХІД, КОРІНЬ, НІЧНІ, ПРИЛАД, ТИМЧАСОВА, видалити


def виконати():
    звіт = Path(__file__).resolve().parent
    тека = ТИМЧАСОВА / 'дознімок'
    if тека.exists():
        raise FileExistsError(тека)
    тека.mkdir()
    for сцена in ['ж3_кафе_20', 'ж4_весілля_гостя']:
        shutil.copytree(ВХІД / сцена, тека / сцена)
    було = {ф.resolve() for ф in НІЧНІ.rglob('*')}
    початок = time.perf_counter()
    try:
        with (звіт / 'дознімок.log').open('wb') as лог:
            процес = subprocess.Popen(['node', str(ТИМЧАСОВА / 'run.cjs'), str(ПРИЛАД), str(ПРИЛАД),
                                       str(тека), str(КОРІНЬ)], cwd=КОРІНЬ,
                                      env=dict(os.environ, NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules'),
                                      stdout=лог, stderr=subprocess.STDOUT)
            try:
                rc = процес.wait(timeout=900)
            except subprocess.TimeoutExpired:
                subprocess.run(['taskkill', '/PID', str(процес.pid), '/T', '/F'], check=True)
                процес.wait()
                raise
        (звіт / 'дознімок.json').write_text(json.dumps({'rc': rc, 'секунд': time.perf_counter() - початок},
                                                     ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Дознімок:', rc, round(time.perf_counter() - початок, 3))
    finally:
        створено = {ф.resolve() for ф in НІЧНІ.rglob('*')} - було
        for ф in sorted(створено, key=lambda ф: len(ф.parts)):
            if ф.is_dir() and ф.exists():
                видалити(ф, НІЧНІ)


if __name__ == '__main__':
    виконати()
