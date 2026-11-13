import subprocess,re,json,csv,collections as C,sys
import os as _os
В=_os.path.dirname(_os.path.abspath(__file__)); R=_os.path.abspath(_os.path.join(В,'../../..'))
def git(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=off',*a],capture_output=True,text=True).stdout
pr={x['number']:x for x in map(json.loads,open(В+'/pr.jsonl'))}
def клас_файлу(f):
    if f=='index.html': return 'збірка'
    if f.startswith(('open-source-stylist/','zhnyvarka/')): return 'продукт'
    if f.startswith('джерела/'):
        s=f[len('джерела/'):]
        if s.startswith(('прилади/','проби/','аудит/','лабораторія/','дані_')): return 'прилади'
        if '/' not in s and re.match(r'(audit_|gate_|measure_|journal)',s): return 'прилади'
        return 'продукт'
    if f.startswith('.github/'): return 'прилади'
    if f.startswith('аудит/адаптери/gemini/') or f.startswith('аудит/адаптери/'): return 'обгортка'
    if f.startswith('аудит/дошка/') or f=='аудит/БЕКЛОГ.md': return 'дошка'
    if f.startswith('аудит/наряди/'): return 'наряди'
    return 'документи'
out=git('log','origin/main','--first-parent','--since=2026-11-05T00:00:00Z','--until=2026-11-12T00:00:00Z','--format=%H%x1f%cI%x1f%an%x1f%P%x1f%s')
рядки=[]
for l in out.strip().split('\n'):
    h,d,an,par,s=l.split('\x1f')
    if an=='github-actions[bot]': continue
    p1=par.split()[0]
    files=[f for f in git('diff','--name-only','--no-renames',p1,h).split('\n') if f]
    кл=C.Counter(клас_файлу(f) for f in files)
    m=re.match(r'Merge pull request #(\d+) from mightyrochy/(.+)',s)
    nums=[int(m.group(1))] if m else [int(x) for x in re.findall(r'#(\d+)',s)]
    гілка=m.group(2) if m else (pr[nums[-1]]['head_ref'] if nums and nums[-1] in pr else '')
    body=git('log','--format=%B',f'{p1}..{h}')
    сесії=sorted(set(re.findall(r'Claude-Session: https://claude.ai/code/(session_\w+)',body)))
    рядки.append(dict(sha=h,час=d,pr=nums[-1] if nums else '',гілка=гілка,тема=s[:120],
        файлів=len(files),продукт=кл['продукт'],прилади=кл['прилади'],обгортка=кл['обгортка'],дошка=кл['дошка'],наряди=кл['наряди'],документи=кл['документи'],
        claude_сесії=' '.join(сесії), gemini_співавтор=int('gemini@local' in body)))
w=csv.DictWriter(open(В+'/злиття.csv','w'),fieldnames=list(рядки[0]))
w.writeheader(); w.writerows(рядки)
print(len(рядки), sum(1 for x in рядки if x['продукт']), sum(1 for x in рядки if not x['гілка']))
