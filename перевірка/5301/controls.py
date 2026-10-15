import importlib.util,json,sys,re,subprocess,os
from pathlib import Path
p=Path('/dev/shm/nested5301');sys.path.insert(0,str(p/'repo/джерела'))
import мовний_шар as М
base=subprocess.check_output(['git','--git-dir=/workspace/scratch/update999/repo','show','47ac855c51b249c6112f0ba0ca64924a50bc32e4:джерела/мовний_шар.py'],env=dict(os.environ,GIT_NO_LAZY_FETCH='1'))
(p/'base.py').write_bytes(base);s=importlib.util.spec_from_file_location('база',p/'base.py');Б=importlib.util.module_from_spec(s);s.loader.exec_module(Б)
changed=[]; rows=[]
for f in sorted((p/'raw').rglob('*_мовний_шар.txt')):
 raw=f.read_text()
 if '\nТЕКСТИ:\n' not in raw:continue
 mark,_=json.JSONDecoder().raw_decode(raw.split('\nТЕКСТИ:\n',1)[1].lstrip());mark=[dict(r,ключ=str(r['н'])) for r in mark]
 answer=re.split(r'── ВІДПОВІДЬ[^\n]*\n',raw,maxsplit=1)[1];before=Б.прийняти(mark,answer);after=М.прийняти(mark,answer)
 if before!=after:changed.append(str(f.relative_to(p/'raw')))
 rows.append({'path':str(f.relative_to(p/'raw')),'before':before,'after':after})
(p/'comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));assert len(changed)==2
mark=[{'н':3,'ключ':'a','текст':'A'},{'н':9,'ключ':'b','текст':'B'}]
cases=[('wrapper',{'3':{'текст':'three','9':'nine'}},{'a':'three','b':'nine'}),('translation',{'3':{'переклад':'three'},'9':{'translation':'nine'}},{'a':'three','b':'nine'}),('plain',{'3':'three','9':'nine'},{'a':'three','b':'nine'}),('forms',[{'n':9,'text':'nine'},{'н':3,'текст':'three'}],{'a':'three','b':'nine'}),('root_priority',{'3':{'текст':'three','9':'other'},'9':'nine'},{'a':'three','b':'nine'}),('self_collision',{'3':{'3':'wrong','9':'wrong','текст':'three'}},{'a':'three','b':'B'}),('opaque',{'3':{'other':'wrong'},'else':{'9':'wrong'}},{'a':'A','b':'B'}),('unknown',{'3':{'translation':'unknown'},'9':{'переклад':''}},{'a':'A','b':'B'})]
for name,obj,want in cases:
 got=М.прийняти(mark,json.dumps(obj,ensure_ascii=False));assert got['тексти']==want,(name,got);print(name,'PASS',got['без_відповіді'])
print('Actual records: changed=2, unchanged=17; full outputs compared; source prompt unchanged=',Б.ПРОМПТ_ВИХОДУ==М.ПРОМПТ_ВИХОДУ)
assert Б.ПРОМПТ_ВИХОДУ==М.ПРОМПТ_ВИХОДУ
