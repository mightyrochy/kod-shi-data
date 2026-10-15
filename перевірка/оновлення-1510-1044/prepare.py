import sys,json,re,subprocess,pathlib,base64,os
sys.path.insert(0,'/workspace/scratch/update1046');from hydrate import git,E,R
P=pathlib.Path('/workspace/scratch/update1044');D=json.loads((P/'classification.json').read_text());B='аудит/БЕКЛОГ.md';main='2fb809276e2683f1f579249662aec7b4ce2740f7'
def rows(data):
 out={}
 for line in data.decode().splitlines(keepends=True):
  if m:=re.match(r'^\|\s*(\d+)\s*\|',line):
   i=int(m[1]);assert i not in out;out[i]=line
 return out
def prep(n):
 x=D[str(n)];h=x['old'];base=x['base'];tree=x['result'].splitlines()[0];assert x['rc'] in [0,1]
 br,orr,mr=[rows(git('show',s+':'+B)) for s in [base,h,main]];changes={i:line for i,line in orr.items() if line!=br.get(i)}
 if x['rc']==1:
  allowed=['БЕКЛОГ.md']+(['РІШЕННЯ_ВЛАСНИКА.md'] if n==991 else [])
  assert 'CONFLICT' in x['result'];assert all(any(p in l for p in allowed) for l in x['result'].splitlines() if l.startswith('CONFLICT'))
  merged=git('show',main+':'+B).decode()
  for i,line in changes.items():
   if i in mr:
    assert mr[i]==br.get(i),(n,i);merged=merged.replace(mr[i],line,1)
   else:
    ids=list(orr);idx=ids.index(i);following=next((j for j in ids[idx+1:] if j in mr),None)
    if following is not None:merged=merged.replace(mr[following],line+mr[following],1)
    else:
     previous=next(j for j in reversed(ids[:idx]) if j in mr);merged=merged.replace(mr[previous],mr[previous]+line,1)
  blob=git('hash-object','-w','--stdin',input=merged.encode()).decode().strip();env={**E,'GIT_INDEX_FILE':str(P/f'index-{n}')}
  subprocess.check_call(['git','--git-dir='+R,'read-tree',tree],env=env);subprocess.check_call(['git','--git-dir='+R,'update-index','--add','--cacheinfo','100644,'+blob+','+B],env=env)
  if n==991:
   path='аудит/РІШЕННЯ_ВЛАСНИКА.md';b,o,m=[git('show',s+':'+path) for s in [base,h,main]];assert o.startswith(b)
   addition=o[len(b):];anchor=b.splitlines(keepends=True)[-1];assert m.count(anchor)==1 and addition not in m
   merged=m.replace(anchor,anchor+addition,1);assert merged.replace(addition,b'',1)==m
   blob2=git('hash-object','-w','--stdin',input=merged).decode().strip();subprocess.check_call(['git','--git-dir='+R,'update-index','--add','--cacheinfo','100644,'+blob2+','+path],env=env)
  tree=subprocess.check_output(['git','--git-dir='+R,'write-tree'],env=env).decode().strip()
 fr=rows(git('show',tree+':'+B));assert set(fr)==set(mr)|set(orr)
 assert [i for i in fr if i in mr]==list(mr)
 for i,line in changes.items():assert fr[i]==line,(n,i)
 for i,line in mr.items():
  if i not in changes:assert fr[i]==line,(n,i)
 assert not re.search(rb'^(<<<<<<< |=======\s*$|>>>>>>> )',git('show',tree+':'+B),re.M)
 own=[p.decode() for p in git('diff','--name-only','-z',base,h).split(b'\0') if p];exact=[];combined=[]
 for path in own:(exact if git('rev-parse',h+':'+path)==git('rev-parse',tree+':'+path) else combined).append(path)
 known={rec.split(b'\t')[0].split()[2].decode() for ref in [h,main] for rec in git('ls-tree','-rz',ref).split(b'\0') if rec};entries=[];newblobs=[];chunks=git('diff-tree','-r','--raw','-z',main,tree).split(b'\0')
 for i in range(0,len(chunks)-1,2):
  m=chunks[i].decode().split();path=chunks[i+1].decode();sha=m[3] if m[4]!='D' else None;entries.append({'path':path,'mode':m[1],'type':'blob','sha':sha})
  if sha and sha not in known:newblobs.append({'sha':sha,'content':base64.b64encode(git('cat-file','blob',sha)).decode()})
 assert all(not e['path'].lower().endswith(('.png','.jpg','.jpeg','.webp','.gif','.svg','.mp4')) for e in entries)
 check=subprocess.run(['git','--git-dir='+R,'diff','--check',main,tree],env=E,capture_output=True,text=True);assert check.returncode==0,check.stdout
 proof={'n':n,'old':h,'branch':x['branch'],'main':main,'base':base,'tree':tree,'base_tree':git('rev-parse',main+'^{tree}').decode().strip(),'elements':entries,'newblobs':newblobs,'own_exact':exact,'combined':combined,'board_ids':len(fr),'board_main_ids':len(mr),'board_source_ids':len(orr),'own_board_rows':sorted(changes),'check':check.returncode,'changed_from_old':[p.decode() for p in git('diff','--name-only','-z',h,tree).split(b'\0') if p]}
 (P/f'prep-{n}.json').write_text(json.dumps(proof,ensure_ascii=False));print(n,tree,'exact',len(exact),'combined',combined,'rows',len(fr),'newblobs',len(newblobs))
for n in map(int,sys.argv[1:]):prep(n)
