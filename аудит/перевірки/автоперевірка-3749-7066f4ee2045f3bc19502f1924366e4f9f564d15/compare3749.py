import json,pathlib
root=pathlib.Path(__file__).parent
def load(name):
    raw=(root/name).read_bytes(); text=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
    value=json.loads(text[text.index('{'):]); (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8'); return value
a=load('focused-base3749.json'); b=load('focused-head3749.json')
def without_repairs(v):
    if isinstance(v,dict):return {k:without_repairs(x) for k,x in v.items() if k not in ('ремонт','ремонт_заяви')}
    if isinstance(v,list):return [without_repairs(x) for x in v]
    return v
assert a['каталог']==b['каталог']==27525
assert a['входи']==b['входи']
for key in ('K-COL-03','K-COL-05','R-CHEV-14'):
    before=a['випадки'][key]; after=b['випадки'][key]
    assert without_repairs(before)==without_repairs(after),key
    print(key,': діагнози, учасники, сила, виміри й запит однакові')
    rows=lambda x:x if isinstance(x,list) else [x]
    print('  ремонт_заяви ДО:',[z.get('ремонт_заяви') for z in rows(before)])
    print('  ремонт_заяви ПІСЛЯ:',[z.get('ремонт_заяви') for z in rows(after)])
if 'K-OUT-13-з' in a['випадки']:
    for key in ('K-OUT-13-без','K-OUT-13-з'):print(key,':',len(a['випадки'][key]),'→',len(b['випадки'][key]))
    assert len(a['випадки']['K-OUT-13-з'])==1 and not b['випадки']['K-OUT-13-з']
print('Каталог: 27525; вхідні id однакові; порівняння пройшло')
