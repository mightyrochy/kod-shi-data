"""Мірило на справжніх worker і планувальниках, підробний лише локальний LM Studio та агент."""
import argparse
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time


SCRIPT = r'''
param([string]$SourceDir, [string]$TestDir, [string]$Lane, [string]$TestMode, [int]$Port)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
. (Join-Path $SourceDir ($Lane + '_run.ps1'))
$script:RealWriteLog = ${function:Write-Log}
$LaneDir = $TestDir
$RunsDir = $TestDir
$WorkDir = $TestDir
$OutDir = $TestDir
$script:SlotDir = $TestDir
$script:Bound = @{}
$script:Limits = @{}
function Write-Log([string]$Text, [switch]$Required) { [IO.File]::AppendAllText((Join-Path $TestDir 'wrapper.log'), $Text + "`n", $script:Utf8) }
function Invoke-RestMethod {
    param([string]$Uri, [string]$Method = 'Get', [string]$ContentType, $Body, [int]$TimeoutSec, $ErrorAction)
    $args_ = @{ Uri = $Uri.Replace('127.0.0.1:1234', "127.0.0.1:$Port"); Method = $Method; TimeoutSec = $TimeoutSec; ErrorAction = 'Stop' }
    if ($ContentType) { $args_.ContentType = $ContentType }
    if ($null -ne $Body) { $args_.Body = $Body }
    Microsoft.PowerShell.Utility\Invoke-RestMethod @args_
}
function Get-StatePath { Join-Path $TestDir 'state' }
function Close-FailedStart { }
function Remove-Claim { }
function Set-BrowserGpuPolicy { }
function Test-ExternalGpuFree { $true }
function Add-HealthException { }
function Get-Markers { }
function Get-NightlyMarker { }
function Save-Skips { }
function Test-Isolation { '' }
function Test-OwnerUser { $true }
function Get-VersionSwitch { '' }
function Get-BootStamp { 'стенд-завантаження' }
function Resume-Interrupted { }
function Write-Heartbeat { }
function Update-Status { }
function Invoke-Git {
    param([string[]]$GitArgs)
    if ($GitArgs[0] -eq 'remote') { return [pscustomobject]@{Out=$RepoUrl;Code=0} }
    [IO.File]::WriteAllText((Join-Path $TestDir 'fetch-failed'), 'так')
    throw 'стенд: GitHub недоступний'
}
function Invoke-Task {
    <# Агент вантажить дві моделі окремим дочірнім процесом, потім закінчується чи чекає вбивства. #>
    $p = [Diagnostics.Process]::Start((New-StartInfo (Get-Command node).Source @((Join-Path $TestDir 'agent.js'), [string]$Port, $TestMode, $TestDir) $TestDir -NoRedirect))
    $p.WaitForExit()
    if ($TestMode -eq 'agent-crash') { throw 'стенд: збій агента' }
    if ($TestMode -eq 'timeout') { throw 'стенд: тайм-аут' }
}
$script:Job = [pscustomobject]@{name='gemini-queue/стенд/gpt-test/1/gpu'; id='стенд-прогін'; limits=[pscustomobject]@{};
    ref='ref';sha='sha';slot='test-slot';gpu=($TestMode -ne 'cpu');lane=$Lane;slug='стенд';model='gpt-test';n='1';cond='gpu';prio=1;deadline='';time=1;claude='cc-test';effort='high'}
if ($TestMode -eq 'recover') { Start-Markers @() | Out-Null; if ($null -eq $script:Held) { throw 'Не ініціалізовано стан утримань' }; exit 0 }
if ($TestMode -eq 'offline') { exit (Main) }
if ($TestMode -eq 'take') { $lock_ = Open-Lock (Get-GpuLockPath); try { Start-GpuModels $script:Job } finally { $lock_.Dispose() }; exit 0 }
if ($TestMode -eq 'locked') {
    $lock_ = Open-Lock (Get-GpuLockPath)
    try { Start-Markers @() | Out-Null } finally { $lock_.Dispose() }
    exit 0
}
if ($TestMode -eq 'log-fail') {
    Set-Item Function:Write-Log $script:RealWriteLog
    $logName = $(if ($Lane -eq 'gemini') { 'wrapper.log' } else { 'claude-run.log' })
    $file_ = [IO.File]::Open((Join-Path $TestDir $logName), 'OpenOrCreate', 'ReadWrite', 'None')
    $lock_ = Open-Lock (Get-GpuLockPath)
    try { Complete-GpuModels; exit 2 } catch { exit 0 } finally { $lock_.Dispose(); $file_.Dispose() }
}
exit (Invoke-Worker)
'''

