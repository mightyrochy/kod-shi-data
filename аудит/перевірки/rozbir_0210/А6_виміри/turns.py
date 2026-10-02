import json,re,glob,os
def rd(fn):
    t=open(fn,encoding='utf8').read()
    m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S)
    return m.group(2),m.group(4)
for r in sorted(os.listdir('/tmp/a6/runs')):
    if not r.startswith('ж'): continue
    V=sorted(glob.glob(f'/tmp/a6/runs/{r}/x/VIDPOVIDI/*хід_розмови*.txt'))
    row=[]
    for f in V:
        p,a=rd(f)
        try: o=json.loads(p); msg=o.get('her_new_message')
        except: msg='?'
        try: u=json.loads(a).get('update',{})
        except Exception as e: u={'НЕ_JSON':a[:80]}
        keep={k:(v.get('value') if isinstance(v,dict) and 'value' in v else v) for k,v in u.items() if k not in('event','stylist_note')}
        row.append(f"«{(msg or '')[:40]}» → {json.dumps(keep,ensure_ascii=False)[:260]}")
    pk=sorted(glob.glob(f'/tmp/a6/runs/{r}/x/VIDPOVIDI/*ПАКЕТ*.txt'))
    d=json.loads(rd(pk[0])[0]).get('day') if pk else None
    print(r,'| ПАКЕТ.day=',json.dumps(d,ensure_ascii=False)); [print('   ',x) for x in row]
