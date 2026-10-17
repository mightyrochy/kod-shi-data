"""6635, 6792: рядки брифа зламаного правила в руки 2 — є й хибні, не зняті; пакет руки 1 незмінний. Аргумент: джерела ДО."""
import pathlib, sys, os, json, hashlib, re
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent)); os.chdir(sys.path[0])
import bridge as Б, правило_руки2 as П, fit as ПС, hypergraph as Г
вх0 = dict(json.load(open('стенд_вх.json')), каталог='каталог_повний.xml', сід=3, сценарій=dict(нагода='побачення', місце='ресторан', година=20, темп_c=5, ошатність=[4, 5]))
ІНШЕ = {'K-BOD-02': dict(обхвати=dict(плечі=92, груди=90, талія=72, стегна=108, високе_стегно=96)),   # вхід — як `рука2_хибні_каталог`
        'R-COL-16': dict(очі='#6b4a2e'), 'K-COL-06-M': dict(драп_сирий=dict(метал='золото'))}
стар, нове = П.жереб, hasattr(П, 'бриф_руки2')
відбиток = lambda п: hashlib.sha256(json.dumps(п, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
def заяви(промпт, код):   # значення заяв `код` у style_rules промпта складання
    return [json.JSONDecoder().raw_decode(промпт, m.end() - 1)[0] for m in re.finditer('"%s":{' % код, промпт)]
for код in ('K-BOD-02', 'K-FIT-03', 'K-CRA-01', 'K-KOH-02', 'K-OUT-33', 'R-COL-16', 'K-COL-06-M', 'K-REG-01', 'K-SIL-03', 'K-ACC-01'):
    вх, запис = dict(вх0, **ІНШЕ.get(код, {})), П.ЗА_ІД[код]
    П.жереб = lambda *а, **к: (П.злити([запис]), [код], {}, dict(дія='pool', чому=None))
    з = json.loads(Б.виклик('запити', json.dumps(вх, ensure_ascii=False))); assert not з.get('помилка'), з
    ключі = set(П.ключі_брифа_для(запис['коди']))
    B, C = ({p['код']: p['рядок'] for p in з['правила_рук'][р] if p['код'] in ключі} for р in 'BC')
    рядки = dict(правило=код, нове=нове, нормальний_пакет=відбиток(з['пакети']['1'])[:12], ключі_руки_1=sorted(B), ключі_руки_2=sorted(C),
                 хибні=sorted(к for к in C if к in B and C[к] != B[к]))
    if код == 'K-BOD-02':
        t = ПС.тіло(вх['зріст'], вх['обхвати']); ярус = Г.крої_для_пулу(t)
        крої = {з_['kind']: з_['cuts'] for з_ in заяви(з['руки']['2'], 'cuts_best_on_her')}
        рядки.update(крої_промпту_2=крої, у_ярусі_руки_1={к: sorted(set(в) & ярус[{'top': 'верх', 'bottom': 'низ'}[к]]['ярус']) for к, в in крої.items()},
                     крої_промпту_1={з_['kind']: з_['cuts'] for з_ in заяви(з['руки']['1'], 'cuts_best_on_her')})
        if нове: assert set(C) == set(B) and set(крої) == {'top', 'bottom'} and not any(рядки['у_ярусі_руки_1'].values()), рядки
    if код == 'K-CRA-01':   # рядок `третя_річ` поза промптом в обох руках (`міст_пакет.ПРАВИЛА_ПОЗА_ПРОМПТОМ`); хибу несе рядок задачі
        рядки.update(без_третьої_в_промпті_2='omit every third piece' in з['руки']['2'])
    if нове: assert set(C) == set(B) and рядки['хибні'], рядки
    рядки.update({'%s_2' % к: C[к][:90] for к in рядки['хибні']})
    print(json.dumps(рядки, ensure_ascii=False), flush=True)
    assert not П.вимкнені() and not getattr(П, 'зламані', lambda: ())()
П.жереб = стар
