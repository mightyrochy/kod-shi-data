#!/usr/bin/env python3
"""Зведення розкладу. Запуск: python3 -I зведення.py <сцени.json> <зведення.json>  (після розклад.py)."""
import json, sys, statistics as st, collections, math

S = json.load(open(sys.argv[1], encoding='utf-8'))
NORM = {'повне': 420, 'повне +фото': 420, 'розмова': 150, 'палітра': None}
def short(m):
    return {'mamaylm-gemma-3-12b-it-v2.0': 'MamayLM', 'qwen/qwen3.5-9b': 'qwen3.5-9b', 'claude-sonnet-5-5': 'sonnet'}.get(m, m)

def повний(d):
    return bool(d['секунд'] and d['є_тривалість_викликів'] and not d['обірвався'] and d['п'] is not None
                and (d['з'] is not None or d['режим'] in ('розмова', 'палітра')) and all(c['модель'] for c in d['виклики']))

for d in S:
    c = d['виклики']; tot = d['секунд'] or 0
    d['повний'] = повний(d)
    d['викид'] = any(x['с'] > 3000 for x in c)
    d['середовище'] = 'sonnet' if c and all(x['модель'] == 'claude-sonnet-5-5' for x in c) else 'локальні'
    d['запитів'] = len(c)
    by = collections.defaultdict(lambda: {'n': 0, 'с': 0.0, 'макс': 0.0})
    for x in c:
        b = by[short(x['модель'])]; b['n'] += 1; b['с'] += x['с']; b['макс'] = max(b['макс'], x['с'])
    d['по_моделях'] = dict(by)
    d['сума_викликів'] = sum(x['с'] for x in c)
    d['найдовший'] = max((x['с'] for x in c), default=0)
    d['відп_симв'] = sum(x.get('відп_симв', 0) for x in c)
    if d['повний']:
        п, з = d['п'], d['з'] if d['з'] is not None else d['п']
        # крок 1 = до «чат → паспорт», 2 = «збирання», 3+ = решта
        k = {1: 0.0, 2: 0.0, 3: 0.0}
        for x in c:
            kk = min(x['крок'] or 3, 3)
            if d['з'] is None and kk == 2: kk = 3   # розмова/палітра: кроку «збирання» нема
            k[kk] += x['с']
        d['крок_с'] = {'1': п, '2': з - п, '3': tot - з}
        d['виклики_у_кроці'] = k
        d['не_модель_у_кроці'] = {'1': п - k[1], '2': (з - п) - k[2], '3': (tot - з) - k[3]}
        d['не_модель'] = tot - d['сума_викликів']

def q(v, p):
    v = sorted(v); i = (len(v) - 1) * p; lo = math.floor(i); hi = math.ceil(i)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)

out = {'всього_сцен': len(S), 'повних': sum(d['повний'] for d in S), 'повних_локальні': sum(d['повний'] and d['середовище']=='локальні' for d in S), 'повних_sonnet': sum(d['повний'] and d['середовище']=='sonnet' for d in S), 'за_режимами': {}}
F = [d for d in S if d['повний'] and d['середовище'] == 'локальні']
FS = [d for d in S if d['повний'] and d['середовище'] == 'sonnet']
for m in ('повне', 'повне +фото', 'розмова', 'палітра'):
    l = [d for d in F if d['режим'] == m]
    allm = [d for d in S if d['режим'] == m and d['середовище'] == 'локальні']
    if not l: out['за_режимами'][m] = {'сцен_усього': len(allm), 'повних': 0}; continue
    t = [d['секунд'] for d in l]
    r = {'сцен_усього': len(allm), 'повних': len(l), 'мед_с': st.median(t), 'q1': q(t, .25), 'q3': q(t, .75), 'мін': min(t), 'макс': max(t),
         'запитів_мед': st.median(d['запитів'] for d in l), 'сума_викликів_мед': st.median(d['сума_викликів'] for d in l),
         'найдовший_мед': st.median(d['найдовший'] for d in l), 'найдовший_макс': max(d['найдовший'] for d in l),
         'не_модель_мед': st.median(d['не_модель'] for d in l)}
    l2 = [d for d in l if not d['викид']]; tot = sum(d['секунд'] for d in l2); r['викидів_поза_частками'] = len(l) - len(l2)
    r['частка'] = {'виклики_моделей': sum(d['сума_викликів'] for d in l2) / tot, 'не_модель': sum(d['не_модель'] for d in l2) / tot}
    for mod in ('MamayLM', 'qwen3.5-9b', 'sonnet'):
        r['частка'][mod] = sum(d['по_моделях'].get(mod, {'с': 0})['с'] for d in l2) / tot
    r['запитів_по_моделях_мед'] = {mod: st.median(d['по_моделях'].get(mod, {'n': 0})['n'] for d in l2) for mod in ('MamayLM', 'qwen3.5-9b', 'sonnet')}
    r['крок_частка'] = {k: sum(d['крок_с'][k] for d in l2) / tot for k in '123'}
    r['не_модель_у_кроці_частка'] = {k: sum(d['не_модель_у_кроці'][k] for d in l2) / tot for k in '123'}
    r['виклики_у_кроці_частка'] = {str(k): sum(d['виклики_у_кроці'][k] for d in l2) / tot for k in (1, 2, 3)}
    r['перевищень_суми_над_тривалістю'] = sum(d['сума_викликів'] > d['секунд'] + 1 for d in l)
    out['за_режимами'][m] = r

