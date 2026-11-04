import asyncio,gzip,json,pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve(); out=pathlib.Path(sys.argv[2]).resolve(); out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'джерела/прилади'))
import знімок_мосту as З
З.підготувати(str(root/'джерела'))
for name in ('палітра_її','плитка_робота'):
    path=root/'аудит/проби/знімок_входи'/f'{name}.jsonl.gz'
    records=[json.loads(line) for line in З.прочитати(str(path)).splitlines() if line.strip()]
    chosen=[r for r in records if r['ім'] in ('палітри','вибір_палітри')]
    text='\n'.join(json.dumps(r,ensure_ascii=False) for r in chosen)
    result,timing=asyncio.run(З.прогнати(text))
    (out/f'{name}.jsonl.gz').write_bytes(gzip.compress(result.encode('utf8'),mtime=0))
    rows=[json.loads(line) for line in result.splitlines()][1:]
    errors=[r for r in rows if 'помилка' in r or isinstance(r.get('результат'),dict) and r['результат'].get('помилка')]
    print(name,'записаних викликів',len(records),'палітри/вибір_палітри',len(rows),'помилок',len(errors),flush=True)
