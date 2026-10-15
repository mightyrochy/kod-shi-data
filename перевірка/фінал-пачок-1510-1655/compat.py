from hydrate import *
import re,hashlib,collections
M='0750a9494e0057995d5f0b4151a71a09b6ddae14';A='9abcc66f0b40e1f2f8c62c90af8786debd085ebf';B='751458dc348f9299405008e9e827ce92943f75f4';BASE='32395d4239a2758c3293ee4e605364e28bc8dc94';BOARD='аудит/БЕКЛОГ.md'
E.update(GIT_AUTHOR_NAME='Read-only QA',GIT_AUTHOR_EMAIL='qa@example.invalid',GIT_COMMITTER_NAME='Read-only QA',GIT_COMMITTER_EMAIL='qa@example.invalid',GIT_AUTHOR_DATE='2026-10-15T17:00:00Z',GIT_COMMITTER_DATE='2026-10-15T17:00:00Z')
def out(*a):return git(*a).stdout.decode().strip()
def tree(ref):
 d={}
 for x in git('ls-tree','-rz',ref).stdout.split(b'\0'):
  if x:
   a,p=x.split(b'\t',1);d[p.decode()]=tuple(a.decode().split())
 return d
def blob(ref,path):return git('show',ref+':'+path).stdout
def rows(ref):
 d={};order=[]
 for l in blob(ref,BOARD).splitlines(keepends=True):
  m=re.match(rb'^\|\s*(\d+)\s*\|',l)
  if m:
   i=int(m[1]);assert i not in d,('dup',ref,i);d[i]=l;order.append(i)
 return order,d
r={}
for label,a,b in [('main1078',M,A),('main1079',M,B),('1078x1079',A,B)]:
 p=git('merge-tree','--write-tree',a,b,check=False);assert p.returncode==0,(label,p.stderr);t=p.stdout.decode().strip();r[label]={'a':a,'b':b,'rc':0,'tree':t};(P/(label+'.txt')).write_bytes(p.stdout)
for label,first,other in [('1078then1079',A,B),('1079then1078',B,A)]:
 t=r['main'+('1078' if first==A else '1079')]['tree'];c=out('commit-tree',t,'-p',M,'-p',first,'-m','Local read-only compatibility fixture; never published')
 p=git('merge-tree','--write-tree',c,other,check=False);assert p.returncode==0,(label,p.stdout,p.stderr);r[label]={'synthetic_local_commit':c,'tree':p.stdout.decode().strip(),'rc':0};(P/(label+'.txt')).write_bytes(p.stdout)
assert r['1078then1079']['tree']==r['1079then1078']['tree'];FINAL=r['1078then1079']['tree'];tm,ta,tb,tbase,tf=map(tree,[M,A,B,BASE,FINAL]);ownA={p for p in ta if ta.get(p)!=tbase.get(p)};ownB={p for p in tb if tb.get(p)!=tbase.get(p)}
assert ownA&ownB=={BOARD},ownA&ownB
for p in set(tm)|set(ta)|set(tb):
 if p==BOARD:continue
 expected=ta.get(p) if p in ownA else tb.get(p) if p in ownB else tm.get(p)
 assert tf.get(p)==expected,('unexpected tree bytes',p)
mi,mr=rows(M);ai,ar=rows(A);bi,br=rows(B);basi,basr=rows(BASE);fi,fr=rows(FINAL)
ida={i for i in set(ar)|set(basr) if ar.get(i)!=basr.get(i)};idb={i for i in set(br)|set(basr) if br.get(i)!=basr.get(i)};assert ida=={5170,5180,5631};assert idb=={3350,3710};ownids=ida|idb
assert set(fr)==set(mr)|set(ar)|set(br);assert [i for i in fi if i in mr]==mi
for i in fr:
 expected=ar.get(i) if i in ida else br.get(i) if i in idb else mr.get(i)
 assert fr[i]==expected,('row bytes',i)
def foreign(ref):
 return b''.join(l for l in blob(ref,BOARD).splitlines(keepends=True) if not((m:=re.match(rb'^\|\s*(\d+)\s*\|',l)) and int(m[1]) in ownids))
assert foreign(FINAL)==foreign(M)
assert 'ВІДКРИТО'.encode() in fr[3350] and 'ВІДКРИТО'.encode() in fr[3710]
for path in ['AGENTS.md','CLAUDE.md','аудит/ПРОДУКТ.md']:assert tm[path]==tbase[path]
sourcepaths=[p for p in set(tm)|set(tbase) if p.startswith('джерела/') and not p.startswith('джерела/аудит/') or p.startswith('.github/workflows/')]
assert all(tm.get(p)==tbase.get(p) for p in sourcepaths)
diff=git('diff','--check',M,FINAL,check=False);assert diff.returncode==0,diff.stdout
ancestry=[]
for head,sources in [(A,['c2ee0b83bd74ef412fec9905493c34392c905fcf','f6739ecc4213363c90e57b825c4c7d95e69aafb6','2660211a681403687494ef71ddcd32b11814d48e']),(B,['24b40122144b20af0904e8bf101e1f609b54ada3','fca5421d9cebe32e547d48ccaeec8352644e2e44'])]:
 for source in [BASE]+sources:assert git('merge-base','--is-ancestor',source,head,check=False).returncode==0;ancestry.append({'head':head,'ancestor':source})
result={'main':M,'base':BASE,'head1078':A,'head1079':B,'merge_tree':r,'both_orders_identical':True,'final_tree':FINAL,'whole_tree_composition_exact':True,'board':{'main_ids':len(mr),'final_ids':len(fr),'duplicates':0,'own1078':sorted(ida),'own1079':sorted(idb),'own_bytes_exact':True,'foreign_full_bytes_exact_main':True,'main_order_exact':True,'3350_3710':'OPEN; model/photo/AA quality unaccepted'},'main_delta_paths':out('diff','--name-only',BASE,M).splitlines(),'all_production_source_and_workflow_exact':True,'rules_exact':True,'ancestry':ancestry,'diff_check':0,'local_synthetic_only':True,'source_main_ref_mutation':0,'own_build_native_battery_model_paid':0}
(P/'compatibility.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
