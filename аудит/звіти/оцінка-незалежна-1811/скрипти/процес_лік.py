import subprocess, re, sys, collections
R='/home/user/kod-shi-data'
mods=set(open('/tmp/модулі_b8.txt').read().split())
def g(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=false',*a],capture_output=True,text=True).stdout
since, until = sys.argv[1], sys.argv[2]
lines=g('log','--first-parent','--format=%H\x1f%P\x1f%cI\x1f%s',f'--since={since}',f'--until={until}','origin/main').strip().split('\n')
def product(f):
    if f.startswith('джерела/показ/'): return True
    if f in ('джерела/показ.html','джерела/показ.css','показ.html','показ.css'): return True
    if re.match(r'(джерела/)?worker[^/]*\.js$',f): return True
    mm=re.match(r'джерела/([^/]+)\.py$',f)
    return bool(mm and mm.group(1) in mods)
stat=collections.Counter(); bot=0; pr=0; nopr=0
for L in lines:
    h,p,d,s=L.split('\x1f')
    ps=p.split()
    files=g('diff-tree','--no-commit-id','-r','--name-only',ps[0] if ps else '--root',h).split('\n')
    files=[f for f in files if f]
    num=re.search(r'#(\d+)',s)
    isbot = s.startswith('збірка:') or s.startswith('дошка: згорнуто') or s.startswith('дошка й паспорти: згор')
    if isbot: bot+=1; continue
    if not num: nopr+=1; stat['безPR']+=1
    if any(product(f) for f in files): k='продукт'
    elif files and all(f.startswith('аудит/') for f in files):
        if all(f=='аудит/СТАН.md' or f.startswith('аудит/наряди/') for f in files): k='аудит:лише стан/наряди'
        else: k='аудит:інше'
    elif files and all(f.startswith('аудит/') or f.endswith('.md') for f in files): k='документи .md поза аудит'
    elif files and all(f.startswith('джерела/прилади/') or 'тест' in f or f.startswith('.github/') or f.startswith('аудит/') for f in files): k='прилади/тести/CI(+аудит)'
    else: k='інше'
    stat[k]+=1
print('усього',len(lines),'бот',bot,'небот',len(lines)-bot)
for k,v in stat.most_common(): print(k,v)
