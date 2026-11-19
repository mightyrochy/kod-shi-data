"""Публічний GitHub API: точна голова, CI та час нової перевірки."""
import datetime
import gzip
import json
from pathlib import Path
import sys
import urllib.request

докази = Path(__file__).resolve().parent
база = 'https://api.github.com/repos/mightyrochy/kod-shi-data/'
голова = '2cfe78bbbfb3b4568099e55c985bffc3b37802fb'


def читати(шлях, назва):
    if '--збережене' in sys.argv:
        with gzip.open(докази / (назва + '.json.gz'), 'rt', encoding='utf-8') as файл:
            return json.load(файл)
    запит = urllib.request.Request(база + шлях, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'independent-review-4295'})
    with urllib.request.urlopen(запит, timeout=60) as відповідь:
        дані = json.load(відповідь)
    with gzip.open(докази / (назва + '.json.gz'), 'wt', encoding='utf-8') as файл:
        json.dump(дані, файл, ensure_ascii=False, indent=2)
    return дані


pr = читати('pulls/4295', 'pr-перед-вердиктом')
assert (pr['user']['login'], pr['base']['repo']['full_name'], pr['head']['repo']['full_name'], pr['base']['ref'], pr['head']['sha']) == (
    'mightyrochy', 'mightyrochy/kod-shi-data', 'mightyrochy/kod-shi-data', 'main', голова)
print('голова:', pr['head']['sha'], flush=True)
ci = читати('commits/' + голова + '/check-runs?per_page=100', 'checks')
print('перевірок:', ci['total_count'], flush=True)
for к in ci['check_runs']:
    print(к['name'], к['status'], к['conclusion'], к['details_url'], flush=True)
новий = next(к for к in ci['check_runs'] if к['name'] == 'тести приладів')
job = читати('actions/jobs/' + новий['details_url'].rsplit('/', 1)[-1], 'job')
for крок in job['steps']:
    if крок['name'] == 'усі тести приладів':
        print('крок:', крок['started_at'], крок['completed_at'], крок['conclusion'], flush=True)
print('job:', job['started_at'], job['completed_at'], job['conclusion'], flush=True)
if '--збережене' not in sys.argv:
    (докази / 'час-api.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat() + '\n', encoding='utf-8')
актуальні = {}
for к in sorted(ci['check_runs'], key=lambda к: к['id'], reverse=True):
    актуальні.setdefault(к['name'], к)
print('актуальні за назвою:', len(актуальні), flush=True)
assert all(к['status'] == 'completed' and к['conclusion'] in ('success', 'skipped', 'neutral') for к in актуальні.values())
