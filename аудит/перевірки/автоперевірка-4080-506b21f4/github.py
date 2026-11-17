"""Публічна звірка призначеної голови й CI без входу в акаунт."""
import collections
import datetime
import json
from pathlib import Path
import urllib.request

sha='506b21f4b061658edb880431d12c150bb7199563'
api='https://api.github.com/repos/mightyrochy/kod-shi-data/'
def get(path):
    with urllib.request.urlopen(urllib.request.Request(api+path,headers={'User-Agent':'kodshi-review'}),timeout=30) as response:
        return json.load(response)
pr=get('pulls/4080')
metadata=dict(перевірено=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              автор=pr['user']['login'],стан=pr['state'],база=pr['base']['ref'],
              репозиторій_бази=pr['base']['repo']['full_name'],
              репозиторій_голови=pr['head']['repo']['full_name'],голова=pr['head']['sha'])
assert metadata['автор']=='mightyrochy' and metadata['база']=='main'
assert metadata['репозиторій_бази']==metadata['репозиторій_голови']=='mightyrochy/kod-shi-data'
assert metadata['голова']==sha, metadata
checks=get(f'commits/{sha}/check-runs?per_page=100')
assert checks['total_count']==len(checks['check_runs'])
latest={}
for row in checks['check_runs']:
    key=(row['app']['id'],row['name'])
    if key not in latest or latest[key]['id']<row['id']:
        latest[key]=row
result=dict(**metadata,перевірки=checks['check_runs'],останні_за_іменем=list(latest.values()))
Path(__file__).with_name('github.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False))
print('Усі висновки:',dict(collections.Counter(r['conclusion'] for r in checks['check_runs'])))
print('Останні за іменем:',dict(collections.Counter(r['conclusion'] for r in latest.values())))
print('Незавершених:',sum(r['status']!='completed' for r in checks['check_runs']))
assert all(r['status']=='completed' for r in checks['check_runs'])
assert all(r['conclusion'] in ('success','skipped','neutral') for r in latest.values())
