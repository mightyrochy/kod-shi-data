import subprocess as S, pathlib as P, difflib, json, re, collections, hashlib
out=P.Path(__file__).parent
main='1b6ebd2c6a846c8e26b1e2ab9c917897a0132f49'; head='78700cad184c76f133e20472eb31267ff5a01674'; old='286b310328eb3f981e403ae9b4ddcabd667b2f97'
sources=['eccb23bb3ad235189b3311a7aea7a1ae6b478b92','c452d9a1426e3be594963fc8925f7c927fbcfd2c','82f451fc9eab6718b0f725fdcf66f56b20cd4e28','6f7f3ffdb5e48573cd68f1f31015247b9f28a7f8']
def git(*a):return S.check_output(['git',*a])
def get(sha,file):return git('show',sha+':'+file).decode()
file='джерела/показ.html'; expected=get(main,file); original=get(old,file)
for sha in sources[1:]:
 a=original.splitlines(True);b=get(sha,file).splitlines(True)
 for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
  if tag=='equal':continue
  before=''.join(a[i:j]);after=''.join(b[k:l])
  if tag=='insert':before=a[i-1]+a[i];after=a[i-1]+after+a[i]
  assert before and expected.count(before)==1,(sha,tag,i,j)
  expected=expected.replace(before,after,1)
assert expected==get(head,file),'Композиція показу не тотожна'
docs={}
for file in ['CLAUDE.md','аудит/МЕНЕДЖЕР.md']:
 base=git('merge-base',main,sources[0]).decode().strip()
 tmp=[]
 for name,sha in [('main',main),('base',base),('source',sources[0])]:
  p=out/('tmp-'+name);p.write_text(get(sha,file));tmp.append(str(p))
 result=S.run(['git','merge-file','-p',*tmp],capture_output=True);assert result.returncode==0
 assert result.stdout.decode()==get(head,file),file
 docs[file]=True
 for p in tmp:P.Path(p).unlink()
file='аудит/РІШЕННЯ_ВЛАСНИКА.md';m=get(main,file);v=get(head,file);assert v.startswith(m)
for sha in [sources[0],sources[3]]:
 base=git('merge-base',main,sha).decode().strip();a=get(base,file);b=get(sha,file);assert b.startswith(a);assert b[len(a):].strip() in v
changed=git('diff','--name-only','-z',main,head).decode().strip('\0').split('\0')
assert set(changed)=={'CLAUDE.md','аудит/БЕКЛОГ.md','аудит/МЕНЕДЖЕР.md','аудит/РІШЕННЯ_ВЛАСНИКА.md','джерела/показ.html'}
board=get(head,'аудит/БЕКЛОГ.md');ids=re.findall(r'^\|\s*(\d+)\s*\|',board,re.M);duplicates=[i for i,c in collections.Counter(ids).items() if c>1];assert not duplicates
def rows(s):return {int(re.match(r'^\|\s*(\d+)',line)[1]):line for line in s.splitlines() if re.match(r'^\|\s*\d+\s*\|',line)}
mainrows=rows(get(main,'аудит/БЕКЛОГ.md'));headrows=rows(board)
assert set(headrows)-set(mainrows)=={5080,5090,5203}
assert set(mainrows)-set(headrows)==set()
assert all(headrows[n]==line for n,line in mainrows.items() if n not in [4943,4944])
assert 'ВІДКРИТО' in headrows[4944] and 'ВІДКРИТО' in headrows[5080] and 'ВІДКРИТО' in headrows[5090]
assert 'ЗАКРИТО #973' in headrows[4943] and 'ЗАКРИТО #975' in headrows[5203]
markers=git('grep','-n','-E','^(<<<<<<< |=======|>>>>>>> )',head).decode() if S.run(['git','grep','-q','-E','^(<<<<<<< |=======|>>>>>>> )',head]).returncode==0 else ''
assert not markers
assert S.run(['git','diff','--check',main,head],capture_output=True).returncode==0
result={'head':head,'main':main,'sources':sources,'code_exact_composition':True,'docs972':docs,'quotes972975':True,'changed':changed,'other_main_files_equal':True,'new_media':0,'duplicate_board_ids':duplicates,'conflict_markers':0,'diff_check':0,'code_sha256':hashlib.sha256(expected.encode()).hexdigest()}
(out/'композиція.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
