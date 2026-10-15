from pathlib import Path
import subprocess,os,json,hashlib
root=Path('/workspace/scratch/qa1058-independent');repo=root/'proof';repo.mkdir(exist_ok=True)
def run(*a,input=None):return subprocess.check_output(['git','-C',str(repo),*a],input=input)
run('init','--quiet');(repo/'.git/objects/info/alternates').write_text('/workspace/scratch/4944-aa-next/repo/.git/objects\n');run('config','user.name','Codex');run('config','user.email','codex@openai.com')
os.environ['GIT_NO_LAZY_FETCH']='1';head='824243ed89fd75b04a9c96552784a51ab6a39888';parent=run('rev-parse','refs/heads/codex/perevirka-1058-1510').decode().strip();run('read-tree',parent)
files=[p for p in root.rglob('*') if p.is_file() and not any(x in ['proof','tmp'] for x in p.relative_to(root).parts) and p.name not in ['archive-sha.txt','SHA256.json']]
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(root/'SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');files.append(root/'SHA256.json')
prefix='аудит/знімки/1058-незалежно/'
for p in files:
 blob=run('hash-object','-w','--stdin',input=p.read_bytes()).decode().strip();run('update-index','--add','--cacheinfo','100644,'+blob+','+prefix+str(p.relative_to(root)))
tree=run('write-tree').decode().strip();sha=run('commit-tree',tree,'-p',parent,input='Незалежна перевірка 5180: клавіатура, фокус і модальний перегляд\n'.encode()).decode().strip();branch='codex/perevirka-1058-1510';run('update-ref','refs/heads/'+branch,sha);print(run('push','origin',sha+':refs/heads/'+branch).decode());remote=run('ls-remote','origin','refs/heads/'+branch).decode().split()[0];assert remote==sha
(root/'archive-sha.txt').write_text(sha+'\n');print(json.dumps({'sha':sha,'branch':branch,'files':len(files),'remote_exact':True}))
