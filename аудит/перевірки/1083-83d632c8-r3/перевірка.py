import copy, json, pathlib, sys
ROOT=pathlib.Path('/dev/shm/qa5238-r3')
sys.path.insert(0,str(ROOT/'frozen/джерела'))
import формальність as F, вердикт_моделі as V, повнота_образу as P
items=[dict(id=i,річ=i,назва=n,тип=n,слот=s,ошатність=f) for i,n,s,f in [
 ('cardigan','кардиган','верх',5),('pumps','човники','взуття',6),
 ('pants','штани','низ',6),('foreign','кеди','взуття',1),('replacement','човники','взуття',6)]]
pool={s:[x for x in items if x['слот']==s] for s in {x['слот'] for x in items}}
def judge(ids,number='о3'):
 es=[x for x in items if x['id'] in ids]
 findings,_=V.знахідки_вердикту(F.вимоги_коду(es,'cocktail')+F.формальність_образу(es,{'діапазон':(7,8)}),number)
 return dict(ід=number,речі=ids,знахідки=findings,структура=dict(ок=False,блокери=[dict(код='no_top_and_bottom')]))
source=judge(['cardigan','pumps']);gate=next(z for z in source['знахідки'] if z['правило']=='K-KOH-05')
WHY='Свідомо обираю ансамбль без коктейльної сукні.'
DEFAULT=object(); rows=[]
def check(name,value=WHY,expected=False,target=None,accept=DEFAULT,chosen='o3',finding=None,extra=None,wrapper=None):
 answer=dict(version='1',chosen=chosen,accept=[dict(finding=finding or gate['ід'],why=value)])
 if accept is not DEFAULT:answer['accept']=accept
 if extra:answer.update(extra)
 raw=json.dumps({wrapper:answer} if wrapper else answer,ensure_ascii=False)
 ids=['cardigan','pumps','pants'] if target is None else target
 verdict=dict(образи=[judge(ids,'о1')]);before=copy.deepcopy(verdict)
 P.донести_прийняття_вибору(verdict,dict(текст=raw,вердикт=dict(образи=[copy.deepcopy(source)])),pool,items)
 sl,nums=P._словник_речей(pool,items),P._за_номером(pool)
 current=verdict['образи'][0]
 after=P._суд_складу(judge(ids,'о1'),ids,P._свідомі_ключі(current,ids,sl,nums),[],sl,nums)
 finding_after=next(z for z in after['знахідки'] if z['правило']=='K-KOH-05')
 conscious=bool(finding_after.get('свідомий'));why=finding_after.get('прийнято_чому')
 ok=conscious==expected and (not expected or why==WHY)
 rows.append(dict(case=name,passed=ok,expected=expected,raw=raw,conscious=conscious,why=why,result=finding_after,**({'before':before,'carried':verdict} if not ok else {})))
for name,value in [('null',None),('bool-false',False),('bool-true',True),('zero',0),('positive-integer',37),('negative-integer',-2),('float',1.25),('empty-array',[]),('string-array',['why']),('valid-string-array',[WHY]),('number-array',[37]),('bool-array',[True]),('null-array',[None]),('nested-array',[[WHY]]),('deep-array',[[[WHY]]]),('mixed-array',[WHY,{'x':1}]),('object',{'why':WHY}),('empty-object',{}),('object-array',[{'why':WHY}]),('nested-object',{'why':[WHY]}),('empty-string',''),('whitespace',' \n\t')]:check(name,value)
check('valid-string',expected=True)
check('valid-trimmed','  '+WHY+' \n',expected=True)
check('valid-unrelated-field-error',expected=True,extra={'title':37,'day':False})
check('foreign-finding',finding='з-о99-99')
check('foreign-existing-finding',finding=gate['ід'].replace('о3','о4'))
check('unknown-chosen',chosen='o99')
check('empty-chosen',chosen='')
check('same-source-items',expected=True,target=['cardigan','pumps'])
check('repaired-superset',expected=True,target=['cardigan','pumps','pants'])
check('source-subset',target=['cardigan','pants'])
check('source-shoe-replaced',target=['cardigan','replacement','pants'])
check('new-forbidden-item',target=['cardigan','pumps','pants','foreign'])
check('single-object-salvage',expected=True,accept=dict(finding=gate['ід'],why=WHY))
for name,value in [('accept-string',WHY),('accept-number',37),('accept-bool',True),('accept-null',None)]:check(name,accept=value)
check('invalid-then-valid-salvage',expected=True,accept=[dict(finding=gate['ід'],why=[WHY]),dict(finding=gate['ід'],why=WHY)])
check('valid-then-invalid-salvage',expected=True,accept=[dict(finding=gate['ід'],why=WHY),dict(finding=gate['ід'],why=True)])
check('foreign-then-valid-salvage',expected=True,accept=[dict(finding='з-о9-9',why=WHY),dict(finding=gate['ід'],why=WHY)])
check('answer-envelope-valid',expected=True,wrapper='answer')
check('answer-envelope-invalid-array',value=[WHY],wrapper='answer')
out=dict(head='83d632c8a756cad5e882bf5a97829b35c08e42c7',actor='/root/review_live_a_h1_5238_r3',producers=['формальність.вимоги_коду','формальність.формальність_образу','вердикт_моделі.знахідки_вердикту','повнота_образу.донести_прийняття_вибору','повнота_образу._суд_складу'],source=source,rows=rows,total=len(rows),failures=sum(not r['passed'] for r in rows))
(ROOT/'proof/результати.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:out[k] for k in ['head','total','failures']},ensure_ascii=False))
for r in rows:
 if not r['passed']:print(r['case'],r['conscious'],repr(r['why']))
sys.exit(bool(out['failures']))
