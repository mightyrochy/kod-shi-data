import ast,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
root=Path('/workspace/dress3710-next/джерела');out=Path('/workspace/dress3710-tmp');os.chdir(root)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
steps=[('гейти_продовження_146_147',['python3',str(out/'гейти_продовження.py')]),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('поділ',['python3','проби/поділ_жнива_ast.py'])]
results=json.loads((out/'батарея_результат.json').read_text())
for name,cmd in steps:
    start=time.monotonic()
    with (out/(name+'.log')).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    result=dict(крок=name,код=p.returncode,секунд=round(time.monotonic()-start,1),голова=head);results.append(result)
    (out/'батарея_результат.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False),flush=True)
