"""Вимірює залишок після ConnectFailure й відокремлює історію REST від поточної нагоди."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


def main():
    """Запускає справжні worker голови на підробному REST, потім іншу смугу відновлення."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    spec = importlib.util.spec_from_file_location('gpu_test', source / 'перевірка/сценарії_gpu_моделі.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    # Лише перший GET отримує відмову з'єднання. Після нього REST доступний агенту й прибиранню.
    script = fixture.SCRIPT.replace(
        "throw (New-Object System.Net.WebException('стенд: LM Studio не слухає',",
        "Remove-Item -LiteralPath (Join-Path $TestDir 'down') -Force\n"
        "        throw (New-Object System.Net.WebException('стенд: LM Studio не слухає',")
    bad = 0
    with tempfile.TemporaryDirectory(prefix='review-2889-') as tmp, fixture.studio() as port:
        root = Path(tmp)
        worker = root / 'worker.ps1'
        worker.write_text(script, encoding='utf-8-sig')
        for lane in ('gemini', 'claude'):
            for mode in ('done', 'kill-tree'):
                run_dir = root / (lane + '-' + mode)
                run_dir.mkdir()
                (run_dir / 'agent.js').write_text(fixture.AGENT, encoding='utf-8')
                (run_dir / 'down').write_text('одна відмова', encoding='utf-8')
                fixture.Studio.loaded = {'owner-id': 'owner-model'}
                historical = ('POST', '/api/v1/models/unload', {'instance_id': 'старий-ID'})
                fixture.Studio.calls = [historical]
                fixture.Studio.fault = ''
                cmd = [shutil.which('powershell'), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                       '-File', str(worker), '-SourceDir', str(source), '-TestDir', str(run_dir),
                       '-Lane', lane, '-Port', str(port), '-TestMode', mode]
                if mode == 'done':
                    result = subprocess.run(cmd, capture_output=True, timeout=45)
                    if result.returncode:
                        raise RuntimeError(result.stdout.decode('utf-8', errors='replace') + result.stderr.decode('utf-8', errors='replace'))
                else:
                    with (run_dir / 'worker.log').open('wb') as output:
                        process = subprocess.Popen(cmd, stdout=output, stderr=output)
                        try:
                            until = time.monotonic() + 30
                            while not (run_dir / 'ready').exists() and process.poll() is None and time.monotonic() < until:
                                time.sleep(.05)
                            if not (run_dir / 'ready').exists():
                                raise RuntimeError('Агент не дійшов до завантаження')
                            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=True)
                            process.wait(timeout=10)
                        finally:
                            if process.poll() is None:
                                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, check=True)
                                process.wait(timeout=10)
                cmd[cmd.index('-Lane') + 1] = 'claude' if lane == 'gemini' else 'gemini'
                cmd[-1] = 'recover'
                subprocess.run(cmd, capture_output=True, timeout=45, check=True)
                calls = fixture.Studio.calls
                current = calls[1:]
                all_unloads = [c for c in calls if c[0] == 'POST' and c[1].endswith('/unload')]
                current_unloads = [c for c in current if c[0] == 'POST' and c[1].endswith('/unload')]
                lease = (run_dir / 'gpu-models.json').exists()
                new = sorted(k for k in fixture.Studio.loaded if k != 'owner-id')
                reproduced = (len(new) == 2 and not lease and not current_unloads
                              and fixture.Studio.loaded.get('owner-id') == 'owner-model')
                bad += not reproduced
                print(f'{lane}/{mode}: нових_ID={len(new)}; знімок={lease}; '
                      f'поточних_unload={len(current_unloads)}; відтворено={reproduced}', flush=True)
                if mode == 'done':
                    print(f'{lane}/історія: усіх_unload={len(all_unloads)}; поточних_unload={len(current_unloads)}; '
                          f'умова_стенда={not all_unloads}; умова_поточної_нагоди={not current_unloads}', flush=True)
                print('стан=' + json.dumps(fixture.Studio.loaded, ensure_ascii=False, sort_keys=True), flush=True)
    print('ПІДСУМОК відтворення: провалів ' + str(bad))
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
