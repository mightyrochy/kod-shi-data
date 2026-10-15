from pathlib import Path
import os,json,subprocess,re,tempfile,hashlib,sys,difflib
OUT=Path('/dev/shm/qa-updates-1078-1079');SRC=Path('/dev/shm/update-after-1078-1079');REPO=str(OUT/'repo');MAIN='7f9e9f8d51c7ea135b68eb3c12aa94c456de324f';B='аудит/БЕКЛОГ.md'
alts=[str(SRC/'repo'/'objects'),'/dev/shm/update-after-1077/repo/objects','/dev/shm/qa-updates-1077/repo/objects','/dev/shm/pachka-1510-5/repo/objects','/dev/shm/final-ready-batches-1655/repo/objects','/dev/shm/update-after-1045-1056/repo/objects','/dev/shm/qa-updates-1045-1056/repo/objects','/dev/shm/listquote5310/repo/.git/objects','/dev/shm/nested5301/repo/.git/objects','/workspace/scratch/update999/repo/objects']+json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text());ENV={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(p for p in alts if Path(p).is_dir()),'TMPDIR':str(OUT/'tmp')}
def git(*args,input=None):return subprocess.check_output(['git','-c','core.quotepath=false','--git-dir='+REPO,*args],env=ENV,input=input)
def blob(ref,p):return git('show',ref+':'+p)
def tree(ref):
 d={}
 for row in git('ls-tree','-rz',ref).split(b'\0'):
  if row:
   a,p=row.split(b'\t',1);d[p.decode()]=tuple(a.decode().split())
 return d
def rows(data):
 ids=[];d={}
 for line in data.splitlines(keepends=True):
  if m:=re.match(rb'^\|\s*(\d+)\s*\|',line):
   i=int(m[1]);assert i not in d,('duplicate',i);ids.append(i);d[i]=line
 return ids,d
