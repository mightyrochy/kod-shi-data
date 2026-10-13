import json, gzip, os, collections
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tot=collections.Counter(); bad=[]; per=[]
for run in sorted(os.listdir(R)):
    p=os.path.join(R,run,'модель_виклики.json.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d=json.load(gzip.open(p,'rt'))
    except Exception: print('ПРОПУЩЕНО',run); continue
    vs=d.get('виклики',[])
    secs=sum(v.get('с') or 0 for v in vs)
    chain=[v for v in vs if '_V1' in (v.get('тип') or '')]
    for v in vs:
        tot['викликів']+=1
        if v.get('статус')!=200 or v.get('помилка') or v.get('стоп') not in ('end_turn',None):
            bad.append((run,v.get('тип'),v.get('статус'),v.get('стоп'),str(v.get('помилка'))[:120],v.get('с')))
    # стадії вердиктів
    pv=os.path.join(R,run,'вердикти.txt.gz'); st=collections.Counter()
    if os.path.exists(pv):
        dv=json.load(gzip.open(pv,'rt'))
        for pr in dv['прогони']:
            for v in pr['вердикти']:
                for s in (v.get('етапи') or {}).get('виклики') or []:
                    k=s.get('крок')
                    if s.get('помилка'): st['помилка:'+k]+=1
                    if s.get('відповідь_помилки'): st['відп_помилки:'+k]+=1
                    if s.get('обрізано'): st['обрізано:'+k]+=1
                    if s.get('нормалізовано'): st['нормалізовано:'+k]+=1
                    if s.get('перевірено') is False: st['не_перевірено:'+k]+=1
                    rb=s.get('розбір_блоків') or {}
                    if rb.get('без_id'): st['без_id:'+k]+=1
                    if rb.get('невідомі_в_образах'): st['невідомі:'+k]+=len(rb['невідомі_в_образах'])
                    if s.get('крок_спроба') not in (None,1,'1'): st['спроба>1:'+k]+=1
                for x in (v.get('етапи') or {}).get('діагноз_руки') or []:
                    if 'retry' in x and 'latin' not in x: st['retry']+=1
    per.append((run,len(vs),len(chain),round(secs),dict(st)))
print(dict(tot)); print('погані виклики:',len(bad)); [print('  ',b) for b in bad]
for x in per: print(x)
