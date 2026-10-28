"""Послідовно виконує стенди латки й зберігає повні журнали."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor


def main():
    """Виконує батарею або повтор обраних сценаріїв без втрати первинних доказів."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['проби', 'стенди', 'бюджет'])
    parser.add_argument('--дерево', type=Path, required=True, dest='work')
    parser.add_argument('--база', type=Path, dest='base')
    parser.add_argument('--лише', nargs='+', dest='only')
    parser.add_argument('--паралельно', type=int, choices=[1, 2, 3], default=1, dest='jobs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    work = args.work.resolve()
    out = Path(__file__).resolve().parent
    logs = out / 'журнали'
    logs.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    bash = (str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe')
            if os.name == 'nt' else shutil.which('bash'))
    results = []
    destination = out / ('результати-' + args.mode + '.json')
    previous = json.loads(destination.read_text(encoding='utf-8')) if args.only and destination.exists() else []
    if previous:
        original = out / ('результати-' + args.mode + '-початково.json')
        if not original.exists():
            shutil.copyfile(destination, original)

    def run(name, command, child_env=None):
        """Чекає завершення процесу й показує підсумок, не лишаючи його у фоні."""
        log = logs / (name + '.txt')
        original = logs / (name + '.початково.txt')
        if log.exists() and not original.exists():
            shutil.copyfile(log, original)
        result = subprocess.run(command, cwd=work, env=child_env or env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode('utf-8', errors='replace')
        log.write_text(json.dumps(command, ensure_ascii=False) + '\n' + output, encoding='utf-8')
        row = {'назва': name, 'код': result.returncode, '✓': output.count('✓'), '✗': output.count('✗')}
        results.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        if result.returncode:
            print(output[-3000:], flush=True)

    if args.mode in ('проби', 'бюджет'):
        for phase, source in [('ДО', args.base or root), ('ПІСЛЯ', work)]:
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            probe = 'бюджет.ps1' if args.mode == 'бюджет' else 'проба.ps1'
            command = ("[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false); & "
                       + quote(out / probe) + ' -SourceDir '
                       + quote(source / 'аудит/адаптери/gemini') + ' -Phase ' + quote(phase))
            name = 'бюджет-' + phase if args.mode == 'бюджет' else phase
            run(name, ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command])
    else:
        temp = Path(tempfile.gettempdir()) / 'live-pr-stend'
        temp.mkdir(exist_ok=True)
        env['TMPDIR'] = temp.resolve().as_posix()
        tests = sorted((work / 'аудит/адаптери/gemini/перевірка').glob('сценарії_*.sh'))
        assert len(tests) in (12, 13), len(tests)
        if args.only:
            assert set(args.only) <= {p.stem for p in tests}, args.only
            tests = [p for p in tests if p.stem in args.only]
        def scenario(script):
            # Кожен процес працює на передньому плані; незалежні стенди мають окремі TMPDIR та заглушки.
            case_env = dict(env)
            if args.jobs > 1:
                case_dir = Path(tempfile.mkdtemp(prefix='review-suite-'))
                case_env['TMPDIR'] = case_dir.resolve().as_posix()
            run(script.stem, [bash, '-lc', "bash '" + script.relative_to(work).as_posix() + "'"], case_env)
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(scenario, tests))
    merged = {row['назва']: row for row in previous}
    merged.update({row['назва']: row for row in results})
    final = list(merged.values())
    destination.write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(row['код'] or row['✗'] for row in final))


if __name__ == '__main__':
    sys.exit(main())
