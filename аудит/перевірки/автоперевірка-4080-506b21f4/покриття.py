"""Звірка реєстру HTTP із кожною фактичною адресою незалежного повтору ПІСЛЯ."""
import collections
import csv
import gzip
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

tree = Path(sys.argv[1]).resolve()
after = Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]).resolve()
folder = tree/'аудит/проби/кадр_варіант_кв2_один_колір_1611'
shops = {r['домен'] for r in csv.DictReader((tree/'zhnyvarka/один_колір.tsv').open(encoding='utf-8'),delimiter='\t')}
with gzip.open(after,'rt',encoding='utf-8') as stream:
    results = list(map(json.loads,stream))
assert len(results)==13882
urls = []
for row in results:
    if urlsplit(row['адреса']).netloc in shops and row['стан']!='без_відповіді' and 'запис' in row:
        urls.extend(row['запис']['фото'])
with gzip.open(folder/'статуси_404.tsv.gz','rt',encoding='utf-8') as stream:
    statuses = list(csv.DictReader(stream,delimiter='\t'))
mapped = {r['адреса']:r for r in statuses}
missing = sorted(set(urls)-set(mapped))
extra = sorted(set(mapped)-set(urls))
frames = {r['адреса_кадру']:r['http_код'] for r in csv.DictReader(
    (tree/'аудит/проби/кадр_варіант_кв1_очима_1511/кадри.tsv').open(encoding='utf-8'),delimiter='\t')}
bad_saved = [r for r in statuses if r['джерело']=='кадри.tsv' and frames.get(r['адреса'])!=r['код']]
report = dict(записів=len(results),адрес_у_записах=len(urls),унікальних=len(set(urls)),
              реєстр_рядків=len(statuses),коди=collections.Counter(r['код'] for r in statuses),
              джерела=collections.Counter(r['джерело'] for r in statuses),
              пропущені=missing,зайві=extra,хибний_збережений_статус=bad_saved,
              sha_дерев=sorted({r['голова'] for r in results}))
(out/'покриття.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=1))
assert len(urls)==12909 and len(mapped)==len(set(urls))==12902
assert not missing and not extra and not bad_saved
assert report['коди']=={'200':12902}
assert report['sha_дерев']==['506b21f4b061658edb880431d12c150bb7199563']
