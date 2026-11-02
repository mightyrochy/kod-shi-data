import csv,gzip,json,pathlib
root=pathlib.Path(__file__).parent/'pr2386'
with gzip.open(root/'аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz','rt',encoding='utf8') as f:
    rows=list(csv.DictReader(f,delimiter='\t'))
print('Колонки:',list(rows[0]))
print('Речей черги:',len(rows))
with gzip.open(root/'каталог_записи_v1.jsonl.gz','rt',encoding='utf8') as f:
    records=[json.loads(x) for x in f][1:]
ids={r['ід'] for r in records}
key=next(k for k in rows[0] if k in ('ід','id','offer_id'))
print('Ід черги (без @магазин), яких немає в каталозі:',sum(r[key].split('@',1)[0] not in ids for r in rows))
with (root/'аудит/жнива_5_3/повний-обхід_стан.tsv').open(encoding='utf8') as f:
    states=list(csv.DictReader(f,delimiter='\t'))
print('Крамниць у стані обходу:',len(states))
print('Відкрито / адрес:',sum(int(r['готово']) for r in states),sum(int(r['адрес']) for r in states))
print('Залишок без коду причини:',[(r['домен'],r['лишилось']) for r in states if int(r['лишилось'])>0 and not r['причина_код']])
