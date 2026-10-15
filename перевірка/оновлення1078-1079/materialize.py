from pathlib import Path
import sys,json,hashlib,os
sys.path.insert(0,str(Path(__file__).parent));from composition import git,OUT
H='0ffb624821c5972d7361c60f73dabcd52e61d9ee';root=OUT/'current';sources=[Path('/dev/shm/pachka-1510-5/work'),Path('/dev/shm/qa-batch-1510-5/work'),Path('/dev/shm/pachka-1510-3/repo'),Path('/workspace/kod-shi-data'),Path('/workspace/scratch/accept3541/repo'),Path('/workspace/scratch/4944-crop-current/repo'),Path('/workspace/scratch/qa1056-independent/proof')];records=[];linked=written=0;missing=[]
for ap in json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()):
 q=Path(ap).parent
 if q.name=='.git':q=q.parent
 if q not in sources:sources.append(q)
for row in git('ls-tree','-rz',H,'--','джерела').split(b'\0'):
 if not row:continue
 m,p=row.split(b'\t');mode,kind,sha=m.decode().split();p=p.decode();assert kind=='blob';dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True)
 found=None
 for src in sources:
  f=src/p
  if not f.is_file():continue
  data=f.read_bytes();digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
  if digest==sha:found=f.resolve();break
 if found:
  if not dest.exists():dest.symlink_to(found)
  linked+=1;storage='readonly_link'
 else:
  try:data=git('cat-file','blob',sha)
  except Exception:missing.append(dict(path=p,sha=sha));continue
  dest.write_bytes(data);written+=1;storage='own_copy'
 data=dest.read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==sha
 records.append(dict(path=p,blob=sha,mode=mode,bytes=len(data),storage=storage))
(OUT/'missing-native.json').write_text(json.dumps(missing));assert not missing,('missing',len(missing),missing[:8])
# Existing cleaned runtime feed is UI fixture data, not a fresh catalogue/RAW acceptance.
feed=Path('/dev/shm/pachka-1510-5/work/джерела/каталог_повний.xml');assert feed.is_file();target=root/'джерела'/'каталог_повний.xml'
if not target.exists():target.symlink_to(feed.resolve())
data=feed.read_bytes()
result=dict(head=H,tracked_entries=len(records),records=records,linked=linked,written=written,feed=dict(path=str(feed),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),kind='existing cleaned UI runtime feed; not RAW photo acceptance'),inputs=str(root/'джерела'))
(OUT/'proof'/'inputs1094.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('source entries',len(records),'readonly links',linked,'own copies',written,'feed bytes',len(data))
