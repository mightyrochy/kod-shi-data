import csv, datetime, re, subprocess, sys
from pathlib import Path

def git(*args):
    p = subprocess.run(['git', '-c', 'core.quotepath=false', *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode: raise RuntimeError(p.stderr.decode('utf-8', 'replace'))
    return p.stdout.decode('utf-8', 'replace')

main = git('rev-parse', 'origin/main').strip()
now = datetime.datetime.fromisoformat(git('show', '-s', '--format=%cI', main).strip())
paths = [x for x in git('ls-tree', '-r', '--name-only', main, 'аудит/наряди/').splitlines() if x.endswith('.md') and x.count('/') == 2]
roots = set(git('ls-tree', '-r', '--name-only', main, 'аудит/корені/').splitlines())
print('refs = []', flush=True)
refs = []
snapshot = Path(__file__).with_name('branches.txt')
if not snapshot.exists():
    snapshot.write_text(git('ls-remote', '--heads', 'origin', 'refs/heads/claude/*', 'refs/heads/gemini/*', 'refs/heads/codex/*'), encoding='utf-8')
for line in snapshot.read_text(encoding='utf-8').splitlines():
    sha, ref = line.split('\t'); refs.append((sha, ref))
names = [Path(p).stem for p in paths]
matched = [(sha, ref) for sha, ref in refs if any(ref.startswith('refs/heads/'+prefix+'/'+name) for prefix in ('claude','gemini','codex') for name in names)]
import tempfile, os
cache = Path(tempfile.gettempdir()) / 'order-heads.git'
if not cache.exists():
    subprocess.run(['git', 'init', '--bare', str(cache)], check=True, stdout=subprocess.PIPE)
url = git('remote', 'get-url', 'origin').strip()
hashes = sorted(set(s for s, _ in matched))
for i in range(0, len(hashes), 80):
    print('fetch', i, '/', len(hashes), flush=True)
    subprocess.run(['git', '--git-dir', str(cache), 'fetch', '--depth=1', '--filter=tree:0', '--no-tags', url, *hashes[i:i+80]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
dates = {}
proc = subprocess.run(['git', '--git-dir', str(cache), 'cat-file', '--batch'], input=('\n'.join(hashes)+'\n').encode(), stdout=subprocess.PIPE, check=True)
data = proc.stdout
pos = 0
for sha in hashes:
    end = data.index(b'\n', pos); header = data[pos:end].decode().split(); size = int(header[2]); body = data[end+1:end+1+size]; pos = end+size+2
    line = next(x for x in body.splitlines() if x.startswith(b'committer ')).decode('utf-8', 'replace')
    stamp, zone = line.rsplit(' ', 2)[-2:]
    dates[sha] = datetime.datetime.fromtimestamp(int(stamp), datetime.timezone.utc).isoformat()
print('creation = {}', flush=True)
creation = {}
for entry in git('log', '--diff-filter=A', '--format=%x1e%cs', '--name-only', main, '--', paths[0].rsplit('/',1)[0]).split('\x1e'):
    lines = entry.strip().splitlines()
    if lines:
        for entry_path in lines[1:]: creation[entry_path] = lines[0]
print('log = git(', flush=True)
log = git('log', main, '--since=2026-10-01', '--format=%H%x1f%cs%x1f%s%x1f%b%x1e').split('\x1e')
commits = []
for item in log:
    parts = item.strip('\n').split('\x1f', 3)
    if len(parts) == 4: commits.append(parts)
print('rows = []', flush=True)
rows = []
print('for path, name in zip(paths, names):', flush=True)
for path, name in zip(paths, names):
    content = git('show', main+':'+path)
    first = content.splitlines()[0] if content else ''
    def field(key):
        m = re.search(r'(?:^|\|)\s*'+key+r'\s*:?\s*([^|]+)', first, re.I)
        return m.group(1).strip() if m else 'не зазначено'
    branches = [(s,r) for s,r in matched if any(r.startswith('refs/heads/'+p+'/'+name) for p in ('claude','gemini','codex'))]
    binfo = [(s, r.removeprefix('refs/heads/'), dates[s]) for s,r in branches]
    found = [c for c in commits if name.casefold() in (c[2]+'\n'+c[3]).casefold()]
    # A title mentioning an order is not proof of its PR: require its branch in the merge message.
    merges = [c for c in found if re.search(r'(?:claude|gemini|codex)/'+re.escape(name)+r'(?=$|[\s)#])', c[2]+'\n'+c[3], re.I) and (re.search(r'\(#[0-9]+\)', c[2]) or c[2].startswith('Merge pull request'))]
    created = [creation[path]] if path in creation else []
    links = sorted(set(re.findall(r'аудит/корені/([^\s`\)\]#]+\.md)', content)))
    proof = ['перший коміт файлу: '+(created[-1] if created else 'не знайдено')]
    if links: proof.append('паспорти: '+', '.join(links))
    if binfo: proof.append('гілки: '+', '.join(f'{r} {s} {d}' for s,r,d in binfo))
    else: proof.append('гілок за шаблонами немає')
    if found: proof.append('згадки в main: '+', '.join(f'{c[0]} {c[1]} {c[2]}' for c in found))
    else: proof.append('згадок у main з 01.10.2026 немає')
    if name in ('автоперевірка','автоживий') or re.search(r'постійни[йм] шаблон',content,re.I): cls='шаблон'
    elif 'аудит/корені/'+name+'.md' in roots: cls='корінь'
    elif merges: cls='злито'; proof.append('злиття PR: '+merges[0][0])
    elif binfo:
        newest = max(datetime.datetime.fromisoformat(b[2]) for b in binfo)
        if found: cls='не визначено: згадки в main потребують перевірки PR'
        elif (now-newest).total_seconds() < 3*86400: cls='іде'
        else: cls='покинуто'
    elif found: cls='не визначено: згадки в main потребують перевірки PR'
    else: cls='не взято'
    after=field('після')
    dependency='—'
    if cls in ('не взято','покинуто'):
        if after in ('—','-', 'нема'): dependency='так'
        else:
            nums=re.findall(r'#(\d+)',after)
            candidates=[c for c in commits if any(re.search(r'\(#'+n+r'\)',c[2]) for n in nums)]
            if nums and len({n for n in nums if any(re.search(r'\(#'+n+r'\)',c[2]) for c in candidates)}) == len(nums): dependency='так: '+', '.join(c[0] for c in candidates)
            else: dependency='не визначено: '+after
    rows.append([name,cls,'; '.join(proof),dependency,field('ризик'),field('сила'),field('номери'),first])
rows.sort(key=lambda r: (0 if r[1]=='не взято' else 1 if r[1]=='покинуто' else 2, r[0]))
out=Path(__file__).with_name('перелік.tsv')
with out.open('w', encoding='utf-8', newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['наряд','клас','доказ','після в main','ризик','сила','номери','перший рядок']); w.writerows(rows)
print(main, len(rows), 'гілок', len(matched), 'класів', {x:sum(r[1]==x for r in rows) for x in sorted(set(r[1] for r in rows))})
