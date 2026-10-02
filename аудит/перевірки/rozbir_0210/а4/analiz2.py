import json, collections, sys, statistics as st, re
rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/а4_v.jsonl')]
H = [r for r in rows if r['рука'] in ('1', '2') and r.get('вибір')]
pos = collections.Counter(); posfree = collections.Counter(); nblk = collections.Counter(); chosen_pole = collections.Counter()
lens = []; chosen_blocked = 0; rules_findings = 0; why_kw = collections.Counter(); compl = []
for r in H:
    v = r['вибір']; order = v['ids_prompt'] or []
    ch = (v['обрано'] or '').replace('о', 'o')
    nb = sum(1 for x in v['з_блоком'].values() if x)
    nblk[nb] += 1
    if ch in order:
        p = order.index(ch) + 1; pos[p] += 1
        free = [x for x in order if not v['з_блоком'].get(x)]
        if ch in free: posfree[(free.index(ch) + 1, len(free))] += 1
        if v['з_блоком'].get(ch): chosen_blocked += 1
    else: pos['?'] += 1
    rules_findings += bool(v.get('rules_has_findings'))
    w = v.get('чому') or ''; lens.append(len(w))
    for k in ('accept', 'remark', 'finding', 'formal', 'occasion', 'intent', 'palette', 'colour', 'color', 'face', 'eyes', 'quiet', 'bold', 'safe', 'her words', 'mother-in-law', 'she said', 'she wants'):
        if k in w.lower(): why_kw[k] += 1
    # полюс обраного: з ремонту за підписом
    cap = (v['підписи'] or {}).get(ch)
    pl = next((o['pole'] for o in r.get('ремонт_відп') or [] if o.get('caption') == cap), None)
    chosen_pole[pl] += 1
    if r.get('повнота'):
        for c in r['повнота']: compl.append((r['run'], r['рука'], [b for _, b in c['образи']], len(c and r.get('повнота_відп') and (r['повнота_відп'][0].get('повернуто') or []))))
print('виборів', len(H)); print('позиція обраного у списку промпту', sorted(pos.items(), key=str))
print('образів із блокером у списку вибору (к-сть → прогонів)', dict(nblk)); print('обрано образ із блокером', chosen_blocked)
print('позиція серед вільних від блокерів (поз, з скількох)', dict(posfree))
print('полюс обраного', dict(chosen_pole)); print('довжина why: медіана', st.median(lens)); print('слова в why', dict(why_kw))
print('ремонт повноти (прогін, рука, блокерів на образ після спроби, повернуто кодом):'); [print('  ', c) for c in compl]
