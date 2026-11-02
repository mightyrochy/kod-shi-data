# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (`аудит/корені/Приховані-перелік-а.md`, група G6, п.12 і «Технології»): js_переліки.

Запуск з кореня репозиторію: python3 -I джерела/прилади/приховані_a_g6_js_переліки.py джерела — друкує лічбу й місця; вимір 31.10 на b3259d70."""
import re,sys,glob,os
d=sys.argv[1]
КОД=re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
py=''
for f in glob.glob(d+'/*.py'):
    b=os.path.basename(f)
    if re.match(r'(тест|стенд|батарея|проба|gate|audit|measure|build_)',b): continue
    py+=open(f,encoding='utf-8').read()
pyset=set(re.findall(r"""["']([a-z][a-z0-9]*(?:_[a-z0-9]+)+)["']""",py))
масиви=re.compile(r"(?:const|let|var)\s+([\wА-ЯІЇЄҐа-яіїєґ_]+)\s*=\s*(?:new Set\()?\[([^\]]{0,2000})\]")
об=re.compile(r"(?:const|let|var)\s+([\wА-ЯІЇЄҐа-яіїєґ_]+)\s*=\s*(?:Object\.freeze\()?\{([^{}]{0,4000})\}")
всього=0; рядки=[]
for f in sorted(glob.glob(d+'/показ/*.js')):
    s=open(f,encoding='utf-8').read()
    for rx,вид in ((масиви,'масив'),(об,'обʼєкт')):
        for m in rx.finditer(s):
            if вид=='масив': кл=re.findall(r"""['"]([^'"]+)['"]""",m.group(2))
            else: кл=re.findall(r"""(?:^|[,{\s])['"]?([a-z][a-z0-9_]*)['"]?\s*:""",m.group(2))
            коди=[k for k in кл if КОД.match(k)]
            if len(коди)>=3:
                у_py=sum(k in pyset for k in коди)
                if у_py>=3:
                    всього+=1; рядки.append("%s:%d %s %s коди=%d з них у Python=%d %s"%(os.path.basename(f),s.count('\n',0,m.start())+1,вид,m.group(1),len(коди),у_py,коди[:4]))
print("JS-переліків кодів (≥3 snake_case), чиї коди є в Python-рядках:",всього)
for r in рядки: print(' ',r)
