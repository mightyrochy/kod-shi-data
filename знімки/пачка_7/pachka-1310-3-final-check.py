import subprocess,re,json
from pathlib import Path
root='/tmp/liusterko-pachka-1310-3';base='834d956e31ab986905d80b08941746d18d25de43';head='af1ab8c37eeb45469646e715c8640f5ab5b86c2d'
def git(*a):return subprocess.check_output(['git','-C',root,*a])
files=git('-c','core.quotepath=false','diff','--name-only',base,head).decode().splitlines()
for path in files:assert not re.search(rb'^(<<<<<<<|=======|>>>>>>>)',git('show',head+':'+path),re.M),path
assert git('diff','--check',base,head)==b''
assert git('rev-parse','HEAD').decode().strip()==head
assert git('ls-remote','origin','refs/heads/main').decode().split()[0]==base
assert git('ls-remote','origin','refs/heads/codex/pachka-1310-3').decode().split()[0]==head
print(json.dumps({'head':head,'main':base,'changed_files':len(files),'all_changed_files_conflict_markers':0,'diff_check':0,'remote_head_confirmed':True,'remote_main_unchanged':True},ensure_ascii=False))
