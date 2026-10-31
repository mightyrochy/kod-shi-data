# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): regex.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_regex.py "$PWD/джерела" (шлях абсолютний) — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import ast,io,re,sys,os
os.chdir(sys.argv[1]); sys.path.insert(0,sys.argv[1]); import status
С=re.compile(r"[а-яіїєґё]{3,}",re.I)
def слова(v):
    s=set()
    for x in ast.walk(v):
        if isinstance(x,ast.Constant) and isinstance(x.value,str): s.update(w.lower() for w in С.findall(x.value))
    return s
бач=0; пропуск=[]
for м in status.МОДУЛІ_ПРОДУКТУ:
    ф=м+'.py'
    try:t=ast.parse(io.open(ф,encoding='utf-8').read())
    except: continue
    seen=set()
    for в in t.body:
        if isinstance(в,(ast.Assign,ast.AnnAssign)) and isinstance(в.value,(ast.Dict,ast.List,ast.Tuple,ast.Set,ast.Call)) and len(слова(в.value))>=2:
            seen.update(id(x) for x in ast.walk(в.value))
    for n in ast.walk(t):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='re' and n.args:
            a=n.args[0]
            if isinstance(a,ast.Constant) and isinstance(a.value,str) and С.search(a.value):
                if id(n) in seen: бач+=1
                else: пропуск.append("%s:%d re.%s %r"%(ф,n.lineno,n.func.attr,a.value[:50]))
print("regex з кирилицею: бачить лічба",бач,"· не бачить",len(пропуск))
for p in пропуск: print(" ",p)
