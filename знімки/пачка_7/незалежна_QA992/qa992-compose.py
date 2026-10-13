import subprocess,re,json,hashlib,pathlib
root='/tmp/liusterko-pachka-1310-3';media='/tmp/liusterko-pachka-1310-3-media'
base='834d956e31ab986905d80b08941746d18d25de43';head='af1ab8c37eeb45469646e715c8640f5ab5b86c2d';a='2f3c56cb12173dc5232dde7e798caf1f179a6593';b='45b32dc958b870f7008881d206d4db927690394e';ev='d45d5d5a4c43cbf3e70af7476a4702cdcd7cba0e';srcmedia='01d7fae41cee83e6da392911e24210e118bfa74a'
def git(*args,where=root):return subprocess.check_output(['git','-C',where,*args])
def tree(sha):return dict(line.split('\t',1)[::-1] for line in git('-c','core.quotepath=false','ls-tree','-r',sha).decode().splitlines())
def blob(sha,p):return git('show',sha+':'+p)
assert git('rev-parse','HEAD').decode().strip()==head,'HEAD'
for sha in [base,a,b]:assert subprocess.run(['git','-C',root,'merge-base','--is-ancestor',sha,head]).returncode==0,'ancestry'
bt,ht=tree(base),tree(head);changed=[p for p in bt.keys()|ht.keys() if bt.get(p)!=ht.get(p)];assert len(changed)==6,changed
handover='аудит/передачі/2026-10-13_1320.md'
for p in changed:assert blob(head,p)==blob(b if p==handover else a,p),p
assert git('-c','core.quotepath=false','diff','--name-only',git('merge-base',base,b).decode().strip(),b).decode().splitlines()==[handover],'989actual'
assert not git('diff','--check',base,head),'diffcheck'
for p in changed:assert not re.search(rb'^(<<<<<<<|=======|>>>>>>>)',blob(head,p),re.M),('conflict',p)
board=blob(head,'аудит/БЕКЛОГ.md').decode();oldboard=blob(base,'аудит/БЕКЛОГ.md').decode();ids=re.findall(r'^\|\s*(\d+)\s*\|',board,re.M);assert len(ids)==1305 and len(set(ids))==1305,'ids'
oldrows=re.findall(r'^\|\s*\d+\s*\|.*$',oldboard,re.M);assert all(r in board for r in oldrows),'oldrows';assert 'ЗАКРИТО #990' in re.search(r'^\|\s*5205\s*\|.*$',board,re.M)[0],'5205';assert 'ВІДКРИТО' in re.search(r'^\|\s*4944\s*\|.*$',board,re.M)[0],'4944'
assert bt['index.html']==ht['index.html'] and bt['джерела/аудит/ДОСЯЖНІСТЬ.md']==ht['джерела/аудит/ДОСЯЖНІСТЬ.md'],'generated'
source=blob(head,'джерела/показ.html').decode();full=pathlib.Path('/tmp/pachka-1310-3-full.html').read_text();assert json.load(open('/tmp/qa992-helper-tokens.json'))['equal'],'built helper tokens'
calls=re.findall(r'привʼязатиГолос\(\{кнопка:',source);assert len(calls)==2,'bindings'
assert not any(re.search(r'\.(png|jpg|webp|svg|gif)$',p) for p in changed),'productMedia'
evnames=git('-c','core.quotepath=false','diff','--name-status',head,ev,where=media).decode().splitlines();assert len(evnames)==64 and all(x.startswith('A\t') for x in evnames),('archive',len(evnames))
sourceNames=git('-c','core.quotepath=false','diff','--name-only',a,srcmedia,where=media).decode().splitlines();assert len(sourceNames)==17,'sourceMedia'
for p in sourceNames:assert git('show',srcmedia+':'+p,where=media)==git('show',ev+':'+p,where=media),('mediaBytes',p)
assert sum(p.endswith('.png') for p in sourceNames)==5,'png'
battery=json.load(open('/tmp/pachka-1310-3-evidence/батарея/результати.json'));assert battery['head']==head and battery['успіх'] and all(x['код']==0 for x in battery['steps']),'battery'
result={'head':head,'base':base,'sixExactSourceFiles':sorted(changed),'otherMainBlobsUnchanged':len(bt.keys()-set(changed)),'ancestry':True,'boardIDs':len(ids),'duplicates':0,'previousRowsUnchanged':True,'4944':'OPEN','fullUIhelperExactBytes':True,'genericActualBindings':len(calls),'archive64Additions0Deletions':True,'sourceEvidence17Files5PNGExactFinalBytes':True,'batteryHead':battery['head'],'batteryElapsed':battery['elapsed_seconds'],'fullUIsha256':hashlib.sha256(full.encode()).hexdigest()};pathlib.Path('/tmp/qa992-composition.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
