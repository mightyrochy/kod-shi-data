import sys,json,re,subprocess,pathlib,base64,os,hashlib,difflib
from hydrate import *
D=json.loads((P/'classification.json').read_text());B='аудит/БЕКЛОГ.md';main='47ac855c51b249c6112f0ba0ca64924a50bc32e4'
def rows(data):
 out={}
 for line in data.decode().splitlines(keepends=True):
  if m:=re.match(r'^\|\s*(\d+)\s*\|',line):
   i=int(m[1]);assert i not in out;out[i]=line
 return out
def prep(n):
 x=D[str(n)];h=x['old'];base=x['base'];tree=x['result'].splitlines()[0];assert x['rc'] in [0,1]
 br,orr,mr=[rows(git('show',s+':'+B)) for s in [base,h,main]];changes={i:line for i,line in orr.items() if line!=br.get(i)};comb={}
 if x['rc']==1:
  assert 'CONFLICT' in x['result'];assert all('БЕКЛОГ.md' in l for l in x['result'].splitlines() if l.startswith('CONFLICT'))
  merged=git('show',main+':'+B).decode()
  for i,line in changes.items():
   if i in mr:
    if mr[i]!=br.get(i):
     assert i==3350 and n in [1059,1079]
     ops=[(tag,a,b,c,d) for tag,a,b,c,d in difflib.SequenceMatcher(None,br[i],line,autojunk=False).get_opcodes() if tag!='equal']
     assert len(ops)==1 and ops[0][0]=='insert'
     _,a,b,c,d=ops[0];addition=line[c:d];assert line.replace(addition,'',1)==br[i]
     anchor=br[i][a:];assert mr[i].count(anchor)==1
     final=mr[i].replace(anchor,addition+anchor,1);assert final.replace(addition,'',1)==mr[i];comb[i]=final
     merged=merged.replace(mr[i],final,1)
    else:merged=merged.replace(mr[i],line,1)
   else:
    ids=list(orr);idx=ids.index(i);following=next((j for j in ids[idx+1:] if j in mr),None)
    if following is not None:merged=merged.replace(mr[following],line+mr[following],1)
    else:
     previous=next(j for j in reversed(ids[:idx]) if j in mr);merged=merged.replace(mr[previous],mr[previous]+line,1)
  blob=git('hash-object','-w','--stdin',input=merged.encode()).decode().strip();env={**E,'GIT_INDEX_FILE':str(P/f'index-{n}')}
  subprocess.check_call(['git','--git-dir='+R,'read-tree',tree],env=env);subprocess.check_call(['git','--git-dir='+R,'update-index','--add','--cacheinfo','100644,'+blob+','+B],env=env)
  tree=subprocess.check_output(['git','--git-dir='+R,'write-tree','--missing-ok'],env=env).decode().strip()
 fr=rows(git('show',tree+':'+B));assert set(fr)==set(mr)|set(orr)
 assert [i for i in fr if i in mr]==list(mr)
 for i,line in changes.items():assert fr[i]==comb.get(i,line),(n,i)
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
 proof={'n':n,'old':h,'branch':x['branch'],'main':main,'base':base,'tree':tree,'base_tree':git('rev-parse',main+'^{tree}').decode().strip(),'elements':entries,'newblobs':newblobs,'own_exact':exact,'combined':combined,'board_ids':len(fr),'board_main_ids':len(mr),'board_source_ids':len(orr),'own_board_rows':sorted(changes),'combined_board_rows':list(comb),'check':check.returncode,'changed_from_old':[p.decode() for p in git('diff','--name-only','-z',h,tree).split(b'\0') if p]}
 (P/f'prep-{n}.json').write_text(json.dumps(proof,ensure_ascii=False));print(n,tree,'exact',len(exact),'combined',combined,'rows',len(fr),'newblobs',len(newblobs))
for n in map(int,sys.argv[1:]):prep(n)

