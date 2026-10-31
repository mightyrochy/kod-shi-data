# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): промпти.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_промпти.py джерела — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import ast,io,re,sys,os,glob
os.chdir(sys.argv[1])
К=re.compile(r"[а-яіїєґё]{3,}",re.I); Л=re.compile(r"[a-z]{3,}",re.I)
for ф in sorted(glob.glob('*.py')):
    if ф.startswith('тест'): continue
    try:t=ast.parse(io.open(ф,encoding='utf-8').read())
    except: continue
    for n in ast.walk(t):
        if isinstance(n,ast.Call) and getattr(n.func,'id',getattr(n.func,'attr',None))=='Оголошення':
            кир=лат=0; прик=[]
            for x in ast.walk(n):
                if isinstance(x,ast.Constant) and isinstance(x.value,str):
                    k=len(К.findall(x.value)); l=len(Л.findall(x.value)); кир+=k; лат+=l
                    if k>=3 and len(прик)<1: прик.append(x.value[:70])
            ім=next((kw.value.value for kw in n.keywords if kw.arg in('імʼя','ім_я','назва','задача') and isinstance(kw.value,ast.Constant)), n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else '?')
            if кир>0: print("%s:%d %s кир=%d лат=%d %r"%(ф,n.lineno,ім,кир,лат,прик))
