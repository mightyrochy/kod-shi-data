"""Зупиняє лише власний запускач між сценами, дочекавшись чинного записувача.

Потрібно для перечитування запуску особливого режиму концерту. Моделей, проксі,
стенда й чужих процесів не торкається.
"""
import base64
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import time

OUT = Path(__file__).resolve().parent
MARKER = OUT.name + '/прогнати.py'
code = """[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress
"""
query = subprocess.run(['powershell.exe', '-NoProfile', '-EncodedCommand',
    base64.b64encode(code.encode('utf-16-le')).decode()], capture_output=True,
    encoding='utf-8', check=True)
processes = json.loads(query.stdout)
if isinstance(processes, dict):
    processes = [processes]
parents = [p for p in processes if MARKER in (p.get('CommandLine') or '').replace('\\', '/')]
if len(parents) != 1:
    raise SystemExit('Нема єдиного власного запускача: ' + str(len(parents)))
parent = parents[0]
children = [p for p in processes if p['ParentProcessId'] == parent['ProcessId']
            and 'записати_сцену.py' in (p.get('CommandLine') or '')]
if len(children) != 1:
    raise SystemExit('Записувач уже завершився або ще не почався; процесів не змінено')
child = children[0]
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
native = ctypes.WinDLL('ntdll')
native.NtSuspendProcess.argtypes = [wintypes.HANDLE]
native.NtResumeProcess.argtypes = [wintypes.HANDLE]
parent_handle = kernel.OpenProcess(0x0800 | 0x0001, False, parent['ProcessId'])
child_handle = kernel.OpenProcess(0x100000 | 0x1000, False, child['ProcessId'])
if not parent_handle or not child_handle:
    raise SystemExit('Не вдалося відкрити власні процеси; їх не змінено')
finished = False
try:
    status = native.NtSuspendProcess(parent_handle)
    if status != 0:
        raise RuntimeError('Власний запускач не призупинено: ' + str(status))
    print('Чекаю завершення власного записувача', child['ProcessId'], flush=True)
    while kernel.WaitForSingleObject(child_handle, 1000) == 258:
        pass
    exit_code = wintypes.DWORD()
    if not kernel.GetExitCodeProcess(child_handle, ctypes.byref(exit_code)):
        raise ctypes.WinError(ctypes.get_last_error())
    (OUT / 'перезапуск_черги.json').write_text(json.dumps({
        'запускач': parent, 'записувач': child, 'код_записувача': exit_code.value,
        'причина': 'Перечитати власний запускач з режимом концерту; чинний запис не переривався.'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not kernel.TerminateProcess(parent_handle, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    finished = True
    print('Чинний запис завершено, rc=' + str(exit_code.value) + '; запускач зупинено між сценами.', flush=True)
finally:
    if not finished:
        native.NtResumeProcess(parent_handle)
    kernel.CloseHandle(child_handle)
    kernel.CloseHandle(parent_handle)
