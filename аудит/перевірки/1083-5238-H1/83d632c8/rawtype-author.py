import sys, json, copy, pathlib
sys.path.insert(0, '/dev/shm/live5238/repo/джерела')
import формальність as F, вердикт_моделі as V, повнота_образу as P, протокол as R

items = [dict(id=i, річ=i, назва=n, тип=n, слот=s, ошатність=f) for i,n,s,f in [
    ('qa-cardigan','кардиган','верх',5), ('qa-pumps','човники','взуття',6),
    ('qa-trousers','штани','низ',6), ('qa-sneakers','кеди','взуття',1),
    ('qa-other-pumps','човники','взуття',6)]]
pool={s:[x for x in items if x['слот']==s] for s in {x['слот'] for x in items}}
def judge(ids, number='о3'):
    es=[x for x in items if x['id'] in ids]
    raw=F.вимоги_коду(es,'cocktail')+F.формальність_образу(es,{'діапазон':(7,8)})
    findings,_=V.знахідки_вердикту(raw,number)
    return dict(ід=number,речі=ids,знахідки=findings,структура=dict(ок=False,блокери=[dict(код='no_top_and_bottom')]))
source_ids=['qa-cardigan','qa-pumps']; target_ids=source_ids+['qa-trousers']
original=judge(source_ids); gate=next(z for z in original['знахідки'] if z['регістр']=='гейт')
why='Свідомо обираю цей ансамбль без коктейльної сукні.'
def run(label, value=why, expected=False, ids=None, finding=None, chosen='o3', extra=None, accept_override=None):
    answer=dict(version='1',chosen=chosen,accept=[dict(finding=finding or gate['ід'],why=value)])
    if extra: answer.update(extra)
    if accept_override is not None:answer['accept']=accept_override
    text=json.dumps(answer,ensure_ascii=False)
    normalized,_,notes=R.розбір_за_схемою(text,'ВИБІР_V1')
    parsed=P.вибір_з_json(text,dict(образи=[copy.deepcopy(original)]),pool,items)
    verdict=dict(образи=[judge(ids or target_ids,'о1')]); before=copy.deepcopy(verdict)
    P.донести_прийняття_вибору(verdict,dict(текст=text,вердикт=dict(образи=[copy.deepcopy(original)])),pool,items)
    current=verdict['образи'][0]; sl,n=P._словник_речей(pool,items),P._за_номером(pool)
    # The real second producer/same-items judge runs again after carry.
    repeated=P._суд_складу(judge(ids or target_ids,'о1'),ids or target_ids,P._свідомі_ключі(current,ids or target_ids,sl,n),[],sl,n)
    result=next(z for z in repeated['знахідки'] if z['регістр']=='гейт')
    conscious=bool(result.get('свідомий')); explanation=result.get('прийнято_чому')
    ok=conscious==expected and (not expected or explanation==str(value).strip())
    return dict(case=label,passed=ok,expected=expected,raw_answer=answer,normalized=normalized,normalization=notes,parser_errors=parsed['помилки'],
                rejudged=result,conscious=conscious,why=explanation,**({'before':before,'after':verdict} if not ok else {}))
rows=[]
for label,value in [('null',None),('false',False),('true',True),('zero',0),('integer',37),('negative',-1),('float',1.25),('array-empty',[]),('array-nonempty',['why']),('array-number',[37]),('array-bool',[True]),('array-nested',[[1]]),('object-empty',{}),('object-nonempty',{'x':1}),('empty-string',''),('whitespace',' \t\n')]:
    rows.append(run(label,value))
rows += [run('valid-string',expected=True),run('valid-trimmed','  '+why+' \n',expected=True),run('valid-other-field-error',expected=True,extra={'title':37}),
         run('foreign-finding',finding='з-о99-99'),run('unknown-chosen',chosen='o99'),
         run('other-outfit',ids=['qa-cardigan','qa-trousers','qa-other-pumps']),
         run('new-forbidden-shoes',ids=target_ids+['qa-sneakers']),
         run('accept-object-salvage',expected=True,accept_override={'finding':gate['ід'],'why':why}),
         run('accept-string',accept_override=why),run('accept-bool',accept_override=True),run('accept-number',accept_override=37),
         run('invalid-plus-valid',expected=True,accept_override=[{'finding':gate['ід'],'why':True},{'finding':gate['ід'],'why':why}])]
out=dict(head='правка після 762ab830, ще до нового коміту',actor='автор: відтворення незалежної проби r2 після rawfix',
         actual_producers=['формальність.вимоги_коду','формальність.формальність_образу','вердикт_моделі.знахідки_вердикту','повнота_образу._суд_складу'],
         original=original,rows=rows,total=len(rows),failures=sum(not x['passed'] for x in rows))
pathlib.Path('/dev/shm/live5238/rawtype-author.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({k:out[k] for k in ['head','total','failures']},ensure_ascii=False))
for x in rows:print(x['case'],x['passed'],x['conscious'],repr(x['why']))
sys.exit(bool(out['failures']))
