"""Повний перезапуск двох планувальників на локальному git і живих замках Windows."""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def worker(lock, ready, stop):
    """Тримає FileShare.None до сигналу; ОС звільняє замок і при Stop-Tree."""
    from ctypes import wintypes
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    api.CreateFileW.restype = wintypes.HANDLE
    api.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = api.CreateFileW(str(lock), 0xC0000000, 0, None, 4, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        ready.write_text(str(os.getpid()), encoding='ascii')
        while not stop.exists():
            time.sleep(0.05)
    finally:
        api.CloseHandle(handle)


def write(path, value):
    """Записує синтетичні файли стану без CRLF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), encoding='utf-8', newline='\n')


def run(args, cwd=None):
    """Чекає кожну команду й повертає її вивід; помилку не приховує."""
    result = subprocess.run(args, cwd=cwd, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(f'{args!r}: {result.returncode}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def main():
    """Збирає факти ДО або ПІСЛЯ без моделей, мережі й установлених копій."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--worker', nargs=3, type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(*args.worker)
        return 0
    source = args.source.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().with_name('перезапуск.ps1')
    log = []
    failures = []

    def check(name, ok, facts=''):
        line = f'{"✓" if ok else "✗"} {name}' + (f': {facts}' if facts else '')
        print(line, flush=True)
        log.append(line)
        if not ok:
            failures.append(name)

    def restart(root, engine, mode='main'):
        return run(['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                    '-File', str(script), '-SourceDir', str(source), '-Root', str(root), '-Engine', engine, '-Mode', mode])

    # Окрема тека кожного запуску: чужих шляхів і процесів стенд не торкається.
    with tempfile.TemporaryDirectory(prefix='slots-1998-') as temp:
        base = Path(temp)
        for n in (4, 6, 12):
            root = base / str(n)
            root.mkdir()
            origin = root / 'origin.git'
            seed = root / 'seed'
            run(['git', 'init', '-q', '--bare', str(origin)])
            run(['git', 'init', '-q', '-b', 'main', str(seed)])
            write(seed / 'аудит/адаптери/gemini/смуги.json', {'v': 1, 'slots': dict.fromkeys(('codex', 'agy', 'claude'), n)})
            run(['git', 'add', '.'], seed)
            run(['git', '-c', 'user.name=Стенд', '-c', 'user.email=stand@example.invalid', 'commit', '-qm', 'Стенд'], seed)
            run(['git', 'remote', 'add', 'origin', str(origin)], seed)
            run(['git', 'push', '-q', 'origin', 'main'], seed)
            run(['git', 'clone', '-q', '-b', 'main', str(origin), str(root / 'clone')])
            for path in ('g/state', 'g/slots', 'c/state', 'c/slots', 'out', 'outbox', 'pub', 'lanes'):
                (root / path).mkdir(parents=True, exist_ok=True)
            processes = []
            stop = root / 'stop'
            try:
                for lane in ('codex', 'agy', 'claude'):
                    home = root / ('c' if lane == 'claude' else 'g')
                    model = {'codex': 'gpt-6.1-sol-high', 'agy': 'gemini-3.8-flash-high', 'claude': 'cc-claude-sonnet-5-5-medium'}[lane]
                    for k in range(1, n + 1):
                        slot = f'{lane}-{k}'
                        lock = home / 'slots' / f'{slot}.lock'
                        ready = root / f'{slot}.ready'
                        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(lock), str(ready), str(stop)], creationflags=subprocess.CREATE_NO_WINDOW)
                        processes.append((lane, k, proc, home))
                        deadline = time.monotonic() + 15
                        while not ready.exists() and proc.poll() is None and time.monotonic() < deadline:
                            time.sleep(0.02)
                        if not ready.exists():
                            raise RuntimeError(f'немає замка {slot}')
                        stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        # StartTime — фактичний час процесу для захисту від повторного PID.
                        start = run(['powershell', '-NoProfile', '-Command', f"(Get-Process -Id {proc.pid}).StartTime.ToUniversalTime().ToString(\"yyyy-MM-dd'T'HH:mm:ss'Z'\")"]).strip()
                        marker = f'gemini-queue/стенд-{slot}/{model}/1'
                        ident = f'20261028-000000-{k:012x}'
                        state = {'id': ident, 'slug': f'стенд-{slot}', 'slot': slot, 'marker': marker, 'model': model,
                                 'pid': proc.pid, 'start': start if lane == 'claude' else '', 'ahead': 0, 'turns': 0, 'code': ''}
                        state_text = f'STARTED {ident} ' if lane == 'claude' else 'STARTED '
                        write(home / 'state' / f'{slot}.txt', state_text + json.dumps(state))
                        write(home / 'slots' / f'{slot}.json', {'slot': slot, 'slug': state['slug'], 'marker': marker, 'model': model, 'since': stamp, 'gpu': k == n})
                # Два справжні входи Main у нових процесах: попередні наряди
                # відомі тільки через STARTED, worker.json і живі замки.
                restart(root, 'gemini')
                restart(root, 'claude')
                for lane in ('codex', 'agy', 'claude'):
                    rows = [(k, proc, home) for ln, k, proc, home in processes if ln == lane]
                    alive = [k for k, proc, _ in rows if proc.poll() is None]
                    started = [k for k, _, home in rows if (home / 'state' / f'{lane}-{k}.txt').read_text(encoding='utf-8').startswith('STARTED ')]
                    check(f'n={n}, {lane}: після перезапуску всі живі та STARTED', len(alive) == n and len(started) == n,
                          f'живі={alive}; STARTED={started}')
                beat = json.loads((root / 'out/heartbeat.json').read_text(encoding='utf-8'))
                check(f'n={n}: писач heartbeat бачить обидві смуги цілком', all(len(l['busy']) == n and l['n'] == n for l in beat['lanes']))
                restart(root, 'claude', 'read')
                read = json.loads((root / 'read.json').read_text(encoding='utf-8'))
                check(f'n={n}: читач heartbeat бачить усі активні слоти', len(read['lanes']) == 2 and all(len(l['busy']) == n for l in read['lanes']))
                body = (root / 'status.md').read_text(encoding='utf-8')
                shown = sum(f'gemini-queue/стенд-{lane}-{k}/' in body for lane in ('codex', 'agy', 'claude') for k in range(1, n + 1))
                check(f'n={n}: статус містить усі активні наряди', shown == n * 3, f'{shown}/{n * 3}')
                check(f'n={n}: GPU зайнята обома зовнішніми смугами', f'codex-{n}' in body.split('GPU: ')[-1] and f'agy-{n}' in body.split('GPU: ')[-1])
                write(evidence / f'heartbeat-{n}.json', beat)
                write(evidence / f'статус-{n}.md', body)
                # Після звільнення ОС-замків відновлення повинно завершувати
                # справді покинуті STARTED, включно з 10–12.
                stop.touch()
                for _, _, proc, _ in processes:
                    proc.wait(timeout=10)
                restart(root, 'gemini')
                restart(root, 'claude')
                done = sum((home / 'state' / f'{lane}-{k}.txt').read_text(encoding='utf-8').startswith('DONE ') for lane, k, _, home in processes)
                check(f'n={n}: після звільнення замків покинуті STARTED завершено', done == n * 3, f'{done}/{n * 3}')
                # Прострочені claim до STARTED: вільні 1,5,10,64 очищаються;
                # живі утримуються. worker.json мусить пройти той самий діапазон.
                for lane in ('codex', 'agy', 'claude'):
                    home = root / ('c' if lane == 'claude' else 'g')
                    for k in (1, 5, 10, 64):
                        ident = f'20261028-010000-{k:012x}'
                        runs = home / 'runs' if lane == 'claude' else home
                        write(runs / ident / 'worker.json', {'slot': f'{lane}-{k}'})
                        claim = home / 'state' / f'orphan-{lane}-{k}.claim'
                        write(claim, ident)
                        os.utime(claim, (time.time() - 1200,) * 2)
                restart(root, 'gemini')
                restart(root, 'claude')
                left = sorted(str(p.relative_to(root)) for p in root.rglob('orphan-*.claim'))
                check(f'n={n}: прострочені claim вільних слотів 1,5,10,64 очищено', not left, str(left))
                # Нульова місткість не скасовує вже зайняті слоти вище N.
                for count in (0, 1, 4, 6, 12, 64, 65, -1, '06', '6.0', '999999999999999999999'):
                    busy = [{'slot': f'{lane}-{k}', 'marker': f'gemini-queue/межа-{lane}-{k}/gpt-6.1-sol-high/1', 'model': 'gpt-6.1-sol-high', 'since': '2026-10-28T00:00:00Z', 'gpu': k == 64}
                            for lane in ('codex',) for k in range(1, 66)]
                    busy += [dict(busy[0], slot=s) for s in ('codex-0', 'codex-01', 'codex--1', '../codex-1', 'agy-1', 'codex-1\n')]
                    write(root / 'out/heartbeat.json', {'lanes': [{'lane': 'codex', 'n': count, 'busy': busy}]})
                    restart(root, 'claude', 'read')
                    read = json.loads((root / 'read.json').read_text(encoding='utf-8'))
                    valid = isinstance(count, int) and 0 <= count <= 64
                    ok = len(read['lanes']) == 1 and len(read['lanes'][0]['busy']) == 64 and read['busy'] if valid else not read['lanes'] and not read['busy']
                    check(f'n={n}: недовірений heartbeat n={count!r}', bool(ok))
            finally:
                stop.touch()
                for _, _, proc, _ in processes:
                    if proc.poll() is None:
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()
    log.append(f'ПІДСУМОК: {len(log) - len(failures)} ✓ / {len(failures)} ✗')
    print(log[-1])
    write(evidence / 'результат.txt', '\n'.join(log) + '\n')
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
