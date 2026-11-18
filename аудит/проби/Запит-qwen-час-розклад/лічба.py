import collections, glob, json, math, os, re, statistics, subprocess, sys, tempfile
from pathlib import Path

root = Path('аудит/проби')
with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f: tmp = f.name
try:
    subprocess.run([sys.executable, '-I', str(root/'Автоживий-час-сцени-розклад/розклад.py'), str(root), tmp], check=True, stdout=subprocess.DEVNULL)
    scenes = json.loads(Path(tmp).read_text(encoding='utf-8'))
finally: os.unlink(tmp)
def stats(a):
    a = sorted(a)
    if not a: return '— (0)'
    return f'{statistics.median(a):.1f}/{a[math.ceil(.9*len(a))-1]:.1f} ({len(a)})'
groups = collections.defaultdict(list)
coverage = collections.Counter()
switches = collections.defaultdict(list)
for s in scenes:
    if not s['дата'] or s['дата'] < '2026-11-07': continue
    run = s['тека'].split(os.sep)[0].split('/')[0]
    dp = root / s['тека']
    files = sorted((dp/'VIDPOVIDI/обмін').glob('*.json'))
    calls = {c['n']: c for c in s['виклики']}
    coverage['сцен'] += 1
    coverage['викликів'] += max(len(files), len(calls))
    coverage['з часом'] += len(calls)
    proxy = dp/'проксі.txt'
    if proxy.exists():
        sw = [int(x) for x in re.findall(r'перемикання #\d+ →[^\n]*?·\s*(\d+) мс', proxy.read_text(encoding='utf-8', errors='replace'))]
        switches[(run,s['дата'])].append((s['тека'],len(sw),sum(sw)))
    else: coverage['без проксі'] += 1
    for p in files:
        n = int(p.stem); c = calls.get(n, {})
        try:
            d = json.loads(p.read_text(encoding='utf-8')); q = d['запит']; q = json.loads(q) if isinstance(q,str) else q
            response = d.get('відповідь', {}); body = response.get('body', {}); body = json.loads(body) if isinstance(body,str) else body
            usage = body.get('usage', {}) or {}; model = q.get('model') or response.get('headers', {}).get('x-model') or 'невідомо'
        except (ValueError, KeyError, TypeError): coverage['помилка обміну'] += 1; continue
        inp = usage.get('prompt_tokens', usage.get('input_tokens')); out = usage.get('completion_tokens', usage.get('output_tokens'))
        dur = c.get('с'); speed = out/dur if isinstance(out,(int,float)) and dur and dur>0 else None
        coverage['з токенами'] += int(inp is not None and out is not None)
        coverage['з часом і токенами'] += int(speed is not None)
        groups[(run,s['дата'],model)].append((inp,out,dur,speed,c.get('вид','невідомо'),s['тека'],n))
print('ОХОПЛЕННЯ',dict(coverage))
print('ПРОГОНИ: медіана/p90 (n); швидкість = вихід / повний час запиту')
for (run,date,model), rows in sorted(groups.items(),key=lambda x:(x[0][1],x[0][0],x[0][2])):
    vals = [stats([r[i] for r in rows if isinstance(r[i],(int,float))]) for i in range(4)]
    print('|',date,'|',run,'|',model,'|',len(rows),'|',' | '.join(vals),'|')
print('ПЕРЕМИКАННЯ: сцена, кількість, сума мс')
for key, rows in sorted(switches.items(),key=lambda x:(x[0][1],x[0][0])):
    for row in rows: print('| ' + ' | '.join(map(str,(key[1],*row))) + ' |')
print('QWEN ЗА ВИДАМИ, до 15 / з 15')
types=collections.defaultdict(lambda:[[],[]])
for (run,date,model), rows in groups.items():
    if 'qwen' not in model.lower(): continue
    for inp,out,dur,speed,kind,scene,n in rows:
        if isinstance(out,(int,float)): types[kind][date >= '2026-11-15'].append(out)
for kind,(before,after) in sorted(types.items()): print(kind,stats(before),stats(after))
print('QWEN РАЗОМ ДО / ПІСЛЯ')
for after in (False, True):
    rows=[r for (run,date,model), rs in groups.items() if 'qwen' in model.lower() and (date >= '2026-11-15') == after for r in rs]
    print('з 15.11' if after else 'до 15.11', 'вихід', stats([r[1] for r in rows if isinstance(r[1],(int,float))]), 'швидкість',stats([r[3] for r in rows if isinstance(r[3],(int,float))]))
