import datetime, hashlib, json, os, pathlib, subprocess, sys, time
P = pathlib.Path('/dev/shm/listquote5310')
R = P / 'repo'
SHA = 'e20db6ad71069116b3a9e189c85c394efbccaa67'
E = {**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'TMPDIR': str(P / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1', 'NODE_PATH': '/workspace/kod-shi-data/джерела/node_modules'}
assert sys.argv[1:] == ['root-token'], 'Потрібен прямий RAM-токен координатора'
assert subprocess.check_output(['git', '-C', str(R), 'rev-parse', 'HEAD'], env=E).decode().strip() == SHA
def git(*args):
    return subprocess.check_output(['git', '-C', str(R), *args], env=E)
for rel in ['каталог_повний.xml.gz', 'джерела/каталог_brief.xml.gz', 'джерела/каталог_збагачення.json.gz', 'джерела/каталог_кадри.json.gz', 'джерела/каталог_показ.json.gz']:
    dst = R / rel
    data = git('show', SHA + ':' + rel)
    dst.write_bytes(data)
manifest = json.loads((P / 'inputs-newhead.json').read_text())
assert manifest['sha'] == SHA
for entry in manifest['inputs']:
    data = (R / entry['path']).read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == entry['sha'], entry['path']
statepath = P / 'battery-checkpoint.json'
state = json.loads(statepath.read_text()) if statepath.exists() else {'sha': SHA, 'stages': {}, 'started': datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert state['sha'] == SHA
prep = "import чистка_каталогу as ч,feed as Ф;print('фід:',ч.забезпечити_чистим('каталог_повний.xml'));print('фікстура:',Ф.каталог_на_диску('каталог_brief.xml'))"
stages = [('01-каталоги', [sys.executable, '-c', prep]), ('02-дим', [sys.executable, 'стенд_знімок.py', '--дим']), ('03-живий-шлях', [sys.executable, 'тест_живого_шляху.py']), ('04-протокол', [sys.executable, 'тест_протоколу.py']), ('05-гейти', [sys.executable, 'прилади/розділи_гейтів.py']), ('06-контракти', [sys.executable, 'audit_contracts.py']), ('07-показ', ['node', 'тест_показу.js'])]
for name, command in stages:
    if name in state['stages']:
        assert state['stages'][name]['rc'] == 0, 'Завершений збій потребує окремого рішення'
        continue
    log = P / (name + '.log')
    print('СТАРТ', name, flush=True)
    start = time.monotonic()
    with log.open('wb') as f:
        rc = subprocess.call(command, cwd=R / 'джерела', env=E, stdout=f, stderr=subprocess.STDOUT)
    state['stages'][name] = {'rc': rc, 'seconds': round(time.monotonic() - start, 2), 'command': command, 'log': log.name}
    statepath.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print('КІНЕЦЬ', name, rc, flush=True)
    if rc:
        raise SystemExit(rc)
state['finished'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
statepath.write_text(json.dumps(state, ensure_ascii=False, indent=2))
print('БАТАРЕЮ ЗАВЕРШЕНО', SHA, flush=True)
