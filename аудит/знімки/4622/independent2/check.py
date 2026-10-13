import copy, hashlib, json, pathlib, subprocess, sys
src=pathlib.Path('/workspace/scratch/liusterko-4622/джерела')
sys.path.insert(0,str(src))
import мовний_шар as M, сценарій as S, паспорт_нагоди as P, внутрішня_мова as V
out=pathlib.Path('/workspace/scratch2/review4622-round2')
record=pathlib.Path('/workspace/scratch/4622-proof/before_seed4_01_мовний_шар_хід_розмови.txt').read_text()
original=json.loads(record.split('── ВІДПОВІДЬ',1)[1].split('──',1)[1].strip().removeprefix('```json').removesuffix('```').strip())
words=json.loads(record.split('\n',1)[1].split('\n── ВІДПОВІДЬ')[0])['her_new_message']
def replay(obj,prior=None,scene=None):
    accepted=M.прийняти_розмову(json.dumps(obj,ensure_ascii=False))
    return M.паспорт_з_шару(accepted['внутрішня'],scene or {},паспорт_досі=prior,слова_ходу=[words],частини=accepted['частини'])
old=replay(original)['паспорт']
fixtures=[]
for name,intent,quote,occasion,place in [
 ('quoted_other','other','кава з подругою','sport','cafe'),
 ('other_everyday','other','кава з подругою','everyday','cafe'),
 ('quoted_sport_park','sport','йога зранку','sport','park'),
 ('unknown','unknown','кава з подругою','sport','cafe'),
 ('unquoted_other','other',None,'sport','cafe'),
 ('foreign_quote','other','відсутня цитата','sport','cafe'),
 ('absent',None,None,'sport','cafe'),
 ('invalid_enum','bogus','кава з подругою','sport','cafe'),
 ('travel','other','кава з подругою','travel','cafe')]:
    o=copy.deepcopy(original)
    o['update']['occasion']['value']=occasion
    o['update']['place']['value']=place
    if intent is None:o['update'].pop('occasion_part',None)
    elif quote is None:o['update']['occasion_part']={'value':intent}
    else:o['update']['occasion_part']={'quote':quote,'value':intent}
    result=replay(o,old,{'нагода':'спорт'})
    p=result['паспорт']; effective=S.з_показу({'нагода':'спорт'},p)[0]
    expected='unknown' if name=='quoted_other' else occasion
    assert p['виміри']['occasion']==expected,(name,p['виміри']['occasion'])
    assert P.виміри_нагоди(p,{'нагода':'спорт'})[0]['occasion']==expected,name
    assert effective.get('нагода')==(None if name=='quoted_other' else p['нагода']),name
    assert p['виміри']['place']==place and p['виміри']['movement']=='sport',name
    fixtures.append({'name':name,'response':o,'result':result,'effective':effective})
# Конфлікт не стирає чинну іншу ручну нагоду; просте мовчання не стирає ручні поля.
manual={'нагода':'робота','місце':'офіс','темп_c':23}
o=copy.deepcopy(original);o['update']={'occasion_part':{'quote':'кава з подругою','value':'other'},'occasion':{'quote':'йога зранку','value':'sport'}}
conflict=replay(o,None,manual)
assert S.з_показу(manual,conflict['паспорт'])[0]['нагода']=='робота'
o['update']={}
missing=replay(o,None,manual)
assert S.з_показу(manual,missing['паспорт'])[0]['нагода']=='робота'
assert S.з_показу(manual,missing['паспорт'])[0]['місце']=='офіс'
assert S.з_показу(manual,missing['паспорт'])[0]['темп_c']==23
assert json.loads((src/'внутрішня_мова.schema.json').read_text())==V.схема()
producer=json.loads(M.промпт_розмови(json.loads(pathlib.Path('/workspace/scratch/4622-proof/producer-input.json').read_text())))
(out/'producer.json').write_text(json.dumps(producer,ensure_ascii=False,indent=2))
(out/'fixtures.json').write_text(json.dumps(fixtures,ensure_ascii=False,indent=2))
(out/'missing.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2))
print(json.dumps({'sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=src,text=True).strip(),'cases':[{'name':f['name'],'metric':f['result']['паспорт']['виміри']['occasion'],'effective':f['effective'].get('нагода'),'not_recorded':f['result']['не_записано']} for f in fixtures],'schema_equal':True,'manual_missing_preserved':True,'manual_other_conflict_preserved':True,'models_called':0},ensure_ascii=False,indent=2))
