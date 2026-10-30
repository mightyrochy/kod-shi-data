import sys, subprocess, gzip, json, collections
from pathlib import Path
import xml.etree.ElementTree as ET
tree = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(tree / 'джерела'))
import чистка_каталогу as ч
sys.path.insert(0, str(tree / 'zhnyvarka'))
import складальник as с
out=Path(sys.argv[2]).resolve()
clean=tree/'джерела/каталог_повний.xml'
root=ET.parse(clean).getroot()
for a,b in ч.всі_двійники(root):
    print('ЛИШИВСЯ ДВІЙНИК', json.dumps([dict(id=o.get('id'),url=o.findtext('url'),name=o.findtext('name'),picture=o.findtext('picture')) for o in [a,b]], ensure_ascii=False), flush=True)
_, records=с.читати_записи()
missing=[r for r in records if r.get('ціна_стара') and not r.get('стара_ціна')]
different=[r for r in records if r.get('ціна_стара') and r.get('стара_ціна') and float(r['ціна_стара'])!=float(r['стара_ціна'])]
print('Стара ціна є, oldprice відсутній',len(missing),'oldprice застарів',len(different), flush=True)
for r in missing[:1]+different[:1]:
    print('СТАРА ЦІНА',json.dumps({k:r.get(k) for k in ['ід','адреса','ціна','ціна_стара','стара_ціна']},ensure_ascii=False),'oldprice у XML',ET.fromstring(с.офер_xml(r)).findtext('oldprice'),flush=True)
base='560fa388e75fe10abe27145644d12d1be2266ab5'
raw=gzip.decompress(subprocess.check_output(['git','show',base+':каталог_повний.xml.gz'],cwd=tree))
baseline=out/'база.xml'
baseline.write_bytes(raw)
try:
    result=ч.забезпечити_чистим(_шлях=str(baseline))
    print('БАЗА чистка успішна',json.dumps(result,ensure_ascii=False,default=str),flush=True)
except SystemExit as e:
    print('БАЗА чистка відмовила',str(e),flush=True)
