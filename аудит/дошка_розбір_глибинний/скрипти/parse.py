# -*- coding: utf-8 -*-
"""Розбір дошки на рядки з клітинками → $ROZBIR/rows.json"""
import os
import re, json, sys
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
ДОШКА = sys.argv[1] if len(sys.argv) > 1 else 'аудит/БЕКЛОГ.md'
txt = open(ДОШКА, encoding='utf-8').read().split('\n')
row = re.compile(r'^\| *(\d+) *\|')
sep = re.compile(r'(?<!\\)\|')
sec = ''
rows = []
for i, l in enumerate(txt, 1):
    if l.startswith('#'):
        sec = l.strip('# ').strip()
        continue
    m = row.match(l)
    if not m:
        continue
    p = [x.start() for x in sep.finditer(l)]
    cells = [l[p[k]+1:p[k+1]].strip() for k in range(len(p)-1)]
    rows.append({'n': int(m[1]), 'line': i, 'sec': sec, 'src': cells[1] if len(cells) > 1 else '',
                 'w': cells[2] if len(cells) > 2 else '', 'st': cells[3] if len(cells) > 3 else '',
                 'rest': ' | '.join(cells[4:]), 'raw': l})
json.dump(rows, open(РОБОЧА + '/rows.json', 'w', encoding='utf-8'), ensure_ascii=False)
print(len(rows))
