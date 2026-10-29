"""Звірити голову, CI та наявні рецензії публічним GitHub API без входу."""
import concurrent.futures, datetime, json, os, pathlib, urllib.request

ROOT = pathlib.Path(os.environ.get('KOD_SHI_REVIEW_ROOT', pathlib.Path(__file__).parent))
SHA = '87c83613f5708ab3d150e166eab55b1f6fddd439'
URL = 'https://api.github.com/repos/mightyrochy/kod-shi-data/'
paths = dict(pr='pulls/2106', checks='commits/'+SHA+'/check-runs?per_page=100',
             status='commits/'+SHA+'/status', reviews='pulls/2106/reviews?per_page=100')

def read(pair):
    name, path = pair
    request = urllib.request.Request(URL+path, headers={'Accept':'application/vnd.github+json', 'User-Agent':'Kod-Shi-review'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return name, json.load(response)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    data = dict(pool.map(read, paths.items()))
pr = data['pr']
identity = dict(number=pr['number'], state=pr['state'], author=pr['user']['login'],
                base_repo=pr['base']['repo']['full_name'], base_ref=pr['base']['ref'], base_sha=pr['base']['sha'],
                head_repo=pr['head']['repo']['full_name'], head_ref=pr['head']['ref'], head_sha=pr['head']['sha'])
result = dict(час_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), PR=identity,
              checks=[{k: r.get(k) for k in ('name','head_sha','status','conclusion','details_url')}
                      for r in data['checks'].get('check_runs', [])],
              status=dict(state=data['status']['state'], total_count=data['status']['total_count'],
                          contexts=[dict(context=r['context'], state=r['state'], target_url=r.get('target_url'))
                                    for r in data['status'].get('statuses', [])]),
              reviews=[dict(author=r['user']['login'], state=r['state'], commit_id=r['commit_id'],
                            html_url=r['html_url'], body=r['body'])
                       for r in data['reviews'] if r['user']['login'] in ('mightyrochy','chatgpt-codex-connector[bot]')])
(ROOT/'review-logs/github-фінал.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps(result, ensure_ascii=False, indent=2))
assert identity['author'] == 'mightyrochy'
assert identity['base_repo'] == identity['head_repo'] == 'mightyrochy/kod-shi-data'
assert identity['base_ref'] == 'main' and identity['head_sha'] == SHA
