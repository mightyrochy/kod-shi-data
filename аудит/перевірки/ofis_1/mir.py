import json,re,sys,glob,os
def rd(f):
    t=open(f,encoding='utf8').read(); m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S); return m.group(2),m.group(4)
for D in sys.argv[1:]:
    r=os.path.basename(D.rstrip('/'))
    хід=sorted(glob.glob(D+'/VIDPOVIDI/*хід_розмови*'))
    fo=[]
    for f in хід:
        try: fo.append((json.loads(rd(f)[1]).get('update') or {}).get('formality'))
        except Exception as e: fo.append('?')
    pk=sorted(glob.glob(D+'/VIDPOVIDI/*ПАКЕТ*'))
    if not pk: print(r,'ходи',fo,'ПАКЕТа нема'); continue
    p=rd(pk[0])[0]; o=json.loads(p); d=o.get('day') or {}
    kn=json.dumps(o.get('kind_notes') or o.get('pool_notes') or {},ensure_ascii=False)
    tc=re.findall(r'"(\w+)": *\{[^{}]*too_casual[^{}]*\}',kn)
    m=re.findall(r'too_casual[^,}]*',kn)
    print(r,'| хід.formality',fo,'| day.place',d.get('place'),'formality',d.get('formality'),'| too_casual:',m[:6])
    print('   «office» у промпті:',sorted(set(re.findall(r'\(1 home[^)]*\)',p))))
