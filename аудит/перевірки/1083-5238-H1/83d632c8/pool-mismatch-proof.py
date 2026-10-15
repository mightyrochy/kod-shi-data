import pathlib,json,hashlib,collections
p=pathlib.Path('/dev/shm/live5238'); q=pathlib.Path('/dev/shm/qa5238-r3')
paths=[p/'recorded/аудит/живі_1510_А/07_ж2_корпоратив_виділитися/вердикти.txt',q/'before-07/вердикти.txt',q/'after-07/вердикти.txt']
results=[];pools=[]
for label,path in zip(['записаний_LIVE8d','актуальний_ДО_b02','ПІСЛЯ83'],paths):
 x=json.loads(path.read_text());v=next(v for v in x['прогони'][0]['вердикти'] if str(v['рука'])=='1');c=v['етапи']['виклики'][0];pool=json.loads(c['запит']['текст'])['pool'];pools.append(pool)
 results.append(dict(джерело=label,path=str(path),file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),assembly_raw_sha256=hashlib.sha256(c['відповідь_сира'].encode()).hexdigest(),pool_count=len(pool),valid_outfits=c['образів'],first_outfit_items=len(c['образи_кроку'][0]['ід']),invalid_pairs=sum(len(y.get('невірні_пари',[])) for y in c['розбір_блоків'].get('невідомі_в_образах',[]))))
sign=lambda v:json.dumps({k:x for k,x in v.items() if k!='n'},ensure_ascii=False,sort_keys=True)
a,b=[collections.Counter(sign(x) for x in pool) for pool in pools[:2]]
out=dict(SHA='83d632c8a756cad5e882bf5a97829b35c08e42c7',tree='630526ee6b3fd13d2bcf73c99b07bc24ab0a96c8',стан='НЕВИМІРЯНО: replay має іншу адресу речей до вибору H1; це не доказ ефекту виправлення',same_response=results[0]['assembly_raw_sha256']==results[1]['assembly_raw_sha256'],shared_pool_fact_records_without_number=sum((a&b).values()),pool_names_equal=collections.Counter(x['name'] for x in pools[0])==collections.Counter(x['name'] for x in pools[1]),виміри=results,модельних_нових_викликів=0)
(p/'pool-mismatch-proof.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
