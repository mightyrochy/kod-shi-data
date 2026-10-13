import json, collections, sys, statistics as st
rows = [json.loads(l) for l in open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/а4_v.jsonl')]
H = [r for r in rows if r['рука'] in ('1', '2') and r.get('ідеї')]
print('рук 1–2 з ланцюгом:', len(H))
# 1) ремонт: які 5 з 10 лишились — чи це ті, де найменше зауважень
ov_s, ov_n, rnd = [], [], []
pole_kept = collections.Counter(); pole_asm = collections.Counter()
acts = collections.Counter(); act_by_code = collections.defaultdict(collections.Counter)
items_changed = []; new_ideas = 0; kept_total = 0
for r in H:
    ideas = {i['id']: i for i in r['ідеї']}
    kept = [o['id'] for o in r.get('ремонт_відп') or []]
    kept_in = [k for k in kept if k in ideas]
    new_ideas += len([k for k in kept if k not in ideas])
    if len(ideas) >= 6 and kept_in:
        lo_s = sorted(ideas, key=lambda k: ideas[k]['сила'])[:len(kept_in)]
        lo_n = sorted(ideas, key=lambda k: ideas[k]['n'])[:len(kept_in)]
        ov_s.append(len(set(kept_in) & set(lo_s)) / len(kept_in)); ov_n.append(len(set(kept_in) & set(lo_n)) / len(kept_in))
        rnd.append(len(kept_in) / len(ideas))
    for i in r['ідеї']: pole_asm[i['pole']] += 1
    fm = r.get('ремонт_знахідки') or {}
    vin = r.get('ремонт_вхід_ідеї') or {}
    for o in r.get('ремонт_відп') or []:
        pole_kept[o['pole']] += 1; kept_total += 1
        before = set(x.split('/')[0] for x in vin.get(o['id'], []))
        after = set(x.split('/')[0] for x in o.get('items') or [])
        if before: items_changed.append(len(after - before) + len(before - after))
        for d in o.get('done') or []:
            acts[d.get('action')] += 1
            for c in (fm.get(d.get('finding')) or {}).get('codes', []): act_by_code[c][d.get('action')] += 1
print('ремонт: частка лишених ідей серед найменших за сумою сила_нп: %.2f (навмання %.2f), за кількістю знахідок %.2f; n=%d' % (st.mean(ov_s), st.mean(rnd), st.mean(ov_n), len(ov_s)))
print('ремонт: повна збіжність (лишились рівно найтихіші за силою):', sum(1 for x in ov_s if x == 1.0), 'з', len(ov_s))
print('полюси складання', dict(pole_asm)); print('полюси після ремонту', dict(pole_kept))
print('нових ідей у ремонті (id не з складання):', new_ideas, 'з', kept_total)
print('речей змінено на лишену ідею: середнє %.1f, медіана %s, 0 змін: %d з %d' % (st.mean(items_changed), st.median(items_changed), items_changed.count(0), len(items_changed)))
print('дії done:', dict(acts))
top = sorted(act_by_code.items(), key=lambda kv: -sum(kv[1].values()))[:25]
for c, a in top: print('   %-45s %s' % (c, dict(a)))
