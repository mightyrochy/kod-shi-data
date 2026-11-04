"""Читає фактичні JSON-запити з обміну, не викликаючи моделей повторно."""
from pathlib import Path
from collections import Counter
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
                pool=packet.get('pool') or []
                rows=pool if isinstance(pool,list) else [dict(zip(pool['cols'],r)) for r in pool.get('rows',[])] if isinstance(pool,dict) and 'cols' in pool else []
                measurements=[r['color_measurement'] for r in rows if isinstance(r,dict) and isinstance(r.get('color_measurement'),dict)]
                color_stats={'речей':len(rows),'color_measurement':len(measurements),
                    'usable':dict(Counter(str(m.get('usable')) for m in measurements)),
                    'джерела':dict(Counter(str(m.get('source')) for m in measurements)),
                    'color_type':dict(Counter(str(r.get('color_type')) for r in rows if isinstance(r,dict))),
                    'L_from':dict(Counter(str(r.get('L_from')) for r in rows if isinstance(r,dict))),
                    'hex_непорожніх':sum(bool(r.get('hex')) for r in rows if isinstance(r,dict))}
                records.append({'файл':'VIDPOVIDI/обмін/'+f.name,'модель':request.get('model'),
                    'case':packet.get('case'),'day':packet.get('day'),'person':person,
                    'pool_keys':packet.get('pool_keys'),'knowledge_legend':packet.get('knowledge_legend'),
                    'пул_колір_числа':color_stats,
                    'приклади_пулу':rows[:3]})
    if records:
        (folder/'дріт_витяг.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(scene,'пакетів:',len(records))
