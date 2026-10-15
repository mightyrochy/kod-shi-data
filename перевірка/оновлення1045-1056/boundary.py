from pathlib import Path
import sys,ast,json,hashlib,copy
ROOT=Path('/dev/shm/qa-updates-1045-1056');sys.path.insert(0,str(ROOT));from composition import blob
result={'models':0,'paid':0,'live_acceptance':False,'ast':[]}
def nodes(ref,f):
 d={}
 for x in ast.parse(blob(ref,'джерела/'+f+'.py')).body:
  if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)):
   if x.body and isinstance(x.body[0],ast.Expr) and isinstance(x.body[0].value,ast.Constant) and isinstance(x.body[0].value.value,str):x.body=x.body[1:]
   d[x.name]=ast.dump(x,include_attributes=False)
 return d
for n,old,new in [(1074,'6f124d64056eb9458b5b78a86f40dfca8d24ed48','37e4c876b57aee8e566e1f691af064acf6061f4f'),(1083,'83d632c8a756cad5e882bf5a97829b35c08e42c7','51dcefe81cf7efd0d9726ce8cb19ddc6c20caedb')]:
 for f in ['міст_відповіді','повнота_образу','протокол']:
  a,b=nodes(old,f),nodes(new,f);assert a==b,(n,f);result['ast'].append(dict(pr=n,file=f,functions=len(a),all_existing_function_ast_unchanged=True,sha256=hashlib.sha256(json.dumps(a,ensure_ascii=False,sort_keys=True).encode()).hexdigest()))
 a,b=nodes(old,'дріт_моделі'),nodes(new,'дріт_моделі');assert [k for k in a if a[k]!=b.get(k)]==['вердикт'];assert set(b)-set(a)=={'_свідомі_на_дріт'}
result['1074_shadow_boundary']='Повний producer від_моделі/суд/повнота/cache AST тотожний old37-parent6f; усі ownshadow модулі exactoldblobs. Main3541 змінив лише declared serializer; повтор samecard fresh/cached producer не потрібен за незмінного шляху ідентичності.'
# Only changed Python modules of1083 overlay the exact current common source; no build/browser/catalog run.
head='51dcefe81cf7efd0d9726ce8cb19ddc6c20caedb';over=ROOT/'boundary1083';over.mkdir(exist_ok=True)
for f in ['pipeline','вердикт_моделі','формальність','міст_відповіді','повнота_образу','протокол']:(over/(f+'.py')).write_bytes(blob(head,'джерела/'+f+'.py'))
sys.path.insert(0,str(ROOT/'current/джерела'));sys.path.insert(0,str(over));sys.dont_write_bytecode=True
import формальність as F,вердикт_моделі as V,повнота_образу as P,протокол as K,дріт_моделі as D
items=[dict(id=i,річ=i,назва=n,тип=n,слот=s,ошатність=f) for i,n,s,f in [('cardigan','кардиган','верх',5),('pumps','човники','взуття',6),('pants','штани','низ',6)]];pool={s:[x for x in items if x['слот']==s] for s in {x['слот'] for x in items}}
def judge(ids,number='о3'):
 es=[x for x in items if x['id'] in ids];findings,_=V.знахідки_вердикту(F.вимоги_коду(es,'cocktail')+F.формальність_образу(es,{'діапазон':(7,8)}),number)
 return dict(ід=number,речі=ids,знахідки=findings,структура=dict(ок=False,блокери=[dict(код='no_top_and_bottom')]))
source=judge(['cardigan','pumps']);gate=next(z for z in source['знахідки'] if z['правило']=='K-KOH-05');WHY='Свідомо лишаю цей хід заради задуму.';cases=[]
for name,why,expected in [('raw-array',[WHY],False),('valid-quoted-string',WHY,True)]:
 raw=json.dumps(dict(version='1',chosen='o3',accept=[dict(finding=gate['ід'],why=why)]),ensure_ascii=False);ids=['cardigan','pumps','pants'];verdict=dict(образи=[judge(ids,'о1')]);P.донести_прийняття_вибору(verdict,dict(текст=raw,вердикт=dict(образи=[copy.deepcopy(source)])),pool,items);sl,nums=P._словник_речей(pool,items),P._за_номером(pool);current=verdict['образи'][0];after=P._суд_складу(judge(ids,'о1'),ids,P._свідомі_ключі(current,ids,sl,nums),[],sl,nums);gate_after=next(z for z in after['знахідки'] if z['правило']=='K-KOH-05');assert bool(gate_after.get('свідомий'))==expected
 wire=D.вердикт(K.вердикт_на_дріт(dict(образи=[current])),вибір=True)
 if expected:assert gate_after.get('прийнято_чому')==WHY
 else:assert not current.get('свідомі')
 cases.append(dict(case=name,raw=raw,expected_conscious=expected,conscious=bool(gate_after.get('свідомий')),current=current,wire=wire,passed=True))
result['1083_raw_guard_cases']=cases;result['1083_head']=head;result['1074_head']='37e4c876b57aee8e566e1f691af064acf6061f4f';(ROOT/'proof/boundary-newmain.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(ast_preserved=len(result['ast']),raw_guard_cases=len(cases),failed=0),ensure_ascii=False))
