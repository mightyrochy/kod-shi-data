# Інструмент менеджера (01.10): `git merge origin/main` у гілці PR → конфлікт у дошці → `python3 аудит/дошка_злиття.py` → `git add аудит/БЕКЛОГ.md && git commit --no-edit`.
# Розв'язує конфлікти злиття в аудит/БЕКЛОГ.md за правилом менеджера:
# по номеру рядка — та сторона, що змінилась відносно бази; обидві змінились — ЗАКРИТО > ЧАСТКОВО > ВІДКРИТО;
# новий рядок лишається з будь-якої сторони. Інші файли не чіпає.
import subprocess, re, sys
from collections import defaultdict
p='аудит/БЕКЛОГ.md'
other=sys.argv[1] if len(sys.argv)>1 else 'origin/main'
base_sha=subprocess.check_output(['git','merge-base','HEAD',other]).decode().strip()
base=subprocess.check_output(['git','show',f'{base_sha}:{p}']).decode('utf-8').split('\n')
num=lambda l: (re.match(r'^\| *(\d+) *\|',l) or [None,None])[1]
B=defaultdict(list)
for l in base:
    if num(l): B[num(l)].append(l)
rank=lambda l: 3 if 'ЗАКРИТО' in l else 2 if 'ЧАСТКОВО' in l else 1
L=open(p,encoding='utf-8').read().split('\n'); out=[]; i=0; log=[]
while i<len(L):
    if L[i].startswith('<<<<<<< '):
        j=L.index('=======',i); k=next(n for n in range(j,len(L)) if L[n].startswith('>>>>>>> '))
        O,T,order={},{},[]
        for side,D in ((L[i+1:j],O),(L[j+1:k],T)):
            for l in side:
                n=num(l) or ('#'+l)
                D[n]=l
                if n not in order: order.append(n)
        for n in order:
            o,t=O.get(n),T.get(n)
            if o is None: out.append(t); log.append(f'{n}:інша'); continue
            if t is None: out.append(o); log.append(f'{n}:гілка'); continue
            if o==t: out.append(o); continue
            ob,tb=o in B.get(n,[]),t in B.get(n,[])
            if ob and not tb: out.append(t); log.append(f'{n}:інша')
            elif tb and not ob: out.append(o); log.append(f'{n}:гілка')
            else:
                ch=o if rank(o)>=rank(t) else t; out.append(ch); log.append(f'{n}:ранг')
        i=k+1
    else:
        out.append(L[i]); i+=1
open(p,'w',encoding='utf-8').write('\n'.join(out))
print(' · '.join(log) or 'конфліктів нема')
