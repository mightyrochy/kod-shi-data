STOP.set()
STOP2 = threading.Event(); CNT = {}; SEQ2 = itertools.count(1000)
def worker2(model, wid, mode):
    while not STOP2.is_set() and time.time() - T0 < 7200:
        i = next(SEQ2); k = CNT.get(model, 0); CNT[model] = k + 1
        pr = '1881' if mode == 'probe' else ORDER[k % 3]; rep = k // 3 + 1 if mode != 'probe' else k + 1
        t = time.time(); rec = {'i': i, 'pr': pr, 'rep': rep, 'w': wid, 'model': model, 'mode': mode, 'start': round(t - T0, 1), 'clock': time.strftime('%H:%M:%S')}
        try:
            r = ai.generate_text(P[pr], model_name=model); rec.update(ok=True, text=r, chars=len(r))
        except Exception as e:
            rec.update(ok=False, err=repr(e)[:1500])
        rec['secs'] = round(time.time() - t, 1)
        with LOCK: LOG.append(rec)
        if mode == 'probe' or not rec['ok']:
            time.sleep(120)
for a in (('google/gemini-3.1-pro-preview', 11, 'probe'), ('google/gemini-3.8-flash', 12, 'flow'), ('google/gemini-3.7-flash', 13, 'flow')):
    threading.Thread(target=worker2, args=a, daemon=True).start()
print('ok', time.strftime('%H:%M:%S'))
