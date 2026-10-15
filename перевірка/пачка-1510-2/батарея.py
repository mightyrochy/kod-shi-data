import ast, json, os, subprocess, sys, time
from pathlib import Path

root = Path(__file__).parent
repo = root / 'repo'
out = root / 'evidence'
sources = repo / 'джерела'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert head == 'f2e099e85f8b2238e9898ec3833d6c80f6f5ba20'
statepath = out / 'стан_батареї.json'
assert not statepath.exists(), 'Повтор завершених етапів заборонений'
env = dict(os.environ, TMPDIR=str(root / 'tmp'), NODE_PATH='/workspace/kod-shi-data/джерела/node_modules', PYTHONDONTWRITEBYTECODE='1')
state = dict(head=head, status='running', started=time.time(), steps=[])
steps = [
 ('підготовка', ['python3', '-c', "import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]),
 ('синтаксис', ['python3', '-c', "import pathlib,ast,subprocess; files=[p for p in pathlib.Path('.').rglob('*.py') if 'node_modules' not in p.parts]; [ast.parse(p.read_text(encoding='utf-8'),filename=str(p)) for p in files]; js=[p for p in pathlib.Path('.').rglob('*.js') if 'node_modules' not in p.parts]; [subprocess.run(['node','--check',str(p)],check=True) for p in js]; print('Python',len(files),'JS',len(js))"]),
 ('поділ', ['python3', '-c', "import glob,subprocess; rc=[subprocess.run(['python3',p]).returncode for p in sorted(glob.glob('проби/поділ_*_ast.py'))]; print('ВПАЛО',sum(x!=0 for x in rc)); raise SystemExit(any(rc))"]),
 ('дим', ['python3', 'стенд_знімок.py', '--дим']),
 ('живий_шлях', ['python3', 'тест_живого_шляху.py']),
 ('протокол', ['python3', 'тест_протоколу.py']),
 ('розділи_гейтів', ['python3', 'прилади/розділи_гейтів.py']),
 ('контракти', ['python3', 'audit_contracts.py']),
 ('показ', ['node', 'тест_показу.js']),
 ('міст', ['node', 'тест_мосту.js']),
 ('досяжність', ['python3', 'досяжність.py']),
]
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
for name, command in steps:
    print('ПОЧАТОК', name, flush=True)
    state['current'] = name
    statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    start = time.monotonic()
    logpath = out / (name + '.log')
    with logpath.open('w') as log:
        rc = subprocess.run(command,cwd=sources,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    if name == 'досяжність':
        rc = rc or int('«НІХТО» = 0' not in logpath.read_text())
        (out / 'ДОСЯЖНІСТЬ.md').write_bytes((sources / 'аудит/ДОСЯЖНІСТЬ.md').read_bytes())
        subprocess.run(['git','restore','--source=HEAD','джерела/аудит/ДОСЯЖНІСТЬ.md'],cwd=repo,check=True)
    state['steps'].append(dict(name=name,command=command,rc=rc,seconds=round(time.monotonic()-start,2),finished=True))
    statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print('КІНЕЦЬ', name, 'rc', rc, flush=True)
    if rc:
        state['status']='failed'
        statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        print(logpath.read_text()[-4000:],flush=True)
        sys.exit(rc)
state.update(status='finished',current=None,finished=time.time())
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
print('БАТАРЕЯ ЗАВЕРШЕНА', head,flush=True)
