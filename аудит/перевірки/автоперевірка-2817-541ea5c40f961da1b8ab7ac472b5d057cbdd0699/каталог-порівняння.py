import sys, os, json, contextlib, io, hashlib
from pathlib import Path
root=Path(sys.argv[1]); out=Path(sys.argv[2])
os.chdir(root/'джерела'); sys.path.insert(0,str(root/'джерела'))
import тест_живого_шляху as Т, bridge as Б, feed as Ф
Т.ПАСПОРТ_МОДЕЛІ.pop('година',None)
Т.ПАСПОРТ_МОДЕЛІ['пора']='evening'
original=Б.виклик; capture={}
def call(name,data):
    text=original(name,data)
    if name in ('паспорт','запити','від_моделі','показ'):
        capture.setdefault(name,[]).append(json.loads(text))
    return text
Б.виклик=call
data=json.loads(Path('стенд_вх.json').read_text(encoding='utf8'))
data['каталог']=Ф.каталог_на_диску('каталог_brief.xml')
data['кеш_кольорів']=str(out.parent/'кеш_живого_шляху.json')
with contextlib.redirect_stdout(io.StringIO()):
    result=Т.прогін(data,None,'conventional')
out.write_text(json.dumps(capture,ensure_ascii=False),encoding='utf8')
cards=capture['показ'][0]
print(json.dumps({'речі':[c['id'] for c in cards], 'карток':len(cards),
                  'з_фото':sum(bool(c.get('фото')) for c in cards),
                  'пора':capture['паспорт'][0]['паспорт'].get('пора'),
                  'етапів':len(result)},ensure_ascii=False))
