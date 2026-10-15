from pathlib import Path
import os,json,subprocess,difflib,sys
p=Path('/workspace/scratch/update1044');out=Path('/workspace/scratch/qa-update1044-independent');repo='/workspace/scratch/update999/repo';os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(json.loads(Path('/workspace/scratch/update1046/alternates.json').read_text()));base='0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc';main='2fb809276e2683f1f579249662aec7b4ce2740f7';path='джерела/показ.html'
def git(*a):return subprocess.check_output(['git','-C',repo,*a])
def data(ref):return git('show',ref+':'+path).decode()
for n in map(int,sys.argv[1:]):
 d=json.loads((p/f'pushed-{n}.json').read_text());old=d['old'];head=d['sha'];b,o,m,f=[data(r) for r in [base,old,main,head]];bl,ol=b.splitlines(keepends=True),o.splitlines(keepends=True);patches=[];expected=m
 for tag,i,j,k,l in difflib.SequenceMatcher(None,bl,ol,autojunk=False).get_opcodes():
  if tag=='equal':continue
  before=''.join(bl[i:j]);after=''.join(ol[k:l]);assert before and expected.count(before)==1,(n,tag,i,j);expected=expected.replace(before,after,1);patches.append({'base_line':i+1,'old_lines':j-i,'own_lines':l-k,'exact_unique_old_chunk':True})
 assert expected==f,(n,'own hunk composition differs')
 source=None
 if n==1056:
  source=next(s['sha'] for s in d['sources'] if s['n']==1038);assert data(source)==f
 result={'pr':n,'head':head,'main':main,'own_hunks':patches,'all_new_main_bytes_preserved_plus_exact_old_own_hunks':True,'updated_source1038_exact':source,'main_HTML_diff_numstat':git('diff','--numstat',base,main,'--',path).decode().strip(),'own_changed_behaviour':'лише author доступне ім’я файлового поля' if n in [1038,1056] else 'збережені власні ділянки; нових змін у них немає','repeated_native_or_source_tests':False}
 (out/f'html-{n}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
