import json,os,pathlib,subprocess,sys
root=pathlib.Path(__file__).parent; src=root/'review3749'/'джерела'; logs=root/'family3749'; logs.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONUTF8='1'); results=[]
for p in sorted((src/'проби').glob('заміна_*.py')):
    args=[sys.executable,'-X','utf8',str(p)]+(['каталог_brief.xml'] if p.name in ('заміна_4945.py','заміна_6616.py') else [])
    r=subprocess.run(args,cwd=src,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out=r.stdout.decode('utf-8',errors='replace').replace('\r\n','\n'); (logs/(p.stem+'.txt')).write_text(out,encoding='utf-8',newline='\n')
    results.append(dict(проба=p.name,код=r.returncode,команда=args)); (logs/'summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(p.name,'код',r.returncode,'\n'+'\n'.join(out.splitlines()[-3:]),flush=True)
