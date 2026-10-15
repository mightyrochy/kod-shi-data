import copy, json, subprocess, sys
from pathlib import Path
r=Path('/workspace/scratch/pachka-1510-1/repo'); sys.path.insert(0,str(r/'джерела'))
import повнота_образу as П, розбір_відповідей as Р, протокол as К, дріт_моделі as Д, збирач_промптів as З
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='c80bea14f73505903d1b99c77b746c45acb34c45'
f=json.loads(Path('/workspace/scratch/accept3541/джерело_3541.json').read_text()); o=next(x for x in f['образи'] if x['номер']=='о3')
nom=dict(zip(o['речі_н'],o['ід'])); zs=[dict(z,речі=[nom.get(i,i) for i in z['речі']]) for z in o['знахідки']]
v=dict(образи=[dict(ід='о3',речі=o['ід'],знахідки=zs,структура=dict(ок=True,блокери=[]))]); orig=copy.deepcopy(v)
catalog=[dict(id=i,**x) for i,x in f['довідник'].items()]; old={'__name__':'до'}
exec(subprocess.check_output(['git','show','531ce082f573d225d444952207930095d2e260fc:джерела/повнота_образу.py'],cwd=r,text=True),old)
for fid,expected in [('f-o3-1',(.75,.45)),('f-o3-12',(.25,.15))]:
 for parse in [old['вибір_з_json'],П.вибір_з_json]:
  c=parse(json.dumps(dict(version='1',chosen='o3',accept=[dict(finding=fid,why='Свідомий хід.')])) ,v,каталог=catalog); judged,_=Р._застосувати_свідомі(zs,c['розриви'],catalog); zid=К.ід_з_дроту(fid)
  assert c['обрано']=='о3' and len(c['прийнято'])==1 and (next(z['сила_нп'] for z in zs if z['ід']==zid),next(z['сила_нп'] for z in judged if z['ід']==zid))==expected
  assert all(z==zs[i] for i,z in enumerate(judged) if z['ід']!=zid)
for fid,why,reason in [('f-o1-1','Чужий.','finding_not_in_chosen_outfit'),('f-o3-999','Немає.','finding_not_in_chosen_outfit'),('f-o3-1',' ','accepted_without_why')]:
 c=П.вибір_з_json(json.dumps(dict(version='1',chosen='o3',accept=[dict(finding=fid,why=why)])),v,каталог=catalog)
 assert not c['прийнято'] and not c['розриви'] and c['прийнято_знехтувано'][0]['чому']==reason
c=П.вибір_з_json(json.dumps(dict(version='1',chosen='o3',why='Загальна причина.')),v,каталог=catalog); assert not c['прийнято'] and not c['розриви']
move=dict(річ='#35·32, #8·01',правило='K-SHO-08',чому='Свідомий хід.',знахідка='f-o3-999'); finding=dict(ід='f-o3-7',правило='K-SHO-08',речі=['#8·01'])
for m,fs,want in [(move,[finding],'f-o3-7'),(dict(move,правило='unknown'),[finding],None),(dict(move,річ='#1·01'),[finding],None),(dict(move,правило=''),[finding],None),(move,[],None),(move,[finding,dict(finding,ід='f-o3-8')],None)]:
 out=Д._свідомі_на_дріт(dict(свідомі=[m],знахідки=fs))[0]; assert out.get('finding')==want and out['why']==m['чому'] and out['item']==m['річ']
prompt=З.зібрати(П.ВИБІР,dict(verdict=[dict(your_outfit=dict(id='o3'))])); prompt=json.loads(prompt) if isinstance(prompt,str) else prompt
assert 'a gate or a remark' in json.dumps(prompt['task']['answer_schema']) and any('do not accept findings by themselves' in x for x in prompt['task']['rules'])
gate=copy.deepcopy(v); gate['образи'][0]['знахідки']=[dict(zs[0],регістр='гейт')]; gid=К.ід_на_дріт(zs[0]['ід'])
for accept,passed in [([],False),([dict(finding=gid,why=' ')],False),([dict(finding=gid,why='Свідомо.')],True)]:
 c=П.вибір_з_json(json.dumps(dict(version='1',chosen='o3',why='Загальне.',accept=accept)),gate,каталог=catalog)
 assert bool(c['обрано'])==passed
 if not passed: assert json.loads(c['повторний_виклик'])['error']=='gates_not_accepted'
assert v==orig
print('Combined frozen: 2 non-gate ДО=ПІСЛЯ 0.75→0.45 / 0.25→0.15; інші знахідки й input незмінні.')
print('Wire current ID/кілька речей/renumber/unknown/no-rule/foreign/missing/ambiguity PASS; assembled prompt PASS.')
print('Bad accept IDs/empty why мають точні причини; why без accept не приймає; gate без accept/why блокує, valid accept пропускає.')
print('Це контрфактичні цільові перевірки збереженого ДО, без нової відповіді моделі або LIVE ПІСЛЯ.')
