# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): js.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_js.py "$PWD/джерела" — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import re,sys,glob,collections
С=re.compile(r"[а-яіїєґё]{3,}",re.I)
def токени(s):
    i=0;n=len(s);prev=''
    while i<n:
        c=s[i]
        if s.startswith('/*',i): j=s.find('*/',i+2); i=n if j<0 else j+2; continue
        if s.startswith('//',i): j=s.find('\n',i); i=n if j<0 else j; continue
        if c in '"\'`':
            j=i+1
            while j<n and s[j]!=c:
                j+= 2 if s[j]=='\\' else 1
            yield ('str',s[i+1:j],s.count('\n',0,i)+1); i=j+1; prev='x'; continue
        if c=='/' and prev in '(,=:[!&|?{};+' :
            j=i+1; кл=False
            while j<n and (s[j]!='/' or кл) and s[j]!='\n':
                if s[j]=='\\': j+=2; continue
                if s[j]=='[': кл=True
                elif s[j]==']': кл=False
                j+=1
            yield ('re',s[i+1:j],s.count('\n',0,i)+1); i=j+1; prev='x'; continue
        if not c.isspace(): prev=c
        i+=1
tot=collections.Counter(); пр=collections.defaultdict(list)
for f in sorted(glob.glob(sys.argv[1]+'/показ/*.js'))+[sys.argv[1]+'/показ_шаблон.js',sys.argv[1]+'/worker_джерело.js']:
    try: s=open(f,encoding='utf-8').read()
    except: continue
    for k,v,l in токени(s):
        if С.search(v):
            tot[(f.split('/')[-1],k)]+=1
            if len(пр[k])<400: пр[k].append('%s:%d %r'%(f.split('/')[-1],l,v[:70]))
by=collections.Counter()
for (f,k),v in tot.items(): by[k]+=v
print('рядків з кирилицею (str):',by['str'],'· regex-літералів з кирилицею:',by['re'])
for (f,k),v in sorted(tot.items(),key=lambda x:-x[1]):
    if k=='str': print('  ',f,v)
print('== regex'); [print('  ',p) for p in пр['re']]
