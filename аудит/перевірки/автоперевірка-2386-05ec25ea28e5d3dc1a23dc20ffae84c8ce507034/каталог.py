import sys, subprocess, gzip, json, io, collections, csv
from pathlib import Path
tree = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(tree / 'zhnyvarka'))
import складальник as с
from жнива_каталог import адреса, перетворити
base = subprocess.check_output(['git', 'merge-base', '8c0361434e0a3f3934f45fb54a8c2d315a31aadb', '05ec25ea28e5d3dc1a23dc20ffae84c8ce507034'], cwd=tree, text=True).strip()
def old_blob(name):
    return subprocess.check_output(['git', 'show', base + ':' + name], cwd=tree)
def rows(data):
    return [json.loads(x) for x in gzip.decompress(data).splitlines()]
old = rows(old_blob('каталог_записи_v1.jsonl.gz'))[1:]
head = rows((tree / 'каталог_записи_v1.jsonl.gz').read_bytes())
header, new = head[0], head[1:]
print('БАЗА', base)
def params(r): return {p[0]: p[1] for p in r['параметри']}
for label, rs in [('ДО', old), ('ПІСЛЯ', new)]:
    urls = collections.Counter(адреса(r['адреса']) for r in rs)
    print(label, json.dumps(dict(записів=len(rs), повторів=sum(v-1 for v in urls.values()), склад=sum(bool(params(r).get('Склад') or params(r).get('склад')) for r in rs), опис=sum(bool(r.get('опис')) for r in rs), стара_ціна=sum(bool(r.get('стара_ціна')) for r in rs), ціна_стара=sum(bool(r.get('ціна_стара')) for r in rs), theoriginals=sum('theoriginals.com.ua' in r['адреса'] for r in rs)), ensure_ascii=False))
print('Втрачених нормалізованих адрес', len({адреса(r['адреса']) for r in old} - {адреса(r['адреса']) for r in new}))
byid = {r['ід']:r for r in new}
lost_comp = [r for r in old if r['ід'] in byid and (params(r).get('Склад') or params(r).get('склад')) and not (params(byid[r['ід']]).get('Склад') or params(byid[r['ід']]).get('склад'))]
lost_desc = [r for r in old if r['ід'] in byid and r.get('опис') and not byid[r['ід']].get('опис')]
print('Втрачено склад', len(lost_comp), 'опис', len(lost_desc))
print('Зразки втраченого опису', json.dumps([dict(id=r['ід'], url=r['адреса'], опис=r['опис'][:160]) for r in lost_desc[:3]], ensure_ascii=False))
import кадри_маніфест
xml = gzip.decompress((tree / 'каталог_повний.xml.gz').read_bytes()).decode('utf-8')
generated = с.скласти(header, new, кадри_маніфест.читати())
print('XML збігається зі складом v1 і маніфестом', generated == xml)
import xml.etree.ElementTree as ET
root = ET.fromstring(xml)
offers = root.findall('.//offer')
print('XML оферів',len(offers),'унікальних ід',len({o.get('id') for o in offers}))
reg = list(csv.DictReader((l for l in (tree/'zhnyvarka/магазини.tsv').read_text(encoding='utf-8').splitlines() if not l.startswith('#')),delimiter='\t'))
enabled={r['домен'] for r in reg if r['стан']=='увімкнено'}
states=list(csv.DictReader((tree/'аудит/жнива_5_3/повний-обхід_стан.tsv').open(encoding='utf-8'), delimiter='\t'))
states=[r for r in states if r['домен'] in enabled]
print('Стани увімкнених',len(states),'адрес',sum(int(r['адрес']) for r in states),'готово',sum(int(r['готово']) for r in states),'лишилось',sum(int(r['лишилось']) for r in states))
print('Незавершені без причини',json.dumps([r for r in states if int(r['лишилось']) and not r['причина_код']],ensure_ascii=False))
queue=tree/'аудит/жнива_5_3/черга_галерей_2026-10-30.tsv.gz'
with gzip.open(queue,'rt',encoding='utf-8') as f:
    q=list(csv.DictReader(f,delimiter='\t'))
print('Черга: стовпці',list(q[0]),'рядків',len(q),'лічба причин',dict(collections.Counter(r.get('стан',r.get('причина','')) for r in q)))
print('Приклад черги',json.dumps(q[0],ensure_ascii=False))
sample = next(r for r in new if r.get('ціна_стара'))
fragment=с.офер_xml(sample)
print('ПРИКЛАД стара ціна',json.dumps({k:sample.get(k) for k in ['ід','адреса','ціна','ціна_стара','стара_ціна']},ensure_ascii=False),'XML oldprice', '<oldprice>' in fragment)
