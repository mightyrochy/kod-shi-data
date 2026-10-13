import subprocess,time,pathlib,json,sys,os
root=pathlib.Path.cwd();out=root/'.qa5090/media/батарея';out.mkdir(exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();res={'head':head,'jobs':[]}
commands=[('підготовка',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print(ч.забезпечити_чистим('каталог_повний.xml')); print(Ф.каталог_на_диску('каталог_brief.xml'))"]),('дим',['python3','стенд_знімок.py','--дим']),('живий-шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('міст',['node','тест_мосту.js']),('досяжність',['python3','досяжність.py'])]
for name,cmd in commands:
 start=time.monotonic()
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(cmd,cwd=root/'джерела',stdout=log,stderr=subprocess.STDOUT)
 r={'name':name,'exit':p.returncode,'seconds':round(time.monotonic()-start,1)};res['jobs'].append(r);(out/'підсумок.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(r,flush=True)
 if p.returncode:sys.exit(p.returncode)
assert '«НІХТО» = 0' in (out/'досяжність.log').read_text()
assert head==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
