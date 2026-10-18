from pathlib import Path
import json,gzip,ast,re,collections,difflib
p=Path('/workspace/work/f2-24-evidence')
def read(path):return {v['н']:v['результат'] for v in map(json.loads,Path(path).read_text().splitlines()[1:])}
a=read('/workspace/work/baseline-results/main-1.jsonl');b=read(p/'final-pyodide/знімок.jsonl')
i=[json.loads(x) for x in gzip.open('аудит/проби/знімок_входи_сід3.jsonl.gz','rt')]
i=[json.loads(x['вхід']) for x in i]
src=Path('джерела/пакет_моделі.py').read_text();node=next(x for x in ast.parse(src).body if isinstance(x,ast.FunctionDef) and x.name=='номери_речей');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-numbering','exec'),ns)
f=ns['номери_речей']
def maps(result,key):
 slots=('верх','низ','сукня','комплект','верхній_шар','взуття','сумка','пояс','головний_убір','шарф','прикраси','сережки','намисто','кольє','браслет','каблучка','брошка')
 n,_=f({s:result[key][s] for s in slots if s in result[key]});return {'#%s·%s'%v:k for k,v in n.items()},n
mapsa={k:maps(a[12],k) for k in ('кандидати','кандидати_донора')};mapsb={k:maps(b[12],k) for k in mapsa}
checks=[]
for phase,result,mm in [('ДО',a[12],mapsa),('ПІСЛЯ',b[12],mapsb)]:
 for key,prompt in [('кандидати','B'),('кандидати_донора','C')]:
  packet=json.loads(result[prompt]); data={r['id']:r for rs in result[key].values() for r in rs}; rows=packet['pool']['rows']; aliases=mm[key][0]
  errors=[(row[0],aliases.get(row[0])) for row in rows if row[0] not in aliases or data[aliases[row[0]]]['назва']!=row[1]]
  assert not errors, errors[:3]
  checks.append({'фаза':phase,'пул':key,'звірено_рядків_пакета':len(rows),'помилок':len(errors)})
out={'всі_mapping_звірені_з_фактичними_prompt_rows':checks,'номерувальник_AST_джерело':'джерела/пакет_моделі.py:номери_речей','пули_джерело':'0.2 н12, повний результат запити','виклики':[]}
for n in (18,23,24,27,28,31):
 inp=i[n];key='кандидати_донора' if inp['донор'] else 'кандидати'
 ma,na=mapsa[key];mb,nb=mapsb[key]
 text=inp.get('текст_моделі','')
 if n in (28,31):text=json.dumps(inp['вибір_над'],ensure_ascii=False)
 aliases=list(dict.fromkeys(re.findall(r'#\d+·\d+',text)))
 rows=[{'alias':x,'ДО_id':ma.get(x),'ПІСЛЯ_id':mb.get(x),'ДО_id_лишився_в_пулі':ma.get(x) in nb,'ПІСЛЯ_alias_ДО_id':('#%s·%s'%nb[ma[x]]) if ma.get(x) in nb else None} for x in aliases]
 missing=[x for x in aliases if x not in mb]
 out['виклики'].append({'н':n,'пул':key,'alias_всього':len(rows),'ДО_невідомі':sum(x['ДО_id'] is None for x in rows),'ПІСЛЯ_невідомі':len(missing),'ПІСЛЯ_інші_id':sum(x['ДО_id']!=x['ПІСЛЯ_id'] and x['ПІСЛЯ_id'] is not None for x in rows),'нема_в_каталозі_факт':b[n].get('нема_в_каталозі'),'missing_calculated':missing,'mapping':rows})
for r in out['виклики']:
 n=r['н']; inp=i[n]; key=r['пул']; ma,na=mapsa[key];mb,nb=mapsb[key]
 if n in (28,31):
  chosen=json.loads(inp['текст_моделі'])['chosen'].replace('o','о'); source=[o for o in inp['вибір_над']['образи'] if o['ід']==chosen]; outfits=[{'id':o['ід'],'items':o['речі']} for o in source]
 else:outfits=json.loads(inp['текст_моделі'])['outfits']
 r['склад_кожного_образу_ПІСЛЯ']=[{'id':o['id'],'записаних':len(o['items']),'лишились':[{ 'alias':x,'id':mb[x]} for x in o['items'] if x in mb]} for o in outfits]
 r['образи_факт_ПІСЛЯ']=[{'id':o['ід_відповіді'],'ід':o['ід']} for o in b[n]['образи']]
 r['перевірено_ДО_ПІСЛЯ']=[a[n].get('перевірено'),b[n].get('перевірено')]
 r['блокери_ПІСЛЯ']=b[n].get('блокує')
 calculated=[q for o in r['склад_кожного_образу_ПІСЛЯ'] for q in o['лишились']]
 if n not in (28,31):
  assert [o['ід'] for o in b[n]['образи']]==[[x['id'] for x in o['лишились']] for o in r['склад_кожного_образу_ПІСЛЯ'] if o['лишились']]
 else:
  assert len(calculated)==1 and not b[n]['образи']
for n in (33,35,39,42):
 key='кандидати_донора' if i[n]['донор'] else 'кандидати';ma,na=mapsa[key];mb,nb=mapsb[key]
 ids=i[n]['ід']; out['виклики'].append({'н':n,'пул':key,'ід_вхід':ids,'поза_кандидатами_ДО':a[n].get('поза_кандидатами'),'поза_кандидатами_ПІСЛЯ':b[n].get('поза_кандидатами'),'mapping':[{'id':x,'ДО_в_пулі':x in na,'ПІСЛЯ_в_пулі':x in nb} for x in ids]})
def diffs(x,y,path=''):
 if type(x)!=type(y):return [(path,x,y)]
 if isinstance(x,dict):return sum([diffs(x.get(k),y.get(k),path+'/'+k) for k in x.keys()|y.keys()],[])
 if isinstance(x,list):
  if len(x)!=len(y):return [(path+'/length',len(x),len(y))]
  return sum([diffs(u,v,path+'/'+str(j)) for j,(u,v) in enumerate(zip(x,y))],[])
 return [] if x==y else [(path,x,y)]
for n in (13,14,17,20,118):
 keys=['зміни_звіт'] if n==118 else ['схема_жінці']
 for k in keys:out.setdefault('інші_зміни',[]).append({'н':n,'поле':k,'диф':diffs(a[n][k],b[n][k])})
(p/'snapshot-causality.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for r in out['виклики']:
 print({k:v for k,v in r.items() if k!='mapping'})
for r in out['інші_зміни']:
 print(r['н'],r['поле'],'deltas',len(r['диф']))
 for d in r['диф']:print(str(d)[:500])
