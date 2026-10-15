import json, os, subprocess, sys, time
from pathlib import Path
root = Path(__file__).parent
repo = root / 'repo'
sources = repo / 'джерела'
out = root / 'докази'
out.mkdir(exist_ok=True)
env = dict(os.environ, TMPDIR=str(root / 'tmp'), NODE_PATH=str(sources / 'node_modules'), PYTHONDONTWRITEBYTECODE='1')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert head == '291a51b9b5ee0f4c6717b12d6194a7c68ff959b5'
statepath = out / 'стан_батареї.json'
state = json.loads(statepath.read_text()) if statepath.exists() else {'head': head, 'steps': []}
assert state['head'] == head
steps = [
 ('підготовка', ['python3', '-c', "import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]),
 ('синтаксис', ['python3', '-c', "import pathlib, ast, subprocess; files=list(pathlib.Path('.').rglob('*.py')); [ast.parse(p.read_text(encoding='utf-8'),filename=str(p)) for p in files if 'node_modules' not in p.parts]; js=[p for p in pathlib.Path('.').rglob('*.js') if 'node_modules' not in p.parts]; [subprocess.run(['node','--check',str(p)],check=True) for p in js]; print('Python',len(files),'JS',len(js))"]),
 ('поділ', ['python3', '-c', "import glob, subprocess; rc=[subprocess.run(['python3',p]).returncode for p in sorted(glob.glob('проби/поділ_*_ast.py'))]; print('ВПАЛО',sum(x!=0 for x in rc)); raise SystemExit(any(rc))"]),
 ('дим', ['python3', 'стенд_знімок.py', '--дим']),
 ('живий_шлях', ['python3', 'тест_живого_шляху.py']),
 ('протокол', ['python3', 'тест_протоколу.py']),
 ('розділи_гейтів', ['python3', 'прилади/розділи_гейтів.py']),
 ('контракти', ['python3', 'audit_contracts.py']),
 ('показ', ['node', 'тест_показу.js']),
 ('міст', ['node', 'тест_мосту.js']),
 ('досяжність', ['python3', 'досяжність.py']),
 ('прийняття_3541', ['python3', 'проби/прийняття_3541.py', str(root / 'джерело_3541.json')]),
 ('контроль_3541', ['python3', str(root / 'контроль_3541.py')]),
]
for name, command in steps:
    if any(s['name'] == name and s['rc'] == 0 for s in state['steps']):
        continue
    print('ПОЧАТОК', name, flush=True)
    start = time.monotonic()
    path = out / (name + '.log')
    with path.open('w') as stream:
        result = subprocess.run(command, cwd=sources, env=env, stdout=stream, stderr=subprocess.STDOUT)
    rc = result.returncode
    if name == 'досяжність' and '«НІХТО» = 0' not in path.read_text():
        rc = 1
    state['steps'].append(dict(name=name, rc=rc, seconds=round(time.monotonic()-start, 2)))
    statepath.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    print('КІНЕЦЬ', name, 'rc', rc, flush=True)
    if rc:
        print(path.read_text()[-3000:], flush=True)
        sys.exit(rc)
print('БАТАРЕЯ ЗАВЕРШЕНА', head, flush=True)
