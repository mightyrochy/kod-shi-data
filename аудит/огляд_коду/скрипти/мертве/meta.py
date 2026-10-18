import os,glob,json,sys,re,subprocess,collections
SP=sys.argv[1]; W=SP+'/wt'; M='/home/user/kod-shi-data'
ages={}
for l in open(SP+'/probe_ages.tsv'):
    d,p=l.rstrip('\n').split('\t',1); ages[os.path.basename(p)]=d
yml=''.join(open(f,encoding='utf-8').read() for f in glob.glob(W+'/.github/workflows/*.yml'))
readme=open(M+'/README.md',encoding='utf-8').read()
board=open(M+'/аудит/БЕКЛОГ.md',encoding='utf-8').read()
# other code mentions
code={}
for dp,dn,fn in os.walk(W+'/джерела'):
    dn[:]=[d for d in dn if d not in('node_modules','__pycache__')]
    for f in fn:
        if f.endswith(('.py','.js','.html')) : code[os.path.join(dp,f)]=open(os.path.join(dp,f),encoding='utf-8',errors='replace').read()
for dp,dn,fn in os.walk(W+'/аудит/проби'):
    for f in fn:
        if f.endswith(('.py','.js','.sh')): code[os.path.join(dp,f)]=open(os.path.join(dp,f),encoding='utf-8',errors='replace').read()
rows=[]
for f in sorted(glob.glob(W+'/джерела/проби/*.py')):
    b=os.path.basename(f); s=b[:-3]; src=open(f,encoding='utf-8').read()
    n=src.count('\n')+(0 if src.endswith('\n') else 1)
    fam=s.split('_')[0]
    cm=sum(1 for g,t in code.items() if g!=f and (b in t or ('проби/'+s) in t))
    rows.append((b,n,fam,ages.get(b,'?'),int(b in yml or s in yml),int(b in readme or s in readme),int(b in board or s in board),cm))
open(SP+'/s/meta.tsv','w').write('файл\tрядків\tсім\'я\tдата\tyml\tREADME\tдошка\tзгадок_у_коді\n'+''.join('\t'.join(map(str,r))+'\n' for r in rows))
print(len(rows),sum(r[1] for r in rows))
print('yml',sum(r[4] for r in rows),'README',sum(r[5] for r in rows),'дошка',sum(r[6] for r in rows),'код',sum(1 for r in rows if r[7]))
print('жодної згадки (yml/README/дошка/код):',sum(1 for r in rows if not(r[4] or r[5] or r[6] or r[7])))
fam=collections.Counter(r[2] for r in rows); print(len(fam),'сімей; ≥5:',sum(1 for v in fam.values() if v>=5))
import statistics
print('рядків: медіана',statistics.median(r[1] for r in rows),'max',max(r[1] for r in rows),'>40:',sum(1 for r in rows if r[1]>40))
dc=collections.Counter(r[3][:7] for r in rows); print(dc)
wk=collections.Counter(r[3] for r in rows); print(sorted(wk.items())[:3],sorted(wk.items())[-3:])
