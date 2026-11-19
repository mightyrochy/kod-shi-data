#!/usr/bin/env python3
"""Повтори «не виміряно» між оцінками. Одиниця: суворо — (PR, сцена, початок питання); м'яко — (PR, сцена).
Запуск з аудит/: python3 проби/Автоживий-не-виміряно-розклад/повтори.py /tmp/r.json"""
import json,re,sys,collections
d=json.load(open(sys.argv[1])); усі=d['усі']
н=lambda q:re.sub(r'\W+',' ',q.lower())[:45].strip()
дата={'О1113':'13.11','Х1115':'15.11','Е1115':'15.11','Х1811':'18.11','Х1811р':'18.11'}
def зв(кл):
    G=collections.defaultdict(list)
    for r in усі: G[кл(r)].append(r)
    return G
for назва,кл in (('суворо',lambda r:(r['pr'],r['сцена'],н(r['питання']))),("м'яко (PR+сцена)",lambda r:(r['pr'],r['сцена']))):
    G=зв(кл); нвк=[k for k,rs in G.items() if any(r['к']=='нв' for r in rs)]
    нв2=[k for k in нвк if len({r['оцінка'] for r in G[k] if r['к']=='нв'})>=2]
    # НВ, що має ще появу в іншій оцінці
    інша=[k for k in нвк if len({r['оцінка'] for r in G[k]})>=2]
    рез=collections.Counter()
    for k in інша:
        rs=G[k]
        for о in {r['оцінка'] for r in rs if r['к']=='нв'}:
            пізн=[r for r in rs if r['оцінка']!=о and дата[r['оцінка']]>=дата[о] ]
            ін=[r for r in rs if r['оцінка']!=о]
            if not ін: continue
            рез[tuple(sorted({r['к'] for r in ін}))]+=1
    print(назва,'ключів з НВ:',len(нвк),'; з НВ у ≥2 оцінках:',len(нв2),'; НВ-ключів із появою в іншій оцінці:',len(інша))
    for k in нв2: print('  ≥2 НВ:',k[0],k[1],k[2][:40] if len(k)>2 else '',[(r['оцінка'],r['к']) for r in G[k]])
    for k in інша:
        if k in нв2: continue
        print('  НВ→інша:',k[0],k[1],k[2][:30] if len(k)>2 else '',[(r['оцінка'],r['к']) for r in G[k]])
