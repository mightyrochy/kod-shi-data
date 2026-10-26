# -*- coding: utf-8 -*-
import os
import json, re, collections
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
rows = json.load(open(РОБОЧА + '/rows2.json', encoding='utf-8'))
nums = {r['n'] for r in rows}
REF = re.compile(r'(?:рядк\w*|рядок|рядку|рядка|рядки|рядків)\s*(?:№\s*)?((?:\d{1,5}(?:\s*(?:,|і|та|–|-|/)\s*)?)+)')
def refs(text, self_n):
    out = set()
    for m in REF.finditer(text):
        for x in re.findall(r'\d{1,5}', m.group(1)):
            x = int(x)
            if x in nums and x != self_n: out.add(x)
    return out
for r in rows:
    r['refs_src'] = sorted(refs(r['src'], r['n']))
    r['refs_all'] = sorted(refs(r['raw'], r['n']))
има = sum(1 for r in rows if r['refs_src'])
има2 = sum(1 for r in rows if r['refs_all'])
print('рядків з посиланням у «джерелі»:', има, 'з посиланням будь-де:', има2, 'з', len(rows))
# parent = earlier-numbered row referenced in src (if any) else in all
par = {}
for r in rows:
    cand = [x for x in r['refs_src'] if x < r['n']] or [x for x in r['refs_all'] if x < r['n']]
    if cand: par[r['n']] = cand
kids = collections.Counter()
for n, ps in par.items():
    for p in ps: kids[p] += 1
print('найбільше нащадків (на кого посилаються пізніші рядки):')
byn = {r['n']: r for r in rows}
for p, k in kids.most_common(25):
    t = byn[p]['raw'][:160].replace('\n',' ')
    print(k, t)
# depth via first parent chain (max parent)
import functools, sys
sys.setrecursionlimit(10000)
@functools.lru_cache(None)
def depth(n, seen=()):
    ps = par.get(n, [])
    if not ps: return 0
    return 1 + max(depth(p) for p in ps if p < n)
d = collections.Counter(depth(r['n']) for r in rows)
print('глибина ланцюжків:', sorted(d.items()))
json.dump({'par': par}, open(РОБОЧА + '/par.json','w'), ensure_ascii=False)
