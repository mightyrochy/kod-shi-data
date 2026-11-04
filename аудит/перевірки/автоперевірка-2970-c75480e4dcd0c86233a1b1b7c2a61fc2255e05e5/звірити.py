"""Відтворює звірку латки, архівного виміру й Git-сценаріїв PR #2970."""
import contextlib
import importlib.util
import io
import tempfile
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess

ROOT = Path(tempfile.mkdtemp(prefix='review-2970-', dir=os.environ['TEMP']))
REPO = Path.cwd()
SHA = 'c75480e4dcd0c86233a1b1b7c2a61fc2255e05e5'
BASE = '067d98cc1f43782566e8b10117411a898a28b4d7'


def run(*args, cwd=REPO, env=None, data=None):
    return subprocess.run(args, cwd=cwd, env=env, input=data,
                          capture_output=True, check=True).stdout


def git(*args, cwd=REPO):
    return run('git', *args, cwd=cwd).decode('utf-8').strip()


SOURCE = '1e790228089f79419c3f6f89641c180728608060'
for name in ('api.json.gz', 'checkout.patch', 'перевірити.py'):
    (ROOT / name).write_bytes(run('git', 'show', SOURCE + ':аудит/латки/CI-checkout-усі-гілки/' + name))
spec = importlib.util.spec_from_file_location('source_probe', ROOT / 'перевірити.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
fixture = ROOT / 'стенд'
with contextlib.redirect_stdout(io.StringIO()):
    probe.перевірити('C:/Program Files/Git/bin/bash.exe', fixture)

snapshot = json.loads(gzip.decompress((ROOT / 'api.json.gz').read_bytes()))
runs = snapshot['запуски']
attempts = snapshot['спроби']
assert len({r['id'] for r in runs}) == 868
assert all('2026-10-31T00:00:00Z' <= r['created_at'] <= '2026-11-03T23:59:59Z' for r in runs)
assert {(a['run_id'], a['attempt']) for a in attempts} == {
    (r['id'], n) for r in runs for n in range(1, r['run_attempt'] + 1)}
assert len(attempts) == 871
jobs = [j for a in attempts for j in a['jobs']]
assert len({j['id'] for j in jobs}) == len(jobs) == 7624
assert set(snapshot['анотації']) == {str(j['id']) for j in jobs if j['conclusion'] in ('failure', 'cancelled')}
durations = []
timeouts = 0
for job in jobs:
    messages = snapshot['анотації'].get(str(job['id']), [])
    timeouts += any(re.search(r'job.*(?:exceeded.*maximum execution time|timed out)',
                             m['message'], re.I) for m in messages)
    for step in job.get('steps', []):
        if 'actions/checkout@' in step['name'] and not step['name'].startswith('Post ') and step['conclusion'] != 'skipped':
            durations.append((dt.datetime.fromisoformat(step['completed_at']) -
                              dt.datetime.fromisoformat(step['started_at'])).total_seconds())
assert (len(durations), statistics.median(durations), max(durations), timeouts) == (5122, 87, 5025, 81)
summary = {'запусків': len(runs), 'спроб': len(attempts), 'jobs': len(jobs),
           'checkout': len(durations), 'медіана_с': statistics.median(durations),
           'максимум_с': max(durations), 'таймаутів': timeouts,
           'анотації_jobs': len(snapshot['анотації']),
           'api_sha256': hashlib.sha256((ROOT / 'api.json.gz').read_bytes()).hexdigest()}

applied = ROOT / 'applied-lf'
(applied / '.github/workflows').mkdir(parents=True)
(applied / '.github/workflows/zbirka.yml').write_bytes(run('git', 'show', BASE + ':.github/workflows/zbirka.yml'))
run('git', '-c', 'core.autocrlf=false', 'apply', '--check', str(ROOT / 'checkout.patch'), cwd=applied)
run('git', '-c', 'core.autocrlf=false', 'apply', str(ROOT / 'checkout.patch'), cwd=applied)
for name in ('.github/workflows/zbirka.yml', '.github/scripts/checkout-history.sh'):
    assert (applied / name).read_bytes() == run('git', 'show', SHA + ':' + name)
summary['застосована_латка_тотожна_голові'] = True

# Додаткові випадки: main просунувся після створення PR; відсутні обидві змінні;
# main перемотано назад. Виконується скрипт саме перевіреної голови.
origin = fixture / 'origin.git'
copy = fixture / 'copy-0'
old_main = git('rev-parse', 'refs/heads/main', cwd=origin)
tree = git('rev-parse', old_main + '^{tree}', cwd=origin)
new_main = git('commit-tree', tree, '-p', old_main, '-m', 'main після PR', cwd=origin)
git('update-ref', 'refs/heads/main', new_main, cwd=origin)
head = git('rev-parse', 'HEAD', cwd=copy)
env = {k: v for k, v in os.environ.items() if k not in
       {'GITHUB_SHA', 'BASE_REF', 'GITHUB_TOKEN', 'GH_TOKEN'}}
env.update(GITHUB_SHA=head, BASE_REF=old_main)
script = str(applied / '.github/scripts/checkout-history.sh')
bash = 'C:/Program Files/Git/bin/bash.exe'
run(bash, '-n', script)
run(bash, script, cwd=copy, env=env)
assert git('rev-parse', 'origin/main', cwd=copy) == new_main
assert git('rev-parse', 'HEAD', cwd=copy) == head
env.pop('GITHUB_SHA')
env.pop('BASE_REF')
run(bash, script, cwd=copy, env=env)
assert git('rev-parse', 'HEAD', cwd=copy) == head
git('update-ref', 'refs/heads/main', old_main, cwd=origin)
run(bash, script, cwd=copy, env=env)
assert git('rev-parse', 'origin/main', cwd=copy) == old_main
assert git('for-each-ref', '--format=%(refname)', 'refs/remotes', cwd=copy) == 'refs/remotes/origin/main'
assert not git('tag', cwd=copy)
summary['додаткових_випадків_пройдено'] = 3
summary['фікстура_виконавця'] = json.loads((ROOT / 'локальна_перевірка.json').read_text(encoding='utf-8'))
(ROOT / 'незалежні_числа.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
