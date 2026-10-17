"""5571: справжні producer запити→від_моделі на наявному каталозі; контрфактичні ід, НЕ модельний LIVE. Аргумент: джерела ДО."""
import pathlib, sys, os, json, hashlib, subprocess
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent)); os.chdir(sys.path[0])
import bridge as Б, правило_руки2 as П, формальність as Ф, fit as ПС, композитор_річ as КР, силует_крої as СК, силует_пропорції as СП, verify as В, реєстри as Р
вх0 = dict(json.load(open('стенд_вх.json')), каталог='каталог_повний.xml', сід=3, сценарій=dict(нагода='побачення', місце='ресторан', година=20, темп_c=5, ошатність=[4, 5]))
# вхід правила: довгий день по бруківці (K-SHO-16), стегна ширші за плечі (K-BOD-02 — зони з роллю), карі очі (R-COL-16 — бік b), її метал «золото» (K-COL-06-M); решта — вхід #1074
ІНШЕ = {'K-SHO-16': dict(сценарій=dict(вх0['сценарій'], тривалість_год=9, поверхня='бруківка')), 'K-BOD-02': dict(обхвати=dict(плечі=92, груди=90, талія=72, стегна=108, високе_стегно=96)), 'R-COL-16': dict(очі='#6b4a2e'), 'K-COL-06-M': dict(драп_сирий=dict(метал='золото'))}
відбиток = lambda п: hashlib.sha256(json.dumps(п, sort_keys=True, ensure_ascii=False).encode()).hexdigest(); стар = П.жереб; нове = hasattr(П, 'хибний_щабель'); C = lambda r: (r['lab'][1] ** 2 + r['lab'][2] ** 2) ** 0.5 if r.get('lab') and r.get('джерело_кольору') == 'фото' else 0; пакети = []; дерево = lambda: (lambda г, з: '%s%s' % (г[:8], '+%d' % len(з.split('\n')) if з else ''))(*(subprocess.run(['git', '-C', sys.path[0], *a], capture_output=True, text=True).stdout.strip() for a in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=no', '--', '.'])))
знайти = lambda в: (([в] if в.get('ремонт_заяви') and в.get('сила_нп', 0) > 0 else []) + sum((знайти(x) for x in в.values()), []) if isinstance(в, dict)
                   else sum((знайти(x) for x in в), []) if isinstance(в, list) else [])
for код in ('K-CRA-01', 'K-KOH-02', 'K-OUT-33', 'K-SHO-16', 'K-FIT-03', 'K-BOD-02', 'R-COL-16', 'K-COL-06-M', 'K-MAT-03', 'K-SIL-03', 'K-REG-01', 'K-ACC-01', 'K-PAL-18'):
    вх, запис, хибне = dict(вх0, **ІНШЕ.get(код, {})), П.ЗА_ІД[код], нове and код in П.ХИБНІ_ПРАВИЛА
    П.жереб = lambda *а, **к: (П.злити([запис]), [код], {}, dict(дія='pool', чому=None))
    з = json.loads(Б.виклик('запити', json.dumps(вх, ensure_ascii=False))); assert not з.get('помилка'), з
    п1, п2 = з['пакети']['1'], з['пакети']['2']; кат = Б.каталог_останнього_пакета(); каталожні_ід = {str(r['id']) for r in кат}
    осн = [next(r for r in кат if r.get('слот') == с) for с in ('верх', 'низ', 'взуття', 'сумка')]; тр = next(r for r in кат if r.get('слот') == 'верхній_шар' and r.get('id'))
    t = ПС.тіло(вх['зріст'], вх['обхвати']); г = lambda r: КР._у_річ(r, r['слот'], t) or {}; рз = lambda р: float(р.get('край_розкид_см') or 0); м = lambda р, d=0.0: ПС.край_проти_локального(t['профіль'], ПС._край(р) + d); поза = lambda р: м(р)['локальний_максимум'] and not any(м(р, d)['на_максимумі'] for d in (-рз(р), 0.0, рз(р)))
    if код == 'K-KOH-02': осн[0] = next(r for r in кат if r.get('слот') == 'верх' and (с:=Ф.інтервал_формальності(r))[0] is not None and 4 < с[0] <= 5)
    if код == 'K-SHO-16': осн[2] = next(r for r in кат if r.get('слот') == 'взуття' and r.get('каблук') is False)   # пласка пара: адресат «вищого каблука»
    if код == 'K-FIT-03': осн[0] = next(r for r in кат if r.get('слот') == 'верх' and г(r).get('край_джерело') in ('слово', 'виріб') and поза(г(r)))   # край і смуга розміру поза опуклістю, опуклість у вікні зсуву
    if код == 'K-BOD-02':   # верх і низ з кроєм; низу справне правило зон не закидає нічого — він робить зі стегнами те, що їм личить
        осн[0] = next(r for r in кат if r.get('слот') == 'верх' and г(r).get('крій') and 'низ_см' in г(r))
        осн[1] = next(r for r in кат if r.get('слот') == 'низ' and г(r).get('крій') and 'низ_см' in г(r) and not [x for x in СП.зонні_операції(t, СК.обгортка(t, [г(осн[0]), г(r)])) if x.get('сила') != 'питання' and r['id'] in x.get('речі', ())])
    if код == 'R-COL-16': осн[0] = next(r for r in кат if r.get('слот') == 'верх' and C(r) > 35 and r['lab'][2] > 10)   # кольоровий верх на теплому боці очей: адресат «протилежного боку»
    if код == 'K-MAT-03': тр = next(r for r in кат if r.get('слот') == 'верхній_шар' and r.get('сезон_тканини') and not В.поза_смугою_тканини(r['сезон_тканини'], 5))   # тканина по сезону: адресат «протилежного сезону»
    if код == 'K-REG-01': осн[0] = next(r for r in кат if r.get('слот') == 'верх' and Р.реєстр_образу([r] + осн[1:] + [тр])['домінанта'])   # один реєстр веде: адресат «жоден не веде»
    if код == 'K-PAL-18': осн[3] = next(r for r in кат if r.get('слот') == 'сумка' and C(r) > 72)   # акцентний слот уже з хромою: адресат «нейтрального акценту»
    ід = [r['id'] for r in осн + [тр]] + ([next(r for r in кат if r.get('слот') == 'прикраси' and r.get('метал') == 'золото')['id']] if код == 'K-COL-06-M' else [])
    в = json.loads(Б.виклик('від_моделі', json.dumps(dict(вх, донор=True, ід=ід), ensure_ascii=False))); assert not в.get('помилка'), в
    if нове: assert set(map(str, в['повнота']['ід'])) == set(map(str, ід)) and len(ід) == len(set(ід)) >= 5
    активні = {(х['правило'], tuple(sorted(str(і) for і in х.get('речі') or [] if str(і) in каталожні_ід)), json.dumps(х['ремонт_заяви'], sort_keys=True)): х for х in знайти(в) if х.get('правило') in запис['коди']}
    тінь = (в.get('палітра') or {}).get('тінь_знахідки') or []; дії = [т for т in тінь if т.get('дія')]; assert not нове or json.loads(Б.виклик('від_моделі', json.dumps(dict(вх, донор=True, ід=ід), ensure_ascii=False)))['палітра']['тінь_знахідки'] == тінь
    рек, пул_рек = п2.get('обмеження') or {}, [т['дія'] for т in (з['поломка'].get('рекомендації') or [])]
    if хибне:
        assert активні and дії and all('правильна' in т and 'хибна' in т for т in дії)
        assert all(т.get('сила') and т.get('суть') and т.get('речі') and т.get('сила_нп', 0) > 0 for т in дії if т.get('дія') != 'drop_correct_advice')
        assert код != 'K-KOH-02' or any(т.get('хибна') == [3.0, 3.0] for т in дії); assert код != 'K-BOD-02' or 'invert_cut_rank' in пул_рек; assert код != 'K-OUT-33' or (not п2['пул'].get('верхній_шар') and рек.get('без_пальта'))
    пакети.append(відбиток(п1)); print(json.dumps(dict(правило=код, нове=нове, хибне=хибне, нормальний_пакет=відбиток(п1), активних_ремонтів=len(активні), пул_різниця=з['поломка'].get('пул_різниця'), верхній_шар_1=len(п1['пул'].get('верхній_шар') or []), верхній_шар_2=len(п2['пул'].get('верхній_шар') or []), пул_рекомендації=sorted(set(пул_рек)), дії=дії, обмеження=рек), ensure_ascii=False), flush=True)
    assert not П.вимкнені() and not getattr(П, 'зламані', lambda: ())()
П.жереб = стар; print('дерево %s · каталог %s · пакет %s' % (дерево(), hashlib.md5(open('каталог_повний.xml.gz', 'rb').read()).hexdigest()[:8], відбиток(пакети)[:8]))
