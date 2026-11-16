"""Зберегти входи вже запущеного моста попередньої версії, не зупиняючи прогін.
Новий міст архівує фото сам. Тут: <PID власного моста> <тека_прогону>.
Передній план до завершення саме цього процесу; жодних сигналів процесам.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import re
import shutil
import sys
import time

pid = int(sys.argv[1])
out = Path(sys.argv[2]) / 'стенд/записи'
source = Path(os.environ['TEMP']) / ('міст-agy-' + str(pid))
k = ctypes.windll.kernel32
k.OpenProcess.restype = ctypes.c_void_p
k.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
k.CloseHandle.argtypes = [ctypes.c_void_p]
handle = k.OpenProcess(0x100000, False, pid)
if not handle:
    raise RuntimeError('Власний міст уже не працює')
try:
    while k.WaitForSingleObject(handle, 0) == 258:
        for folder in source.glob('в*-*'):
            n = int(re.match(r'в(\d+)-', folder.name)[1])
            try:
                for file in folder.iterdir():
                    if not file.is_file():
                        continue
                    dest = out / 'фото' / f'{n:04d}' / file.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists() or dest.stat().st_size != file.stat().st_size:
                        shutil.copyfile(file, dest)
            except FileNotFoundError:
                pass  # Завершений запит прибирає свою теку; наступні ще працюють.
        time.sleep(.5)
finally:
    k.CloseHandle(handle)
    rows = [{'файл': p.relative_to(out).as_posix(), 'байтів': p.stat().st_size,
             'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((out / 'фото').rglob('*')) if p.is_file()]
    (out / 'фото_входів.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Фото входів збережено:', len(rows), flush=True)
