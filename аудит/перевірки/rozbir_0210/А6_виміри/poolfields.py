import json,re,glob,collections as C
tot=C.Counter(); dflt=C.Counter(); allc=0; n_items=0; files=0; cyr=0
for f in glob.glob('/tmp/a6/runs/*/x/VIDPOVIDI/*ПАКЕТ*.txt'):
    t=open(f,encoding='utf8').read(); m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ',t,re.S); o=json.loads(m.group(2))
    files+=1; s=json.dumps(o['pool'],ensure_ascii=False); allc+=len(s); cyr+=len(re.findall('[А-Яа-яІіЇїЄєҐґ]',s))
    for it in o['pool']:
        n_items+=1
        for k,v in it.items():
            c=len(json.dumps({k:v},ensure_ascii=False))-1
            tot[k]+=c
            if (k,v) in (('in_arc',True),('branch','core')): dflt[k]+=c
print('ПАКЕТ файлів',files,'речей у пулі сер',n_items//files,'симв. пулу сер',allc//files, 'кирилиці частка %.0f%%'%(100*cyr/allc))
for k,v in tot.most_common(25): print(f'{k:14s} {100*v/allc:5.1f}%  за замовч.: {100*dflt[k]/allc:4.1f}%')
