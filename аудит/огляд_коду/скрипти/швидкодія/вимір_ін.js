/* Інструмент виміру ЗЗОВНІ сторінки (сторінку не правимо): addInitScript + обгортки.
   ставити(стор)          — до goto: longtask, atob/Uint8Array.from, loadPyodide → unpackArchive / імпорт bridge
   післяЗавантаження(стор) — після goto: обгортки містП / рендерКартку / підвʼязатиКартку
   зняти(стор, файл)       — JSON усього зібраного (події, longtask, таймінги навігації, виклики bridge зі входами) */
const fs = require('fs');

const ПЕРЕД_ІМПОРТОМ = `
import builtins, sys, time
import importlib._bootstrap_external as _be
_pc = time.perf_counter
__ВИМ = {'імп': {}, 'комп': [], 'dont_write_bytecode': sys.dont_write_bytecode, 'версія': sys.version,
         'модулів_до': len(sys.modules)}
_стек = []
_орг_імп = builtins.__import__
def _імп(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name in sys.modules:
        return _орг_імп(name, globals, locals, fromlist, level)
    ключ = name if level == 0 else ((globals or {}).get('__package__') or '') + ':' + name
    t0 = _pc(); _стек.append(0.0)
    try:
        return _орг_імп(name, globals, locals, fromlist, level)
    finally:
        dt = _pc() - t0; діти = _стек.pop()
        if _стек: _стек[-1] += dt
        if ключ not in __ВИМ['імп']:
            __ВИМ['імп'][ключ] = [dt * 1000, (dt - діти) * 1000]
builtins.__import__ = _імп
_орг_stc = _be.SourceLoader.source_to_code
def _stc(self, data, path, *, _optimize=-1):
    t0 = _pc()
    try:
        return _орг_stc(self, data, path, _optimize=_optimize)
    finally:
        __ВИМ['комп'].append([path, (_pc() - t0) * 1000, len(data), time.time() * 1000])
_be.SourceLoader.source_to_code = _stc
builtins.__ВИМ = __ВИМ
`;
const ПІСЛЯ_ІМПОРТУ = `
import builtins, json, sys, time, hashlib
builtins.__import__ = _орг_імп
__ВИМ['модулів_після'] = len(sys.modules)
import bridge
if not hasattr(bridge, '_вим_о'):
    bridge._вим_о = bridge.виклик
    bridge._вим_оа = bridge.виклик_а
    bridge._вим = []
    def _запис(ім, вхід, t0, w0, r, async_=False):
        dt = (time.perf_counter() - t0) * 1000
        try: вх = вхід if isinstance(вхід, str) else json.dumps(вхід, ensure_ascii=False)
        except Exception as e: вх = 'ПОМИЛКА ' + repr(e)
        try: хеш = hashlib.md5(str(r).encode()).hexdigest()
        except Exception: хеш = '?'
        bridge._вим.append({'ім': ім, 'w0': w0 * 1000, 'мс': dt, 'вхід': вх, 'хеш': хеш, 'async': async_})
    def _в(ім, вхід):
        t0 = time.perf_counter(); w0 = time.time(); r = None
        try:
            r = bridge._вим_о(ім, вхід); return r
        finally:
            _запис(ім, вхід, t0, w0, r)
    async def _ва(ім, вхід):
        if ім != 'оцінка':
            return _в(ім, вхід)
        t0 = time.perf_counter(); w0 = time.time(); r = None
        try:
            r = await bridge._вим_оа(ім, вхід); return r
        finally:
            _запис(ім, вхід, t0, w0, r, True)
    bridge.виклик = _в
    bridge.виклик_а = _ва
json.dumps(__ВИМ, ensure_ascii=False)
`;

