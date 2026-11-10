"""Ч10: класи змін вікна `вікно_з_кадром` (ширина, зсув кінця, повне коло) і переходи сім'ї, нейтралі й гучності меж
речей із кадром ДО → ПІСЛЯ. Запуск із джерела/: python3 <цей файл> <кадр_до.json.gz> <кадр_після.json.gz>
(вихід `входи_кадру.py` на дереві ДО і ПІСЛЯ)."""
import gzip, json, collections, sys
sys.path.insert(0,'.')
import колір_тон as T
до=json.load(gzip.open(sys.argv[1])); пс=json.load(gzip.open(sys.argv[2]))
print('входи однакові:', [x[:2] for x in до['входи']]==[x[:2] for x in пс['входи']], len(до['входи']))
c=collections.Counter()
for (a,b,o),(_,_,n) in zip(до['входи'],пс['входи']):
    if o==n: c['=']+=1; continue
    if o[:4]!=n[:4]: c['L/C']+=1
    do,dn=o[4],n[4]
    if do is None or dn is None: c['None %s %s'%(do,dn)]+=1; continue
    if tuple(dn)==T.ПОВНЕ_КОЛО: c['повне']+=1; continue
    w=T.ширина_дуги(dn)-T.ширина_дуги(do)
    кр=max(T.відстань_тонів(do[0],dn[0]),T.відстань_тонів(do[1],dn[1]))
    c['Δширини %+.0f, зсув кінця %s'%(round(w), '<1°' if кр<1 else '%.2f'%кр)]+=1
print(dict(c))
Д={r[0]:r[1:] for r in до['вікна_речей']}; П={r[0]:r[1:] for r in пс['вікна_речей']}
print('ids однакові', set(Д)==set(П), len(Д))
пер=collections.Counter(); зм=0
for і in sorted(Д):
    if Д[і][0]!=П[і][0]: зм+=1
    for k,ім in ((1,'сім_я'),(2,'нейтраль'),(3,'гучність')):
        if Д[і][k]!=П[і][k]: пер['%s: %s → %s'%(ім,Д[і][k],П[і][k])]+=1; print('  ',і,ім,Д[і][0][4],'→',П[і][0][4],Д[і][k],'→',П[і][k])
print('вікон змінено', зм); print(dict(пер))
print("сім'ї ДО", dict(collections.Counter(str(v[1]) for v in Д.values()))); print("сім'ї ПІСЛЯ", dict(collections.Counter(str(v[1]) for v in П.values())))
