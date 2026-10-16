import sys,os,re,glob,json
sys.path.insert(0,os.getcwd())
import оцінка_образу as О, річ_з_фото as Ф
n_bad=0;out=[]
for f in sorted(glob.glob(sys.argv[1]+'/*.txt')):
    t=open(f,encoding='utf-8').read()
    ids=sorted(set(re.findall(r'"photo"\s*:\s*"([^"]+)"',t))) or ['ф1']
    фото=[{'ід':i} for i in ids]
    r=О.речі_з_відповіді(t,фото)
    r2=Ф.речі_з_відповіді_фото(t,[{'ід':i} for i in ids])
    k=len(r['речі']); bad = (k==0 or r['причина'])
    n_bad+=bool(bad)
    out.append((os.path.basename(f)[:14],k,len(r2.get('речі_з_фото') or []),r['причина'],[x for x in r['нотатки']] if r.get('нотатки') else []))
for o in out: print(o)
print('НЕ_РОЗІБРАНО',n_bad)
