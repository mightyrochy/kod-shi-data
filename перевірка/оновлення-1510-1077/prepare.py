import sys,json,re,subprocess,pathlib,base64,os,hashlib,difflib
from hydrate import *
D=json.loads((P/'classification.json').read_text());B='аудит/БЕКЛОГ.md';main='32395d4239a2758c3293ee4e605364e28bc8dc94'
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
    if mr[i]!=br.get(i) and line!=mr[i]:
     if n==1083 and i==5238:
      assert br.get(i) is None
      assert line.startswith(mr[i][:-3]) and line.endswith(' |\n')
      final=line
     elif n==965 and i==4960:
      bc,oc,mc=[v.strip().split('|') for v in [br[i],line,mr[i]]];assert len(bc)==len(oc)==len(mc)
      fc=[]
      for b,o,m in zip(bc,oc,mc):
       if o==b:fc.append(m)
       elif m==b or o==m:fc.append(o)
       else:
        common=b.rstrip();assert o.startswith(common) and m.startswith(common)
        fc.append(common+o[len(common):].rstrip()+m[len(common):])
      final='|'.join(fc)+'\n'
      assert '**ВІДКРИТО**' in final and 'салату назв 0 з 44' in final and '#965 передає визначення' in final
     else:raise AssertionError((n,i,'unknown overlap'))
     comb[i]=final;merged=merged.replace(mr[i],final,1)
    else:merged=merged.replace(mr[i],line,1)
   else:
    ids=list(orr);idx=ids.index(i);following=next((j for j in ids[idx+1:] if j in mr),None)
    if following is not None:merged=merged.replace(mr[following],line+mr[following],1)
    else:
     previous=next(j for j in reversed(ids[:idx]) if j in mr);merged=merged.replace(mr[previous],mr[previous]+line,1)
  if n==1082:
   merged=merged.replace(orr[5685],'\n'+orr[5685],1)
  blob=git('hash-object','-w','--stdin',input=merged.encode()).decode().strip()
  def replace_entry(t,name,sha):
   data=git('ls-tree','-z',t);out=[];found=False
   for rec in data.split(b'\0'):
    if not rec:continue
    meta,path=rec.split(b'\t',1)
    if path.decode()==name:
     mode,typ,_=meta.decode().split();rec=(mode+' '+typ+' '+sha).encode()+b'\t'+path;found=True
    out.append(rec)
   assert found,name
   return git('mktree','-z','--missing',input=b'\0'.join(out)+b'\0').decode().strip()
  audit=git('rev-parse',tree+':аудит').decode().strip();audit=replace_entry(audit,'БЕКЛОГ.md',blob);tree=replace_entry(tree,'аудит',audit)
 fr=rows(git('show',tree+':'+B));assert set(fr)==set(mr)|set(orr)
 assert [i for i in fr if i in mr]==list(mr)
 for i,line in changes.items():assert fr[i]==comb.get(i,line),(n,i)
 for i,line in mr.items():
  if i not in changes:assert fr[i]==line,(n,i)
 assert not re.search(rb'^(<<<<<<< |=======\s*$|>>>>>>> )',git('show',tree+':'+B),re.M)
 own=[p.decode() for p in git('diff','--name-only','-z',base,h).split(b'\0') if p];exact=[];combined=[]
 for path in own:(exact if git('rev-parse',h+':'+path)==git('rev-parse',tree+':'+path) else combined).append(path)
 known=set();entries=[];newblobs=[];chunks=git('diff-tree','-r','--raw','-z',main,tree).split(b'\0')
 for i in range(0,len(chunks)-1,2):
  m=chunks[i].decode().split();path=chunks[i+1].decode();sha=m[3] if m[4]!='D' else None;entries.append({'path':path,'mode':m[1],'type':'blob','sha':sha})
  for ref in [h,main]:
   try:known.add(git('rev-parse','--verify',ref+':'+path).decode().strip())
   except subprocess.CalledProcessError:pass
  if sha and sha not in known:newblobs.append({'sha':sha,'content':base64.b64encode(git('cat-file','blob',sha)).decode()})
 assert all(not e['path'].lower().endswith(('.png','.jpg','.jpeg','.webp','.gif','.svg','.mp4')) for e in entries)
 check=subprocess.run(['git','--git-dir='+R,'diff','--check',main,tree],env=E,capture_output=True,text=True);assert check.returncode==0,check.stdout
 proof={'n':n,'old':h,'branch':x['branch'],'main':main,'base':base,'tree':tree,'base_tree':git('rev-parse',main+'^{tree}').decode().strip(),'elements':entries,'newblobs':newblobs,'own_exact':exact,'combined':combined,'board_ids':len(fr),'board_main_ids':len(mr),'board_source_ids':len(orr),'own_board_rows':sorted(changes),'combined_board_rows':list(comb),'check':check.returncode,'changed_from_old':'Inherited main323 docs/source probes only; authoritative main-compare.json plus own exact path SHA map.'}
 (P/f'prep-{n}.json').write_text(json.dumps(proof,ensure_ascii=False));print(n,tree,'exact',len(exact),'combined',combined,'rows',len(fr),'newblobs',len(newblobs))
for n in map(int,sys.argv[1:]):prep(n)