out['sonnet'] = {'сцен': len(FS), 'мед_с': st.median(d['секунд'] for d in FS), 'мін': min(d['секунд'] for d in FS), 'макс': max(d['секунд'] for d in FS),
                 'запитів_мед': st.median(d['запитів'] for d in FS), 'сума_викликів_мед': st.median(d['сума_викликів'] for d in FS),
                 'найдовший_мед': st.median(d['найдовший'] for d in FS), 'дата': sorted({d['дата'] for d in FS}), 'режими': sorted({d['режим'] for d in FS})}
# найбільші складники: вид запиту (за всіма повними), частка від сумарної тривалості повних сцен
F = [d for d in F if not d['викид']]
kind = collections.defaultdict(float); kn = collections.Counter()
import re
for d in F:
    for x in d['виклики']:
        key = re.sub(r'\s+', ' ', x['вид'])
        if x['вид'].startswith('мовний шар') or x['вид'] == 'мовний шар': key = 'мовний шар (' + short(x['модель']) + ')'
        else: key = key + ' (' + short(x['модель']) + ')'
        kind[key] += x['с']; kn[key] += 1
T = sum(d['секунд'] for d in F)
out['види_запитів'] = sorted(({'вид': k, 'сума_с': v, 'частка': v / T, 'запитів': kn[k], 'сер_с': v / kn[k]} for k, v in kind.items()), key=lambda a: -a['сума_с'])[:15]
out['сума_с_повних'] = T
out['не_модель_частка_усіх'] = sum(d['не_модель'] for d in F) / T

# динаміка за датами для повного/+фото
by = collections.defaultdict(list)
for d in F:
    if d['режим'] in ('повне', 'повне +фото'): by[d['дата']].append(d)
out['за_датами'] = {dt: {'сцен': len(l), 'мед_с': st.median(x['секунд'] for x in l), 'запитів_мед': st.median(x['запитів'] for x in l),
                         'сер_с_на_запит_мед': st.median(x['сума_викликів'] / max(x['запитів'], 1) for x in l),
                         'відп_симв_мед': st.median(x['відп_симв'] for x in l),
                         'частка_MamayLM_запитів': sum(x['по_моделях'].get('MamayLM', {'n': 0})['n'] for x in l) / sum(x['запитів'] for x in l),
                         'не_модель_мед': st.median(x['не_модель'] for x in l)} for dt, l in sorted(by.items())}
def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b)); den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else None
G = [d for d in F if d['режим'] in ('повне', 'повне +фото')]
out['кореляції_повних'] = {'тривалість~запитів': corr([d['секунд'] for d in G], [d['запитів'] for d in G]),
                           'тривалість~сума_викликів': corr([d['секунд'] for d in G], [d['сума_викликів'] for d in G]),
                           'тривалість~сер_с_на_запит': corr([d['секунд'] for d in G], [d['сума_викликів'] / max(d['запитів'], 1) for d in G]),
                           'тривалість~відп_симв': corr([d['секунд'] for d in G], [d['відп_симв'] for d in G]),
                           'тривалість~не_модель': corr([d['секунд'] for d in G], [d['не_модель'] for d in G]),
                           'тривалість~дата': corr([d['секунд'] for d in G], [int(d['дата'][-2:]) + (31 if d['дата'][5:7] == '11' else 0) for d in G]),
                           'n': len(G)}
