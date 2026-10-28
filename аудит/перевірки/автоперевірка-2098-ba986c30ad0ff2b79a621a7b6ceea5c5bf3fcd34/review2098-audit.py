"""Зіставляє первинні записи запитів із кадрами й відповідями, без моделі."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(r'C:\Users\gemini\gemini-runs\w\review-2098-ba986c30')
P = ROOT/'аудит/проби/обгортка-живий/webp'
OUT = Path(r'C:\Users\gemini\gemini-runs\review2098-evidence')
result={}
for scene in ['б1_концерт_стримано','ж1_вокал_просто_зручно']:
    model=json.loads((P/scene/'знімки/модель_виклики.json').read_text(encoding='utf-8'))['виклики']
    calls=[]
    for file in sorted((P/scene/'відповіді/обмін').glob('*.json')):
        exchange=json.loads(file.read_text(encoding='utf-8'))
        sources=[b['source'] for m in exchange['запит']['messages'] for b in m.get('content',[]) if isinstance(b,dict) and b.get('type')=='image']
        if not sources:
            continue
        index=int(file.stem)-1
        record=model[index]
        frames=record['кадри']
        assert len(sources)==len(frames)
        assert [s.get('url','base64') for s in sources]==[f['джерело'] for f in frames]
        assert record['фото_не_дійшло']==0 and record['статус']==200
        assert all(f['вихід']['тип'] in ['image/jpeg','image/png'] and f['вихід']['байтів']>0 for f in frames)
        calls.append(dict(номер=index+1,кадрів_запиту=len(sources),кадрів_журналу=len(frames),HTTP=record['статус']))
    assert calls
    result[scene]=calls
with zipfile.ZipFile(P/'ДО.zip') as archive:
    before={}
    for scene in result:
        log=archive.read(scene+'/лог.txt').decode('utf-8')
        before[scene]={'втрати_рядки':[line for line in log.splitlines() if 'кадрів не дійшло' in line or 'фото не дійшло' in line or 'HTTP 400' in line],
                       'провали':[line for line in log.splitlines() if line.startswith('  ✗')]}
    result['архів_ДО']=before
for name in ['відтворення400.json','відтворення400-ПІСЛЯ.json']:
    data=json.loads((P/name).read_text(encoding='utf-8'))
    for call in data['виклики']:
        image=P/('кадри-ДО/'+call['файл'] if name=='відтворення400.json' else call['файл'])
        assert hashlib.sha256(image.read_bytes()).hexdigest()==call['sha256']
    result[name]=data['виклики']
for rev in ['5b4f087d13d577b90520aa277df978fccecce39c','39dfa31c8412eb3fd028bfdc6898f928a9c1e264','869f9a537af609bf130ec38676bce43d1978be4f']:
    changed=subprocess.check_output(['git','diff','--name-only',rev,'HEAD','--','джерела','аудит/проби/кадр_моделі.js','аудит/проби/рв6_стенд.js','аудит/ноутбук_стенд_2'],cwd=ROOT,text=True,encoding='utf-8').splitlines()
    assert not changed,changed
    result[rev]={'змін_продукту_кадрів_транспорту':len(changed)}
text=json.dumps(result,ensure_ascii=False,indent=2)
(OUT/'первинні-докази.json').write_text(text,encoding='utf-8')
print(text)
