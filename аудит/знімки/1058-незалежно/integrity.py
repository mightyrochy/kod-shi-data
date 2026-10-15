import subprocess,os,json,re,hashlib,sys
from pathlib import Path
os.environ['GIT_NO_LAZY_FETCH']='1';repo=Path('/workspace/scratch/4944-aa-next/repo');out=Path('/workspace/scratch/qa1058-independent');head='824243ed89fd75b04a9c96552784a51ab6a39888';base='0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc'
def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false','-C',str(repo),*args])
def blob(ref,p):return git('show',ref+':'+p)
subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',base,head],check=True)
paths=git('diff','--name-only',base,head).decode().splitlines();assert set(paths)=={'аудит/БЕКЛОГ.md','джерела/показ.html'}
old=blob(base,'аудит/БЕКЛОГ.md');new=blob(head,'аудит/БЕКЛОГ.md');own=re.compile(rb'^\|\s*5180\s*\|')
assert b''.join(x for x in new.splitlines(keepends=True) if not own.match(x))==old
ids=[int(m[1]) for x in new.splitlines() if (m:=re.match(rb'^\|\s*(\d+)\s*\|',x))];assert len(ids)==len(set(ids))
assert blob('42d185b23a07162c71d038b8c9db038dd2eaa4f0','джерела/показ.html')==blob(base,'джерела/показ.html')
sys.path.insert(0,str(repo/'джерела'));import build_артефакт as build
builds={}
for stage,ref in [('before',base),('after',head)]:
 template=build._чистка_показу(blob(ref,'джерела/показ.html').decode());built=Path('/workspace/scratch/4944-aa-next-evidence',stage,'index.html').read_bytes();parts=re.split(r'__(?:МОДУЛІ_ПОКАЗУ|ЗБІРКА_ПОКАЗУ|ВІДБИТОК|ФІД_ПОКАЗУ|КАТАЛОГ_ПОКАЗУ|ДОВІДНИК_ПОКАЗУ|ПРОМПТ_КОЛІР_ПОКАЗУ|ВИБІРКА_ПОКАЗУ)__',template);pos=0
 for p in parts:
  if p:pos=built.index(p.encode(),pos)+len(p.encode())
 builds[stage]={'template_fragments_exact':len(parts),'sha256':hashlib.sha256(built).hexdigest(),'bytes':len(built)}
result={'head':head,'base':base,'ancestry':True,'changed_files':paths,'foreign_board_bytes_exact':True,'unchanged_4944_history':True,'own_new_row':5180,'board_ids':len(ids),'duplicates':0,'before_source42_equals_base':True,'builds':builds,'battery_repeated':False}
(out/'integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
