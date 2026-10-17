"""Те саме ядро під нативним CPython: імпорт bridge (холодний — без .pyc; теплий — з __pycache__) і відтворення
записаних викликів bridge.
  python3.12 -B cpy_відтворення.py <тека показу> <виклики.json> <вихід.json> <холодний|теплий> [профіль=0|1]
Тека показу — розпакований МОДУЛІ_ПОКАЗУ зі зібраного index.html (ті самі модулі й дані, що в /показ Pyodide)."""
import sys, os, time, json, shutil, builtins, asyncio
тека, виклики, вихід, режим = sys.argv[1:5]
профіль = len(sys.argv) > 5 and sys.argv[5] == '1'
скрипти = os.path.dirname(os.path.abspath(__file__))
if режим == 'холодний':
    shutil.rmtree(os.path.join(тека, '__pycache__'), ignore_errors=True)
    sys.dont_write_bytecode = True
else:
    sys.dont_write_bytecode = False
import importlib._bootstrap_external as _be
_pc = time.perf_counter
ВИМ = {'імп': {}, 'комп': [], 'версія': sys.version, 'модулів_до': len(sys.modules)}
_стек = []
_орг = builtins.__import__
def _імп(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name in sys.modules:
        return _орг(name, globals, locals, fromlist, level)
    ключ = name if level == 0 else ((globals or {}).get('__package__') or '') + ':' + name
    t0 = _pc(); _стек.append(0.0)
    try:
        return _орг(name, globals, locals, fromlist, level)
    finally:
        dt = _pc() - t0; діти = _стек.pop()
        if _стек: _стек[-1] += dt
        if ключ not in ВИМ['імп']:
            ВИМ['імп'][ключ] = [dt * 1000, (dt - діти) * 1000]
_орг_stc = _be.SourceLoader.source_to_code
def _stc(self, data, path, *, _optimize=-1):
    t0 = _pc()
    try:
        return _орг_stc(self, data, path, _optimize=_optimize)
    finally:
        ВИМ['комп'].append([path, (_pc() - t0) * 1000, len(data)])
_be.SourceLoader.source_to_code = _stc
os.chdir(тека); sys.path.insert(0, тека)
builtins.__import__ = _імп
t0 = _pc()
import bridge
ВИМ['імпорт_bridge_мс'] = (_pc() - t0) * 1000
builtins.__import__ = _орг
ВИМ['модулів_після'] = len(sys.modules)
sys.path.insert(0, скрипти)
import відтворення
семпли = None
if os.environ.get('SEMPLER'):
    import threading, collections
    sys.setswitchinterval(0.0005)
    головний = threading.main_thread().ident
    семпли = {'вкл': collections.Counter(), 'власн': collections.Counter(), 'за_викликом': collections.Counter(),
              'вкл_за_іменем': collections.Counter(), 'n': 0}
    стоп = threading.Event()
    def _семплер():
        while not стоп.is_set():
            time.sleep(0.002)
            f = sys._current_frames().get(головний)
            п = відтворення.ПОТОЧНИЙ
            if f is None or п is None: continue
            семпли['n'] += 1
            семпли['за_викликом'][п[1]] += 1
            бачено = set(); листок = True
            while f is not None:
                к = os.path.basename(f.f_code.co_filename) + ':' + f.f_code.co_name
                if листок: семпли['власн'][к] += 1; листок = False
                if к not in бачено:
                    бачено.add(к); семпли['вкл'][к] += 1; семпли['вкл_за_іменем'][п[1] + '|' + к] += 1
                f = f.f_back
    нитка = threading.Thread(target=_семплер, daemon=True); нитка.start()
t0 = _pc()
р = json.loads(asyncio.run(відтворення.прогнати(виклики, профіль=профіль)))
ВИМ['відтворення_мс'] = (_pc() - t0) * 1000
ВИМ['відтворення'] = р
if семпли is not None:
    стоп.set(); нитка.join()
    ВИМ['семпли'] = {'n': семпли['n'], 'за_викликом': dict(семпли['за_викликом']),
                     'вкл': семпли['вкл'].most_common(400), 'власн': семпли['власн'].most_common(200),
                     'вкл_за_іменем': семпли['вкл_за_іменем'].most_common(1500)}
json.dump(ВИМ, open(вихід, 'w', encoding='utf-8'), ensure_ascii=False)
print('імпорт', round(ВИМ['імпорт_bridge_мс']), 'мс · компіляцій', len(ВИМ['комп']),
      round(sum(к[1] for к in ВИМ['комп'])), 'мс · відтворення', round(ВИМ['відтворення_мс']), 'мс')