AGENT = r'''
const fs = require('fs'), path = require('path');
const [port, mode, dir] = process.argv.slice(2);
async function main() {
  if (mode !== 'cpu') for (const model of ['owner-model', 'job-model']) {
    const r = await fetch(`http://127.0.0.1:${port}/api/v1/models/load`, {
      method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({model})});
    if (!r.ok) throw Error('стенд: завантаження');
  }
  fs.writeFileSync(path.join(dir, 'ready'), String(process.pid));
  if (mode === 'kill-tree') setInterval(() => {}, 1000);
}
main().catch(e => { console.error(e); process.exit(1); });
'''


class Studio(BaseHTTPRequestHandler):
    """REST з окремими ID: один початковий екземпляр і два екземпляри агента."""

    loaded = {}
    calls = []
    fault = ''

    def log_message(self, *_):
        """Прибирає шум HTTP з виміру."""

    def reply(self, value, status=200):
        """Віддає JSON так само, як локальний сервер моделей."""
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        """Читає каталог або моделює відмову читання."""
        self.calls.append(('GET', self.path))
        if self.fault == 'get':
            return self.reply({'error': 'недоступно'}, 503)
        if self.fault == 'schema':
            return self.reply({'models': None})
        self.reply({'models': [dict(key=key, loaded_instances=[{'id': i} for i, m in self.loaded.items() if m == key])
                               for key in ['owner-model', 'job-model']]})

    def do_POST(self):
        """Завантажує новий ID чи вивантажує лише названий екземпляр."""
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.calls.append(('POST', self.path, body))
        if self.path.endswith('/load'):
            identifier = 'job-' + body['model']
            self.loaded[identifier] = body['model']
            return self.reply({'status': 'loaded', 'instance_id': identifier})
        if self.fault == 'unload':
            return self.reply({'error': 'відмова'}, 503)
        self.loaded.pop(body['instance_id'], None)
        self.reply({'status': 'unloaded'})


