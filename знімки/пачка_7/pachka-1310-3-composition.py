from pathlib import Path
import subprocess,json,hashlib,re,collections
root=Path('/tmp/liusterko-pachka-1310-3');out=Path('/tmp/pachka-1310-3-evidence')
def git(*a):return subprocess.check_output(['git','-C',str(root),*a])
def blob(ref,path):return git('show',ref+':'+path)
base='834d956e31ab986905d80b08941746d18d25de43';full='af1ab8c37eeb45469646e715c8640f5ab5b86c2d';heads={990:'2f3c56cb12173dc5232dde7e798caf1f179a6593',989:'45b32dc958b870f7008881d206d4db927690394e'}
assert git('rev-parse','HEAD').decode().strip()==full
changed=set(git('-c','core.quotepath=false','diff','--name-only',base,full).decode().splitlines());union=set();own=[]
for n,sha in heads.items():
 subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',sha,full],check=True)
 mb=git('merge-base',base,sha).decode().strip();files=git('-c','core.quotepath=false','diff','--name-only',mb,sha).decode().splitlines();union.update(files)
 for path in files:
  data=blob(sha,path);assert data==blob(full,path),(n,path)
  own.append({'pr':n,'path':path,'sha256':hashlib.sha256(data).hexdigest()})
assert changed==union,(changed,union)
board='аудит/БЕКЛОГ.md';actual=blob(full,board).decode();original=blob(base,board).decode();ids=re.findall(r'^\|\s*(\d+)\s*\|',actual,re.M);dups={k:v for k,v in collections.Counter(ids).items() if v>1};assert not dups
rows=lambda s:{m.group(1):m.group(0) for m in re.finditer(r'^\|\s*(\d+)\s*\|.*$',s,re.M)}
a,b=rows(actual),rows(original);assert set(a)-set(b)=={'5205'};assert all(a[k]==v for k,v in b.items());assert 'ЗАКРИТО #990' in a['5205'];assert blob(full,board)==blob(heads[990],board)
assert not re.search(r'^(<<<<<<<|=======|>>>>>>>)',actual,re.M)
protected=['AGENTS.md','CLAUDE.md','index.html','джерела/аудит/ДОСЯЖНІСТЬ.md',*git('-c','core.quotepath=false','ls-tree','-r','--name-only',base,'.github/workflows').decode().splitlines()]
for path in protected:assert blob(base,path)==blob(full,path),path
media=[p for p in changed if re.search(r'\.(png|jpe?g|webp|gif|svg|mp4)$',p,re.I)];assert not media
mediahead='01d7fae41cee83e6da392911e24210e118bfa74a';mediafiles=git('-c','core.quotepath=false','diff','--name-only',heads[990],mediahead).decode().splitlines();assert len(mediafiles)==17 and all(p.startswith('знімки/5205/') for p in mediafiles);assert len([p for p in mediafiles if p.endswith('.png')])==5
quote='Надиктований текст завжди можна виправити рукою — на будь-якому телефоні, в будь-якому браузері й у кожному полі з мікрофоном';assert quote in blob(full,'аудит/ПРОДУКТ.md').decode();assert 'Це не важливо. Працювати має завжди і всюди.' in blob(full,'аудит/РІШЕННЯ_ВЛАСНИКА.md').decode()
result={'head':full,'main':base,'sources':heads,'changed_files':sorted(changed),'source_owned_bytes':own,'all_board_ids':len(ids),'duplicate_ids':dups,'board_only_change':'новий5205 дослівно source990; усі попередні рядки байтово main','protected_main_unchanged':protected,'product_media':0,'source_media_final':mediahead,'source_media_files':17,'source_media_png':5,'composition':'нормальні merge точних sourceHEAD; усі6files побайтово source;989 лише нова передача','limits':'SpeechRecognition fake у Chromium не доводить фізичні телефони;5204/5190 не реалізовано'}
(out/'композиція.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
