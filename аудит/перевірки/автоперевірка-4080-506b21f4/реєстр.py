import collections, csv, gzip, io, json, random, ssl, subprocess, sys, urllib.request, urllib.error
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sha='506b21f4b061658edb880431d12c150bb7199563'
repo=Path.cwd()
out=repo/'аудит/перевірки/автоперевірка-4080-506b21f4'
out.mkdir(parents=True,exist_ok=True)
folder='аудит/проби/кадр_варіант_кв2_один_колір_1611/'
data=subprocess.check_output(['git','show',sha+':'+folder+'статуси_404.tsv.gz'])
rows=list(csv.DictReader(io.StringIO(gzip.decompress(data).decode('utf-8')),delimiter='\t'))
urls={r['адреса']:r for r in rows}
assert len(rows)==len(urls)==12902
counts=collections.Counter(r['код'] for r in rows)
assert counts=={'200':12902}
ca='C:/Users/gemini/gemini-data/кадр_варіант_кв1_канал_1411/системні_CA/довірені_CA.pem'
context=ssl.create_default_context(cafile=ca)
sample=[]
rng=random.Random(20261117)
for shop in sorted({r['крамниця'] for r in rows}):
    pool=sorted([r for r in rows if r['крамниця']==shop],key=lambda r:r['адреса'])
    sample+=rng.sample(pool,6)
def get(r):
    try:
        request=urllib.request.Request(r['адреса'],method='HEAD',headers={'User-Agent':'Mozilla/5.0 (kodshi-probe)'})
        with urllib.request.urlopen(request,context=context,timeout=30) as response:
            return dict(**r,повтор_код=response.status,тип=response.headers.get('Content-Type'),кінцева=response.url)
    except Exception as error:
        return dict(**r,повтор_помилка=type(error).__name__+': '+str(error))
with ThreadPoolExecutor(max_workers=6) as pool:
    checked=list(pool.map(get,sample))
result=dict(голова=sha,унікальних=len(urls),коди=counts,
            джерела=collections.Counter(r['джерело'] for r in rows),
            крамниці=collections.Counter(r['крамниця'] for r in rows),
            зерно=20261117,повторено=checked)
(out/'реєстр-статусів.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='повторено'},ensure_ascii=False))
print('Незалежний HEAD:',dict(collections.Counter(r.get('повтор_код',r.get('повтор_помилка')) for r in checked)))
print('Типи:',dict(collections.Counter(r.get('тип') for r in checked)))
assert all(r.get('повтор_код')==200 for r in checked)
for r in checked:
    if not r.get('тип'):
        request=urllib.request.Request(r['адреса'],headers={'User-Agent':'Mozilla/5.0 (kodshi-probe)'})
        with urllib.request.urlopen(request,context=context,timeout=30) as response:
            body=response.read()
        im=Image.open(io.BytesIO(body))
        im.verify()
        r['GET_формат']=im.format
(out/'реєстр-статусів.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
assert all((r.get('тип') or '').startswith('image/') or r.get('GET_формат') for r in checked)
print('Без Content-Type: зображення підтверджено GET і декодуванням:',sum(bool(r.get('GET_формат')) for r in checked))
