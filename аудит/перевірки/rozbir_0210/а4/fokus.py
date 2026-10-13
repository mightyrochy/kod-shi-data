# K-CRA-02 «фокусів N при стелі 1»: чи «фокуси» — це акцент і його відлуння (одна сім'я кольору)
import json, gzip, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../джерела'))
import colorspace as cs, колір_образу as K
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
h = lambda x: tuple(int(x[i:i+2], 16) for i in (1, 3, 5))
c = collections.Counter(); ex = []
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d = json.load(gzip.open(p, 'rt'))
    except Exception: continue
    for v in d['прогони'][0]['вердикти']:
        if v['рука'] not in ('1', '2'): continue
        for s in v['етапи']['виклики']:
            if s['крок'] != 'assembly': continue
            for o in s['образи_кроку']:
                fs = o.get('знахідки') or []
                foc = [f for f in fs if any(z['code'] == 'focus_count_over_ceiling' for z in f.get('заяви') or [])]
                orph = any(any(z['code'] == 'accent_orphan' for z in f.get('заяви') or []) for f in fs)
                if not foc: continue
                c['фокус>1'] += 1
                if orph: c['фокус>1 і accent_orphan разом'] += 1
                ds = o.get('описи_н') or {}
                fam = []
                for n in foc[0].get('речі') or []:
                    dd = ds.get(n) or next((x for x in ds.values() if x.get('назва') == n), None)
                    if dd and dd.get('hex') and K.нейтраль(cs.to_lab(h(dd['hex']))) is None:
                        fam.append(K.сім_я(cs.to_lab(h(dd['hex']))))
                if len(fam) >= 2 and len(set(fam)) == 1:
                    c['фокуси = одна сім\'я кольору (акцент+відлуння)'] += 1
                    if len(ex) < 4: ex.append((run, v['рука'], o['номер'], o['підпис'], fam, foc[0]['суть'][:160]))
print(dict(c))
for e in ex: print('  ', e)
