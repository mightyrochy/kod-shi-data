"""5571: справжні producer запити→від_моделі на наявному каталозі; контрфактичні ід, НЕ модельний LIVE. Аргумент: джерела ДО."""
import pathlib, sys, os, json, hashlib
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent)); os.chdir(sys.path[0])
import bridge as Б, правило_руки2 as П, формальність as Ф
вх = dict(json.load(open('стенд_вх.json')), каталог='каталог_повний.xml', сід=3,
          сценарій=dict(нагода='побачення', місце='ресторан', година=20, темп_c=5, ошатність=[4, 5]))
стар = П.жереб; нове = hasattr(П, 'хибний_щабель')
def знайти(в):
    if isinstance(в, dict):
        return ([в] if в.get('ремонт_заяви') and в.get('сила_нп', 0) > 0 else []) + sum((знайти(x) for x in в.values()), [])
    return sum((знайти(x) for x in в), []) if isinstance(в, list) else []
for код in ('K-CRA-01', 'K-KOH-02', 'K-OUT-33'):
    запис = П.ЗА_ІД[код]
    П.жереб = lambda *а, **к: (П.злити([запис]), [код], {}, dict(дія='pool', чому=None))
    з = json.loads(Б.виклик('запити', json.dumps(вх, ensure_ascii=False))); assert not з.get('помилка'), з
    п1, п2 = з['пакети']['1'], з['пакети']['2']; кат = Б.каталог_останнього_пакета(); каталожні_ід = {str(r['id']) for r in кат}
    осн = [next(r for r in кат if r.get('слот') == с) for с in ('верх', 'низ', 'взуття', 'сумка')]
    тр = next(r for r in кат if r.get('слот') == 'верхній_шар' and r.get('id'))
    if код == 'K-KOH-02': тр = next(r for r in кат if (с:=Ф.інтервал_формальності(r))[0] is not None and 4 < с[0] <= 5)
    ід = [r['id'] for r in осн + [тр]]
    в = json.loads(Б.виклик('від_моделі', json.dumps(dict(вх, донор=True, ід=ід), ensure_ascii=False)))
    assert not в.get('помилка'), в
    активні = {(х['правило'], tuple(sorted(str(і) for і in х.get('речі') or [] if str(і) in каталожні_ід)), json.dumps(х['ремонт_заяви'], sort_keys=True)): х for х in знайти(в) if х.get('правило') in запис['коди']}
    тінь = (в.get('палітра') or {}).get('тінь_знахідки') or []; дії = [т for т in тінь if т.get('дія')]
    рек = п2.get('обмеження') or {}
    if нове:
        assert активні and дії and all('правильна' in т and 'хибна' in т for т in дії)
        assert all(т.get('сила') and т.get('суть') and т.get('речі') and т.get('сила_нп', 0) > 0 for т in дії if т.get('дія') in ('remove_items', 'target_band'))
        if код == 'K-KOH-02': assert any(т.get('хибна') == [3.0, 3.0] for т in дії)
        if код == 'K-OUT-33': assert not п2['пул'].get('верхній_шар') and рек.get('без_пальта')
    відбиток = lambda п: hashlib.sha256(json.dumps(п, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    print(json.dumps(dict(правило=код, нове=нове, нормальний_пакет=відбиток(п1),
          верхній_шар_1=len(п1['пул'].get('верхній_шар') or []), верхній_шар_2=len(п2['пул'].get('верхній_шар') or []),
          активних_ремонтів=len(активні), пул_різниця=з['поломка'].get('пул_різниця'), дії=дії, обмеження=рек), ensure_ascii=False), flush=True)
    assert not П.вимкнені() and not getattr(П, 'зламані', lambda: ())()
П.жереб = стар
