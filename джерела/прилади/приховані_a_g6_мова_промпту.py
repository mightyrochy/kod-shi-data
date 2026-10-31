# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): мова_промпту.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_мова_промпту.py джерела — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import ast,io,sys,os,glob
os.chdir(sys.argv[1])
так=[];ні=[]
for ф in sorted(glob.glob('*.py')):
    if ф.startswith('тест'): continue
    try:t=ast.parse(io.open(ф,encoding='utf-8').read())
    except: continue
    for n in ast.walk(t):
        if isinstance(n,ast.Call) and getattr(n.func,'id',getattr(n.func,'attr',None))=='Оголошення':
            kw={k.arg:k.value for k in n.keywords}
            з=kw.get('задача'); з=з.value if isinstance(з,ast.Constant) else (n.args[0].value if n.args and isinstance(n.args[0],ast.Constant) else '?')
            м=kw.get('мова_промпту'); мв=м.value if isinstance(м,ast.Constant) else ('вираз' if м else None)
            (так if мв=='en' else ні).append("%s:%d %s мова_промпту=%s"%(ф,n.lineno,з,мв))
print("en:",len(так)); [print(' ',x) for x in так]
print("не en:",len(ні)); [print(' ',x) for x in ні]