ba = collections.defaultdict(list)
for d in G0 if False else [x for x in F if x['режим'] in ('повне', 'повне +фото')]:
    ba[(d['дата'], d['акаунт'])].append(d)
out['за_датою_і_акаунтом'] = {f'{k[0]} {k[1]}': {'сцен': len(l), 'мед_с': st.median(x['секунд'] for x in l), 'сер_с_на_запит_мед': st.median(x['сума_викликів'] / max(x['запитів'], 1) for x in l)} for k, l in sorted(ba.items(), key=lambda a: (a[0][0], str(a[0][1])))}
kd = collections.defaultdict(list)
for d in S:
    if d['обірвався'] or d['середовище'] != 'локальні': continue
    for x in d['виклики']:
        if x['с'] > 1000 or not x['модель']: continue
        kk = 'ПАКЕТ→ОБРАЗИ (qwen)' if x['вид'] == 'ПАКЕТ_V1→ОБРАЗИ_V1' and x['модель'].startswith('qwen') else ('мовний шар (MamayLM)' if x['вид'].startswith('мовний шар') and x['модель'].startswith('mamay') else None)
        if kk: kd[(d['дата'], kk)].append(x['с'])
out['мед_запиту_за_датою'] = {f'{k[0]} {k[1]}': {'запитів': len(v), 'мед_с': st.median(v)} for k, v in sorted(kd.items()) if len(v) >= 8}
# та сама сцена у різні дати (повне/+фото)
sc = collections.defaultdict(list)
for d in G: sc[d['сцена']].append(d)
pairs = []
for k, l in sc.items():
    ds = sorted(l, key=lambda x: x['дата'])
    if ds[0]['дата'] != ds[-1]['дата'] and ds[0]['режим'] == ds[-1]['режим']:
        pairs.append({'сцена': k, 'режим': ds[0]['режим'], 'перша': ds[0]['дата'], 'остання': ds[-1]['дата'], 'с1': ds[0]['секунд'], 'с2': ds[-1]['секунд'],
                      'запитів1': ds[0]['запитів'], 'запитів2': ds[-1]['запитів'], 'сер1': ds[0]['сума_викликів'] / ds[0]['запитів'], 'сер2': ds[-1]['сума_викликів'] / ds[-1]['запитів']})
out['пари_сцен'] = pairs
out['пари_зміна_мед'] = {'с': st.median(p['с2'] / p['с1'] for p in pairs) if pairs else None, 'n': len(pairs),
                         'запитів': st.median(p['запитів2'] / p['запитів1'] for p in pairs) if pairs else None,
                         'сер_с_на_запит': st.median(p['сер2'] / p['сер1'] for p in pairs) if pairs else None}
out['виключені'] = collections.Counter(('обірвався' if d['обірвався'] else 'нема_тривалості_викликів' if not d['є_тривалість_викликів'] else 'нема_кроків' if d['п'] is None or (d['з'] is None and d['режим'] not in ('розмова', 'палітра')) else 'нема_секунд') for d in S if not d['повний'] or d['середовище'] == 'sonnet' and False)
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
pass
print(json.dumps(out, ensure_ascii=False, indent=1))

import csv
with open(sys.argv[2].replace('.json', '_сцени.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['тека', 'дата', 'акаунт', 'режим', 'середовище', 'повний_розклад', 'секунд', 'запитів', 'MamayLM_запитів', 'MamayLM_с', 'qwen_запитів', 'qwen_с',
                'sonnet_запитів', 'sonnet_с', 'найдовший_запит_с', 'не_модель_с', 'крок1_с', 'крок2_с', 'крок3_с', 'викид'])
    for d in S:
        b = d['по_моделях']; g = lambda m, k: round(b.get(m, {'n': 0, 'с': 0})[k], 1)
        k = d.get('крок_с', {})
        w.writerow([d['тека'], d['дата'], d.get('акаунт'), d['режим'], d['середовище'], int(d['повний']), d['секунд'], d['запитів'], g('MamayLM', 'n'), g('MamayLM', 'с'),
                    g('qwen3.5-9b', 'n'), g('qwen3.5-9b', 'с'), g('sonnet', 'n'), g('sonnet', 'с'), round(d['найдовший'], 1), round(d.get('не_модель', 0), 1) if d['повний'] else '',
                    round(k.get('1', 0), 1) if k else '', round(k.get('2', 0), 1) if k else '', round(k.get('3', 0), 1) if k else '', int(d['викид'])])
