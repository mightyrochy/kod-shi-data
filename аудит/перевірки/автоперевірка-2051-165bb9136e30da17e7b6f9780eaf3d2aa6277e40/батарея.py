import gzip, json, os, pathlib, subprocess, sys, time
root=pathlib.Path('C:/Users/gemini/gemini-runs/review-2051-165bb913')
out=pathlib.Path('C:/Users/gemini/gemini-runs/review-2051-evidence')
src=root/'джерела'
env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONHASHSEED='0',NODE_PATH=str(src/'node_modules'))
commands=[[sys.executable,*a] for a in [['стенд_знімок.py','--дим'],['тест_живого_шляху.py'],['тест_протоколу.py'],['прилади/розділи_гейтів.py'],['audit_contracts.py']]]
commands += [['node','тест_показу.js']]
commands += [[sys.executable,'проби/поділ_'+n+'_ast.py'] for n in ('palette','bridge','pipeline')]
commands += [[sys.executable,str(p.relative_to(src))] for p in sorted((src/'проби').glob('*.py')) if p.name.startswith(('pal_','col_','comp_')) and p.name not in ('pal_вердикт.py','pal_вимір.py')]
commands += [[sys.executable,'прилади/згорнути_дошку.py','--лише-перевірити']]
results=[]
for i,cmd in enumerate(commands,1):
    start=time.monotonic()
    p=subprocess.run(cmd,cwd=src,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=f'батарея-{i:02}.txt.gz'
    (out/log).write_bytes(gzip.compress(p.stdout,mtime=0))
    r=dict(команда=cmd[1:],код=p.returncode,секунд=round(time.monotonic()-start,1),журнал=log)
    results.append(r)
    (out/'батарея.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{i}/{len(commands)} код={p.returncode} {r["секунд"]}с '+ ' '.join(cmd[1:]),flush=True)
    if p.returncode:
        print(p.stdout.decode('utf-8',errors='replace')[-1800:],flush=True)
print('Завершено:',len(results),'Провалів:',sum(bool(r['код']) for r in results),flush=True)