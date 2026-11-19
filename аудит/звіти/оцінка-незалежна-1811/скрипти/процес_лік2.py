import subprocess,re,sys
R='/home/user/kod-shi-data'
def g(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=false',*a],capture_output=True,text=True).stdout
out=g('log','--first-parent','--name-only','--format=@@%s','--since=2026-10-28T14:07:24+02:00','--until=2026-11-18T14:07:24+02:00','origin/main')
cs=[];cur=None
for L in out.split('\n'):
    if L.startswith('@@'): cur=[L[2:],[]]; cs.append(cur)
    elif L.strip(): cur[1].append(L)
cs=[c for c in cs if not re.match(r'(збірка:|дошка: згорнуто|дошка й паспорти: згор)',c[0])]
def src(f): return f.startswith('джерела/') and not re.search(r'^джерела/(прилади|лабораторія|аудит|дані_корпусу|дані_5191)|тест|проб|\.md$',f)
print('небот',len(cs),'джерела/ без приладів/тестів/проб/md',sum(any(src(f) for f in c[1]) for c in cs),'лише аудит/',sum(bool(c[1]) and all(f.startswith('аудит/') for f in c[1]) for c in cs))
