import subprocess,re,csv,json,glob
import os as _os
В=_os.path.dirname(_os.path.abspath(__file__)); R=_os.path.abspath(_os.path.join(В,'../../..'))
def git(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=off',*a],capture_output=True,text=True).stdout
A,B=open(В+'/межі.txt').read().split()
out=git('log','--reverse','--first-parent','--format=%H %P %cI %an',f'{A}..{B}')
поява={}
for l in out.strip().split('\n'):
    h,p1,*_,d,an=l.split()[:2]+l.split()[2:]
    h,p1=l.split()[0],l.split()[1]; d=l.split()[-2]
    if 'github-actions' in l: continue
    for m in re.finditer(r'^\+\| *(\d{4,6}) *\|',git('diff',p1,h,'--','аудит/дошка','аудит/БЕКЛОГ.md'),re.M):
        поява.setdefault(int(m.group(1)),(h,d))
# зміст рядків на B
текст=git('show',f'{B}:аудит/БЕКЛОГ.md')
for f in git('ls-tree','--name-only',B,'аудит/дошка/').split('\n'):
    if f.endswith('.md'): текст+='\n'+git('show',f'{B}:{f}')
рядки={}
for m in re.finditer(r'^\| *(\d{4,6}) *\|(.*)$',текст,re.M):
    рядки.setdefault(int(m.group(1)),m.group(2))
pr={x['number']:x for x in map(json.loads,open(В+'/pr.jsonl'))}
w=csv.writer(open(В+'/дошка_нові.csv','w'))
w.writerow(['рядок','поява_sha','поява_час','виявлено','внесено_pr','pr_злито','клас'])
from datetime import datetime
def t(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
n=0
for н,(h,d) in sorted(поява.items()):
    з=рядки.get(н,'')
    в=re.search(r'виявлено: *([^;|<]+?)(?:;|\||$)',з); вн=re.search(r'внесено: *#(\d+)',з)
    вн=int(вн.group(1)) if вн else ''
    pm=pr.get(вн,{}).get('merged_at') if вн else None
    кл='' if not вн else ('PR не злито' if not pm else ('після злиття' if t(d)>t(pm) else 'до злиття'))
    w.writerow([н,h,d,в.group(1).strip() if в else '',вн,pm or '',кл]); n+=1
print(n,'нових рядків')
