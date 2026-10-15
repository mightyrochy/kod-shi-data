"""Окрема відтворюваність старого очищеного stage; не вхід producer #1060."""
import gzip, hashlib, json, os, socket, subprocess, sys
from pathlib import Path
repo=Path('/workspace/dress3710-next'); out=Path('/workspace/qa3710-source-recovery')
head='d569a89565bf7b34e3d37e4539e72870d9dd9adb'
sys.dont_write_bytecode=True;sys.path.insert(0,str(repo/'джерела'))
def no_network(*args,**kwargs):
    raise AssertionError('Жодної мережі у QA')
socket.socket.connect=no_network
socket.create_connection=no_network
import чистка_каталогу as C
source=subprocess.check_output(['git','-C',str(repo),'show',head+':джерела/чистка_каталогу.py'])
assert source==(repo/'джерела/чистка_каталогу.py').read_bytes()
raw=gzip.decompress(subprocess.check_output(['git','-C',str(repo),'show',head+':каталог_повний.xml.gz']))
source_fd=os.memfd_create('qa3710_clean_source'); target_fd=os.memfd_create('qa3710_clean_target')
assert os.write(source_fd,raw)==len(raw)
facts=C.почистити('/proc/self/fd/%d'%source_fd,'/proc/self/fd/%d'%target_fd)
clean=Path('/proc/self/fd/%d'%target_fd).read_bytes()
shared=Path('/workspace/scratch/pachka-1510-2/repo/джерела/каталог_повний.xml').read_bytes()
assert clean==shared
report={'head':head,'producer_використовує_cleaner':False,
    'опис':'Додаткова QA старого shared-clean stage; очищення лише між власними RAM memfd.',
    'raw_sha256':hashlib.sha256(raw).hexdigest(),'clean_sha256':hashlib.sha256(clean).hexdigest(),
    'clean_байтів':len(clean),'shared_побайтно_збігається':True,'cleaner_факти':facts}
(out/'clean_lineage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
os.close(source_fd);os.close(target_fd)
