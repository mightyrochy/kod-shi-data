import collections, csv, gzip, io, json, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd()
sys.path.insert(0,str(root/'zhnyvarka'))
from жнива_каталог import адреса, чужа_мова
def read(ref):
    raw=subprocess.check_output(['git','show',ref+':каталог_записи_v1.jsonl.gz'])
    return [json.loads(x) for x in gzip.decompress(raw).splitlines()]
old=read('560fa388e75fe10abe27145644d12d1be2266ab5'); new=read('9ef27f98adc6cdc4cd1b03fdeebf6938e571e56a')
def params(r): return {p[0]:p[1] for p in r['параметри']}
for tag, records in [('ДО',old),('ПІСЛЯ',new)]:
    rows=records[1:]; urls=[r['адреса'] for r in rows]
    dom=lambda r:r['адреса'].split('/')[2].removeprefix('www.')
    stores=list(csv.DictReader((x for x in (root/'zhnyvarka/магазини.tsv').read_text(encoding='utf8').splitlines() if not x.startswith('#')),delimiter='\t'))
    enabled=[s['домен'].removeprefix('www.') for s in stores if s['стан']=='увімкнено']
    count=collections.Counter(dom(r) for r in rows)
    print(tag,json.dumps(dict(записів=len(rows),повторів_точних=len(urls)-len(set(urls)),повторів_нормалізованих=len(urls)-len(set(map(адреса,urls))),ru=sum('/ru/' in u for u in urls),en=sum('/en/' in u for u in urls),theoriginals=count['theoriginals.com.ua'],склад_theoriginals=sum(dom(r)=='theoriginals.com.ua' and any(p[0] in ('Склад','склад') and p[1] for p in r['параметри']) for r in rows),увімкнених_нуль=[s for s in enabled if not count[s]],зі_складом=sum(any(p[0] in ('склад','Склад') and p[1] for p in r['параметри']) for r in rows)),ensure_ascii=False))
    cats=ET.fromstring(records[0]['початок']+records[0]['кінець']).findall('.//category')
    cats={c.get('id'):c.text for c in cats}
    print(tag,'категорії',collections.Counter(cats.get(r['категорія']) for r in rows).most_common(6))
print('Втрачених нормалізованих адрес:',len(set(адреса(r['адреса']) for r in old[1:])-set(адреса(r['адреса']) for r in new[1:])))
print('Втрачених точних адрес:',len(set(r['адреса'] for r in old[1:])-set(r['адреса'] for r in new[1:])))
olds={r['адреса']:r for r in old[1:]}; news={r['адреса']:r for r in new[1:]}
print('Приклад повтору:',next((u for u,c in collections.Counter(r['адреса'] for r in new[1:]).items() if c>1),None))
byid={r['ід']:r for r in new[1:]}
for field in ('опис','кадри','назва'):
    lost=[r for r in old[1:] if r.get(field) and not byid.get(r['ід'],{}).get(field)]
    print('Втрачено поле',field,len(lost),[r['адреса'] for r in lost[:2]])
for field in ('слот','стать','Колір','розміри','склад','свотч_hex','мова_опису'):
    lost=[r for r in old[1:] if params(r).get(field) and not params(byid.get(r['ід'],{'параметри':[]})).get(field)]
    print('Втрачено параметр',field,len(lost),[r['адреса'] for r in lost[:2]])
oldids={r['ід'] for r in old[1:]}
added=[r for r in new[1:] if r['ід'] not in oldids]
print('Нових записів:',len(added),'без категорії:',sum(cats.get(r['категорія']) in ('без категорії','без розділу') for r in added),'без слота:',sum(not params(r).get('слот') for r in added))
print('Зразки нових:',json.dumps([dict(url=r['адреса'],назва=r['назва'],категорія=cats.get(r['категорія']),слот=params(r).get('слот'),стать=params(r).get('стать')) for r in added[:5]],ensure_ascii=False))
with gzip.open(root/'каталог_повний.xml.gz','rb') as f: xml=ET.parse(f)
offers=xml.findall('.//offer'); print('XML речей:',len(offers),'ід повторів:',len(offers)-len({o.get('id') for o in offers}))
for tag,rows in [('ДО',old[1:]),('ПІСЛЯ',new[1:])]:
    c=collections.Counter(адреса(r['адреса']) for r in rows)
    print(tag,'повторів груп:',sum(v>1 for v in c.values()))
states=list(csv.DictReader((root/'аудит/жнива_5_3/повний-обхід_стан.tsv').open(encoding='utf8'),delimiter='\t'))
print('Станів:',len(states),'адрес:',sum(int(x['адрес']) for x in states),'готово:',sum(int(x['готово']) for x in states))
states_enabled=[x for x in states if x['домен']!='theoriginals.com.ua']
print('Увімкнених станів:',len(states_enabled),'адрес:',sum(int(x['адрес']) for x in states_enabled),'готово:',sum(int(x['готово']) for x in states_enabled))
print('Незавершені без коду причини:',json.dumps([x for x in states if int(x['лишилось']) and not x['причина_код']],ensure_ascii=False))
