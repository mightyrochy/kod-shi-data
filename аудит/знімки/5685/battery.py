import subprocess, os, json, time, pathlib, hashlib
p=pathlib.Path('/dev/shm/security5685'); r=p/'repo'; e={**os.environ,'TMPDIR':str(p/'tmp'),'GIT_NO_LAZY_FETCH':'1','NODE_PATH':str(r/'джерела/node_modules')}
commands=[('підготовка',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]),('дим',['python3','стенд_знімок.py','--дим']),('живий_шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('сімʼя',['python3','проби/захист_ci.py']),('збірка',['python3','build_артефакт.py','.',str(p/'assembled/index.html'),'показ-повний'])]
(p/'assembled').mkdir(exist_ok=True); out=[]
for name,cmd in commands:
 start=time.time()
 with (p/'evidence'/('батарея_'+name+'.log')).open('w') as f:
  v=subprocess.run(cmd,cwd=r/'джерела',env={**e,'LYUSTERKO_CATALOG':'повний'},stdout=f,stderr=subprocess.STDOUT,timeout=1500)
 out.append({'етап':name,'код':v.returncode,'секунд':round(time.time()-start,2),'команда':cmd,'SHA':e.get('SOURCE_SHA','5a8124b792e109d1cb01f87b1a7860900a158a65')}); (p/'evidence/battery.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)); print(name,v.returncode,flush=True)
 if v.returncode: break
(p/'evidence/battery-complete.json').write_text(json.dumps({'завершено':True,'успішно':len(out)==len(commands) and all(x['код']==0 for x in out)},ensure_ascii=False))