@contextmanager
def studio():
    """Тримає підробний сервер окремо від дерева GPU-наряду до завершення виміру."""
    server = ThreadingHTTPServer(('127.0.0.1', 0), Studio)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def main():
    """Перевіряє нормальні й аварійні кінці та відновлення обома смугами без живої моделі."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--before', action='store_true', help='Очікувати історичний залишок після вбитого дерева')
    opts = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('Потрібна Windows для мірилa taskkill /T /F')
    powershell = shutil.which('powershell')
    bad = 0

    def check(name, ok):
        """Кожний хибний факт робить результат стенда червоним."""
        nonlocal bad
        print(('✓ ' if ok else '✗ ') + name, flush=True)
        bad += not ok

    with tempfile.TemporaryDirectory(prefix='gpu-models-') as tmp, studio() as port:
        root = Path(tmp)
        script = root / 'worker.ps1'
        script.write_text(SCRIPT, encoding='utf-8-sig')
        for lane in ['gemini', 'claude']:
            modes = ['kill-tree'] if opts.before else ['done', 'blocked', 'timeout', 'agent-crash', 'kill-tree', 'cpu']
            for mode in modes:
                d = root / (lane + '-' + mode)
                d.mkdir()
                (d / 'agent.js').write_text(AGENT, encoding='utf-8')
                Studio.loaded = {'owner-id': 'owner-model'}
                Studio.calls = []
                Studio.fault = ''
                args = [powershell, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(script),
                        '-SourceDir', str(opts.source_dir.resolve()), '-TestDir', str(d), '-Lane', lane, '-Port', str(port)]

                def run(mode_):
                    """Чекає завершення конкретного процесу; вивід читається тільки при збої."""
                    p = subprocess.run(args + ['-TestMode', mode_], capture_output=True, timeout=45)
                    if p.returncode and mode_ not in ('timeout', 'agent-crash'):
                        print(p.stdout.decode('utf-8', errors='replace'), p.stderr.decode('utf-8', errors='replace'))
                        if mode_ not in ('done', 'log-fail'):
                            raise RuntimeError('Збій процесу стенда: ' + mode_)
                    return p

                if mode == 'kill-tree':
                    with (d / 'process.log').open('wb') as output:
                        p = subprocess.Popen(args + ['-TestMode', mode], stdout=output, stderr=output)
                        try:
                            until = time.monotonic() + 30
                            while not (d / 'ready').exists() and p.poll() is None and time.monotonic() < until:
                                time.sleep(.05)
                            if not (d / 'ready').exists():
                                raise RuntimeError((d / 'process.log').read_text(encoding='utf-8', errors='replace'))
                            check(lane + ': до вбивства завантажено 3 екземпляри', len(Studio.loaded) == 3)
                            child = int((d / 'ready').read_text())
                            killed = subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
                            gone = subprocess.run(['tasklist', '/FI', 'PID eq ' + str(child), '/NH', '/FO', 'CSV'], capture_output=True)
                            check(lane + ': taskkill знищив worker і дочірній агент', str(child).encode() not in gone.stdout)
                            p.wait(timeout=10)
                        finally:
                            if p.poll() is None:
                                subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
                                p.wait(timeout=10)
                    # Новий процес планувальника іншої смуги відтворює також перезапуск обгортки.
                    args[args.index('-Lane') + 1] = 'claude' if lane == 'gemini' else 'gemini'
                    run('recover')
                else:
                    result = run(mode)
                    check(lane + '/' + mode + ': код завершення worker', result.returncode == (1 if mode in ('timeout', 'agent-crash') else 0))
                clean = Studio.loaded == {'owner-id': 'owner-model'}
                check(lane + '/' + mode + ': стан до замка відновлено' + (' (ДО: очікуваний залишок)' if opts.before else ''), not clean if opts.before else clean)
                check(lane + '/' + mode + ': початкова модель збережена', Studio.loaded.get('owner-id') == 'owner-model')
                if not opts.before:
                    check(lane + '/' + mode + ': запис прибрано після підтвердження', not (d / 'gpu-models.json').exists())
                    unloads = [c[2]['instance_id'] for c in Studio.calls if c[0] == 'POST' and c[1].endswith('/unload')]
                    log = (d / 'wrapper.log').read_text(encoding='utf-8') if (d / 'wrapper.log').exists() else ''
                    check(lane + '/' + mode + ': кожне вивантаження має модель, ID і наряд у журналі',
                          len(unloads) == (0 if mode == 'cpu' else 2) and all(
                              any(identifier in line and 'модель=' in line and 'наряд=gemini-queue/стенд/' in line and 'прогін=стенд-прогін' in line
                                  for line in log.splitlines()) for identifier in unloads))
                    if mode == 'cpu':
                        check(lane + ': CPU-наряд не читає і не змінює LM Studio', not Studio.calls)
            if opts.before:
                continue
            # Збої між знімком і прибиранням не стирають межу власності та не пускають наступний наряд.
            for fault in ['unload', 'get', 'schema']:
                Studio.loaded = {'owner-id': 'owner-model'}
                Studio.fault = ''
                run('take')
                Studio.loaded['job-job-model'] = 'job-model'
                Studio.fault = fault
                run('recover')
                check(lane + '/' + fault + ': збій лишає знімок і власний екземпляр',
                      (d / 'gpu-models.json').exists() and 'job-job-model' in Studio.loaded)
                Studio.fault = ''
                run('recover')
                check(lane + '/' + fault + ': повтор відновлює тільки початкову модель', Studio.loaded == {'owner-id': 'owner-model'})
            Studio.fault = 'get'
            run('done')
            check(lane + ': без початкового REST-знімка агент не вантажить моделей', Studio.loaded == {'owner-id': 'owner-model'})
            Studio.fault = ''
            Studio.loaded = {}
            run('done')
            check(lane + ': порожня початкова множина відновлюється', not Studio.loaded and not (d / 'gpu-models.json').exists())
            Studio.loaded = {'owner-id': 'owner-model'}
            run('take')
            Studio.loaded['job-job-model'] = 'job-model'
            before_calls = len(Studio.calls)
            run('locked')
            check(lane + ': зайнятий GPU-замок не дозволяє прибирати активний наряд',
                  len(Studio.calls) == before_calls and 'job-job-model' in Studio.loaded)
            check(lane + ': недоступний журнал зупиняє POST unload',
                  run('log-fail').returncode == 0 and len(Studio.calls) == before_calls + 1 and 'job-job-model' in Studio.loaded)
            run('recover')
            before_calls = len(Studio.calls)
            run('recover')
            check(lane + ': завершене прибирання не повторює REST і вивантаження',
                  len(Studio.calls) == before_calls and Studio.loaded == {'owner-id': 'owner-model'})
            (d / 'gpu-models.json').write_text('{"v":1}', encoding='utf-8')
            run('recover')
            check(lane + ': пошкоджений знімок не дозволяє вивантажувати початкову модель',
                  (d / 'gpu-models.json').exists() and Studio.loaded == {'owner-id': 'owner-model'} and len(Studio.calls) == before_calls)
            (d / 'gpu-models.json').unlink()
            run('take')
            Studio.loaded['job-job-model'] = 'job-model'
            offline = run('offline')
            check(lane + ': Main прибирає залишок, навіть якщо fetch падає',
                  offline.returncode == 0 and (d / 'fetch-failed').exists() and Studio.loaded == {'owner-id': 'owner-model'}
                  and not (d / 'gpu-models.json').exists())
    print('ПІДСУМОК: провалів ' + str(bad))
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
