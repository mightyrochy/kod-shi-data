# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): слова.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_слова.py "$PWD/джерела" (шлях абсолютний) — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import ast, io, os, re, sys, collections
ТУТ = sys.argv[1]; sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import status
СЛОВО = re.compile(r"[а-яіїєґё]{3,}", re.I)
RE_F = {"compile","search","match","fullmatch","findall","finditer","sub","split","subn"}
підсумок = collections.Counter(); приклади = collections.defaultdict(list); файли = collections.defaultdict(set)
def док(n):
    return isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant)
for м in status.МОДУЛІ_ПРОДУКТУ:
    ф = м + ".py"
    try: дер = ast.parse(io.open(ф, encoding="utf-8").read())
    except Exception: continue
    доки = set()
    for n in ast.walk(дер):
        if док(n): доки.add(id(n.body[0].value))
        for c in ast.iter_child_nodes(n): c._бать = n
    # верхні Assign контейнерів, що їх бачить лічба
    бачить = set()
    for в in дер.body:
        if isinstance(в,(ast.Assign,ast.AnnAssign)) and isinstance(в.value,(ast.Dict,ast.List,ast.Tuple,ast.Set,ast.Call)):
            сл=set()
            for x in ast.walk(в.value):
                if isinstance(x,ast.Constant) and isinstance(x.value,str): сл.update(w.lower() for w in СЛОВО.findall(x.value))
            if len(сл)>=2:
                for x in ast.walk(в.value): бачить.add(id(x))
    for n in ast.walk(дер):
        if not (isinstance(n,ast.Constant) and isinstance(n.value,str)) or id(n) in доки: continue
        if not СЛОВО.search(n.value): continue
        if id(n) in бачить: підсумок["бачить_лічба"]+=1; continue
        # класифікація
        б = getattr(n,'_бать',None); кл="інше"
        # всередині функції?
        x=n; у_функції=False
        while getattr(x,'_бать',None) is not None:
            x=x._бать
            if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)): у_функції=True; break
        if isinstance(б,ast.JoinedStr): кл="f-рядок"
        elif isinstance(б,ast.Call) and isinstance(б.func,ast.Attribute) and б.func.attr in RE_F and isinstance(б.func.value,ast.Name) and б.func.value.id=="re": кл="regex"
        elif isinstance(б,ast.Compare) or (isinstance(б,(ast.Tuple,ast.List,ast.Set)) and isinstance(getattr(б,'_бать',None),ast.Compare)): кл="порівняння"
        elif isinstance(б,ast.Call) and isinstance(б.func,ast.Attribute) and б.func.attr in {"startswith","endswith","find","index","count","replace"}: кл="метод_рядка"
        elif isinstance(б,ast.Call) and isinstance(б.func,ast.Name) and б.func.id in {"print"}: кл="print"
        elif isinstance(б,(ast.Raise,)) or (isinstance(б,ast.Call) and isinstance(getattr(б,'_бать',None),ast.Raise)): кл="виняток"
        elif isinstance(б,ast.Return): кл="return"
        ключ = ("функція:" if у_функції else "модуль:")+кл
        підсумок[ключ]+=1; файли[ключ].add(ф)
        if len(приклади[ключ])<6: приклади[ключ].append("%s:%d %r"%(ф,n.lineno,n.value[:60]))
for k,v in sorted(підсумок.items(), key=lambda kv:-kv[1]):
    print("%-28s %6d  файлів=%d"%(k,v,len(файли[k])))
for k in приклади:
    print("==",k); [print("  ",p) for p in приклади[k]]
