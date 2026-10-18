"""Скільки викликів функції мають той самий вхід (repr аргументів) і той самий вихід — на відтворенні.
python3.12 -B повтори.py <тека показу> <виклики.json> модуль:функція ...  (патчить усі модулі, де лежить той самий об'єкт)"""
import sys, os, json, asyncio, hashlib, collections, time, importlib
тека, виклики = sys.argv[1:3]
os.chdir(тека); sys.path.insert(0, тека)
import bridge
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import відтворення
лік = {}
def обгорнути(мод_ім, ім):
    мод = importlib.import_module(мод_ім); о = getattr(мод, ім)
    к = collections.Counter(); т = [0.0, 0.0, 0, 0]; перший = {}; глиб = [0]
    def w(*a, **kw):
        if глиб[0]: return о(*a, **kw)
        глиб[0] += 1
        try:
            ключ = hashlib.md5(repr((a, sorted(kw.items()))).encode()).hexdigest()
            повтор = ключ in к; к[ключ] += 1
            t0 = time.perf_counter(); r = о(*a, **kw); dt = time.perf_counter() - t0
            т[0] += dt
            хр = hashlib.md5(repr(r).encode()).hexdigest()
            if повтор: т[1] += dt; т[2] += 1; т[3] += (перший[ключ] == хр)
            else: перший[ключ] = хр
            return r
        finally: глиб[0] -= 1
    for м in list(sys.modules.values()):
        try:
            if getattr(м, ім, None) is о: setattr(м, ім, w)
        except Exception: pass
    лік[мод_ім + '.' + ім] = (к, т)
for а in sys.argv[3:]: обгорнути(*а.split(':'))
asyncio.run(відтворення.прогнати(виклики))
for ім, (к, т) in лік.items():
    print(ім, 'викликів', sum(к.values()), 'різних входів', len(к), '· час %.1f с, з них на повторних входах %.1f с · повторів %d, вихід = першому в %d' % tuple(т))
