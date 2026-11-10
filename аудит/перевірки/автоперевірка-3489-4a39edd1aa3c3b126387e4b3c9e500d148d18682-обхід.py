import ctypes
from ctypes import wintypes
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

source = pathlib.Path(sys.argv[1]).resolve() / 'джерела'
sys.path.insert(0, str(source))
import _замок_важких as lock

folder = pathlib.Path(tempfile.mkdtemp(prefix='heavy-bypass-'))
env = dict(os.environ, KODSHI_HEAVY_DIR=str(folder), PYTHONIOENCODING='utf-8')
env.pop('KODSHI_HEAVY_HELD', None)
assert [lock._слот(str(folder), 2) for _ in range(2)] == [1, 2]
print('ЗАЙНЯТО: heavy-1.lock і heavy-2.lock; N=2; KODSHI_HEAVY_HELD відсутня', flush=True)

class Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ('peakWS', 'WS', 'peakPaged', 'paged',
                                           'peakNonPaged', 'nonPaged', 'pagefile', 'peakPagefile', 'private')]
get_memory = ctypes.WinDLL('psapi').GetProcessMemoryInfo
get_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
get_memory.restype = wintypes.BOOL
check = subprocess.Popen([sys.executable, str(source / '_замок_важких.py'), '0'], env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
try:
    line = check.stderr.readline().strip()
    assert 'чекаю замок' in line and check.poll() is None
    print('КОНТРОЛЬ: ' + line, flush=True)
finally:
    check.kill()
    check.communicate()

out = pathlib.Path(os.environ['TEMP']) / 'review-3489-bypass.log'
with out.open('w', encoding='utf-8') as output:
    command = [sys.executable, 'проби/movni_dviynyky_144.py']
    process = subprocess.Popen(command, cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT)
    peak = 0
    try:
        while process.poll() is None:
            memory = Counters()
            memory.cb = ctypes.sizeof(memory)
            if get_memory(wintypes.HANDLE(int(process._handle)), ctypes.byref(memory), memory.cb):
                peak = max(peak, memory.private)
            time.sleep(.1)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
print(json.dumps(dict(command=command, exit_code=process.returncode,
                      peak_private_MiB=round(peak / 2**20, 1),
                      held_slots=2, lock_handles_still_held=len(lock._ТРИМАЮ)), ensure_ascii=False), flush=True)
text = out.read_text(encoding='utf-8', errors='replace')
print('\n'.join(text.splitlines()[:3]), flush=True)
assert process.returncode == 0 and peak >= 2**30
assert 'чекаю замок' not in text
print('ОБХІД ДОВЕДЕНО: важка наявна проба завершилась, поки обидва слоти зайняті', flush=True)
