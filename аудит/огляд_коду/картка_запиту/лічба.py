import json, sys, re, os
S = os.path.dirname(os.path.abspath(__file__))
ГОДИНА = {"вечір у театрі, вистава о 19:00": 19, "кава з подругою в кафе о 20:00": 20,
          "Вечеря з подругою в ресторані о сьомій вечора": 19,
          "я гостя на весіллі сестри в серпні, церемонія надворі о 16:00, потім ресторан": 16}
ПРОСТО_НЕБА = ("просто неба", "надворі")
def стан(x):
    с = x['сторож']
    вн = с[0] if isinstance(с, list) and с and isinstance(с[0], dict) else x['внутрішня']
    return вн
for ВЕР in sys.argv[1:]:
    d = json.load(open(os.path.join(S, 'replay_%s.json' % ВЕР), encoding='utf8'))
    т = dict(ходів=len(d), година_вигадана=[], година_втрачена=[], рух_всупереч=[], просто_неба_втрачено=[],
             нагода_втрачена=[], без_цитати=0, полів=0)
    for x in d:
        вн, her = стан(x), x['її']
        q = вн.get('quotes') or {}
        h = вн.get('hour')
        очік = ГОДИНА.get(her)
        if очік is None and h is not None:
            т['година_вигадана'].append((x['сцена'], h, q.get('hour')))
        if очік is not None and h != очік:
            т['година_втрачена'].append((x['сцена'], h))
        if 'стоя' in her and вн.get('movement') not in (None, 'stand'):
            т['рух_всупереч'].append((x['сцена'], вн.get('movement'), q.get('movement')))
        if any(w in her for w in ПРОСТО_НЕБА) and вн.get('setting') != 'outdoor':
            т['просто_неба_втрачено'].append((x['сцена'], вн.get('setting')))
        if not вн.get('occasion') and not вн.get('occasions'):
            т['нагода_втрачена'].append((x['сцена'], her[:30]))
        for к, v in вн.items():
            if к in ('quotes',) or к.startswith('_'):
                continue
            т['полів'] += 1
            if к not in q:
                т['без_цитати'] += 1
    print('==', ВЕР, 'ходів', т['ходів'], '· полів прийнято', т['полів'], '· з них без цитати', т['без_цитати'])
    for к in ('година_вигадана', 'година_втрачена', 'рух_всупереч', 'просто_неба_втрачено', 'нагода_втрачена'):
        print(' ', к, len(т[к]))
        for y in т[к][:14]:
            print('     ', y)
