import collections, gzip, json, os, pathlib, subprocess, sys, time

root = pathlib.Path(sys.argv[1]).resolve()
results = root / 'перевірка4041'
results.mkdir(exist_ok=True)
env = dict(os.environ, PYTHONIOENCODING='utf-8')
summary = {}
for label, tree in [('до', 'base4041'), ('після', 'source4041')]:
    cwd = root / tree
    started = time.monotonic()
    p = subprocess.run([sys.executable, 'джерела/прилади/корінь_е3_сила_правила.py'], cwd=cwd, env=env, capture_output=True, encoding='utf-8')
    (results / (label + '_прилад.txt')).write_text(p.stdout+p.stderr, encoding='utf-8')
    print(label, 'прилад', p.returncode, p.stdout.splitlines()[-1:], flush=True)
    weights = results / (label + '_ваги.json.gz')
    p = subprocess.run([sys.executable, 'джерела/проби/е3_формальність_знімок.py', str(weights)], cwd=cwd, env=env, capture_output=True, encoding='utf-8')
    (results / (label + '_ваги.txt')).write_text(p.stdout+p.stderr, encoding='utf-8')
    print(label, 'ваги', p.returncode, p.stdout[-2000:], p.stderr[-1000:], flush=True)
    summary[label] = {'код':p.returncode, 'секунд':round(time.monotonic()-started,2)}
if all(x['код']==0 for x in summary.values()):
    with gzip.open(results/'до_ваги.json.gz','rt',encoding='utf-8') as f: before=json.load(f)
    with gzip.open(results/'після_ваги.json.gz','rt',encoding='utf-8') as f: after=json.load(f)
    summary['звірка']={'до':len(before), 'після':len(after), 'відмінностей':sum(a!=b for a,b in zip(before,after))+abs(len(before)-len(after))}
    print(json.dumps(summary,ensure_ascii=False),flush=True)
(results/'числа.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
