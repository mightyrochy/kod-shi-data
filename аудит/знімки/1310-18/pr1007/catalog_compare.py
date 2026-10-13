import sys,json,hashlib,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
if sys.argv[1]=='before':sys.path.insert(0,'/workspace/reasons4390-evidence/before-modules')
import bridge as B,чистка_каталогу as C,feed as F
print('catalog',C.забезпечити_чистим('каталог_повний.xml'),file=sys.stderr)
d=json.load(open('стенд_вх.json'));d.update(каталог='каталог_повний.xml',варіантів=1,ліміт_фото=0)
d['сценарій']=dict(нагода='робота',місце='офіс',година=9,темп_c=18,дрес_код='business_casual',мета='експресія',мета_слова='  “хочу уваги. K-IO-02 (цитата)”\n'+('цитата '*25))
r=json.loads(B.виклик('запити',json.dumps(d,ensure_ascii=False)))
print(json.dumps(r,ensure_ascii=False,indent=2,default=str))
