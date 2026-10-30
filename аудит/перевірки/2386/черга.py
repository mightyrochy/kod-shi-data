import collections, csv, gzip, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
root=Path.cwd()
with gzip.open(root/'аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz','rt',encoding='utf8') as f:
    rows=list(csv.DictReader(f,delimiter='\t'))
with gzip.open(root/'каталог_записи_v1.jsonl.gz','rt',encoding='utf8') as f:
    records=[json.loads(x) for x in f][1:]
ids={r['ід'] for r in records}; counts=collections.Counter()
for r in rows:
    for part in r['причини'].split(';'):
        for piece in part.split(','):
            k,sep,v=piece.strip().partition('=')
            if sep: counts[k]+=int(v)
print('Черга: речей',len(rows),'кадрів',sum(int(r['кадрів']) for r in rows))
print('Повторів ід:',len(rows)-len({r['ід'] for r in rows}))
print('Ід поза сирим v1:',sum(r['ід'].split('@')[0] not in ids for r in rows))
print('Причини:',dict(counts))