async function ставити(стор){
  await стор.addInitScript(([ПЕРЕД, ПІСЛЯ]) => {
    const В = window.__ВИМ = {lt: [], події: [], ltErr: null};
    const тепер = () => performance.now();
    try {
      new PerformanceObserver(l => { for (const e of l.getEntries()) В.lt.push([e.startTime, e.duration]); })
        .observe({type: 'longtask', buffered: true});
    } catch (e) { В.ltErr = String(e); }
    const мітка = (к, t0, t1, extra) => В.події.push(Object.assign({к, t0, t1}, extra || {}));
    В.мітка = мітка;
    const оAtob = window.atob;
    window.atob = function(s){ const t0 = тепер(); const r = оAtob.call(this, s);
      if (s && s.length > 1e6) мітка('atob', t0, тепер(), {n: s.length}); return r; };
    const оFrom = Uint8Array.from;
    Uint8Array.from = function(a, ...r){ const t0 = тепер(); const x = оFrom.call(this, a, ...r);
      if (a && a.length > 1e6) мітка('Uint8Array.from', t0, тепер(), {n: a.length}); return x; };
    let lp;
    const обгорнути = v => async function(opts){
      const t0 = тепер(); В.стек_підйому = String(new Error().stack).slice(0, 1500);
      const pd = await v.call(this, opts); мітка('loadPyodide', t0, тепер());
      window.__ПД = pd;
      const оUnp = pd.unpackArchive.bind(pd);
      pd.unpackArchive = function(...a){ const t0 = тепер(); const r = оUnp(...a);
        мітка('unpackArchive', t0, тепер(), {байт: a[0] && a[0].byteLength});
        if (window.__PYC){ const t = тепер();
          pd.runPython('import compileall, sys\nsys.dont_write_bytecode = False\ncompileall.compile_dir("/показ", quiet=1, workers=1)');
          мітка('compileall', t, тепер()); }
        return r; };
      const оRPA = pd.runPythonAsync.bind(pd);
      pd.runPythonAsync = async function(code, ...a){
        if (/import bridge\n/.test(code) && /sys\.path\.insert/.test(code)){
          pd.runPython(ПЕРЕД);
          const t0 = тепер(); const r = await оRPA(code, ...a); мітка('import_bridge', t0, тепер());
          const t2 = тепер();
          В.імпорт = JSON.parse(pd.runPython(ПІСЛЯ));
          мітка('обгортка_bridge', t2, тепер());
          return r;
        }
        return оRPA(code, ...a);
      };
      return pd;
    };
    Object.defineProperty(window, 'loadPyodide', {configurable: true,
      get(){ return lp; }, set(v){ lp = (typeof v === 'function') ? обгорнути(v) : v; }});
  }, [ПЕРЕД_ІМПОРТОМ, ПІСЛЯ_ІМПОРТУ]);
}

async function післяЗавантаження(стор){
  await стор.evaluate(() => {
    const В = window.__ВИМ, тепер = () => performance.now();
    const оМіст = window.містП;
    window.містП = async function(ім, д){
      const з = {к: 'містП', ім, t0: тепер()}; В.події.push(з);
      try { return await оМіст.call(this, ім, д); } finally { з.t1 = тепер(); }
    };
    for (const ім of ['рендерКартку', 'підвʼязатиКартку', 'малюватиПоступП']){
      const о = window[ім]; if (typeof о !== 'function') continue;
      window[ім] = function(){ const t0 = тепер(); try { return о.apply(this, arguments); }
        finally { В.події.push({к: ім, t0, t1: тепер(), поз: arguments[0]}); } };
    }
  });
}

async function зняти(стор, файл){
  const д = await стор.evaluate(() => {
    const В = window.__ВИМ;
    const nav = performance.getEntriesByType('navigation')[0];
    const res = performance.getEntriesByType('resource').filter(e => /pyodide|python_stdlib/.test(e.name))
      .map(e => ({name: e.name.split('/').pop(), start: e.startTime, end: e.responseEnd, dur: e.duration, size: e.transferSize}));
    let python = [];
    try { python = JSON.parse(pyodide_показу.runPython('import json, bridge\njson.dumps(getattr(bridge, "_вим", []), ensure_ascii=False)')); } catch (e) { python = [{помилка: String(e)}]; }
    return {стек_підйому: В.стек_підйому || null, події: В.події, lt: В.lt, ltErr: В.ltErr, імпорт: В.імпорт || null,
      nav: nav ? nav.toJSON() : null, paint: performance.getEntriesByType('paint').map(e => e.toJSON()),
      res, python, тепер: performance.now(), timeOrigin: performance.timeOrigin};
  });
  fs.writeFileSync(файл, JSON.stringify(д));
  return д;
}

module.exports = {ставити, післяЗавантаження, зняти, ПЕРЕД_ІМПОРТОМ, ПІСЛЯ_ІМПОРТУ};
