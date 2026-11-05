"""Повторює вимір наряду на збережених git-блобах без запуску обгортки чи моделі."""
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'повтор-20261105'
TMP = ROOT.parent / 'tmp' / 'no-report-repeat'
SOURCE = 'аудит/адаптери/gemini'
BASE = 'ec8ba921ab8ae6210420b84b438502d906ff81fd'
REVIEW = 'f46cabc1505f64f65e82a1626689f469e165ea7c'
CURRENT = 'f25a5608369414b91bf247c725b278d3d326b286'


def extract(rev, name):
    target = TMP / name
    target.mkdir(parents=True, exist_ok=True)
    archive = subprocess.check_output(['git', 'archive', rev, SOURCE], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(target, filter='data')
    return target / SOURCE


def run(name, command):
    result = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONUTF8='1'),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = result.stdout.decode('utf-8', errors='replace')
    (OUT / (name + '.txt')).write_text(output, encoding='utf-8', newline='\n')
    print(f'{name}: код {result.returncode}', flush=True)
    return dict(назва=name, команда=command, код=result.returncode)


def ps(name, script, source, *args):
    # Окремий процес Windows PowerShell 5.1 з явним UTF-8 для каналу stdout.
    quote = lambda value: "'" + str(value).replace("'", "''") + "'"
    command = ("[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); & "
               + quote(script) + ' -SourceDir ' + quote(source) + ' ' + ' '.join(args)
               + '; exit $LASTEXITCODE')
    return run(name, ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command])


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    before = extract(BASE, 'before')
    review = extract(REVIEW, 'review')
    current = extract(CURRENT, 'current')
    probe = Path(__file__).with_name('проба_знеособлення.ps1')
    results = [
        ps('знеособлення-до', probe, review),
        ps('знеособлення-після', probe, current),
        ps('розбір-до', current / 'перевірка/сценарії_no_report.ps1', before, '-Before'),
        ps('розбір-після', current / 'перевірка/сценарії_no_report.ps1', current),
        run('хеші', ['python', '-X', 'utf8', str(current / 'перевірка/перевірити_хеші.py'), '--диск']),
    ]
    old = (OUT / 'знеособлення-до.txt').read_text(encoding='utf-8')
    new = (OUT / 'знеособлення-після.txt').read_text(encoding='utf-8')
    assert old.count('=True') == 9 and old.count('=False') == 3, old
    assert new.count('=False') == 12 and '=True' not in new, new
    (OUT / 'результати.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(int(any(item['код'] for item in results)))
