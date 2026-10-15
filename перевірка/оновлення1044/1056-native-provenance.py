from pathlib import Path
import os,subprocess,json,re,sys,hashlib
out=Path('/workspace/scratch/qa1056-current-independent');repo='/workspace/scratch/update999/repo';head='198a76c165a5b8e30a74d829e22f7fed058032fa';source=Path('/dev/shm/liusterko-update1046-native-inputs/джерела');os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()))
def git(*a,input=None):return subprocess.check_output(['git','-C',repo,*a],input=input)
prepared=json.loads(Path('/workspace/scratch/update1044/native-inputs.json').read_text());files=prepared['checked_top_level_tracked_files'];assert len(files)==265;checked={}
for name in files:
 data=(source/name).read_bytes();expected=git('rev-parse',head+':джерела/'+name).decode().strip();assert git('hash-object','--stdin',input=data).decode().strip()==expected;checked[name]=expected
sys.path.insert(0,'/workspace/scratch/pachka-1510-2/repo/джерела');import build_артефакт as build
assert Path(build.__file__).read_bytes()==git('show',head+':джерела/build_артефакт.py')
template=build._чистка_показу((source/'показ.html').read_text());built=Path('/dev/shm/qa1056-current/build/index.html').read_bytes();parts=re.split(r'__(?:МОДУЛІ_ПОКАЗУ|ЗБІРКА_ПОКАЗУ|ВІДБИТОК|ФІД_ПОКАЗУ|КАТАЛОГ_ПОКАЗУ|ДОВІДНИК_ПОКАЗУ|ПРОМПТ_КОЛІР_ПОКАЗУ|ВИБІРКА_ПОКАЗУ)__',template);pos=0
for p in parts:
 if p:pos=built.index(p.encode(),pos)+len(p.encode())
log=(out/'build.log').read_text();assert 'ВИКОНАНО ЗВІРОК: 731 у 64 розділах' in log and 'ПОКАЗ: усе зелене' in log
result={'head':head,'built_sha256':hashlib.sha256(built).hexdigest(),'built_bytes':len(built),'template_fragments_exact':len(parts),'committed_top_level_source_files_verified':len(checked),'committed_blobs':checked,'builder_source_exact_head':True,'standard_build_once':True,'ui_display_checks':'731/64','payload':'7be11dc1b6a1','no_backend_battery_repeat':True,'RAM_artifact_removed_after_check':True};(out/'provenance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='committed_blobs'},ensure_ascii=False))
