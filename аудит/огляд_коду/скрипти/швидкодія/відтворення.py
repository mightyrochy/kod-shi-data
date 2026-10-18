"""Відтворення записаних викликів bridge (ті самі входи, той самий порядок) — однаково в Pyodide і в CPython.
Виклик: await прогнати(шлях_json, профіль=False) → JSON з часом кожного виклику (мс) і, з профілем, топом cProfile."""
import json, time, hashlib, io
ПОТОЧНИЙ = None


async def прогнати(шлях, профіль=False, топ=40, лише=None):
    import bridge
    о = getattr(bridge, '_вим_о', bridge.виклик)
    оа = getattr(bridge, '_вим_оа', bridge.виклик_а)
    виклики = json.load(open(шлях, encoding='utf-8'))
    виклики = sorted([в for в in виклики if 'вхід' in в], key=lambda в: в['w0'])
    if лише:
        виклики = виклики[:лише]
    pr = None
    if профіль:
        import sys
        # у теці показу лежить СВІЙ `profile.py` (профіль жінки) — він затуляє stdlib `profile`, який тягне cProfile
        свій = sys.modules.pop('profile', None); шлях = list(sys.path)
        sys.path[:] = [x for x in sys.path if x not in ('', '.', '/показ') and 'показ' not in x]
        try:
            import cProfile
        finally:
            sys.path[:] = шлях
            if свій is not None: sys.modules['profile'] = свій
            else: sys.modules.pop('profile', None)
        pr = cProfile.Profile()
    вих = []
    for в in виклики:
        вх = json.loads(в['вхід'])
        global ПОТОЧНИЙ
        ПОТОЧНИЙ = (len(вих), в['ім'])
        t0 = time.perf_counter()
        if pr: pr.enable()
        try:
            if в.get('async'):
                r = await оа(в['ім'], вх)
            else:
                r = о(в['ім'], вх)
            помилка = None
        except Exception as e:
            r = None; помилка = repr(e)[:200]
        finally:
            if pr: pr.disable()
        мс = (time.perf_counter() - t0) * 1000
        try: хеш = hashlib.md5(str(r).encode()).hexdigest()
        except Exception: хеш = '?'
        import os
        if os.environ.get('VIDTV_DUMP'):
            open(os.path.join(os.environ['VIDTV_DUMP'], '%03d_%s.txt' % (len(вих), в['ім'])), 'w').write(str(r))
        вих.append({'ім': в['ім'], 'мс': мс, 'мс_сторінка': в['мс'], 'хеш_збіг': хеш == в.get('хеш'),
                    'помилка': помилка, 'вхід_симв': len(в['вхід'])})
    рез = {'виклики': вих}
    if pr:
        import pstats
        st = pstats.Stats(pr)
        рядки = []
        for (файл, рядок, ф), (cc, nc, tt, ct, _) in st.stats.items():
            рядки.append([файл.split('/')[-1] + ':' + str(рядок) + ':' + ф, nc, tt * 1000, ct * 1000])
        рез['власний'] = sorted(рядки, key=lambda р: -р[2])[:топ]
        рез['сукупний'] = sorted(рядки, key=lambda р: -р[3])[:топ]
        рез['усі'] = рядки
        import os
        if os.environ.get('PSTATS_OUT'): pr.dump_stats(os.environ['PSTATS_OUT'])
    return json.dumps(рез, ensure_ascii=False)
