"""Зберігає первинні переліки фото-оцінки з точними посиланнями на обмін."""
from pathlib import Path
import json

folder=Path(__file__).resolve().parent/'ж1_оціни_образ_6б'
records=[]
for file in sorted((folder/'VIDPOVIDI/обмін').glob('*.json')):
    exchange=json.loads(file.read_text(encoding='utf-8'))
    body=json.loads(exchange['відповідь']['body'])
    texts=[v.get('text','') for v in body.get('content',[]) if isinstance(v,dict)]
    if body.get('choices'):
        texts.append(body['choices'][0].get('message',{}).get('content',''))
    for text in texts:
        try: response=json.loads(text)
        except (ValueError,TypeError): continue
        answer=response.get('answer',response) if isinstance(response,dict) else {}
        items=answer.get('items',[]) if isinstance(answer,dict) else []
        if not items or not all(isinstance(v,dict) and 'photo' in v for v in items): continue
        records.append({'джерело':'VIDPOVIDI/обмін/'+file.name,'відповідь':response})
(folder/'оцінка_переліки.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Переліків фото-оцінки:',len(records))
