import subprocess,re,sys,collections as C
R='/home/user/kod-shi-data'
def git(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=off',*a],capture_output=True,text=True).stdout
def клас_файлу(f):
    if f=='index.html': return 'збірка'
    if f.startswith(('open-source-stylist/','zhnyvarka/')): return 'продукт'
    if f.startswith('джерела/'):
        s=f[len('джерела/'):]
        if s.startswith(('прилади/','проби/','аудит/','лабораторія/','дані_')): return 'прилади'
        if '/' not in s and re.match(r'(audit_|gate_|measure_|journal)',s): return 'прилади'
        return 'продукт'
    if f.startswith('.github/'): return 'прилади'
    if f.startswith('аудит/адаптери/'): return 'обгортка'
    if f.startswith('аудит/дошка/') or f=='аудит/БЕКЛОГ.md': return 'дошка'
    if f.startswith('аудит/наряди/'): return 'наряди'
    return 'документи'
ПРАВИЛА={'AGENTS.md','CLAUDE.md','GEMINI.md',*['аудит/'+x+'.md' for x in 'МЕНЕДЖЕР ДИСПЕТЧЕР ВИКОНАВЕЦЬ ПЕРЕВІРКА НОУТБУК МОДЕЛІ КОД CHATGPT'.split()]}
def правило(f): return f in ПРАВИЛА or (f.startswith('аудит/адаптери/') and f.endswith('.md'))
a,b=sys.argv[1:3]
out=git('log','origin/main','--first-parent',f'--since={a}T00:00:00Z',f'--until={b}T00:00:00Z','--format=%H%x1f%an%x1f%P%x1f%s')
N=0;c=C.Counter();кор=C.Counter();add=rem=0;prod=[]
for l in out.strip().split('\n'):
    h,an,par,s=l.split('\x1f')
    if an=='github-actions[bot]': continue
    p1=par.split()[0]; N+=1
    files=[f for f in git('diff','--name-only','--no-renames',p1,h).split('\n') if f]
    k=C.Counter(клас_файлу(f) for f in files)
    if k['продукт']:
        c['продукт']+=1
        m=re.search(r'(Е[23]-[\w\-]+|Річ-[\w\-]+)',s); кор[m.group(1) if m else '(без кореня)']+=1
        for ln in git('diff','--numstat','--no-renames',p1,h).split('\n'):
            p=ln.split('\t')
            if len(p)==3 and клас_файлу(p[2])=='продукт' and p[0]!='-': add+=int(p[0]); rem+=int(p[1])
        prod.append(s[:90])
    elif k['прилади'] or k['збірка']: c['прилади/CI(без продукту)']+=1
    elif k['обгортка']: c['обгортка(без продукту/приладів)']+=1
    else: c['лише наряди/стан/дошка/документи']+=1
    if any(k[x] for x in ('прилади',)) : c['усього зачепили прилади']+=1
    if k['обгортка']: c['усього зачепили обгортку']+=1
    if any(правило(f) for f in files): c['змінили файли правил']+=1
print(a,b,'усього',N); [print(' ',x,y) for x,y in c.items()]
print(' продукт +',add,'-',rem); print(' корені',dict(кор.most_common(25)))
if len(sys.argv)>3: print('\n'.join(prod))
