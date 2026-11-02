import sys, xml.etree.ElementTree as ET, json, gzip, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
root=Path.cwd(); sys.path.insert(0,str(root/'джерела'))
import чистка_каталогу as ч
new=root.parent/'evidence2386/head-once.xml'
new.write_bytes(gzip.decompress(subprocess.check_output(['git','show','9ef27f98adc6cdc4cd1b03fdeebf6938e571e56a:каталог_повний.xml.gz'])))
ч.почистити(str(new),str(new))
for label,path in [('ДО',root.parent/'evidence2386/base.xml'),('ПІСЛЯ',new)]:
    tree=ET.parse(path).getroot(); d=ч.всі_двійники(tree)
    print(label,'двійників після штатної чистки:',len(d))
    for pair in d:
        a,b=pair[:2]
        print(json.dumps([dict(id=x.get('id'),url=x.findtext('url'),назва=x.findtext('name')) for x in (a,b)],ensure_ascii=False))
