"""Читає фактичні JSON-запити з обміну, не викликаючи моделей повторно."""
from pathlib import Path
import json

OUT=Path(__file__).resolve().parent
plan=json.loads((OUT/'план.json').read_text(encoding='utf-8'))
for scene in plan['scenes']:
    folder=OUT/scene
    records=[]
    for f in sorted((folder/'VIDPOVIDI/обмін').glob('*.json')):
        exchange=json.loads(f.read_text(encoding='utf-8'))
        request=exchange.get('запит',{})
        for message in request.get('messages',[]):
            content=message.get('content','')
            texts=[content] if isinstance(content,str) else [v.get('text','') for v in content if isinstance(v,dict)]
            for text in texts:
                try: packet=json.loads(text)
                except (ValueError,TypeError): continue
                if not isinstance(packet,dict) or not ('case' in packet and 'pool' in packet): continue
                person=packet.get('person',{})
                records.append({'файл':'VIDPOVIDI/обмін/'+f.name,'модель':request.get('model'),
                    'case':packet.get('case'),'day':packet.get('day'),'person':person,
                    'pool_keys':packet.get('pool_keys'),'knowledge_legend':packet.get('knowledge_legend'),
                    'приклади_пулу':(packet.get('pool') or [])[:3] if isinstance(packet.get('pool'),list) else packet.get('pool')})
    if records:
        (folder/'дріт_витяг.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(scene,'пакетів:',len(records))
