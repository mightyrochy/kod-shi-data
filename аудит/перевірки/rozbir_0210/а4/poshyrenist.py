# Поширеність вад А4 по прогонах: скільки прогонів (і рук) має кожну
import json, gzip, os, re, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../джерела'))
import colorspace as cs, колір_образу as K
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
h = lambda x: tuple(int(x[i:i+2], 16) for i in (1, 3, 5))
TOP = re.compile(r'блуз|сороч|\bтоп|футбол|светр|джемпер|гольф|водолаз|лонгслів|боді|кофт|майк|пуловер', re.I)
JKT = re.compile(r'піджак|жакет|жилет|блейзер|костюм|двійка', re.I)
KNIT = re.compile(r'в[ʼ\'’]?яз|светр|джемпер|кардиган|гольф|пуловер|трикотаж', re.I)
runs = collections.defaultdict(set); hands = collections.Counter()
def codes(f): return {z['code'] for z in f.get('заяви') or []}
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not run.startswith('ж') or not os.path.exists(p): continue
    try: d = json.load(gzip.open(p, 'rt'))
    except Exception: continue
    runs['прогонів'].add(run)
    for v in d['прогони'][0]['вердикти']:
        if v['рука'] not in ('1', '2'): continue
        its = v.get('речі_образу') or []
        suit = [r for r in its if (r.get('укладка') or {}).get('тип') in ('костюм', 'комплект') and JKT.search(r['назва']) and not TOP.search(r['назва'])]
        if suit and not any(TOP.search(r['назва']) for r in its if r not in suit):
            runs['В-1 фінал: піджак/жилет комплекту без верху'].add(run); hands['В-1'] += 1
        st = v['етапи']['виклики']
        for s in st:
            for o in s.get('образи_кроку') or []:
                for b in o.get('блокери') or []:
                    if isinstance(b, dict) and any(z['code'] == 'set_with_separate_part' for z in b.get('заяви') or []):
                        runs['В-1 блокер комплект+верх у ланцюгу'].add(run)
        for s in st:
            if s['крок'] != 'assembly': continue
            for o in s['образи_кроку']:
                sl = set((o.get('слоти_н') or {}).values()); fs = o.get('знахідки') or []
                for f in fs:
                    c = codes(f)
                    if 'dress_code_requires_type' in c and f.get('регістр') == 'гейт' and 'сукня' in sl:
                        runs['В-5 гейт «нема сукні» на образі з сукнею'].add(run)
                    if 'outer_will_not_fit_over_bulky' in c:
                        under = (f.get('суть') or '').split('обʼємного')[-1]
                        if not KNIT.search(under): runs['В-6 K-OUT-06 над тонким не-в\'язаним'].add(run)
                    if 'focus_count_over_ceiling' in c:
                        ds = o.get('описи_н') or {}; fam = []
                        for n in f.get('речі') or []:
                            dd = ds.get(n) or next((x for x in ds.values() if x.get('назва') == n), None)
                            if dd and dd.get('hex') and K.нейтраль(cs.to_lab(h(dd['hex']))) is None: fam.append(K.сім_я(cs.to_lab(h(dd['hex']))))
                        if len(fam) >= 2 and len(set(fam)) == 1: runs['В-3 відлуння акценту = другий фокус'].add(run)
                if any('scheme_promised_accent_all_neutral' in codes(f) for f in fs) and 'похорон' in run:
                    runs['В-8 похорон: суд вимагає кольору'].add(run)
        ch = [s for s in st if s['крок'] == 'choice']
        if ch:
            pj = json.loads(ch[0]['запит']['текст']); cid = ch[0]['вибір']['обрано'].replace('о', 'o')
            for x in pj['verdict']:
                if x['your_outfit']['id'] == cid and any((it.get('formality') or [0, 0])[1] - (it.get('formality') or [0, 0])[0] >= 6 for it in x['your_outfit']['items']):
                    runs['В-7 обрана сукня зі смугою ошатності ≥6 щаблів'].add(run); hands['В-7'] += 1
    t = open(os.path.join(R, run, 'картки.txt')).read() if os.path.exists(os.path.join(R, run, 'картки.txt')) else ''
    for blk in re.split(r'═══ картка', t)[1:]:
        m = re.match(r' \d з \d · рука (\d)', blk)
        if m and m.group(1) in '12' and re.search(r'(суто|повністю|цілком|геть) нейтральн|речі в (цьому )?образі (—\s)?нейтральн', blk):
            runs['В-9 картка: «образ вийшов нейтральним»'].add(run); hands['В-9'] += 1
for k, v in runs.items(): print('%-55s %2d прогонів %s' % (k, len(v), '' if k == 'прогонів' else ' '.join(sorted(v))[:400]))
print('рук:', dict(hands))
