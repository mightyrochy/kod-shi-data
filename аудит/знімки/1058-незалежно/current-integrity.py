from pathlib import Path
import subprocess,os,json,re
p=Path('/workspace/scratch/qa1058-independent');repo='/workspace/scratch/4944-aa-next/repo';os.environ['GIT_NO_LAZY_FETCH']='1';base='0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc';old='824243ed89fd75b04a9c96552784a51ab6a39888';main='2fb809276e2683f1f579249662aec7b4ce2740f7';head='a88629d475412f1ae2a3d76bcbbfc844422d89ac'
def git(*a):return subprocess.check_output(['git','-c','core.quotepath=false','-C',repo,*a])
for ref in [old,main]:subprocess.run(['git','-C',repo,'merge-base','--is-ancestor',ref,head],check=True)
parents=git('show','-s','--format=%P',head).decode().split();assert parents==[old,main]
def patch(a,b):return [x for x in git('diff',a,b,'--','джерела/показ.html').splitlines(keepends=True) if not x.startswith((b'diff --git ',b'index ',b'--- ',b'+++ ',b'@@ '))]
assert patch(base,old)==patch(main,head)
B='аудит/БЕКЛОГ.md';mb=git('show',main+':'+B);hb=git('show',head+':'+B);own=re.compile(rb'^\|\s*5180\s*\|');assert b''.join(l for l in hb.splitlines(keepends=True) if not own.match(l))==mb
ob=git('show',old+':'+B);assert next(l for l in hb.splitlines(keepends=True) if own.match(l))==next(l for l in ob.splitlines(keepends=True) if own.match(l))
ids=[int(m[1]) for l in hb.splitlines() if (m:=re.match(rb'^\|\s*(\d+)\s*\|',l))];assert len(ids)==len(set(ids))==1381
changed=git('diff','--name-only',main,head).decode().splitlines();assert set(changed)=={'джерела/показ.html',B}
assert subprocess.run(['git','-C',repo,'diff','--check',main,head],capture_output=True).returncode==0
result={'head':head,'main':main,'old':old,'parents':parents,'exact_old_preview_diff_ignoring_offsets':True,'only_files':changed,'foreign_board_bytes_exact':True,'own_5180_exact':True,'board_ids':len(ids),'duplicates':0,'source_or_battery_repeated':False,'current_native':'очікує READY нового штатного HTML'};(p/'current-integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
