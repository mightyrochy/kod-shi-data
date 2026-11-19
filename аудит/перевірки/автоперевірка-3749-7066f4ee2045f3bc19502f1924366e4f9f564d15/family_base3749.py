import json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).parent; src=root/'base3749'/'джерела'; logs=root/'family-base3749'; logs.mkdir(exist_ok=True)
head=json.loads((root/'family3749/summary.json').read_text(encoding='utf-8')); results=[]
for entry in head:
    if not entry['код']:continue
    name=entry['проба']; args=[sys.executable,'-X','utf8',str(src/'проби'/name)]
    p=subprocess.run(args,cwd=src,env=dict(os.environ,PYTHONUTF8='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out=p.stdout.decode('utf-8',errors='replace').replace('\r\n','\n');(logs/(pathlib.Path(name).stem+'.txt')).write_text(out,encoding='utf-8',newline='\n')
    results.append(dict(проба=name,код=p.returncode,команда=args));print(name,'ДО',p.returncode,'ПІСЛЯ',entry['код'],'\n'+'\n'.join(out.splitlines()[-2:]),flush=True)
    (logs/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
