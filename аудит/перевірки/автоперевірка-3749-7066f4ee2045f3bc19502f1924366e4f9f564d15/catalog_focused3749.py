import gzip,json,os,pathlib,sys
src=pathlib.Path(sys.argv[1]).resolve(); sys.path.insert(0,str(src)); os.chdir(src)
import таблиця_каталогу as TK, фід_розбір as FR, colorspace as cs, колір_річ as KR
import палітра_схеми as PS, колір_хрома as CH, палітра_запити as PZ, верхнє_стан as VS
table=pathlib.Path(sys.argv[2]).resolve(); xml=pathlib.Path(sys.argv[3]).resolve()
t=json.load(gzip.open(table,'rt',encoding='utf-8')); cat=TK.відновити(t,FR.офери_фіду(str(xml)))['каталог']
points={r['id']:KR.точка_кольору(r) for r in cat}; valid=[r for r in cat if points[r['id']]]
lch=lambda r:cs.lch(points[r['id']]); first=lambda slot,p:next(r for r in valid if r.get('слот')==slot and p(r))
neutral=lambda r:lch(r)[1]<10
dress=first('сукня',lambda r:lch(r)[1]>25); top=first('верх',neutral)
bag=first('сумка',lambda r:lch(r)[1]>=40)
families=[dict(роль=r,дуга=list(PS.СХЕМИ['приглушена_комплементарна']['тон'](lch(dress)[2])[r])) for r in ('домінанта','секундант')]
special={'_поверхні':'великі','_сім_ї':families,'_схема':'приглушена_комплементарна'}
cases={}; index={r['id']:r for r in cat}
cases['K-COL-03']=PS.обіцянка_великих([dress,top],special,index,{'сукня':[dress]},None,межа_людини=False)
base=[first(slot,neutral) for slot in ('верх','низ','взуття')]+[bag]
entries=[]
for r in base:
    L,C,h=lch(r); slot=r['слот']; area=.02 if slot=='сумка' else .3
    entries.append(dict(річ=r['id'],слот=slot,hex=r.get('hex'),lab=points[r['id']],L=L,C=C,h=h,площа=area,площа_межі=(area,area),джерело_площі='маски',near=.5,текстура=None,нейтраль=C<10,сім_я=None,назва=r['назва']))
cases['K-COL-05']=CH.відлуння(entries,None)
cases['R-CHEV-14']=PZ.тиск_знахідка(lch(dress)[2],40.,'сукня','тло')
coat=next((r for r in cat if r.get('слот')=='верхній_шар' and r.get('комір')=='стійка'),None)
scarf=next(r for r in cat if r.get('слот')=='шарф')
if coat:
    cases['K-OUT-13-без']=[z for z in VS.команди_укладки([coat],смуга_вітру='strong') if z['правило']=='K-OUT-13']
    cases['K-OUT-13-з']=[z for z in VS.команди_укладки([coat,scarf],смуга_вітру='strong') if z['правило']=='K-OUT-13']
assert cases['K-COL-03'], 'немає вимірюваної K-COL-03'
assert any(z.get('правило')=='K-COL-05' for z in cases['K-COL-05']), 'немає вимірюваної K-COL-05'
print(json.dumps(dict(каталог=len(cat),входи=[r['id'] for r in [dress,top,bag]+base+([coat,scarf] if coat else [])],випадки=cases),ensure_ascii=False,default=str,indent=2))
