"""Почерговий замір двох прогрітих справжніх мостів, із часом CPU."""
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path('C:/Users/gemini/gemini-runs/20261028-212800-69ae34a8110f/review-2106')
OUT = Path('C:/Users/gemini/gemini-runs/20261028-212800-69ae34a8110f/review-logs')
TEMP = Path('C:/Users/gemini/gemini-runs/20261028-212800-69ae34a8110f')


def worker(source):
    sys.path.insert(0, str(source))
    os.chdir(source)
    import bridge as B
    import feed
    feed.каталог_на_диску('каталог_повний.xml')
    brief = dict(json.loads(Path('стенд_вх.json').read_text(encoding='utf8')), сід=4242,
                 варіантів=10, ремонт_варіантів=5, бюджет_символів=120000, без_фото=1, пакети=1)
    pool = json.loads(B.виклик('запити', json.dumps(brief, ensure_ascii=False)))['пакети']['1']['пул']
    outfits = [dict(ід='о%d' % (i + 1), речі=[pool[s][i % len(pool[s])]['н']
                   for s in ('верх', 'низ', 'взуття', 'сумка')]) for i in range(10)]
    brief['текст_моделі'] = json.dumps(dict(версія='1', образи=outfits), ensure_ascii=False)
    payload = json.dumps(brief, ensure_ascii=False)
    B.виклик('від_моделі', payload)
    print('ГОТОВО', flush=True)
    for line in sys.stdin:
        if line.strip() != 'замір':
            break
        wall, cpu = time.perf_counter(), time.process_time()
        answer = B.виклик('від_моделі', payload)
        print(json.dumps(dict(секунд=time.perf_counter() - wall, cpu=time.process_time() - cpu,
                              символів=len(answer))), flush=True)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        worker(Path(sys.argv[1]))
    else:
        os.environ['PYTHONUTF8'] = '1'
        processes = {}
        measurements = {'до': [], 'після': []}
        try:
            for name, source in [('до', TEMP / 'before-2106/джерела'), ('після', ROOT / 'джерела')]:
                processes[name] = subprocess.Popen([sys.executable, '-X', 'utf8', __file__, str(source)],
                                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                   encoding='utf8', cwd=ROOT)
            for name, proc in processes.items():
                ready = proc.stdout.readline().strip()
                if ready != 'ГОТОВО':
                    raise RuntimeError((name, ready, proc.poll()))
                print(name, 'прогріто', flush=True)
            for pair in range(6):
                for name in (('до', 'після') if pair % 2 == 0 else ('після', 'до')):
                    proc = processes[name]
                    proc.stdin.write('замір\n')
                    proc.stdin.flush()
                    record = json.loads(proc.stdout.readline())
                    measurements[name].append(record)
                    print(name, pair + 1, record, flush=True)
            result = dict(пари=measurements, медіани={name: {key: statistics.median(r[key] for r in records)
                          for key in ('секунд', 'cpu')} for name, records in measurements.items()})
            (OUT / 'час-почергово.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        finally:
            for proc in processes.values():
                proc.stdin.close()
            for proc in processes.values():
                proc.wait()
