"""Незалежний повтор команд PR #2116 без виклику моделей."""
import json, os, pathlib, subprocess, sys, time

root = pathlib.Path('C:/Users/gemini/gemini-runs/review-2116-b995869')
out = pathlib.Path('C:/Users/gemini/gemini-runs/review-2116-evidence')
out.mkdir(exist_ok=True)
sources = root / 'джерела'
before = pathlib.Path('C:/Users/gemini/gemini-runs/tmp/dorobka-2093-do/джерела')
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_PATH='C:/Users/gemini/gemini-runs/w/codex-1/джерела/node_modules')
results = []
def run(name, cmd, cwd=root, tree=sources, expected=0):
    log = out / ('%02d.log' % len(results))
    start = time.monotonic()
    with log.open('w', encoding='utf-8') as stream:
        p = subprocess.run(list(map(str, cmd)), cwd=cwd, env=dict(env, E2_SOURCES=str(tree)), stdout=stream, stderr=subprocess.STDOUT)
    row = dict(name=name, command=list(map(str,cmd)), cwd=str(cwd), sources=str(tree), code=p.returncode, expected=expected, seconds=round(time.monotonic()-start,2), log=str(log))
    results.append(row)
    (out/'commands.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(row,ensure_ascii=False),flush=True)

for name, tree in [('ДО', before), ('ПІСЛЯ', sources)]:
    run(name+' механізм', [sys.executable,'-X','utf8',root/'аудит/проби/доробка-2093/механізм.py'],tree=tree,expected=1 if name=='ДО' else 0)
    run(name+' повтор', [sys.executable,'-X','utf8',sources/'проби/шлях_шар_повтор.py'],tree=tree,expected=1 if name=='ДО' else 0)
for filename in ['стенд_знімок.py','тест_живого_шляху.py','тест_протоколу.py','прилади/розділи_гейтів.py','audit_contracts.py']:
    run(filename,[sys.executable,'-X','utf8',filename]+(['--дим'] if filename=='стенд_знімок.py' else []),cwd=sources)
run('тест_показу.js',['node','тест_показу.js'],cwd=sources)
for filename in sorted((sources/'проби').glob('шлях_шар_*.py')):
    if filename.name != 'шлях_шар_повтор.py':
        run(filename.name,[sys.executable,'-X','utf8',filename],cwd=sources)
for filename in ['шлях_шар_репліка.js','шлях_шар_межі.js']:
    run(filename,['node',sources/'проби'/filename])
run('показ справжній ендпойнт',['node',root/'аудит/проби/доробка-2093/показ_повтор.js'])
run('сусідня сім’я: паспорт повтор',[sys.executable,'-X','utf8',sources/'проби/паспорт_повтор_8115.py'])
run('обходи',[sys.executable,'-X','utf8',root/'аудит/проби/доробка-2093/обходи.py'])
run('дошка',[sys.executable,'-X','utf8',sources/'прилади/згорнути_дошку.py','--лише-перевірити'])
run('досяжність',[sys.executable,'-X','utf8','досяжність.py'],cwd=sources)
print('НЕОЧІКУВАНИХ КОДІВ:',sum(r['code']!=r['expected'] for r in results),flush=True)
