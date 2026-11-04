"""Завершення власного запуску після блокера, зі штатним finally записувача."""
import base64
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
code = """[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Get-CimInstance Win32_Process | Select-Object Name,ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress
"""
query = subprocess.run(['powershell.exe', '-NoProfile', '-EncodedCommand',
    base64.b64encode(code.encode('utf-16-le')).decode()], capture_output=True,
    encoding='utf-8', check=True)
all_processes = json.loads(query.stdout)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
native = ctypes.WinDLL('ntdll')
native.NtSuspendProcess.argtypes = [wintypes.HANDLE]
native.NtResumeProcess.argtypes = [wintypes.HANDLE]


def open_process(pid, access):
    handle = kernel.OpenProcess(access, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle


def terminate(pid):
    handle = open_process(pid, 0x0001 | 0x100000)
    try:
        if not kernel.TerminateProcess(handle, 2):
            raise ctypes.WinError(ctypes.get_last_error())
        while kernel.WaitForSingleObject(handle, 1000) == 258:
            pass
    finally:
        kernel.CloseHandle(handle)


def descendants(parent):
    result = []
    for child in all_processes:
        if child['ParentProcessId'] == parent:
            result.extend(descendants(child['ProcessId']))
            result.append(child)
    return result


actions = []
for filename in ('прогнати.py', 'підготувати_до.py'):
    marker = OUT.name + '/' + filename
    parents = [p for p in all_processes if marker in (p.get('CommandLine') or '').replace('\\', '/')
               and p.get('Name', '').lower() == 'python.exe']
    if len(parents) > 1:
        raise RuntimeError('Неоднозначний власний процес: ' + filename)
    if not parents:
        continue
    parent = parents[0]
    handle = open_process(parent['ProcessId'], 0x0800)
    suspended = False
    try:
        if native.NtSuspendProcess(handle) != 0:
            raise RuntimeError('Власний запускач не призупинено')
        suspended = True
        children = descendants(parent['ProcessId'])
        if filename == 'прогнати.py':
            recorders = [p for p in children if 'записати_сцену.py' in (p.get('CommandLine') or '')]
            stands = [p for p in children if 'рв6_стенд.js' in (p.get('CommandLine') or '')]
            if len(recorders) != 1 or len(stands) != 1:
                raise RuntimeError('Нема єдиного власного записувача й стенда; процесів не завершено')
            recorder = open_process(recorders[0]['ProcessId'], 0x100000)
            try:
                terminate(stands[0]['ProcessId'])
                while kernel.WaitForSingleObject(recorder, 1000) == 258:
                    pass
            finally:
                kernel.CloseHandle(recorder)
            actions.append({'запускач': parent, 'зупинений_стенд': stands[0],
                            'записувач': recorders[0], 'очищення': 'дочекалися finally записувача'})
        else:
            for child in children:
                try:
                    terminate(child['ProcessId'])
                except OSError as error:
                    if error.winerror != 87:
                        raise
            actions.append({'підготовка': parent, 'дочірні': children})
        terminate(parent['ProcessId'])
        suspended = False
    finally:
        if suspended:
            native.NtResumeProcess(handle)
        kernel.CloseHandle(handle)
(OUT / 'зупинено_власне.json').write_text(json.dumps(actions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Власні запуски завершено; чужих процесів не змінено.', flush=True)