for n in (map(int,sys.argv[1:]) if __name__=='__main__' else []):
 receipt=json.loads(((OUT/'proof/receipt-1094.json') if n==1094 else (SRC/f'pushed-{n}.json')).read_text());old=receipt['old'];head=receipt['sha'];base=git('merge-base',old,MAIN).decode().strip();tb,to,tm,tn=map(tree,[base,old,MAIN,head]);own={p for p in set(tb)|set(to) if tb.get(p)!=to.get(p)};expected=dict(tm);exact=[];combined=[]
 sources=receipt.get('sources',receipt.get('source_heads',[]));source_shas=[x['sha'] if isinstance(x,dict) else x for x in sources]
 for r in [old,MAIN]+source_shas:subprocess.run(['git','--git-dir='+REPO,'merge-base','--is-ancestor',r,head],env=ENV,check=True)
 for p in own-{B}:
  oldentry,baseentry,mainentry=to.get(p),tb.get(p),tm.get(p)
  if mainentry==baseentry or oldentry==mainentry:
   if oldentry is None:expected.pop(p,None)
   else:expected[p]=oldentry
   exact.append(p)
  else:
   assert oldentry and baseentry and mainentry,(n,p,'add/delete')
   with tempfile.TemporaryDirectory(dir=OUT/'tmp') as t:
    paths=[]
    for label,ref in [('own',old),('base',base),('main',MAIN)]:q=Path(t)/label;q.write_bytes(blob(ref,p));paths.append(str(q))
    proc=subprocess.run(['git','merge-file','-p',*paths],capture_output=True)
    assert proc.returncode==0,(n,p,'unresolved threeway',proc.returncode)
    data=proc.stdout;assert data==blob(head,p),(n,p,'not exact clean threeway')
   expected[p]=(oldentry[0],oldentry[1],hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest());combined.append(p)
 bb,bo,bm,bn=[blob(r,B) for r in [base,old,MAIN,head]];bi,br=rows(bb);oi,orr=rows(bo);mi,mr=rows(bm);ni,nr=rows(bn);ownids={i for i in set(br)|set(orr) if br.get(i)!=orr.get(i)};mergedrows={}
 assert set(nr)==set(mr)|set(orr),(n,'row loss/add');assert [i for i in ni if i in mr]==mi,(n,'main order')
 for i in ownids:
  if i in mr and mr[i]!=br.get(i) and mr[i]!=orr.get(i):
   if n==965 and i==4960:
    a,b=br[i].decode(),mr[i].decode();ops=[x for x in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if x[0]!='equal'];assert len(ops)==1 and ops[0][0]=='insert';add=b[ops[0][3]:ops[0][4]].encode();assert nr[i].count(add)==1 and nr[i].replace(add,b'',1)==orr[i];mergedrows[i]={'main_append_bytes':len(add),'own_exact_after_removal':True};continue
   if n==1083 and i==5238:
    assert i not in br and nr[i]==orr[i] and mr[i][:-3] in nr[i];mergedrows[i]={'own_row_exact':True,'main_full_row_prefix_preserved':True};continue
   assert i==3350 and n in [1059,1079],(n,i,'unexpected intersecting row')
   a,b=br[i].decode(),orr[i].decode();ops=[x for x in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes() if x[0]!='equal'];assert len(ops)==1 and ops[0][0]=='insert';_,_,_,c,d=ops[0];addition=b[c:d].encode();assert nr[i].count(addition)==1 and nr[i].replace(addition,b'',1)==mr[i],(n,i,'history lost');mergedrows[i]={'own_append_bytes':len(addition),'main_bytes_exact_after_removal':True}
  else:assert nr[i]==orr[i],(n,i,'own row changed')
 def foreign(data):return b''.join(l for l in data.splitlines(keepends=True) if not((m:=re.match(rb'^\|\s*(\d+)\s*\|',l)) and int(m[1]) in ownids))
 own_nonrow_delta=foreign(bo).removeprefix(foreign(bb)) if foreign(bo).startswith(foreign(bb)) else None
 if n in [1082,1094]:
  oldbase,oldown,mainlines,newlines=[foreign(x).splitlines(keepends=True) for x in [bb,bo,bm,bn]]
  oldops=[o for o in difflib.SequenceMatcher(None,oldbase,oldown,autojunk=False).get_opcodes() if o[0]!='equal'];newops=[o for o in difflib.SequenceMatcher(None,mainlines,newlines,autojunk=False).get_opcodes() if o[0]!='equal'];assert len(oldops)==len(newops)==1 and oldops[0][0]==newops[0][0]=='insert'
  _,a,b,c,d=oldops[0];_,e,f,g,h=newops[0];assert oldown[c:d]==newlines[g:h]==[b'\n'] and (oldbase[a-1]==mainlines[e-1] or (a<len(oldbase) and e<len(mainlines) and oldbase[a]==mainlines[e])),(n,'nonrow LF anchor lost');own_nonrow_delta=b'\n'
 else:assert foreign(bn)==foreign(bm),(n,'foreign board bytes')
 expected[B]=tn[B]
 assert expected==tn,(n,'tree differs',[(p,expected.get(p),tn.get(p)) for p in set(expected)|set(tn) if expected.get(p)!=tn.get(p)])
 for p in ['AGENTS.md','CLAUDE.md','аудит/ПРОДУКТ.md','build.txt','index.html','джерела/аудит/ДОСЯЖНІСТЬ.md']:assert tn[p]==tm[p],(n,p,'main file changed')
 assert all(tn[p]==tm[p] for p in tm if p.startswith('джерела/проби/') and p not in own)
 check=subprocess.run(['git','--git-dir='+REPO,'diff','--check',MAIN,head],env=ENV,capture_output=True);assert check.returncode==0,(n,check.stdout)
 paths=git('diff','--name-only',MAIN,head).decode().splitlines();assert not any(p.lower().endswith(('.png','.jpg','.jpeg','.webp','.svg','.gif','.mp4')) for p in paths)
 production=lambda p:p.startswith('.github/workflows/') or (p.startswith('джерела/') and not p.startswith(('джерела/проби/','джерела/аудит/','джерела/прилади/')))
 sourceexact=all(to.get(p)==tn.get(p) for p in set(to)|set(tn) if production(p))
 result=dict(production_inputs_exact_old=sourceexact,new_build_native_battery=0,pr=n,old=old,base=base,main=MAIN,head=head,tree=git('rev-parse',head+'^{tree}').decode().strip(),parents=[l[7:] for l in git('cat-file','commit',head).decode().split('\n\n',1)[0].splitlines() if l.startswith('parent ')],ancestry=True,source_heads=sources,whole_tree_exact=True,own_exact=sorted(exact),own_clean_threeway=sorted(combined),own_rows=sorted(ownids),combined_board_rows=mergedrows,own_rows_already_identical_main=[i for i in ownids if mr.get(i)==orr.get(i)],board_ids=len(nr),duplicates=0,main_order=True,foreign_board_bytes_exact=(n not in [1082,1094]),own_nonrow_delta_hex=(own_nonrow_delta.hex() if n in [1082,1094] else ''),foreign_board_exact_after_own_nonrow_delta=True,own_rows_preserved=True,main_rules_generated_exact=True,no_new_media=True,diff_check=0,ci='окремий exact-head gate координатора; не оцінено')
 (OUT/'proof'/f'{n}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(n,head,'treePASS','board',len(nr),'ownrows',sorted(ownids),'combined',combined)
