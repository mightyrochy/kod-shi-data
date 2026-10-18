import re,json,collections as C,sys
SP=sys.argv[1]
rows={}
for i,l in enumerate(open('аудит/БЕКЛОГ.md',encoding='utf-8'),1):
    m=re.match(r'^\| *(\d+) *\|',l)
    if m:
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        rows[int(m.group(1))]=dict(src=c[1] if len(c)>1 else '',st=c[3] if len(c)>3 else '',txt=l)
lab={int(a):(b,c) for a,b,c in (x.split() for x in open(SP+'/labels.txt'))}
sel=sorted(lab,reverse=True)
SUB=dict(К='колір/палітра',С='суд/корпус',П='пул/добір',М='міст/промпти/моделі',Р='паспорт/розмова',І='показ',Д='каталог/жниварка',Х='рука 2/3/4',Б='батарея/стенд/проби',О='процес/документи')
ct=C.Counter(lab.values()); rs=C.Counter(v[1] for v in lab.values()); ss=C.Counter(v[0] for v in lab.values())
print('ROOT',rs.most_common()); print('SUB',[(SUB[k],v) for k,v in ss.most_common()])
roots=[r for r,_ in rs.most_common()]
print('\t'+'\t'.join(roots))
for s,_ in ss.most_common():
    print(SUB[s][:14]+'\t'+'\t'.join(str(ct[(s,r)] or '.') for r in roots))
# references: row numbers mentioned (not after #), only existing rows, not self
refre=re.compile(r'(?<![#\d.,:])(\d{3,4})(?![\d%])')
sys.path.insert(0,SP)
from refs import make_refs
refs=make_refs(rows)
par={n:refs(n,'src') for n in rows}
# depth over whole board via source-column refs
import functools
@functools.lru_cache(None)
def depth(n,seen=()):
    if n in seen: return 0
    ps=[p for p in par[n]]
    return 0 if not ps else 1+max(depth(p,seen+(n,)) for p in ps)
dsel=[depth(n) for n in sel]
print('src-refs: rows with parent',sum(1 for n in sel if par[n]),'/300; depth dist',sorted(C.Counter(dsel).items()))
deep=sorted(sel,key=lambda n:-depth(n))[:5]
for n in deep:
    ch=[n]; x=n
    while par[x]: x=max(par[x],key=lambda p:depth(p)); ch.append(x)
    print('chain',' ← '.join(map(str,ch)))
# children count: how many rows (whole board) cite each selected row in source
kids=C.Counter(p for n in rows for p in par[n])
print('top parents (whole board):',[(p,kids[p],rows[p]['st'][:25]) for p,_ in kids.most_common(12)])
# full-text refs to rows that are closed
fullref={n:refs(n,'txt') for n in sel}
closedref=[n for n in sel if any('ЗАКРИТО' in rows[p]['st'] for p in fullref[n])]
rek=re.compile(r'не трима|знову|досі|лишив|лишає|залишок|ще без|те саме|той самий|та сама|повтор|не досягнуто|після #\d+',re.I)
reop=[n for n in sel if any('ЗАКРИТО' in rows[p]['st'] for p in par[n]) and rek.search(rows[n]['txt'])]
print('cites closed row (full text):',len(closedref),'; src cites closed row + recurrence word:',len(reop))
regre=re.compile(r'після #\d+|з #\d+ |падає на `?main|червон|зламал|зламав|ДО .{0,40}ПІСЛЯ',)
reg=[n for n in sel if re.search(r'після #\d+|з #\d+[ ,(]|падає на `?main|червон[аіи] на `?main|зламав|зламала',rows[n]['txt'])]
print('regression-word rows',len(reg))
# explicit "залишок"/"живцем не тримається"/"дубль"
for k,pat in [('живцем не тримається','живцем не трима'),('залишок','залишок'),('дубль','дубль'),('прикрас','прикрас|обруч|каблучк|сережк'),('"answer"','"answer"'),('ДО/ПІСЛЯ','ПІСЛЯ')]:
    print(k,sum(1 for n in sel if re.search(pat,rows[n]['txt'])))
with open(SP+'/рядки.tsv','w') as f:
    f.write('рядок\tпідсистема\tкорінь\tрядок_дошки_файлу\tбатьки(джерело)\tглибина\tзакритий_батько+повтор\tслово_регресії\tстан\n')
    for n in sel:
        f.write(f"{n}\t{SUB[lab[n][0]]}\t{lab[n][1]}\t\t{','.join(map(str,sorted(par[n])))}\t{depth(n)}\t{int(n in reop)}\t{int(n in reg)}\t{rows[n]['st'][:60]}\n")
json.dump(dict(reop=reop,reg=reg),open(SP+'/a1.json','w'))
# fix-of-parent: child text mentions the PR that closed a cited parent
def prs(s): return set(re.findall(r'#(\d{3,4})',s))
fixpar=[]
for n in sel:
    cp=set()
    for p in fullref[n]:
        if 'ЗАКРИТО' in rows[p]['st']: cp|=prs(rows[p]['st'])
    body=rows[n]['txt'].split('|',4)[-1]
    if cp & prs(body): fixpar.append(n)
print('child mentions PR that closed a cited parent:',len(fixpar))
after=[n for n in sel if re.search(r'(після|і після|з|від|до) #\d{3,4}',rows[n]['txt'].split('|',4)[-1])]
print('mentions «після/з/до #PR» in body:',len(after))
both=sorted(set(fixpar)&set(after),reverse=True); print('both',len(both),both[:40])
lab2=C.Counter(lab[n][1] for n in both); print('roots of both',lab2.most_common())
json.dump(dict(fixpar=fixpar,after=after,both=both),open(SP+'/a1b.json','w'))
