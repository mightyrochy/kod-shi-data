from pathlib import Path
import subprocess,json,hashlib,re,collections,gzip
root=Path('/tmp/liusterko-pachka-1310-4');out=Path('/tmp/pachka-1310-4-evidence');base='7c90a0093b5d7dc8587a90c541eaf11e23b9a3be';head='cfbe2671b868cdcf124d25bd3d1c895fc14055fe';sources={994:'52fc8503656b13369ad538ec30d920701cf45dfe',995:'4d60cce0ecadca38252b11f934c874b871bb8bf7'}
def git(*a):return subprocess.check_output(['git','-C',str(root),*a])
def blob(ref,path):return git('show',ref+':'+path)
def tree(ref):return {x.split('\t',1)[1]:x.split()[2] for x in git('-c','core.quotepath=false','ls-tree','-r',ref).decode().splitlines()}
assert git('rev-parse','HEAD').decode().strip()==head
main=tree(base);actual=tree(head);expected=dict(main);owned=[];board='аудит/БЕКЛОГ.md';before=blob(base,board).decode();combined=before
for n,sha in sources.items():
 subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',sha,head],check=True)
 files=git('-c','core.quotepath=false','diff','--name-only',base,sha).decode().splitlines();source=tree(sha)
 for p in files:
  if p==board:continue
  expected[p]=source[p];assert actual[p]==source[p];owned.append({'source':n,'path':p,'blob':source[p],'sha256':hashlib.sha256(blob(sha,p)).hexdigest()})
 oldrows={m.group(1):m.group(0) for m in re.finditer(r'^\|\s*(\d+)\s*\|.*$',before,re.M)};newrows={m.group(1):m.group(0) for m in re.finditer(r'^\|\s*(\d+)\s*\|.*$',blob(sha,board).decode(),re.M)}
 changed=[k for k,v in oldrows.items() if newrows[k]!=v];assert set(changed)==({'4944'} if n==994 else {'5191','5192','5193','5194'})
 for k in changed:
  assert 'ВІДКРИТО' in newrows[k];combined=combined.replace(oldrows[k],newrows[k])
  if n==995:
   a=oldrows[k].split('|');b=newrows[k].split('|');assert len(a)==len(b);assert [i for i,(x,y) in enumerate(zip(a,b)) if x!=y]==[5]
assert blob(head,board).decode()==combined;expected[board]=actual[board];assert actual==expected
rows=re.findall(r'^\|\s*(\d+)\s*\|',combined,re.M);duplicates={k:v for k,v in collections.Counter(rows).items() if v>1};assert len(rows)==1305 and not duplicates
changed=git('-c','core.quotepath=false','diff','--name-only',base,head).decode().splitlines();assert len(changed)==13
for p in changed:assert not re.search(rb'^(<<<<<<<|=======|>>>>>>>)',blob(head,p),re.M)
assert git('diff','--check',base,head)==b''
assert not any(re.search(r'\.(png|jpe?g|webp|svg|gif|mp4)$',p,re.I) for p in changed)
assert blob(head,'джерела/показ.html')==blob(sources[994],'джерела/показ.html')
assert len(list((root/'.github/workflows').glob('*.yml')))==4
format_proof={}
for p in changed:
 if p.endswith('.json.gz'):
  compressed=blob(head,p);b=gzip.decompress(compressed);v=json.loads(b);assert int.from_bytes(compressed[4:8],'little')==0;assert b==(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
  if isinstance(v,list):assert v==sorted(set(v))
  else:assert all(a==sorted(set(a)) for a in v.values())
  format_proof[p]={'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'json_sha256':hashlib.sha256(b).hexdigest()}
result={'head':head,'base':base,'sources':sources,'source_owned_bytes':owned,'full_tree_blobs':len(actual),'main_other_blobs_unchanged':len(main)-len([p for p in changed if p in main]),'changed_files':changed,'board_rows':len(rows),'duplicate_ids':duplicates,'board':'точна композиція рядка4944 source994 та4клітинок опису5191–4 source995; усііншібайти main; усі5OPEN','product_code':'тільки byteexact джерела/показ.html source994','workflows_present':4,'new_product_media':0,'markers':0,'diffcheck':0,'format':format_proof,'source_native':'29d077b8fdee5937f0f5c597050b78ad5b92aee1','limits':'Вимірнаявності неякістьфото/моделей; archiveUIsynthetic notlive;globalAAOPEN;pool28982notLLMauthorization'}
(out/'композиція.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_owned_bytes','format','changed_files']},ensure_ascii=False,indent=2))
