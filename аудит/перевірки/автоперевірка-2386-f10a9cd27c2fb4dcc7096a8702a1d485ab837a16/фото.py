"""Читає адреси фото нових карток і збереженої черги, перевіряє HTTP без зміни каталогу."""
import csv, gzip, json, sys, urllib.request
from pathlib import Path
sys.stdout = open(sys.argv[1], 'w', encoding='utf-8', buffering=1)
rows=[json.loads(x) for x in gzip.decompress(Path('каталог_записи_v1.jsonl.gz').read_bytes()).splitlines()][1:]
new=[r for r in rows if r['ід'].startswith('ж53-') and r['адреса'].startswith('https://25union.com.ua/')][:2]
кеш = Path(sys.argv[2]); кеш.mkdir(parents=True, exist_ok=True)
відповідність = {}
with gzip.open('аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz','rt',encoding='utf8') as f:
    q=list(csv.DictReader(f,delimiter='\t'))
bad=[r for r in q if '25union.com.ua/katalog/' in json.dumps(r) and '/image/cache/' in json.dumps(r)]
print('Черга:',len(q),'хибні:',len(bad),'приклад:',json.dumps(bad[:1],ensure_ascii=False))
print('Стовпці черги:',list(q[0]))
for r in new:
    print('Картка:',r['адреса'],'кадри:',r['кадри'][:1])
    for url in r['кадри'][:1]:
        try:
            with urllib.request.urlopen(url,timeout=30) as f:
                тіло = f.read()
                print('GET:',url,f.status,f.headers.get('Content-Type'),len(тіло))
                файл = кеш/f'{len(відповідність)}.webp'; файл.write_bytes(тіло)
                відповідність[url] = str(файл.resolve())
        except Exception as e: print('GET:',url,type(e).__name__,str(e))
if bad:
    import re
    urls = re.findall(r'https?://[^\s"\]]+', json.dumps(bad[0],ensure_ascii=False))
    for url in urls:
        if '/image/cache/' not in url:
            continue
        for u in [url, re.sub(r'^(https?://[^/]+)/(?!image/)[^?#]*?(/image/cache/)',r'\g<1>\g<2>',url)]:
            try:
                with urllib.request.urlopen(u,timeout=30) as f: print('GET черга:',u,f.status,f.headers.get('Content-Type'),len(f.read()))
            except Exception as e: print('GET черга:',u,type(e).__name__,str(e))
        break
(кеш/'адреси.json').write_text(json.dumps(відповідність,ensure_ascii=False),encoding='utf-8')
