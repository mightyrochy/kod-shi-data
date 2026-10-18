"""Точний call 12 CPython і roundtrip кожного фактичного промпту пошуку бюджету."""
import os,sys,json,gzip,hashlib,time,re,base64,zipfile,io,shutil
from pathlib import Path
root=Path('/workspace/work/f2-210')
stage=root/'work/compact/runtime'; stage.mkdir(parents=True,exist_ok=True)
html=(root/'work/after/index.html').read_text()
zipfile.ZipFile(io.BytesIO(base64.b64decode(re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"',html)[1]))).extractall(stage)
for source in (root/'джерела').glob('*.py'):shutil.copy2(source,stage/source.name)
os.chdir(stage);sys.path.insert(0,str(stage))
import знання_дріт as ЗД, збирач_промптів as ЗП, пакет_моделі as П
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def expand(x):
    if isinstance(x,list):return [expand(v) for v in x]
    if isinstance(x,dict):
        if set(x)=={'cols','rows'}:return expand(ЗП.рядки_таблиці(x))
        return {k:expand(v) for k,v in x.items()}
    return x
original=ЗД.ущільнити; checks=[]
def checked(prompt,*args):
    result=original(prompt,*args)
    if 'knowledge_legend' in result:
        restored=ЗД.відновити(result)
        task=args[0] if args else 'task'; inp=args[1] if len(args)>1 else 'input'
        restored[task][inp].remove(ЗД.ОПИС)
        assert canonical(expand(restored))==canonical(expand(prompt)), 'lossless roundtrip failed'
        checks.append(sum(len(s['rows']) if 'rows' in s else 1 for s in result['knowledge_legend']['sections'].values()))
    return result
ЗД.ущільнити=checked
import bridge
rows=list(map(json.loads,gzip.open('/workspace/work/baseline02/аудит/проби/знімок_входи_сід3.jsonl.gz','rt')))
r=rows[12];start=time.time();out=bridge.виклик(r['ім'],json.loads(r['вхід']))
if isinstance(out,str):out=json.loads(out)
dest=root/'work/compact';dest.mkdir(exist_ok=True)
(dest/'call12.json').write_text(canonical(out))
summary={'seconds':round(time.time()-start,2),'roundtrips':len(checks),'max_roundtrip_items':max(checks,default=0),'prompts':{}}
for key in ['B','C']:
    text=out.get(key)
    if not text: continue
    data=json.loads(text);pool=ЗП.рядки_таблиці(data['pool']); budget=ЗД.додаток_бюджету(data)
    summary['prompts'][key]={'items':len(pool),'unique':len({x['n'] for x in pool}), 'bytes':len(text.encode()),'tokens':П.токенів(text),'pool_bytes':len(canonical(data['pool']).encode()),'pool_tokens':П.токенів(json.dumps(data['pool'],ensure_ascii=False,separators=(',',':'))),'knowledge_bytes':len(canonical(budget).encode()),'knowledge_tokens':П.токенів(json.dumps(budget,ensure_ascii=False,separators=(',',':'))),'budget':П.вага_пулу(text),'descriptors':len(data['knowledge_legend']['descriptors']),'facts':len(data['knowledge_legend']['facts'])}
(dest/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
