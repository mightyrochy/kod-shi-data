import collections, concurrent.futures, copy, gzip, importlib.util, json, pathlib, subprocess, sys, tempfile, xml.etree.ElementTree as ET
import urllib.request, urllib.error
root = pathlib.Path(__file__).parent / 'pr2386'
out = pathlib.Path(__file__).parent / 'evidence2386'
sys.path.insert(0, str(root/'zhnyvarka'))
import складальник as s
import жнива_каталог as harvest
spec = importlib.util.spec_from_file_location('counter', root/'джерела/прилади/схема_записів_5624.py')
counter = importlib.util.module_from_spec(spec); spec.loader.exec_module(counter)
header, records = s.читати_записи(root/'каталог_записи_v1.jsonl.gz')
raw = subprocess.check_output(['git','show','cc92707d4:каталог_записи_v1.jsonl.gz'], cwd=root)
before = [json.loads(line) for line in gzip.decompress(raw).splitlines()][1:]
print('ДО, лічильник голови:', dict(counter.порахувати(before)[0]), flush=True)
print('ПІСЛЯ, лічильник голови:', dict(counter.порахувати(records)[0]), flush=True)
xml = gzip.decompress((root/'каталог_повний.xml.gz').read_bytes()).decode('utf-8')
rebuilt = s.скласти(header, records, s.кадри_маніфест.читати())
print('XML = складання v1 з маніфестом:', xml == rebuilt, flush=True)
offers = {o.get('id'):o for o in ET.fromstring(xml).iter('offer')}
print('Розбіжностей oldprice запис / справжній XML:', sum(str(r.get('стара_ціна') or '') != (offers[r['ід']].findtext('oldprice') or '') for r in records), flush=True)
with tempfile.TemporaryDirectory() as journal:
    _, repeat, stats = harvest.зібрати(journal, header, copy.deepcopy(records))
    print('Повтор застосування без нових відповідей:', repeat == records, dict(stats), flush=True)
old = {r['ід']:r for r in before}
changed = [r for r in records if r['ід'] not in old or r.get('кадри') != old[r['ід']].get('кадри')]
print('Нові / змінені галереї після продовження 8:', len(changed), flush=True)
selected=[]
for domain in ['25union.com.ua','vmma','theoriginals.com.ua']:
    candidates=[r for r in (changed if domain == 'vmma' else records) if domain in r['адреса'] and r.get('кадри')]
    step=max(1,len(candidates)//4)
    selected.extend(candidates[::step][:4])
def download(item):
    i, r=item; url=r['кадри'][0]
    result={'номер':i,'ід':r['ід'],'адреса':r['адреса'],'назва':r['назва'],'ціна':r['ціна'], 'фото':url}
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            content=response.read()
            result.update({'код':response.status,'тип':response.headers.get('Content-Type',''),'байтів':len(content)})
        if result['код'] == 200 and result['тип'].startswith('image/'):
            file=out/f'photo-{i:02d}.img';file.write_bytes(content);result['файл']=str(file)
        return result
    except Exception as e:
        result['помилка']=str(e)
        if isinstance(e, urllib.error.HTTPError): result['код']=e.code
        return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    photos=list(pool.map(download, enumerate(selected)))
(out/'photos.json').write_text(json.dumps(photos,ensure_ascii=False,indent=2),encoding='utf-8')
for p in photos:
    print('Фото:',p['номер'],p['ід'],p.get('код',p.get('помилка')),p.get('тип'),p.get('байтів'),flush=True)
