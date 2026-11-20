#!/usr/bin/env python3
"""Числа прогону однієї ситуації з обміни.jsonl, хід.md й verdykty-*.json: python3 -I числа.py <тека результату> <ситуація> (з будь-якої теки)."""
import json, re, sys, collections, datetime as D
import os, glob
тека, с = sys.argv[1], sys.argv[2]
r = [json.loads(l) for l in open(os.path.join(тека, 'стенд', 'службове', с, 'обміни.jsonl'), encoding='utf-8')]
print('викликів', len(r), dict(collections.Counter(x.get('статус') for x in r)), 'по проходах', dict(collections.Counter(x['прохід'] for x in r)))
print('моделі', dict(collections.Counter(x.get('заголовки', {}).get('x-model') for x in r)), 'x-thinking', dict(collections.Counter(x.get('заголовки', {}).get('x-thinking') for x in r)))
tin = tout = cr = 0
for x in r:
    try: u = json.loads(x['відповідь']).get('usage', {})
    except Exception: continue
    tin += u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0); tout += u.get('output_tokens', 0); cr += u.get('cache_read_input_tokens', 0)
print('токени вхід', tin, 'з кешу', cr, 'вихід', tout, 'найбільший запит симв.', max(len(x['запит']) for x in r), 'найдовший виклик с', round(max(x['с'] for x in r)))
for x in r:
    if x.get('статус') != 200: print('не200', x['прохід'], x.get('статус'), (x.get('відповідь') or x.get('помилка') or '')[:160].replace('\n', ' '))
t = open(os.path.join(тека, с, 'хід.md'), encoding='utf-8').read()
st = [(int(m[1]), D.datetime.fromisoformat(m[2].replace('Z', '+00:00')), m[3], m[4]) for m in re.finditer(r'### (\d+) · (\S+) · прохід (\d) · [^\n]*\n(.*?)(?=\n### |\Z)', t, re.S)]
for p in sorted({x[2] for x in st}):
    S = [x for x in st if x[2] == p]
    ck = [x for x in S if 'Зібрати образи»' in x[3] and 'дія скрипта' in x[3]]
    рядок = f'прохід {p}: {round((S[-1][1]-S[0][1]).total_seconds())} с'
    if ck:
        n = [x for x in S if x[0] > ck[0][0] and 'Твої образи.' in x[3]]
        рядок += f'; клік→перша картка {round((n[0][1]-ck[0][1]).total_seconds())} с' if n else '; КАРТОК НЕ БУЛО'
    else: рядок += '; кліку «Зібрати образи» не було'
    print(рядок)

# Справжні повтори формату: у запиті є КЛЮЧ "format_error": (а не слово в статичній інструкції) або «Correct the previous answer».
пов = collections.Counter()
for x in r:
    q = x['запит']
    m = re.search(r'format_error\\*"\s*:|Correct the previous answer', q)
    if m:
        х = q[m.start():m.start() + 500]
        пов['contract' if 'contract:' in х else 'items_not_described' if 'items_not_described' in х else 'not_json_object' if 'not_json_object' in х else 'інше'] += 1
print('повторів формату', sum(пов.values()), dict(пов))
# Відкинуті частини відповіді за видами — записи сторінки в verdykty-*.json: прогони[].спільне.етапи.діагноз_прогону[]
відк = collections.Counter()
for вф in glob.glob(os.path.join(тека, с, 'verdykty-*.json')):
    for пр in json.load(open(вф, encoding='utf-8'))['прогони']:
        for д in (пр['спільне'].get('етапи', {}).get('діагноз_прогону') or []):
            if 'dropped' in str(д): відк[re.sub(r'\s+', ' ', str(д))[:90]] += 1
print('відкинуто частин', sum(відк.values()), dict(відк))
