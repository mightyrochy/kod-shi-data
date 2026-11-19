#!/usr/bin/env python3
"""Розклад часу сцени за записами в main (наряд Автоживий-час-сцени-розклад).
Запуск: python3 -I розклад.py <аудит/проби> <сцени.json>
Джерела сцени: результат.json (секунд, змінні), лог.txt (позначки кроків «N. … за T с», рядки викликів
«↔ модель #N … → T с» або «· вид — HTTP … T с» у блоці ЖИВА МОДЕЛЬ), VIDPOVIDI/обмін/NNNNN.json (модель виклику).
Модель виклику #N — поле model у запиті файлу NNNNN.json; час виклику — з логу; крок виклику — за номером рядка."""
import json, os, re, sys, glob
from datetime import datetime as D

ROOT, OUT = sys.argv[1], sys.argv[2]
ROOTS = (sorted(glob.glob(ROOT + '/автоживий-*')) + sorted(glob.glob(ROOT + '/Е1-нічний-живий-*')) + [ROOT + '/нічні'])

def mode(z):
    do = z.get('DO')
    if do in ('rozmova', 'palitra', 'koment'): return {'rozmova': 'розмова', 'palitra': 'палітра', 'koment': 'коментар'}[do]
    return 'повне +фото' if z.get('FOTO') == '1' else 'повне'

def модель_файлу(p):
    try:
        d = json.load(open(p, encoding='utf-8'))
        q = d['запит']; q = json.loads(q) if isinstance(q, str) else q
        return q.get('model') or d['відповідь'].get('headers', {}).get('x-model')
    except Exception:
        return None

A = re.compile(r'^\s+↔ модель #(\d+) (.*?) \((\d+) симв\..*?\) → ([\d.]+) с · HTTP (\d+) · (\d+) симв\.', re.M)
B = re.compile(r'^   · (.*?) — HTTP (\d+) · ([\d.]+) с · вхід (\d+) т\. · вихід за лічильником CLI \(з міркуванням\) (\d+) т\.', re.M)
STEP = re.compile(r'^(\d+)\. ', re.M)

scenes = []
for rt in ROOTS:
    for dp, dn, fn in os.walk(rt):
        if 'результат.json' not in fn: continue
        try: r = json.load(open(dp + '/результат.json', encoding='utf-8'))
        except Exception: continue
        z = r.get('змінні', {})
        lp = dp + '/лог.txt'
        t = open(lp, encoding='utf-8', errors='replace').read() if os.path.exists(lp) else ''
        d = {'тека': os.path.relpath(dp, ROOT), 'сцена': r.get('сцена') or z.get('SCENA') or os.path.basename(dp),
             'дата': (r.get('початок') or '')[:10], 'режим': mode(z), 'з_оцінкою': 'OTSINKA' not in z,
             'rc': r.get('rc'), 'секунд': r.get('секунд'), 'змінна_модель': z.get('MODEL'), 'змінна_мова': z.get('MODEL_MOVA')}
        if d['секунд'] is None and r.get('початок') and r.get('кінець'):
            d['секунд'] = (D.fromisoformat(r['кінець']) - D.fromisoformat(r['початок'])).total_seconds()
        m = re.search(r'чат → паспорт за ([\d.]+) с', t); d['п'] = float(m[1]) if m else None
        m = re.search(r'збирання \(сід \d+\) за ([\d.]+) с', t); d['з'] = float(m[1]) if m else None
        cm = re.search(r'Users.([^\\\\/]+)', ' '.join(r.get('команда', [])))
        d['акаунт'] = cm[1] if cm else None
        d['обірвався'] = 'прогін обірвався' in t
        steps = [(t.count('\n', 0, m.start()), int(m[1])) for m in STEP.finditer(t)]
        def крок(pos):  # крок, у якому надруковано виклик: останній надрукований крок = попередній, виклик належить наступному
            n = t.count('\n', 0, pos)
            k = 1
            for ln, num in steps:
                if ln < n: k = num + 1
            return k
        calls = []
        for m in A.finditer(t):
            calls.append({'n': int(m[1]), 'вид': m[2], 'с': float(m[4]), 'відп_симв': int(m[6]), 'крок': крок(m.start())})
        if not calls:
            blk = t[t.find('ЖИВА МОДЕЛЬ'):] if 'ЖИВА МОДЕЛЬ' in t else ''
            for i, m in enumerate(B.finditer(blk), 1):
                calls.append({'n': i, 'вид': m[1], 'с': float(m[3]), 'вхід_т': int(m[4]), 'вихід_т': int(m[5]), 'крок': None})
        obm = sorted(glob.glob(dp + '/VIDPOVIDI/обмін/*.json'))
        d['файлів_обміну'] = len(obm)
        mod = {int(os.path.basename(p)[:5]): модель_файлу(p) for p in obm}
        for c in calls: c['модель'] = mod.get(c['n'])
        d['моделі_обміну'] = {}
        for v in mod.values(): d['моделі_обміну'][v] = d['моделі_обміну'].get(v, 0) + 1
        d['виклики'] = calls
        d['є_тривалість_викликів'] = bool(calls) and len(calls) == len(obm)
        scenes.append(d)
json.dump(scenes, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(scenes), 'сцен із результат.json;', sum(s['є_тривалість_викликів'] for s in scenes), 'із тривалістю кожного виклику')
