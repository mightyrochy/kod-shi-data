# -*- coding: utf-8 -*-
"""Зведення розмітки груп: $ROZBIR/out/g*.tsv → таблиці в stdout і $ROZBIR/розмітка.tsv"""
import os
import glob, json, re, collections, sys
РОБОЧА = os.environ.get('ROZBIR', '/tmp/rozbir')  # робоча тека розбору; запуск — з кореня репозиторію
rows3 = {r['n']: r for r in json.load(open(РОБОЧА + '/rows3.json', encoding='utf-8'))}
K = ['n','стан','рід','підсистема','ланка','механізм','виявлено','закриття','доказ','повтор','батьки','суть']
R = []
for fn in sorted(glob.glob(РОБОЧА + '/out/g*.tsv')):
    for l in open(fn, encoding='utf-8'):
        if not l.strip() or l.startswith('n\t'): continue
        c = [x.strip().replace('’', "'").replace('ʼ', "'") for x in l.rstrip('\n').split('\t')]
        if len(c) != 12: continue
        d = dict(zip(K, c)); d['n'] = int(d['n']); R.append(d)
print('розмічено рядків:', len(R), 'унікальних:', len({d['n'] for d in R}))
by = {d['n']: d for d in R}
def тиждень(n):
    d = rows3.get(n, {}).get('дата', '??')
    if d == '??': return '6) 19.10–' if n > 8648 else '??'
    m, dd = map(int, d.split('-')); doy = dd if m == 9 else 30 + dd
    return {0:'1) 14–20.09',1:'2) 21–27.09',2:'3) 28.09–04.10',3:'4) 05–11.10',4:'5) 12–18.10',5:'6) 19.10–'}.get((doy-14)//7, '6) 19.10–')
for d in R: d['тиждень'] = тиждень(d['n'])
def tab(key, sub=None, rows=R, top=40):
    c = collections.Counter(d[key] for d in rows)
    if sub is None:
        tot = sum(c.values())
        for k, v in c.most_common(top): print(f'  {v:5d} {100*v/tot:5.1f}% {k}')
    else:
        ct = collections.defaultdict(collections.Counter)
        for d in rows: ct[d[key]][d[sub]] += 1
        for k, _ in c.most_common(top): print(f'  {k:22s} {sum(ct[k].values()):5d}', dict(ct[k].most_common(8)))
def mech(rows):
    c = collections.Counter()
    for d in rows:
        for t in d['механізм'].split('+'):
            t = t.strip(); c['інше:*' if t.startswith('інше:') else t] += 1
    return c
if __name__ == '__main__':
    for k in ['стан','рід','підсистема','ланка','виявлено','закриття','доказ']:
        print('==', k); tab(k)
    print('== рід × стан'); tab('рід', 'стан')
    print('== підсистема × рід'); tab('підсистема', 'рід')
    print('== ланка × виявлено (лише вади)'); tab('ланка', 'виявлено', [d for d in R if d['рід'].startswith('вада')])
    print('== механізм (усі)'); tot = len(R)
    for k, v in mech(R).most_common(): print(f'  {v:5d} {100*v/tot:5.1f}% {k}')
    print('== механізм: відкриті (ВІДКРИТО+ЧАСТКОВО)')
    op = [d for d in R if d['стан'] in ('ВІДКРИТО','ЧАСТКОВО')]
    for k, v in mech(op).most_common(15): print(f'  {v:5d} {k}')
    print('== тиждень × рід'); tab('тиждень', 'рід')
    print('== тиждень × закриття'); tab('тиждень', 'закриття')
    print('== тиждень × виявлено'); tab('тиждень', 'виявлено')
    # повернення: на рядок посилаються пізніші як «повернення:N» або «тема:N»
    назад = collections.defaultdict(set)
    for d in R:
        m = re.match(r'^(тема|повернення|регресія):(.*)$', d['повтор'])
        if m:
            for x in re.findall(r'\d{2,5}', m.group(2)):
                x = int(x)
                if x in by and x < d['n'] and not m.group(2).strip().startswith('#'): назад[x].add((m.group(1), d['n']))
    zak = [d for d in R if d['стан'] in ('ЗАКРИТО','ЧАСТКОВО')]
    print('== чи вада поверталась (пізніший рядок посилається «тема/повернення» на закритий) × закриття')
    ct = collections.defaultdict(lambda: [0, 0])
    for d in zak:
        ct[d['закриття']][0] += 1
        if any(t == 'повернення' for t, _ in назад[d['n']]) or len(назад[d['n']]) > 0: ct[d['закриття']][1] += 1
    for k, (a, b) in sorted(ct.items(), key=lambda x: -x[1][0]): print(f'  {k:12s} закрито {a:5d}, потім той самий механізм/повернення {b:4d} ({100*b/max(a,1):.0f}%)')
    ct = collections.defaultdict(lambda: [0, 0])
    for d in zak:
        ct[d['доказ']][0] += 1
        if назад[d['n']]: ct[d['доказ']][1] += 1
    print('== те саме × доказ')
    for k, (a, b) in sorted(ct.items(), key=lambda x: -x[1][0]): print(f'  {k:8s} закрито {a:5d}, повертались {b:4d} ({100*b/max(a,1):.0f}%)')
    print('== повтор (вид)'); c = collections.Counter(d['повтор'].split(':')[0] for d in R); print(' ', c.most_common())
    with open(РОБОЧА + '/розмітка.tsv', 'w', encoding='utf-8') as f:
        f.write('\t'.join(K + ['тиждень']) + '\n')
        for d in sorted(R, key=lambda x: x['n']): f.write('\t'.join(str(d[k]) for k in K + ['тиждень']) + '\n')
