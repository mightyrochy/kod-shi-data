import subprocess,os,json,re,hashlib,sys
from pathlib import Path
repo=Path('/workspace/scratch/pachka-1510-2/repo');out=Path('/workspace/scratch/qa1056-independent')
os.environ['GIT_NO_LAZY_FETCH']='1'
def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false','-C',str(repo),*args])
base='bf86396aa1631c31fd83fd2d1d20fd07f92a672a';head='f2e099e85f8b2238e9898ec3833d6c80f6f5ba20';a='c1fff7d727feaa16a00eb4491d15dc46502c28be';b='9575ae69980dfd26175614b1e9d31404548c32f0'
assert git('rev-parse','HEAD').decode().strip()==head
for source in [base,a,b]:subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',source,head],check=True)
paths=git('diff','--name-only',base,head).decode().splitlines()
assert set(paths)=={'аудит/БЕКЛОГ.md','джерела/показ.html','джерела/проби/сімї_сектори_3350.py'}
def blob(ref,path):return git('show',ref+':'+path)
assert blob(head,'джерела/показ.html')==blob(a,'джерела/показ.html')
assert blob(head,'джерела/проби/сімї_сектори_3350.py')==blob(b,'джерела/проби/сімї_сектори_3350.py')
def board(ref):
 data=blob(ref,'аудит/БЕКЛОГ.md');rows={};ids=[]
 for line in data.splitlines(keepends=True):
  m=re.match(rb'^\|\s*(\d+)\s*\|',line)
  if m:
   i=int(m[1]);assert i not in rows;rows[i]=line;ids.append(i)
 return data,rows,ids
old,olds,oldids=board(base);new,news,newids=board(head)
assert newids==oldids and len(news)==1350
for i in newids:assert news[i]==(board(b if i==3350 else a)[1][i] if i in [3350,4944,5100] else olds[i])
foreign=lambda data:b''.join(line for line in data.splitlines(keepends=True) if not re.match(rb'^\|\s*(3350|4944|5100)\s*\|',line))
assert foreign(old)==foreign(new)
assert b'**' in news[3350] and 'ВІДКРИТО'.encode() in news[3350] and 'ВІДКРИТО'.encode() in news[4944]
# Перевірка походження built без повторної збірки.
sys.path.insert(0,str(repo/'джерела'));import build_артефакт as build
clean=build._чистка_показу(blob(head,'джерела/показ.html').decode())
built=Path(sys.argv[1]).read_text();parts=re.split(r'__(?:МОДУЛІ_ПОКАЗУ|ЗБІРКА_ПОКАЗУ|ВІДБИТОК|ФІД_ПОКАЗУ|КАТАЛОГ_ПОКАЗУ|ДОВІДНИК_ПОКАЗУ|ПРОМПТ_КОЛІР_ПОКАЗУ|ВИБІРКА_ПОКАЗУ)__',clean);pos=0
for p in parts:
 if p:pos=built.index(p,pos)+len(p)
result={'head':head,'base':base,'sources':[a,b],'ancestry':True,'changed_files':paths,'source_files_exact':True,'source_rows_exact':[3350,4944,5100],'board_ids':len(news),'duplicate_ids':0,'order_preserved':True,'foreign_bytes_exact':True,'open_rows':[3350,4944],'built_template_parts_exact':len(parts),'built_sha256':hashlib.sha256(built.encode()).hexdigest(),'source_blobs':{p:git('rev-parse',head+':'+p).decode().strip() for p in paths}}
(out/'склад.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
