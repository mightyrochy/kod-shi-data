# -*- coding: utf-8 -*-
"""Компактний друк: корпус проти коду для списку ID."""
import sys, re, glob
ТЕМИ=['тема-1_тіло-посадка-силует.md','тема-2_колір.md','тема-3_матеріали-і-ремесло_v3.md',
 'тема-4_композиція-і-когерентність-EN.md','тема-5_знання.md','тема-6_людина-профіль-і-діалог_v2.md',
 'topic-7-data-catalogue-wardrobe.md','тема-8_психо-шар_первинники.md',
 'тема-9_retrieval-шар_аудит-першоджерел.md','тема-10_взуття-аксесуари-прикраси.md',
 'тема-11_верхній-шар.md','тема-12_чоловічий-стиль.md','тема-13_стилі-реєстри.md']
МОД=[f for f in sorted(glob.glob('*.py')) if not f.startswith(('вимір','прогін','патч','механізм','звірка','_'))]
# БЕЗ АРГУМЕНТІВ — ПІДКАЗКА, А НЕ IndexError (08.09.2026, крок A7). Прилад
# документований у ПЛАН.md рядком «python3 звірка.py K-XXX-NN», і голий запуск
# падав трасою. Траса замість підказки читається як «прилад зламаний».
if len(sys.argv) < 2:
    raise SystemExit("вжиток: python3 звірка.py [кількість_байтів] K-XXX-NN [K-YYY-NN …]\n"
                     "  друкує, що корпус каже про кожен ID і де код його згадує")
КБ=int(sys.argv[1]) if sys.argv[1].isdigit() else 620
ІД=sys.argv[2:] if sys.argv[1].isdigit() else sys.argv[1:]
for rid in ІД:
    print('\n▛▀▀ %s ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀' % rid)
    канд=[]
    for f in ТЕМИ:
        t=open(f,encoding='utf-8').read()
        for m in re.finditer(r'(?:^|\n)[>\s#*]*\*{0,2}'+re.escape(rid)+r'[.\s—–,*]', t):
            кін=min([x for x in (t.find('\n\n> **',m.end()), t.find('\n### ',m.end()), m.end()+2000) if x>0])
            бл=' '.join(t[m.start():кін].split())
            бал=(3 if 'FORCE' in бл else 0)+(2 if re.search(r'\*\*'+re.escape(rid),t[max(0,m.start()-4):m.end()]) else 0)+(1 if 'CHANGES' in бл or 'WHEN' in бл else 0)
            канд.append((бал,f,бл))
    if канд:
        бал,f,бл=max(канд,key=lambda x:x[0])
        print('КОРПУС %s: %s' % (f.split('_')[0], бл[:КБ]))
    else: print('КОРПУС: блоку нема')
    for f in МОД:
        рядки=open(f,encoding='utf-8').read().split('\n')
        for i,l in enumerate(рядки):
            if rid in l and ('_зн(' in l or re.search(r'правило\s*=\s*"'+re.escape(rid),l)):
                бл='\n'.join(рядки[max(0,i-3):i+11])
                print('КОД %s:%d\n%s' % (f,i+1,бл[:900]))
                break
