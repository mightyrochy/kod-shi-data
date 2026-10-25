import os, re, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt_keys import load
L = sys.argv[1]
def обʼєкт(r):
    i = r.find('{'); j = r.rfind('}')
    if i < 0 or j < 0: return None
    try: return json.loads(r[i:j+1])
    except Exception: return None
def сцена(f):
    s = f[len(L)+1:]
    s = re.sub(r'^zhyvi-[^/]+/аудит/', '', s)
    return s.split('/VIDPOVIDI/')[0]
РЕЧ = re.compile(r'[^.!?…]+[.!?…]*')
ЧИСЛО = re.compile(r"\d|перш|друг|трет|четверт|п'ят|шост|сьом|восьм|дев'ят|десят|одинадц|дванадц|полудн|опівно", re.I)
рядки = {'хід': [], 'рем': [], 'пл': []}
for f in sorted(glob.glob(L + '/**/VIDPOVIDI/*.txt', recursive=True)):
    ob, r = load(f)
    відп = обʼєкт(r)
    с = сцена(f)
    if 'хід_розмови' in f:
        her = (ob or {}).get('her_new_message') or ''
        u = (відп or {}).get('update') or {}
        for k in ('hour', 'part_of_day', 'movement', 'occasion', 'place', 'setting', 'month', 'event_part', 'occasion_part'):
            p = u.get(k)
            if p is None: continue
            q = p.get('quote') if isinstance(p, dict) else None
            v = p.get('value') if isinstance(p, dict) else p
            n = p.get('named') if isinstance(p, dict) else None
            рядки['хід'].append((с, her, k, q, json.dumps(v, ensure_ascii=False)[:80], n))
    elif 'ремонт_поради' in f:
        inv = (відп or {}).get('invite') or ''
        her = ''
        if ob:
            her = (ob.get('her_new_message') or (ob.get('task') or {}).get('her_new_message') or '')
        речень = len([x for x in РЕЧ.findall(inv) if x.strip()])
        рядки['рем'].append((с, речень, inv[:220], json.dumps((відп or {}).get('invite_topics'), ensure_ascii=False)))
    elif 'хід_плиток' in f:
        ch = (ob or {}).get('chosen')
        рядки['пл'].append((с, json.dumps(ch, ensure_ascii=False)[:200]))
for k, v in рядки.items():
    print('=====', k, len(v))
    for x in v:
        print(' | '.join(str(y) for y in x))
