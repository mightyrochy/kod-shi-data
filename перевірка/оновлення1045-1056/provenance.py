from pathlib import Path
import sys,json,hashlib,re,importlib.util,base64,io,zipfile,bz2
ROOT=Path('/dev/shm/qa-updates-1045-1056');d=json.loads((ROOT/'proof/inputs1078.json').read_text());src=Path(d['inputs']);html=(ROOT/'current1078.html').read_bytes()
for r in d['records']:
 data=(ROOT/'current'/r['path']).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==r['blob']
sys.path.insert(0,str(src));spec=importlib.util.spec_from_file_location('provenance_builder',src/'build_артефакт.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
template=mod._чистка_показу((src/'показ.html').read_text());parts=re.split(r'__(?:МОДУЛІ_ПОКАЗУ|ЗБІРКА_ПОКАЗУ|ВІДБИТОК|ФІД_ПОКАЗУ|КАТАЛОГ_ПОКАЗУ|ДОВІДНИК_ПОКАЗУ|ПРОМПТ_КОЛІР_ПОКАЗУ|ВИБІРКА_ПОКАЗУ)__',template);pos=0;checks=[]
for p in parts:
 if p:pos=html.index(p.encode(),pos)+len(p.encode());checks.append(hashlib.sha256(p.encode()).hexdigest())
assert len(parts)==9
m=re.search(r'const МОДУЛІ_ПОКАЗУ = "([A-Za-z0-9+/=]+)"'.encode(),html);assert m
payload=base64.b64decode(m[1]);z=zipfile.ZipFile(io.BytesIO(payload));entries=z.namelist();matches={}
for name in ['дріт_моделі','повнота_образу','протокол','міст_відповіді']:
 p=name+'.py';key=p if p in entries else p+'.bz2';data=z.read(key)
 if key.endswith('.bz2'):data=bz2.decompress(data)
 # Builder strips source comments; verify actual shipped producer exists alongside browser-executed result.
 matches[name]={'zip_entry':key,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'contains_new_producer':('_свідомі_на_дріт'.encode() in data) if name=='дріт_моделі' else None}
assert matches['дріт_моделі']['contains_new_producer']
result=dict(head=d['head'],all_source_blobs_exact=len(d['records']),source_rechecked_after_build=True,html_bytes=len(html),html_sha256=hashlib.sha256(html).hexdigest(),zip_sha256=hashlib.sha256(payload).hexdigest(),zip_entries=len(entries),shipped_new_modules=matches,template_fragments=len(checks),fragment_sha256=checks,build_rc=0,display_test='SKIPPED by builder: no local node_modules path; deferred to ONE batch battery, no 741/65 claim',models=0,paid=0)
(ROOT/'native/provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
