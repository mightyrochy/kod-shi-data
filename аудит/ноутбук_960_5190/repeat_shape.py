"""Офлайн-звірка сирих повторних відповідей зі схемою їх фактичного запиту."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
root=Path(__file__).resolve().parent
result={}
for name in ('повтор_mamay_3','повтор_lapa_3'):
    checks=[]
    for path in (root/name/'requests').glob('*.json'):
        record=json.loads(path.read_text(encoding='utf-8'))
        if 'response' not in record: continue
        response=json.loads(record['response']['choices'][0]['message']['content'])
        schema=record['request']['response_format']['json_schema']['schema']
        errors=[e.message for e in Draft202012Validator(schema).iter_errors(response)]
        checks.append({'file':path.name,'rows':len(response['rows']),'schema_errors':errors})
    result[name]=checks
(root/'repeat_shape.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({n:{'responses':len(c),'rows':sum(r['rows'] for r in c),'schema_errors':sum(len(r['schema_errors']) for r in c)} for n,c in result.items()},ensure_ascii=False))
