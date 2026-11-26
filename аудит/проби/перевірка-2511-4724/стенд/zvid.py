import json, sys, os, glob
for d in sorted(glob.glob('/tmp/r3w/out/*/')):
    м = os.path.basename(d.rstrip('/'))
    try: чат = json.load(open(d + 'чат.json')); ж = json.load(open(d + 'журнал_моделі.json')); пс = json.load(open(d + 'підсумок.json'))
    except Exception as e: print(м, 'нема', e); continue
    print('=' * 8, м, '· штамп', пс['штамп'][:8], '· викликів', пс['викликів'], '· моделі', sorted({з['модель_фактична'] for з in ж}))
    for ч in чат:
        if ч['хто'] != 'ші': continue
        for з in ч['мова_шару']:
            if з.get('де') != 'chat' or з.get('напрям') != 'out': continue
            print('  ПОВТОР:', (з.get('повтор') or {}).get('причина'), '| ПРИЧИНА:', з.get('причина'), '| запасний_текст:', з.get('запасний_текст'), '| required:', з.get('required'), '| recorded:', list((з.get('recorded') or {}).keys()))
            for в in з.get('відкинуто') or []: print('    ✗', в.get('чому'), '·', (в.get('зняте') if isinstance(в.get('зняте'), str) else json.dumps(в.get('зняте'), ensure_ascii=False))[:150])
        print('  ЕКРАН:', ч['текст'])
