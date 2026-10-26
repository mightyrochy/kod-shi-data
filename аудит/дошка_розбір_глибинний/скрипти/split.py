# -*- coding: utf-8 -*-
"""Рядки дошки → записи з перенесенням рядків → частини ≤ 24 тис. знаків, групи ~125 тис. знаків на субагента."""
import os
import json, re, textwrap, os
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
rows = json.load(open(РОБОЧА + '/rows2.json', encoding='utf-8'))
sep = re.compile(r'(?<!\\)\|')
def wrap(s, w=900):
    return '\n'.join(textwrap.wrap(s, w, break_long_words=True, break_on_hyphens=False)) if s else '—'
recs = []
for r in rows:
    l = r['raw']; p = [x.start() for x in sep.finditer(l)]
    cells = [l[p[k]+1:p[k+1]].strip() for k in range(len(p)-1)]
    src = cells[1] if len(cells) > 1 else ''
    w = cells[2] if len(cells) > 2 else ''
    st = cells[3] if len(cells) > 3 else ''
    tail = cells[4:]
    if len(cells) == 7:
        body = f"ОПИС/ДОКАЗ: {tail[0]}\nФАЙЛИ: {tail[1]}\nПРИЙМАННЯ: {tail[2][:220]}{'…' if len(tail[2])>220 else ''}"
    else:
        body = 'РЕШТА КЛІТИНОК: ' + ' ¦ '.join(tail)
    rec = f"=== РЯДОК {r['n']} · розділ дошки: {r['sec'][:60]}\nДЖЕРЕЛО: {src}\nВАГА: {w}\nСТАТУС: {st}\n{body}\n"
    rec = '\n'.join(wrap(x) for x in rec.split('\n')) + '\n'
    recs.append((r['n'], rec))
# групи
GROUP = 125000; PART = 17000
groups = []; cur = []; size = 0
for n, rec in recs:
    if size + len(rec) > GROUP and cur:
        groups.append(cur); cur = []; size = 0
    cur.append((n, rec)); size += len(rec)
if cur: groups.append(cur)
index = []
for gi, g in enumerate(groups, 1):
    parts = []; buf = ''; k = 1
    for n, rec in g:
        if len(buf) + len(rec) > PART and buf:
            fn = f'{РОБОЧА}/parts/g{gi:02d}_p{k}.txt'; open(fn, 'w', encoding='utf-8').write(buf); parts.append(fn); k += 1; buf = ''
        buf += rec + '\n'
    if buf:
        fn = f'{РОБОЧА}/parts/g{gi:02d}_p{k}.txt'; open(fn, 'w', encoding='utf-8').write(buf); parts.append(fn)
    index.append({'g': gi, 'rows': len(g), 'first': g[0][0], 'last': g[-1][0], 'chars': sum(len(x[1]) for x in g), 'parts': parts, 'nums': [x[0] for x in g]})
json.dump(index, open(РОБОЧА + '/index.json', 'w', encoding='utf-8'), ensure_ascii=False)
for x in index: print(x['g'], x['rows'], x['first'], x['last'], x['chars'], len(x['parts']))
print('groups', len(index), 'max part', max(os.path.getsize(p) for x in index for p in x['parts']))
