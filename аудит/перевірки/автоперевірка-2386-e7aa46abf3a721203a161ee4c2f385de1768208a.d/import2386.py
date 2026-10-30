import json,os,pathlib,subprocess,sys,tempfile,time
task=pathlib.Path(__file__).resolve().parent
source=task/'pr2386/джерела'
env=dict(os.environ,PYTHONPATH=str(source))
result=[]
before={p.name for p in source.iterdir()}
with tempfile.TemporaryDirectory(prefix='імпорт2386_',dir=task) as folder:
    assert pathlib.Path(folder).resolve().is_relative_to(task)
    for module in ['траса_петлі','гейти_нові','measure_person_axis']:
        start=time.time()
        command=[sys.executable,'-c','import '+module]
        p=subprocess.run(command,cwd=folder,env=env,capture_output=True,text=True,timeout=10)
        item={'команда':' '.join(command),'код':p.returncode,'секунд':round(time.time()-start,2),'stderr':p.stderr[-200:]}
        result.append(item)
        print(json.dumps(item,ensure_ascii=False),flush=True)
    trash=[p.name for p in pathlib.Path(folder).iterdir() if p.name!='__pycache__' and p.suffix!='.pyc']
    print('Сторонні файли у порожній теці:',trash,flush=True)
added={p.name for p in source.iterdir()}-before-{'__pycache__'}
print('Нові файли у джерелах:',sorted(added),flush=True)
sys.exit(0 if all(r['код']==0 and r['секунд']<2 for r in result) and not trash and not added else 1)
