"""Докази порушення цитат: точний raw, quote і можливий сусідній raw."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent
result={}
for name in ('повтор_mamay_3','повтор_lapa_3'):
    problems=[]
    for path in (root/name/'requests').glob('*.json'):
        record=json.loads(path.read_text(encoding='utf-8'))
        if record['state']!='failed' or 'response' not in record: continue
        incoming=json.loads(record['request']['messages'][1]['content'])['rows']
        rows=json.loads(record['response']['choices'][0]['message']['content'])['rows']
        raws={r['row_id']:r['raw'] for r in incoming}
        for row in rows:
            raw=raws[row['row_id']]
            for variant in row['variants']:
                for kind,quote,parent in [('variant',variant['quote'],raw)]+[('colour',c['quote'],variant['quote']) for c in variant['colors']]:
                    if quote not in parent:
                        problems.append({'row_id':row['row_id'],'raw':raw,'kind':kind,'quote':quote,'parent':parent,
                                         'other_raws_containing_quote':[r for r in incoming if r['row_id']!=row['row_id'] and quote in r['raw']]})
    result[name]=problems
(root/'repeat_quote_errors.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
