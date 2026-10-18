import subprocess,os,collections,sys,re
SP=sys.argv[1]
sys.path.insert(0,'джерела'); import склад
core=set(склад.модулі_системи('джерела'))
fs=[f for f in subprocess.run(['git','ls-files','-z'],capture_output=True).stdout.decode().split('\0') if f and os.path.exists(f)]
def grp(f):
    if f.startswith('джерела/проби/') or f.startswith('аудит/проби/'): return 'проби'
    if f.startswith('.github/') : return 'CI'
    if f=='README.md': return 'README'
    if f.startswith('джерела/') and f.endswith('.py') and f.count('/')==1 and os.path.basename(f)[:-3] in core: return 'ядро'
    if f.startswith('джерела/') and f.endswith(('показ.html','worker.js','worker_джерело.js','показ_шаблон.js')): return 'ядро'
    if f.startswith('джерела/') and f.endswith(('.py','.js','.html','.ps1')): return 'прилади/інше'
    return None
src={f:open(f,encoding='utf-8',errors='replace').read() for f in fs if grp(f)}
rows=[l.split('\t') for l in open(SP+'/s/nonpy_tracked.tsv').read().splitlines()]
res=collections.defaultdict(lambda:[0,0]); lst=collections.defaultdict(list)
for s,f in rows:
    s=int(s)
    if f.startswith('джерела/проби/'): continue
    b=os.path.basename(f); d=os.path.dirname(f)
    keys=[b]
    for sub in('/попередні_спроби/','/фото_v2/','/рядки_5190/','/дані_5191_5194/'):
        if sub in f: keys=[os.path.basename(os.path.dirname(f)) if 'попередні' in sub or 'фото_v2' in sub else sub.strip('/')]
    if f.startswith('джерела/прилади/рядки_5190/'): keys=['рядки_5190','попередні_спроби']
    gs=set()
    for k in keys:
        for g,t in src.items():
            if g!=f and k in t: gs.add(grp(g))
    cls='ніхто (ні код, ні CI)' if not gs else ('лише проби' if gs=={'проби'} else ('продукт' if 'ядро' in gs or 'CI' in gs else 'прилади'))
    ext=os.path.splitext(f)[1]
    kind='документи(md/txt)' if ext in('.md','.txt') else ('дані' if ext in('.gz','.json','.tsv','.jpg','.xml') else 'код/інше')
    res[(cls,kind)][0]+=1; res[(cls,kind)][1]+=s
    lst[(cls,kind)].append((s,f))
for k,v in sorted(res.items()): print(k,v)
with open(SP+'/дані_використання.tsv','w') as o:
    o.write('клас\tвид\tбайт\tфайл\n')
    for k,l in lst.items():
        for s,f in sorted(l,reverse=True): o.write('%s\t%s\t%d\t%s\n'%(k[0],k[1],s,f))
