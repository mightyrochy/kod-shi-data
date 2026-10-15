from pathlib import Path
import os,json,subprocess,re,tempfile,hashlib,sys
out=Path('/dev/shm/qa-update1064-independent');source=Path(__import__('sys').argv[1]);repo='/workspace/scratch/update999/repo';main='b02ef36e2d42f089c7c9366ebd9bdeabf00c45e3'
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()));os.environ['TMPDIR']=str(out/'tmp')
def git(*a,input=None):return subprocess.check_output(['git','-c','core.quotepath=false','-C',repo,*a],input=input)
def blob(ref,path):return git('show',ref+':'+path)
def tree(ref):
 d={}
 for line in git('ls-tree','-rz',ref).split(b'\0'):
  if line:
   meta,path=line.split(b'\t',1);d[path.decode()]=tuple(meta.decode().split())
 return d
def rows(data):
 ids=[];d={}
 for line in data.splitlines(keepends=True):
  m=re.match(rb'^\|\s*(\d+)\s*\|',line)
  if m:i=int(m[1]);assert i not in d;d[i]=line;ids.append(i)
 return ids,d
D=json.loads(Path('/dev/shm/liusterko-update1064/classification.json').read_text());results=[]
for n in map(int,sys.argv[2:]):
 pushed=json.loads((source/f'pushed-{n}.json').read_text());old=D[str(n)]['old'];base=D[str(n)]['base'];head=pushed['sha'];tbase,told,tmain,tnew=[tree(r) for r in [base,old,main,head]]
 for r in [old,main]+[x['sha'] for x in pushed.get('sources',pushed.get('source_heads',[]))]:subprocess.run(['git','-C',repo,'merge-base','--is-ancestor',r,head],check=True)
 own={p for p in set(tbase)|set(told) if tbase.get(p)!=told.get(p)};expected=dict(tmain);exact=[];combined=[];details={}
 for p in own:
  if p=='аудит/БЕКЛОГ.md':continue
  if p=='аудит/РІШЕННЯ_ВЛАСНИКА.md' and n==991 and D[str(n)]['rc']!=0 and tmain.get(p)!=tbase.get(p):
   b,o,m,f=[blob(r,p) for r in [base,old,main,head]];assert o.startswith(b);addition=o[len(b):];assert addition and f.count(addition)==1;assert f.replace(addition,b'',1)==m
   anchor=b.splitlines(keepends=True)[-1];assert f.count(anchor)==1;assert anchor+addition in f;expected[p]=(tnew[p][0],tnew[p][1],git('hash-object','--stdin',input=f).decode().strip());combined.append(p);details[p]={'source_append_bytes':len(addition),'all_main_bytes_preserved':True};continue
  a,b,c=told.get(p),tbase.get(p),tmain.get(p)
  if c==b or a==c:
   if a is None:expected.pop(p,None)
   else:expected[p]=a
   exact.append(p)
  else:
   assert a and b and c,(n,p,'unsupported add/delete conflict')
   with tempfile.TemporaryDirectory(prefix='threeway-',dir=out/'tmp') as tmp:
    paths=[]
    for name,ref in [('old',old),('base',base),('main',main)]:q=Path(tmp)/name;q.write_bytes(blob(ref,p));paths.append(str(q))
    proc=subprocess.run(['git','merge-file','-p',*paths],capture_output=True);assert proc.returncode==0,(n,p,proc.returncode)
    data=proc.stdout;assert data==blob(head,p),(n,p,'not exact clean threeway')
   expected[p]=(a[0],a[1],git('hash-object','--stdin',input=data).decode().strip());combined.append(p);details[p]={'clean_threeway_exact':True}
 B='аудит/БЕКЛОГ.md';bb,bo,bm,bf=[blob(r,B) for r in [base,old,main,head]];bi,br=rows(bb);oi,orr=rows(bo);mi,mr=rows(bm);fi,fr=rows(bf)
 ownrows={i for i in set(br)|set(orr) if br.get(i)!=orr.get(i)}
 for i in ownrows:
  if n==1067 and i==5631:
   marker='  **ПІСЛЯ #1067:**'.encode();after=orr[i][orr[i].index(marker):-3];assert fr[i].count(after)==1;assert fr[i].replace(after,b'',1).replace('**ЗАКРИТО #1067**'.encode(),'**ВІДКРИТО**'.encode(),1)==mr[i];assert fr[5634]==mr[5634]
  else:assert fr[i]==orr[i]
 assert [i for i in fi if i in mr]==mi;assert set(fr)==set(mr)|set(orr)
 def foreign(data):return b''.join(line for line in data.splitlines(keepends=True) if not((m:=re.match(rb'^\|\s*(\d+)\s*\|',line)) and int(m[1]) in ownrows))
 assert foreign(bf)==foreign(bm),(n,'foreignboardbytes');expected[B]=tnew[B]
 assert expected==tnew,(n,'tree differs',[(p,expected.get(p),tnew.get(p)) for p in set(expected)|set(tnew) if expected.get(p)!=tnew.get(p)])
 for p in ['AGENTS.md','CLAUDE.md','аудит/ПРОДУКТ.md','.github/workflows/zbirka.yml','джерела/проби/смужка_оновлення.py']:assert tnew[p]==tmain[p]
 check=subprocess.run(['git','-C',repo,'diff','--check',main,head],capture_output=True);assert check.returncode==0
 newpaths=git('diff','--name-only',main,head).decode().splitlines();assert not any(p.lower().endswith(('.png','.jpg','.jpeg','.webp','.svg','.gif','.mp4')) for p in newpaths)
 input_exact=all(told.get(p)==tnew.get(p) for p in tnew if p.startswith('джерела/') or p.startswith('.github/workflows/'))
 parents=git('show','-s','--format=%P',head).decode().strip().split()
 result={'pr':n,'old':old,'base':base,'main':main,'head':head,'tree':git('rev-parse',head+'^{tree}').decode().strip(),'ancestry':True,'parents':parents,'whole_tree_composition_exact':True,'nonboard_own_files_exact':exact,'combined':combined,'combined_details':details,'board_ids':len(fi),'duplicate_ids':0,'own_rows':sorted(ownrows),'own_rows_exact':True,'foreign_board_bytes_exact':True,'main_order_preserved':True,'new_main_rules_exact':True,'no_new_media':True,'entire_product_inputs_equal_old':input_exact,'product_tests_repeated':False,'ci_acceptance':'окремий exact-head gate координатора; не переноситься'}
 (out/f'{n}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');results.append(result)
print(json.dumps(results,ensure_ascii=False,indent=2))
