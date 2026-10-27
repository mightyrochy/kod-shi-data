import threading, time, json, itertools
from google.colab import ai
M = 'google/gemini-3.1-pro-preview'
LOG = []; LOCK = threading.Lock(); STOP = threading.Event()
T0 = time.time(); SEQ = itertools.count(1)
ORDER = ['1868', '1852', '1881']
def worker(wid, start_after):
    while time.time() - T0 < start_after and not STOP.is_set(): time.sleep(5)
    while not STOP.is_set() and time.time() - T0 < 7200:
        i = next(SEQ); pr = ORDER[(i - 1) % 3]; rep = (i - 1) // 3 + 1
        t = time.time(); rec = {'i': i, 'pr': pr, 'rep': rep, 'w': wid, 'model': M, 'start': round(t - T0, 1), 'clock': time.strftime('%H:%M:%S')}
        try:
            r = ai.generate_text(P[pr], model_name=M)
            rec.update(ok=True, text=r, chars=len(r))
        except Exception as e:
            rec.update(ok=False, err=repr(e)[:1500])
        rec['secs'] = round(time.time() - t, 1)
        with LOCK: LOG.append(rec)
        if not rec['ok']: time.sleep(120)
THREADS = [threading.Thread(target=worker, args=(w, s), daemon=True) for w, s in ((1, 0), (2, 3600), (3, 3600), (4, 3600))]
for th in THREADS: th.start()
print('started', time.strftime('%H:%M:%S'))
