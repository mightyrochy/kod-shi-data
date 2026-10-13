# Колір у ланцюгу: частка образів із ≥1 кольоровою річчю (K-COL-06 нейтраль=None) на кожному кроці
import json, gzip, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../джерела'))
import colorspace as cs, колір_образу as K
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
h = lambda x: tuple(int(x[i:i+2], 16) for i in (1, 3, 5))
def chrom(o):
    n = 0
    for d in (o.get('описи_н') or {}).values():
        x = d.get('hex')
        if x and len(x) == 7 and K.нейтраль(cs.to_lab(h(x))) is None: n += 1
    return n
agg = collections.defaultdict(lambda: [0, 0]); per = []
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d = json.load(gzip.open(p, 'rt'))
    except Exception: continue
    for v in d['прогони'][0]['вердикти']:
        if v['рука'] not in ('1', '2'): continue
        row = [run, v['рука']]
        seen = set()
        for s in v['етапи']['виклики']:
            k = s['крок']
            if k in seen: continue
            seen.add(k)
            os_ = s.get('образи_кроку') or []
            c = sum(1 for o in os_ if chrom(o) > 0)
            agg[k][0] += c; agg[k][1] += len(os_)
            row.append('%s %d/%d' % (k[:4], c, len(os_)))
        per.append(row)
for k, (a, b) in agg.items(): print('%-20s образів з кольором %d з %d (%.0f%%)' % (k, a, b, 100 * a / max(b, 1)))
if '-v' in sys.argv:
    for r in per: print(r)
# Лишені ремонтом ідеї: колір ДО ремонту (та сама ідея на складанні) і ПІСЛЯ
tr = collections.Counter(); lost = []
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d = json.load(gzip.open(p, 'rt'))
    except Exception: continue
    for v in d['прогони'][0]['вердикти']:
        if v['рука'] not in ('1', '2'): continue
        st = {s['крок']: s for s in reversed(v['етапи']['виклики'])}
        a, r = st.get('assembly'), st.get('repair')
        if not a or not r: continue
        asm = {o['номер'].replace('о', 'o'): o for o in a['образи_кроку']}
        try: resp = json.loads(r['відповідь_сира'])['outfits']
        except Exception: continue
        reps = r['образи_кроку']
        for i, ro in enumerate(resp):
            if i >= len(reps) or ro.get('id') not in asm: continue
            b, af = chrom(asm[ro['id']]), chrom(reps[i])
            tr[('кольорова' if b else 'нейтральна') + '→' + ('кольорова' if af else 'нейтральна')] += 1
            if b and not af and len(lost) < 8: lost.append((run, v['рука'], ro['id'], asm[ro['id']]['підпис'], '→', ro.get('caption')))
print('лишені ідеї, колір до→після ремонту:', dict(tr))
for x in lost: print('  ', x)
