# Інструмент менеджера (02.10): звірка дошки після злиття гілок — кожен рядок main і кожна зміна гілок є рівно раз;
# друкує двійники номерів і порожні рядки всередині таблиці (на main навмисні лише перед 263, 267, 311, 780).
# Запуск: python3 аудит/дошка_звірка.py <файл дошки> <main-реф> <гілка> [<гілка> …]
# Доповнює аудит/дошка_злиття.py: той лишає двійники давніх версій і порожній рядок, коли гілка дописала рядок після порожнього.
import subprocess, re, sys, collections
P='аудит/БЕКЛОГ.md'; num=lambda l:(re.match(r'^\| *(\d+) *\|',l) or [None,None])[1]
def rows(ref, path=None):
    t=open(path,encoding='utf-8').read() if path else subprocess.check_output(['git','show',f'{ref}:{P}']).decode()
    return t.split('\n')
def m(L):
    d=collections.defaultdict(list)
    for l in L:
        n=num(l)
        if n: d[n].append(l)
    return d
C=rows(None, sys.argv[1]); Cm=m(C); main=sys.argv[2]; br=sys.argv[3:]
dup=[n for n,v in Cm.items() if len(v)>1]; print('двійники:',dup)
emp=[num(C[i+1]) for i in range(1,len(C)-1) if C[i]=='' and num(C[i-1]) and num(C[i+1])]; print('порожні перед:',emp)
M=m(rows(main)); bad=0
for b in br:
    base=subprocess.check_output(['git','merge-base',main,b]).decode().strip(); B=m(rows(base)); X=m(rows(b))
    for n,v in X.items():
        if B.get(n)!=v:
            ok=all(l in Cm.get(n,[]) for l in v); bad+=not ok
            print(f'{b.split("/")[-1]} {n}: {"нове" if n not in B else "змінене"} {"✔" if ok else "✗ НЕМА В ЗВЕДЕНІЙ"}')
for n,v in M.items():
    for l in v:
        if l not in Cm.get(n,[]) and not any(m(rows(b)).get(n) for b in br): bad+=1; print('рядок main загублено:',n)
print('рядків: main',sum(len(v) for v in M.values()),'зведена',sum(len(v) for v in Cm.values()),'вад',bad)
