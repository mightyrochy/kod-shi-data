from pathlib import Path
import sys,os,json,copy,ast
source=Path('/dev/shm/liusterko-update1069-native-1056/джерела');sys.path.insert(0,str(source));import правило_руки2 as r
expected={'R-COL-16','K-BOD-02','K-CRA-01','K-KOH-02','K-OUT-33','K-COL-06-M','K-REG-01','K-SIL-03','K-FIT-03','K-ACC-01','K-SHO-16','K-PAL-18','K-MAT-03'}
assert {x['ід'] for x in r.ПЕРЕЛІК}-r.ПОЗА_ЖЕРЕБОМ==expected and r.ПОЗА_ЖЕРЕБОМ=={'R-MUA-02'}
d={'обхвати':{'груди':90,'талія':70,'стегна':100},'сценарій':{'нагода':'робота','місце':'офіс','година':9,'темп_c':5,'тривалість_год':8,'дрес_код':'business_casual'},'самозвіт':{'метал':'срібло'}};p={'особа':{'бік_b':{'вхід':True},'рівень':'low','температура':{'придатно':True}},'палітри':{'розвилка':[{'спец':{'слоти':{'accent':{'роль':'акцент','C':30}}}}]}}
samples=[]
for seed in [1,7,13]:
 rec,available,missing,pair=r.жереб(dict(d,сід=seed),p);chosen=rec['правила'];aspects=rec['аспект'];assert 1<=len(chosen)<=len(set(aspects));assert set(chosen)<=expected;assert len(chosen)==rec['поломок']==len(set(aspects));samples.append({'seed':seed,'rules':chosen,'aspects':aspects,'count':rec['поломок']})
with r.вимкнено(['K-SHO-16']):
 for suffix in ['a','b']:
  findings=[{'правило':'K-SHO-16','речі':[suffix+'-shoe'],'суть':'scope-'+suffix,'сила':'hard','блокує':True}];assert r.відсіяти(findings,[suffix+'-shoe',suffix+'-bag'])==[]
 shadow=r.тінь();one=r.тінь_образу(shadow,['a-shoe','a-bag'],{'a-shoe':'взуття','b-shoe':'взуття'});two=r.тінь_образу(shadow,['b-shoe','b-bag'],{'a-shoe':'взуття','b-shoe':'взуття'});assert len(one)==len(two)==1;assert one[0]['речі']==['a-shoe'] and two[0]['речі']==['b-shoe'];assert one[0]['слоти']==two[0]['слоти']==['взуття']
assert r.вимкнені()==frozenset() and r.тінь()==[]
code=ast.parse((source/'міст_рука2.py').read_text());salt=next(n for n in code.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='СІЛЬ_РУКИ_2' for t in n.targets));fn=next(n for n in code.body if isinstance(n,ast.FunctionDef) and n.name=='_сід_руки');ns={};exec(compile(ast.Module(body=[salt,fn],type_ignores=[]),'<actual-source-seed-scope>','exec'),ns);f=ns['_сід_руки'];assert f(7,False)==7 and f(7,True)==30 and f(0,True)==0
result={'head':'d25ed4b4934b7c72889c2d1c061ee1cc0808317a','scope':'pure current hand2 integration, no catalogue/model/full battery','normative_rules':sorted(expected),'makeup_excluded':'R-MUA-02','samples':samples,'shadow_a':one,'shadow_b':two,'shadow_cross_card_leak':False,'context_restored':True,'raw_pool_seed_and_salted_display_seed':'7/30, zero0','production_quality_accepted':False};Path('/workspace/scratch/qa-update1069-independent/hand2-scope.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
