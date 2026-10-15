import argparse, datetime, gzip, hashlib, json, os, pathlib, re, subprocess, sys, time

P = pathlib.Path('/dev/shm/pachka-1510-4')
G = P / 'repo'
W = P / 'work'
S = W / 'джерела'
D = P / 'proof'
SHA = '751458dc348f9299405008e9e827ce92943f75f4'
TREE = '52b3fc857ac0568cc5afa7b3bb595272150e9869'
MAIN = '32395d4239a2758c3293ee4e605364e28bc8dc94'
SOURCES = {'1059': '24b40122144b20af0904e8bf101e1f609b54ada3', '1060': 'fca5421d9cebe32e547d48ccaeec8352644e2e44'}
E = {**os.environ, 'GIT_NO_LAZY_FETCH': '1', 'TMPDIR': str(P / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': str(P / 'pycache'), 'NODE_PATH': '/workspace/kod-shi-data/джерела/node_modules', 'PATH': '/workspace/liusterko-tools/bin:/workspace/liusterko-tools/node22/node_modules/node/bin:' + os.environ['PATH']}

def git(*args, input=None):
    return subprocess.check_output(['git', '--git-dir=' + str(G), *args], env=E, input=input)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def blob_sha(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def resources():
    return {name: pathlib.Path('/sys/fs/cgroup', name).read_text().strip() for name in ['memory.current', 'memory.max', 'memory.events']}

def save(name, data):
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode()
    (D / name).write_bytes(raw)
    if name == 'battery-checkpoint.json':
        assert len(raw) < 50000
        pathlib.Path('/workspace/scratch/pachka-1510-4-checkpoint.json').write_bytes(raw)

def stages():
    syntax = "import pathlib,py_compile,subprocess,sys; fs=[p for p in pathlib.Path('.').rglob('*') if p.is_file() and 'node_modules' not in p.parts]; py=[p for p in fs if p.suffix=='.py']; js=[p for p in fs if p.suffix=='.js']; [py_compile.compile(str(p),doraise=True) for p in py]; rs=[subprocess.run(['node','--check',str(p)]).returncode for p in js]; print('Синтаксис Python',len(py),'JS',len(js),'збоїв',sum(x!=0 for x in rs)); sys.exit(any(rs))"
    split = "import pathlib,subprocess,sys; fs=sorted(pathlib.Path('проби').glob('поділ_*_ast.py')); rs=[subprocess.run([sys.executable,str(f)]).returncode for f in fs]; print('Проби поділу',len(fs),'ВПАЛО',sum(x!=0 for x in rs)); sys.exit(any(rs))"
    prep = "import чистка_каталогу as ч,feed as Ф; print('фід:',ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:',Ф.каталог_на_диску('каталог_brief.xml'))"
    return [('01-синтаксис', [sys.executable, '-c', syntax]), ('02-поділ', [sys.executable, '-c', split]), ('03-каталоги', [sys.executable, '-c', prep]), ('04-дим', [sys.executable, 'стенд_знімок.py', '--дим']), ('05-живий-шлях', [sys.executable, 'тест_живого_шляху.py']), ('06-протокол', [sys.executable, 'тест_протоколу.py']), ('07-гейти', [sys.executable, 'прилади/розділи_гейтів.py']), ('08-контракти', [sys.executable, 'audit_contracts.py']), ('09-показ', ['node', 'тест_показу.js']), ('10-міст', ['node', 'тест_мосту.js']), ('11-досяжність', [sys.executable, 'досяжність.py']), ('12-сімя-3350', [sys.executable, 'проби/сімї_нетранзитивність_3350.py']), ('13-сімя-3710', [sys.executable, 'проби/фіг4_джерело_3710.py', str(W / 'каталог_повний.xml.gz')])]

def prepare():
    assert git('rev-parse', SHA + '^{tree}').decode().strip() == TREE
    for ref in [MAIN, *SOURCES.values()]:
        git('merge-base', '--is-ancestor', ref, SHA)
    expected = json.loads((P / 'inputs-expected.json').read_text())
    assert sum(x['path'].startswith('джерела/') for x in expected) == 1542
    assert next(x['sha'] for x in expected if x['path'] == 'каталог_повний.xml.gz') == '04d84f5556cf4654f10a594128c3531530773649'
    for x in expected:
        git('cat-file', '-e', x['sha'])
    provenance = {'pr': 1079, 'sha': SHA, 'tree': TREE, 'main': MAIN, 'sources': SOURCES, 'source_entries': 1542, 'inputs_sha256': sha256((P / 'inputs-expected.json').read_bytes()), 'workflow_blob': next(x['sha'] for x in expected if x['path'] == '.github/workflows/zbirka.yml'), 'fixture_root_blob': '04d84f5556cf4654f10a594128c3531530773649', 'fixture_root_sha256': '71cffbd27a4916db4676cc57cfd2174e94288a3f32458c4dda4dab0e5b877331', 'raw_gunzip_bytes': 50813000, 'raw_gunzip_sha256': '75d5362253e1ebdd47bfc91e8bdbee08cc81d98a43ff6be4d8d74bc9c946150e', 'raw_offers': 12426, 'runtime_items': 12280, 'previous_sha': '965b7e0a09b9b66798b6980b5e031ac1752ac212', 'previous_stages_started': 0, 'composition_content_comment': 'W2 DIRECT PASS /root/review_updates_1045_1056', 'update_final_comment': None, 'independent_update_archive': '/dev/shm/qa-updates-1077/proof/1079.json', 'author_update_archive': '/dev/shm/update-after-1077/pushed-1079.json', 'ui_native_scope': 'N/A: власного UI немає; спільний main UI незалежно перевірено на #1078, окремим native #1079 не називаємо', 'commands': dict(stages()), 'status': 'PREPARED_WAIT_DIRECT_TOKEN_1078', 'battery_started': False, 'model_calls': 0, 'own_background_jobs': 0, 'resources': resources()}
    save('battery-provenance.json', provenance)
    save('battery-checkpoint.json', {'sha': SHA, 'tree': TREE, 'status': provenance['status'], 'stages': {}, 'battery_started': False, 'own_background_jobs': 0, 'prepared_at': stamp()})
    print('ПІДГОТОВЛЕНО, батарея0; чекає прямого ресурсу #1078', SHA, flush=True)

def export():
    W.mkdir(exist_ok=True)
    (W / '.git').write_text('gitdir: ' + str(G) + '\n')
    expected = json.loads((P / 'inputs-expected.json').read_text())
    verified = []
    for x in expected:
        target = W / x['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if x['path'] == 'каталог_повний.xml.gz':
            shared = pathlib.Path('/workspace/kod-shi-data/каталог_повний.xml.gz')
            assert blob_sha(shared.read_bytes()) == x['sha']
            if not target.exists():
                target.symlink_to(shared)
        elif not target.exists() or blob_sha(target.read_bytes()) != x['sha']:
            data = git('cat-file', 'blob', x['sha'])
            assert blob_sha(data) == x['sha']
            target.write_bytes(data)
        data = target.read_bytes()
        assert blob_sha(data) == x['sha'], x['path']
        verified.append({**x, 'bytes': len(data), 'sha256': sha256(data)})
    git('update-ref', 'refs/heads/codex/pachka-1510-4', SHA)
    git('symbolic-ref', 'HEAD', 'refs/heads/codex/pachka-1510-4')
    git('config', 'core.bare', 'false')
    git('config', 'core.worktree', str(W))
    assert git('rev-parse', 'HEAD').decode().strip() == SHA
    assert all((pathlib.Path(E['NODE_PATH']) / x).is_dir() for x in ['jsdom', 'fake-indexeddb'])
    save('inputs-verified.json', verified)
    return sha256(json.dumps(verified, ensure_ascii=False, sort_keys=True).encode())

def run(token_path):
    token = json.loads(pathlib.Path(token_path).read_text())
    assert token['holder'] == 'build_batch_1510_4' and token['sha'] == SHA and token['authorized_by'] in ['root', 'build_batch_1510_3'], token
    save('heavy-token.json', token)
    state = json.loads((D / 'battery-checkpoint.json').read_text())
    assert state['sha'] == SHA and state['tree'] == TREE
    assert state['status'] != 'COMPLETED', 'Завершену батарею не повторювати'
    state.update(status='RUNNING', battery_started=True, own_background_jobs=1)
    save('battery-checkpoint.json', state)
    if 'verified_input_sha256' not in state:
        state['verified_input_sha256'] = export()
        save('battery-checkpoint.json', state)
    for name, command in stages():
        previous = state['stages'].get(name, {})
        if previous.get('status') == 'completed':
            assert previous['rc'] == 0, ('Завершений збій потребує рішення', name)
            continue
        assert git('rev-parse', 'HEAD').decode().strip() == SHA
        log = D / (name + '.log')
        rec = {'status': 'running', 'sha': SHA, 'input_sha256': state['verified_input_sha256'], 'command': command, 'started_at': stamp(), 'log': log.name, 'resources_before': resources()}
        state['stages'][name] = rec
        state['current'] = name
        save('battery-checkpoint.json', state)
        print('СТАРТ', name, SHA, flush=True)
        start = time.monotonic()
        with log.open('ab' if previous else 'wb') as handle:
            if previous:
                handle.write('\nПРОДОВЖЕННЯ ЛИШЕ НЕЗАВЕРШЕНОГО ЕТАПУ\n'.encode())
            rc = subprocess.call(command, cwd=S, env=E, stdout=handle, stderr=subprocess.STDOUT)
        after = git('rev-parse', 'HEAD').decode().strip()
        assert after == SHA
        if name == '11-досяжність' and rc == 0:
            hits = re.findall(r'«НІХТО» = (\d+)', log.read_text())
            assert hits and hits[-1] == '0', hits
            (D / 'досяжність-звіт.md').write_bytes((S / 'аудит/ДОСЯЖНІСТЬ.md').read_bytes())
            (S / 'аудит/ДОСЯЖНІСТЬ.md').write_bytes(git('show', SHA + ':джерела/аудит/ДОСЯЖНІСТЬ.md'))
        rec.update(status='completed', rc=rc, after_sha=after, seconds=round(time.monotonic() - start, 2), finished_at=stamp(), log_sha256=sha256(log.read_bytes()), resources_after=resources())
        state['current'] = None
        if rc:
            state.update(status='FAILED', own_background_jobs=0)
        save('battery-checkpoint.json', state)
        print('КІНЕЦЬ', name, 'rc', rc, flush=True)
        if rc:
            raise SystemExit(rc)
    state.update(status='COMPLETED', finished_at=stamp(), own_background_jobs=0)
    save('battery-checkpoint.json', state)
    print('БАТАРЕЯ ЗАВЕРШЕНА', SHA, flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--token')
    args = parser.parse_args()
    D.mkdir(exist_ok=True)
    if args.action == 'prepare':
        prepare()
    else:
        assert args.token
        run(args.token)
