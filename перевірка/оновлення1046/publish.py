from pathlib import Path
import subprocess,json,os,hashlib
root=Path('/workspace/scratch/qa-update1046-independent');repo=root/'proof';repo.mkdir(exist_ok=True)
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(['/workspace/scratch/update999/repo/objects']+json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()))
def git(*a,input=None):return subprocess.check_output(['git','-C',str(repo),*a],input=input)
first=not (repo/'.git').exists()
if first:
 git('init','--quiet');git('config','user.name','Codex');git('config','user.email','codex@openai.com');git('remote','add','origin','https://github.com/mightyrochy/kod-shi-data.git')
branch='codex/perevirka-update1046-1510';parent='0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc' if first else git('rev-parse','refs/heads/'+branch).decode().strip();git('read-tree',parent)
files=[p for p in root.iterdir() if p.is_file() and p.name not in ['archive-sha.txt','SHA256.json']]
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(root/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');files.append(root/'SHA256.json')
for p in files:
 blob=git('hash-object','-w','--stdin',input=p.read_bytes()).decode().strip();git('update-index','--add','--cacheinfo','100644,'+blob+',перевірка/оновлення1046/'+p.name)
tree=git('write-tree').decode().strip();sha=git('commit-tree',tree,'-p',parent,input='Незалежна перевірка композиції оновлених гілок\n'.encode()).decode().strip();git('update-ref','refs/heads/'+branch,sha);git('push','origin',sha+':refs/heads/'+branch);assert git('ls-remote','origin','refs/heads/'+branch).decode().split()[0]==sha;(root/'archive-sha.txt').write_text(sha+'\n');print(json.dumps({'sha':sha,'branch':branch,'files':len(files)}))
