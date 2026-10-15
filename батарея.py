import subprocess, json, os, time
from pathlib import Path
root=Path('/workspace/dress3710-next/джерела'); out=Path('/workspace/dress3710-tmp')
steps=[('дим',['python3','стенд_знімок.py','--дим']),('живий_шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('поділ',['python3','проби/поділ_жнива_ast.py'])]
results=[]
for name,cmd in steps:
    start=time.monotonic()
    with (out/(name+'.log')).open('w') as f: p=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT)
    result=dict(крок=name,код=p.returncode,секунд=round(time.monotonic()-start,1));results.append(result)
    (out/'батарея_результат.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
    print(json.dumps(result,ensure_ascii=False),flush=True)
