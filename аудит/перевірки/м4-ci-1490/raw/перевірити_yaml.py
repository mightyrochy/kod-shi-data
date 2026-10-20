import yaml,copy,re,subprocess
from types import SimpleNamespace as NS
base='/workspace/work/qa-m4-2010/'
a=yaml.load(open(base+'before.yml'),Loader=yaml.BaseLoader);b=yaml.load(open(base+'after.yml'),Loader=yaml.BaseLoader)
def clean(x):
 x=copy.deepcopy(x)
 if isinstance(x,dict):
  if 'run' in x:x['run']='\n'.join(l for l in x['run'].splitlines() if not l.lstrip().startswith('#'))
  return {k:clean(v) for k,v in x.items()}
 if isinstance(x,list):return [clean(v) for v in x]
 return x
for key in ('name','on','permissions','concurrency'): assert a[key]==b[key],key
for name in ('zminy','perevirka','rozdily','pravyla'):
 old=clean(a['jobs'][name]);new=clean(b['jobs'][name]);new.pop('permissions')
 for s in new['steps']:
  if 'actions/checkout@' in s.get('uses',''):assert s['with'].pop('persist-credentials')=='false'
 assert old==new,name
 print(name,': усі',len(old['steps']),'наявні steps, умови й команди збережено; лише read/no-persist і вилучення comments')
old=clean(a['jobs']['zbirka']);new=clean(b['jobs']['zbirka'])
new['steps'][0]['with'].pop('persist-credentials');new['steps'][0].pop('with')
assert old['steps'][:5]==new['steps'][:5]
assert len(new['steps'])==6 and 'upload-artifact@' in new['steps'][-1]['uses']
assert {k:v for k,v in old.items() if k not in ('steps','permissions')}=={k:v for k,v in new.items() if k not in ('steps','permissions')}
print('zbirka: 5 попередніх PR steps збережено; 1 transport upload додано; залежності й умова незмінні')
pub=clean(b['jobs']['publish'])
for x,y in zip(old['steps'][5:],pub['steps'][3:]):
 if x.get('if')=="github.event_name != 'pull_request' && github.ref == 'refs/heads/main'":x.pop('if')
 assert x==y,(x.get('name'),y.get('name'))
assert len(pub['steps'])==6
print('publish: 3 publication steps перенесено без зміни команд; охоплено job-level push-main guard')
assert b['jobs']['zbirka']['steps'][-1]['with']['path'].splitlines()==['index.html','джерела/аудит/ДОСЯЖНІСТЬ.md']
assert pub['steps'][2]['with']['name']==b['jobs']['zbirka']['steps'][-1]['with']['name']
assert len(re.findall(r'python3 build_артефакт.py',open(base+'after.yml').read()))==1
assert not re.search('м4_ci_запис|GH_TOKEN|m4-probe',open(base+'after.yml').read())
print('збірка: один виклик; transport: index.html+reach, same-run+same-SHA; тимчасову пробу прибрано')
for name,j in b['jobs'].items():
 checks=[s for s in j['steps'] if 'actions/checkout@' in s.get('uses','')];assert len(checks)==1
 if name!='publish':assert j['permissions']=={'contents':'read'} and checks[0]['with']['persist-credentials']=='false'
 else:assert j['permissions']=={'contents':'write'}
print('5 read jobs без persist; 1 write job лише publish')
def evaluate(expr,event,ref,z='success',p='success',r='success',board='false',built='success',cancelled=False):
 expr=expr.removeprefix('${{').removesuffix('}}').strip().replace('&&',' and ').replace('||',' or ').replace('!cancelled()','not cancelled()')
 return eval(expr,{'__builtins__':{}},{'github':NS(event_name=event,ref=ref),'needs':NS(zminy=NS(result=z,outputs=NS(lyshe_doshka=board)),perevirka=NS(result=p),rozdily=NS(result=r),zbirka=NS(result=built)),'cancelled':lambda:cancelled})
for event,ref,board,p,r,built,expected in [('pull_request','refs/pull/1490/merge','false','success','success','success',False),('push','refs/heads/main','false','success','success','success',True),('push','refs/heads/main','true','skipped','skipped','success',True),('workflow_dispatch','refs/heads/main','false','success','success','success',False),('push','refs/heads/other','false','success','success','success',False),('push','refs/heads/main','false','failure','success','skipped',False)]:
 result=evaluate(pub['if'],event,ref,board=board,p=p,r=r,built=built);assert result==expected
 print('publish condition:',event,ref,'board='+board,'perevirka='+p,'zbirka='+built,'→',result)
assert not evaluate(pub['if'],'push','refs/heads/main',cancelled=True)
print('cancelled push → publish false')
repo='/workspace/kod-shi-data';oldsha='b2272977da85a2e581b5d6d8a657012a61ba6dd0';newsha='cf3d51e1872c38fc231993b6005675abc0fc71fa'
for path in ('.github/workflows/rozvidka.yml','.github/workflows/zhnyvarka.yml'):
 assert subprocess.check_output(['git','-C',repo,'rev-parse',oldsha+':'+path])==subprocess.check_output(['git','-C',repo,'rev-parse',newsha+':'+path])
print('rozvidka/zhnyvarka: точні blobs незмінні; лише workflow_dispatch поза scope')
print('PASS; source freeze:',newsha)
