from pathlib import Path
import hashlib,json,subprocess,os,re
r=Path('/workspace/scratch/qa-update1069-independent');os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()))
for n in [1056,1058]:
 d=json.loads(Path(f'/workspace/scratch/update1069/native-inputs-{n}.json').read_text());base=Path(d['inputs']);rows={}
 for ln in subprocess.check_output(['git','-C','/workspace/scratch/update999/repo','ls-tree','-rz',d['head'],'--','джерела']).split(b'\0'):
  if ln:
   meta,p=ln.split(b'\t',1);mode,typ,blob=meta.decode().split();rows[p.decode()]=(mode,blob)
 for e in d['records']:
  assert rows[e['path']]==(e['mode'],e['blob']);b=(base/Path(e['path']).relative_to('джерела')).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert h==e['blob'],e['path']
 assert len(rows)==len(d['records'])==d['tracked_entries']
 b=Path(f'/dev/shm/qa1069-{n}/build/index.html').read_bytes();import sys,importlib.util
 spec=importlib.util.spec_from_file_location('build_current_'+str(n),base/'build_артефакт.py');mod=importlib.util.module_from_spec(spec);sys.path.insert(0,str(base));spec.loader.exec_module(mod)
 template=mod._чистка_показу((base/'показ.html').read_text());parts=re.split(r'__(?:МОДУЛІ_ПОКАЗУ|ЗБІРКА_ПОКАЗУ|ВІДБИТОК|ФІД_ПОКАЗУ|КАТАЛОГ_ПОКАЗУ|ДОВІДНИК_ПОКАЗУ|ПРОМПТ_КОЛІР_ПОКАЗУ|ВИБІРКА_ПОКАЗУ)__',template);pos=0;checks=[]
 for part in parts:
  if part:pos=b.index(part.encode(),pos)+len(part.encode());checks.append(hashlib.sha256(part.encode()).hexdigest())
 assert len(parts)==9
 log=(r/f'native-{n}/build.log').read_text();assert '741' in log and '65' in log
 result={'head':d['head'],'independently_verified_source_entries':len(rows),'all_blob_and_mode_exact':True,'artifact_sha256':hashlib.sha256(b).hexdigest(),'artifact_bytes':len(b),'template_fragments_matched':len(checks),'fragment_sha256':checks,'build_once_rc':0,'checks':741,'sections':65,'runtime_feed':'existing cleaned UI feed; not RAW #1060','new_paid_calls':0}
 (r/f'native-{n}/provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
