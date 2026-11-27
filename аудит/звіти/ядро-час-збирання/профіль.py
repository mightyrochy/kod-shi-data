# Де йдуть ~120 с «коду» до першого виклику складання (пункт 1 наряду, «час поза викликами»): профіль CPython на тих самих
# входах моста. У Pyodide той самий код, лише повільніший, тому частки читаємо як порядок, а не секунди стенда.
# Запуск: python3 профіль.py <index.html стенда> <виклики_моста.jsonl> [<до_якого_виклику, типово до першого «почати» включно>]
import cProfile, pstats, json, sys, os, time, io, zipfile, tempfile, asyncio, importlib.util

сторінка, входи = sys.argv[1], sys.argv[2]
пряд = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'джерела', 'прилади', 'знімок_мосту.py')
спец = importlib.util.spec_from_file_location('знімок_мосту', пряд)
зм = importlib.util.module_from_spec(спец)
спец.loader.exec_module(зм)
sys.modules.pop('profile', None)   # модуль продукту `profile` не має затінюватись stdlib-овим, який тягне cProfile
тека = tempfile.mkdtemp(prefix='профіль_')
zipfile.ZipFile(io.BytesIO(зм.модулі_зі_сторінки(сторінка))).extractall(тека)
sys.path.insert(0, os.path.dirname(os.path.abspath(пряд)))
зм.підготувати(тека, None)
import bridge
рядки = [json.loads(р) for р in open(входи, encoding='utf8') if р.strip()]
меж = next(i for i, в in enumerate(рядки) if в['ім'] == 'ядро' and json.loads(в['вхід']).get('дія') == 'почати')
проф = cProfile.Profile()
for н, в in enumerate(рядки[:меж + 1]):
    вхід = json.loads(в['вхід'])
    t = time.perf_counter()
    if н == меж:
        os.environ.get('БЕЗ_ПРОФІЛЮ') or проф.enable()
    р = asyncio.run(bridge.виклик_а(в['ім'], вхід)) if в.get('async') else bridge.виклик(в['ім'], вхід)
    if н == меж:
        os.environ.get('БЕЗ_ПРОФІЛЮ') or проф.disable()
    print(н, в['ім'], round(time.perf_counter() - t, 2), 'с', file=sys.stderr)
s = io.StringIO()
pstats.Stats(проф, stream=s).sort_stats('cumulative').print_stats(45)
print(s.getvalue())
