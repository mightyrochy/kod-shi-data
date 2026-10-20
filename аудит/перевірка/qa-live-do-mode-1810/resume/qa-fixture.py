"""Незалежна перевірка справжнього CLI у тимчасовому Git-репозиторії."""
from pathlib import Path
import subprocess as sp, os, json, hashlib, shutil
scratch=Path('/workspace/qa-live-do-mode-1810/work/fixture-resume')
out=Path('/workspace/qa-live-do-mode-1810/аудит/перевірка/qa-live-do-mode-1810/resume')
assert not scratch.exists(), 'Не перезаписувати попередні артефакти'
scratch.mkdir(); git=shutil.which('git')
def g(*args):
 return sp.check_output([git,'-C',str(scratch),*args],text=True).strip()
def commit(message):
 g('add','.'); g('-c','user.name=QA','-c','user.email=qa@example.invalid','commit','-qm',message); return g('rev-parse','HEAD')
g('init','-q')
source=sp.check_output([git,'-C','/workspace/live-do-mode-1810','show','2a33b90737f8990e63e7b483a64bc372a27e021f:аудит/проби/живі_до.py'])
p=scratch/'аудит/проби'; p.mkdir(parents=True); (p/'живі_до.py').write_bytes(source)
registry=sp.check_output([git,'-C','/workspace/live-do-mode-1810','show','2a33b90737f8990e63e7b483a64bc372a27e021f:аудит/проби/живі_сцени.txt'])
(p/'живі_сцени.txt').write_bytes(registry); (p/'живі_прогони.txt').write_text('')
base=commit('Основа незалежної CLI-перевірки')
(scratch/'revision.txt').write_text('2'); mid=commit('Ближчий код без фото')
(scratch/'revision.txt').write_text('3'); last=commit('Найближчий код лише розмови')
full='показ ПОВНИЙ\n2. збирання (сід 3)\n2б. чотири картки за 10 с\n'
for name,sha,log in [('full-photo',base,full+'(FOTO=1)\n'),('full-no-photo',mid,full),('conversation',last,'показ ПОВНИЙ\nНГ-4 · ВОНА: свято\n'),('missing',last,'показ ПОВНИЙ\n(FOTO=1)\n')]:
 d=scratch/'артефакти'/name; d.mkdir(parents=True); (d/'код.txt').write_text(f'{sha} ж3_свято_др ПІСЛЯ fixture-model\n'); (d/'лог.txt').write_text(log)
old=commit('Зріз чотирьох чотирипольових результатів')
ref='refs/remotes/origin/claude/zhyvi-qa1459'; g('update-ref',ref,old)
(scratch/'артефакти/full-photo/лог.txt').write_text('НГ-4 · ВОНА: гілку пересунуто після знімка\n')
new=commit('Інший вміст рухомої гілки')
# Усі CLI порівнюють однаковий код, отже вивід детермінований.
cases={'fixture-registry':([],0,mid),'fixture-photo':(['--режим','повне +фото'],0,base),'fixture-conversation':(['--режим','розмова'],0,last),'fixture-no-candidate':(['--режим','функція'],1,None),'fixture-unknown-mode':(['--режим','невідомий'],2,None)}
results={}
def run(name,extra,env=None):
 cmd=['python3',str(p/'живі_до.py'),'ж3_свято_др',last,*extra]
 r=sp.run(cmd,capture_output=True,text=True,env=env)
 (out/f'{name}.txt').write_text('$ '+' '.join(cmd)+'\n'+r.stdout+r.stderr+f'\nexit {r.returncode}\n')
 return r
for name,(extra,rc,sha) in cases.items():
 r=run(name,extra); assert r.returncode==rc,(name,r.stderr)
 if sha: assert f'код {sha} ·' in r.stdout,(name,r.stdout)
 if rc==0: assert 'без доказу режиму 1' in r.stdout
 if rc==1: assert 'Порівняння не виконано' in r.stderr and 'ДО =' not in r.stdout
 results[name]={'exit':rc,'selected_code':sha}
# Єдиний кандидат із відсутнім доказом: явна відмова, не повне ДО.
g('update-ref',ref,new)
for d in ['full-photo','full-no-photo','conversation']: shutil.rmtree(scratch/'артефакти'/d)
missing=commit('Лише невідомий виконаний режим'); g('update-ref',ref,missing)
r=run('fixture-missing-only',[]); assert r.returncode==1 and 'без доказу режиму 1' in r.stdout and 'Порівняння не виконано' in r.stderr
results['fixture-missing-only']={'exit':1,'selected_code':None}
# Знімок old прочитано, але до ls-tree/show ref вже вказує на new.
g('update-ref',ref,old)
wrapper=scratch/'bin'; wrapper.mkdir(); trace=out/'git-moved-ref-trace.jsonl'
(wrapper/'git').write_text('''#!/usr/bin/env python3
import subprocess, sys, os, json
args=sys.argv[1:]
with open(os.environ['QA1459_TRACE'],'a') as f: f.write(json.dumps(args,ensure_ascii=False)+'\\n')
r=subprocess.run([os.environ['QA1459_GIT'],*args],capture_output=True)
if 'for-each-ref' in args:
 subprocess.run([os.environ['QA1459_GIT'],'-C',os.environ['QA1459_REPO'],'update-ref',os.environ['QA1459_REF'],os.environ['QA1459_NEW']],check=True)
sys.stdout.buffer.write(r.stdout); sys.stderr.buffer.write(r.stderr); sys.exit(r.returncode)
'''); (wrapper/'git').chmod(0o755)
env=os.environ|{'PATH':str(wrapper)+':'+os.environ['PATH'],'QA1459_TRACE':str(trace),'QA1459_GIT':git,'QA1459_REPO':str(scratch),'QA1459_REF':ref,'QA1459_NEW':new}
r=run('fixture-stable-sha',['--режим','повне +фото'],env)
assert r.returncode==0 and f'джерело refs {old}' in r.stdout and f'код {base} ·' in r.stdout
assert g('rev-parse',ref)==new
normal=(out/'fixture-photo.txt').read_text().split('\n',1)[1]
assert normal==r.stdout+r.stderr+f'\nexit {r.returncode}\n'
reads=[a for a in map(json.loads,trace.read_text().splitlines()) if 'show' in a or 'ls-tree' in a]
assert all(ref not in ' '.join(a) and 'origin/claude/zhyvi-qa1459' not in ' '.join(a) for a in reads)
results['fixture-stable-sha']={'exit':0,'snapshot':old,'moved_ref':new,'selected_code':base,'byte_identical_to_unmoved':True}
results['script_sha256']=hashlib.sha256(source).hexdigest()
(out/'fixture-summary.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
