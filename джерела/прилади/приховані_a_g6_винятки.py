# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): винятки.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_винятки.py "$PWD/джерела" (шлях абсолютний) — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import ast,io,sys,os,collections
os.chdir(sys.argv[1]); sys.path.insert(0,sys.argv[1]); import status
c=collections.Counter(); пр=collections.defaultdict(list); фф=collections.defaultdict(set)
for м in status.МОДУЛІ_ПРОДУКТУ:
    ф=м+'.py'
    try:t=ast.parse(io.open(ф,encoding='utf-8').read())
    except: continue
    for n in ast.walk(t):
        if not isinstance(n,ast.ExceptHandler): continue
        c['усього']+=1
        тіло=n.body
        тип=ast.unparse(n.type) if n.type else 'bare'
        лише_pass=all(isinstance(s,ast.Pass) or (isinstance(s,ast.Expr) and isinstance(s.value,ast.Constant)) for s in тіло)
        є_raise=any(isinstance(x,ast.Raise) for s in тіло for x in ast.walk(s))
        вжито_ім= n.name and any(isinstance(x,ast.Name) and x.id==n.name for s in тіло for x in ast.walk(s))
        виклики={ (x.func.attr if isinstance(x.func,ast.Attribute) else getattr(x.func,'id','')) for s in тіло for x in ast.walk(s) if isinstance(x,ast.Call)}
        журнал=bool(виклики & {'print','warn','warning','error','exception','log','debug','info','append','журнал','записати','збій','помилка'}) 
        if лише_pass: k='pass'
        elif є_raise or вжито_ім or журнал: k='видно'
        else:
            k='без_сліду'
        c[k]+=1; фф[k].add(ф)
        if k!='видно': c[k+':'+тип]+=1
        if k!='видно' and len(пр[k])<8: пр[k].append('%s:%d except %s: %s'%(ф,n.lineno,тип,ast.unparse(тіло[0])[:50]))
for k,v in sorted(c.items(),key=lambda x:-x[1]): print('%-40s %d'%(k,v))
print('файлів pass:',len(фф['pass']),' без_сліду:',len(фф['без_сліду']))
for k in пр: print('==',k); [print('  ',p) for p in пр[k]]
