import json,re,glob,os,gzip,collections as C,statistics as st,subprocess
R='/tmp/a6/runs'; runs=sorted(d for d in os.listdir(R) if re.match(r'ж\d_',d))
out=[]
def P(*a): out.append(' '.join(str(x) for x in a))
calls=json.load(open('/tmp/a6/calls.json'))
P(f'Прогонів: {len(runs)}; викликів моделі: {len(calls)}; на прогін сер {len(calls)/len(runs):.1f}')
def rd(f):
    t=open(f,encoding='utf8').read(); m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \(([^)]*)\) ──\n(.*)\n$',t,re.S); return m.group(2),m.group(4)
# файли відповідей проти журналу
nf=len(glob.glob(R+'/*/x/VIDPOVIDI/*.txt')); P(f'Файлів у відповіді.tar.gz: {nf} з {len(calls)} викликів ({100*nf/len(calls):.0f}%) — решта перезаписана однаковим номером')
# ОПИС без задуму/дня
a=b=0; rr=set()
for f in glob.glob(R+'/*/x/VIDPOVIDI/*ОПИС*'):
    o=json.loads(rd(f)[0]); a+=1
    if 'idea' not in o: b+=1; rr.add(f.split('/')[4])
P(f'ОПИС без idea і your_day_sentence: {b} з {a} промптів (у {len(rr)} прогонах)')
# слова_знято причини
cl=lo=0; rcl=set()
for r in runs:
    s=gzip.open(f'{R}/{r}/вердикти.txt.gz','rt',encoding='utf8').read()
    for m in set(re.findall(r'слова_знято":"([^"]*)"',s)):
        if 'виконано' in m: cl+=1; rcl.add(r)
        else: lo+=1
P(f'Причини зняття задуму/дня (унікальні записи звіту): заява «виконано» без підтвердження кодом — {cl} у {len(rcl)} прогонах; річ моделі знята з картки — {lo}')
# ПОВНОТА days
pd=[];
for f in glob.glob(R+'/*/x/VIDPOVIDI/*ВЕРДИКТ_V1_ОБРАЗИ*'):
    p,an=rd(f)
    if 'cannot be shown yet' in p[:400]:
        for x in json.loads(an).get('outfits',[]): pd.append((f.split('/')[4],x.get('day')))
P(f'Ремонт повноти: образів {len(pd)}; їхні day: '+' | '.join(f'{r}: {d}' for r,d in pd))
# хід розмови: зсув ошатності на ході без слів
fl=[];tot=0
for r in runs:
    V=sorted(glob.glob(f'{R}/{r}/x/VIDPOVIDI/*хід_розмови*.txt'))
    last=None
    for f in V:
        p,an=rd(f); o=json.loads(p)
        try: u=json.loads(an).get('update',{})
        except: continue
        fo=u.get('formality')
        if o.get('her_new_message')=='unknown':
            tot+=1
            pf=(o.get('passport') or {}).get('formality')
            if fo and pf and (fo.get('from'),fo.get('to'))!=(pf.get('from'),pf.get('to')): fl.append(f"{r}: {pf['from']}–{pf['to']}→{fo['from']}–{fo['to']} (chosen={json.dumps(o.get('chosen'),ensure_ascii=False)})")
P(f'Ходи без слів (лише плитки): {tot}; ошатність змінено: {len(fl)}'); [P('   ',x) for x in fl]
# офіс
for r in runs:
    pk=sorted(glob.glob(f'{R}/{r}/x/VIDPOVIDI/*ПАКЕТ*'))
    if pk:
        o=json.loads(rd(pk[0])[0]); d=o.get('day') or {}
        if d.get('place','').startswith('office') or (o.get('case') or {}).get('occasion')=='work':
            P(f"   робота: {r} place={d.get('place')} formality={d.get('formality')} event={(o.get('case') or {}).get('event')}")
open('/tmp/a6/numbers.txt','w').write('\n'.join(out)); print('\n'.join(out))
