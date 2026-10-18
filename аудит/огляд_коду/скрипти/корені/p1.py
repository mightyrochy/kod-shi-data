import re,json,sys
rows={}
for i,l in enumerate(open('аудит/БЕКЛОГ.md',encoding='utf-8'),1):
    m=re.match(r'^\| *(\d+) *\|(.*)',l)
    if not m: continue
    n=int(m.group(1)); cells=[c.strip() for c in l.strip().strip('|').split('|')]
    rows.setdefault(n,[]).append((i,cells))
dup=[n for n,v in rows.items() if len(v)>1]
print('rows',len(rows),'dups',len(dup),dup[:10])
print('max',max(rows),'min',min(rows))
ncols={}
for n,v in rows.items(): ncols[len(v[0][1])]=ncols.get(len(v[0][1]),0)+1
print('ncols',ncols)
closed=sorted([n for n,v in rows.items() if 'ЗАКРИТО' in v[0][1][3] if len(v[0][1])>3],reverse=True)
print('closed',len(closed),closed[:5],closed[299] if len(closed)>299 else None)
sel=closed[:300]
out=[]
for n in sel:
    ln,c=rows[n][0]
    out.append({'n':n,'line':ln,'name':c[1],'imp':c[2],'state':c[3],'desc':'|'.join(c[4:])})
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False)
L=[len(o['desc'])+len(o['state']) for o in out]; print('chars',sum(L), 'avg',sum(L)//len(L))
