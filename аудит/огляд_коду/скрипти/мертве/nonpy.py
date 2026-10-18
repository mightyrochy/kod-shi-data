import subprocess,os,collections,re,sys
SP=sys.argv[1]
fs=[f for f in subprocess.run(['git','ls-files','-z'],capture_output=True).stdout.decode().split('\0') if f and os.path.exists(f)]
code={};docs={}
for f in fs:
    e=os.path.splitext(f)[1]
    if e in('.py','.js','.html','.yml','.ps1','.sh') or f in('README.md',):
        code[f]=open(f,encoding='utf-8',errors='replace').read()
    elif e in('.md','.txt','.tsv') and os.path.getsize(f)<3e6:
        docs[f]=open(f,encoding='utf-8',errors='replace').read()
# add generated probe-run? no
rows=[l.split('\t') for l in open(SP+'/s/nonpy_tracked.tsv').read().splitlines()]
out=[]
for s,f in rows:
    s=int(s); b=os.path.basename(f); stem=b.split('.')[0]
    names={b}
    d=os.path.dirname(f)
    key=[b]
    if '/попередні_спроби/' in f or '/фото_v2/' in f or '/рядки_5190/' in f: key=[os.path.basename(d)]
    if f.startswith('джерела/проби/'): continue
    cc=0;dc=0;who=[]
    for k in key:
        for g,t in code.items():
            if g==f: continue
            n=t.count(k)
            if n: cc+=n; who.append(g.replace('джерела/',''))
        for g,t in docs.items():
            if g==f: continue
            dc+=t.count(k)
    out.append((s,f.replace('джерела/',''),cc,dc,';'.join(who[:3])))
open(SP+'/s/nonpy_refs.tsv','w').write(''.join('%d\t%s\t%d\t%d\t%s\n'%r for r in out))
z=[r for r in out if r[2]==0]
print('без згадки в коді:',len(z),sum(r[0] for r in z))
zd=[r for r in z if r[3]==0]
print('без згадки ні в коді, ні в документах:',len(zd),sum(r[0] for r in zd))
for r in sorted(z,reverse=True)[:60]: print(r[0],r[1],'docs=%d'%r[3])
