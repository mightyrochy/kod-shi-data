"""6791: рука 1 з жеребом K-REG-01 на образі з двома рівними реєстрами (домінанти нема) — `тінь_знахідки` руки 1 і число K-REG-01 у відрі `реєстри` (ДО правки: без K-REG-01).
Запуск: cd джерела && python3 проби/рука2_регістр_тінь.py [теку_джерел_ДО]"""
import pathlib, sys, os, json, itertools
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parent.parent)); os.chdir(sys.path[0])
import bridge as Б, поломки as П, реєстри as Р
вх = dict(json.load(open('стенд_вх.json')), каталог='каталог_повний.xml', сід=3, сценарій=dict(нагода='побачення', місце='ресторан', година=20, темп_c=5, ошатність=[4, 5]))
П.жереб = lambda *а, **к: (П.злити([П.ЗА_ІД['K-REG-01']]), ['K-REG-01'], {}, dict(дія='pool', чому=None))
assert not json.loads(Б.виклик('запити', json.dumps(вх, ensure_ascii=False))).get('помилка')
кат = Б.каталог_останнього_пакета(); слот = lambda с: [r for r in кат if r.get('слот') == с and r.get('id')][:60]
рівні = lambda речі: (lambda о: not о['домінанта'] and len([1 for _, б in о['ранг'] if б > 0]) >= 2)(Р.реєстр_образу(речі))
образ = next(c for c in itertools.product(слот('верх'), слот('низ'), слот('взуття')[:3], слот('верхній_шар')[:3]) if рівні(c))
в = json.loads(Б.виклик('від_моделі', json.dumps(dict(вх, ід=[r['id'] for r in образ]), ensure_ascii=False))); assert not в.get('помилка'), в
рег = [z for z in ((в.get('реєстри') or {}).get('знахідки') or []) if z.get('правило') == 'K-REG-01']; тінь = (в.get('палітра') or {}).get('тінь_знахідки') or []
print(json.dumps(dict(образ=[r['id'] for r in образ], слова=(в.get('реєстри') or {}).get('словами'), правило_діяло=в.get('правило_діяло'), K_REG_01_у_відрі=len(рег),
                      тінь_знахідки_правила=sorted({т['правило'] for т in тінь}), K_REG_01_у_тіні=sum(1 for т in тінь if т['правило'] == 'K-REG-01')), ensure_ascii=False))
