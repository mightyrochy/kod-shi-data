import json, os, subprocess, sys, time, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
root=Path.cwd(); out=root.parent/'evidence2386'; out.mkdir(exist_ok=True)
state=root.parent/'state2386'; state.mkdir(exist_ok=True)
shutil.copyfile(root/'аудит/жнива_5_3/повний-обхід_стан.tsv',state/'обхід_стан.tsv')
env=dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_PATH=str(Path.home()/'kod-shi-test-node/node_modules'))
commands=[([sys.executable,'-c',"import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"],root/'джерела','підготовка')]
commands += [([sys.executable,*args],root/'джерела',f'батарея-{i}') for i,args in enumerate([['стенд_знімок.py','--дим'],['тест_живого_шляху.py'],['тест_протоколу.py'],['прилади/розділи_гейтів.py'],['audit_contracts.py']],1)]
commands += [(['node','тест_показу.js'],root/'джерела','батарея-6')]
probes=sorted(p for p in (root/'джерела/проби').glob('каталог_зависла_крамниця*.py') if not p.stem.endswith(('_до','_проба')))
probes += [root/'джерела/проби'/f for f in ['каталог_рецепт_повтор.py','каталог_цикл_53.py','картка_вузол_5_1.py','каталог_обхід_стан.py','каталог_проблеми_г_стеля.py','каталог_проблеми_г_крамниці.py','каталог_проблеми_г_мова.py','каталог_проблеми_г_дублі.py','каталог_проблеми_г_формати.py']]
commands += [([sys.executable,str(p),*([str(state)] if p.stem=='каталог_обхід_стан' else [])],root,p.stem) for p in probes]
summary=[]
for cmd,cwd,name in commands:
    start=time.monotonic()
    with (out/(name+'.txt')).open('w',encoding='utf8') as log:
        log.write('КОМАНДА: '+subprocess.list2cmdline(cmd)+'\nТЕКА: '+str(cwd)+'\n'); log.flush()
        p=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
        log.write('\nКОД: '+str(p.returncode)+'\n')
    result=dict(назва=name,код=p.returncode,секунд=round(time.monotonic()-start,2))
    summary.append(result); print(json.dumps(result,ensure_ascii=False),flush=True)
(out/'підсумок.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print('Усього:',len(summary),'ненульових:',sum(x['код']!=0 for x in summary))
