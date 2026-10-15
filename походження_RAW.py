import gzip,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,'джерела')
import фід_розбір as Р
out=Path('/workspace/dress3710-tmp'); compressed=Path('/workspace/scratch/pachka-1510-2/repo/каталог_повний.xml.gz').read_bytes(); raw=gzip.decompress(compressed)
fd=os.memfd_create('3710_lineage');os.write(fd,raw)
rawrows=Р.офери_фіду('/proc/self/fd/%d'%fd)
shared=Path('/workspace/scratch/pachka-1510-2/repo/джерела/каталог_повний.xml'); clean=shared.read_bytes();cleanrows=Р.офери_фіду(str(shared))
a={r['id'] for r in rawrows};b={r['id'] for r in cleanrows}
rawpilot=json.loads((out/'пілот_3710_RAW.json').read_text()); oldpilot=json.loads((out/'пілот_3710_clean_ПОМИЛКА.json').read_text())
sha=lambda x:hashlib.sha256(x).hexdigest()
meta=dict(наряд=3710,стан='ВІДКРИТО',producer='жнива_прогін.main:309–311: gzip/open переданого --каталог → feed.читати_yml; без cleaner',blob=subprocess.check_output(['git','hash-object','--stdin'],input=compressed).decode().strip(),raw=dict(байтів=len(raw),sha256=sha(raw),offers=len(rawrows),унікальних_id=len(a),runtime_каталог=12280,суконь=1763,пілот=len(rawpilot),канонічних_суконь=709),попередній_shared_clean=dict(байтів=len(clean),sha256=sha(clean),offers=len(cleanrows),унікальних_id=len(b),runtime_каталог=11887,пілот=len(oldpilot),статус='ПОМИЛКА первинного evidence: cleaned input було названо exact raw; збережено без приховування'),id_raw_поза_clean=sorted(a-b),id_clean_поза_raw=sorted(b-a),пілот_raw_поза_clean=sorted({r['id'] for r in rawpilot}-{r['id'] for r in oldpilot}),foreign_write='Не було: shared XML використовувався тільки читанням; root бачив його розмір 49504146B до роботи; cleaner батареї писав власний /dev/shm/liusterko-3710-1510/каталог_повний.xml',post_shared_sha256=sha(shared.read_bytes()),qa_shared_sha256='374492934617994073a0780b17c06c08d1ef05c8a7cd02b4352693d77de49226',пілот_canonical_sha256=sha(json.dumps(rawpilot,ensure_ascii=False,sort_keys=True).encode()),помилковий_пілот_збережено='пілот_3710_clean_ПОМИЛКА.json',якість_фото='не виміряно; лише підготовка входу')
(out/'походження_RAW.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print({k:meta[k] for k in ('blob','raw','попередній_shared_clean','пілот_canonical_sha256')}); print('IDdelta',len(a-b),len(b-a),'pilotdelta',len(meta['пілот_raw_поза_clean']))
os.close(fd)
