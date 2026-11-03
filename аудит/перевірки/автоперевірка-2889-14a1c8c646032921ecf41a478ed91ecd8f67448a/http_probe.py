"""Відтворення втрати межі власності при реальній відмові TCP, без живого LM Studio."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-dir', type=Path, required=True)
source = parser.parse_args().source_dir
spec = importlib.util.spec_from_file_location('gpu_cases', source / 'перевірка/сценарії_gpu_моделі.py')
cases = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases)

with socket.socket() as unused:
    unused.bind(('127.0.0.1', 0))
    closed_port = unused.getsockname()[1]

with tempfile.TemporaryDirectory(prefix='review-http-') as tmp, cases.studio() as live_port:
    root = Path(tmp)
    script = root / 'worker.ps1'
    script.write_text(cases.SCRIPT, encoding='utf-8-sig')
    for lane in ['gemini', 'claude']:
        for case in ['server-off-at-start', 'server-off-at-cleanup']:
            d = root / (lane + '-' + case)
            d.mkdir()
            cases.Studio.loaded = {'owner-id': 'owner-model'}
            cases.Studio.calls = []
            cases.Studio.fault = ''

            def run(mode, port):
                result = subprocess.run([
                    shutil.which('powershell'), '-NoProfile', '-NonInteractive',
                    '-ExecutionPolicy', 'Bypass', '-File', str(script),
                    '-SourceDir', str(source.resolve()), '-TestDir', str(d),
                    '-Lane', lane, '-TestMode', mode, '-Port', str(port),
                ], capture_output=True, timeout=45)
                if result.returncode:
                    raise RuntimeError(result.stdout.decode('utf-8', errors='replace') +
                                       result.stderr.decode('utf-8', errors='replace'))

            run('take', closed_port if case == 'server-off-at-start' else live_port)
            lease = d / 'gpu-models.json'
            before = json.loads(lease.read_text(encoding='utf-8-sig'))['before']
            if case == 'server-off-at-start':
                run('recover', live_port)
                reproduced = before == [] and cases.Studio.loaded == {}
                print(f'{lane}/{case}: before={json.dumps(before)}; '
                      f'loaded={json.dumps(cases.Studio.loaded)}; '
                      f'unloads={json.dumps([c[2] for c in cases.Studio.calls if c[0] == "POST"])}; '
                      f'відтворено={reproduced}', flush=True)
            else:
                cases.Studio.loaded['job-id'] = 'job-model'
                run('recover', closed_port)
                reproduced = not lease.exists() and 'job-id' in cases.Studio.loaded
                print(f'{lane}/{case}: lease_exists={lease.exists()}; '
                      f'loaded={json.dumps(cases.Studio.loaded)}; '
                      f'відтворено={reproduced}', flush=True)
            assert reproduced
