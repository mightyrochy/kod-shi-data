import json, pathlib, importlib.util, copy
from jsonschema import Draft202012Validator
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pilot991',root/'джерела/прилади/рядки_кольору_5190.py')
pilot=importlib.util.module_from_spec(spec); spec.loader.exec_module(pilot)
schema,_,_,codes=pilot.контракт()
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema)
out=root/'аудит/ноутбук_960_5190'
results=[]
for folder in ['пілот_mamay','пілот_lapa']:
 for path in sorted((out/folder/'requests').glob('*.json')):
  record=json.loads(path.read_text(encoding='utf-8'))
  inputs=json.loads(record['request']['messages'][1]['content'])['rows']
  answer=pilot.читати_json(record['response']['choices'][0]['message']['content'])
  schema_errors=[e.message for e in validator.iter_errors(answer)]
  raws={r['row_id']:r['raw'] for r in inputs}
  rows=[]
  for row in answer['rows']:
   incoming=next(r for r in inputs if r['row_id']==row['row_id'])
   try: pilot.перевірити_відповідь({'rows':[row]},[incoming],codes); error=None
   except Exception as e: error=str(e)
   quote_errors=[]
   for variant in row['variants']:
    try: pilot._цитата(variant['quote'],incoming['raw'])
    except Exception as e: quote_errors.append(str(e))
    for color in variant['colors']:
     try: pilot._цитата(color['quote'],variant['quote'])
     except Exception as e: quote_errors.append(str(e))
   rows.append(dict(raw=incoming['raw'],row_id=row['row_id'],relation=row['relation'],status=row['status'],
     variants=len(row['variants']),colors_per_variant=[len(v['colors']) for v in row['variants']],
     schema_valid=validator.is_valid({'rows':[row]}),validator_error=error,quote_errors=quote_errors))
  results.append(dict(model=record['identity']['model'],request=path.name,finish=record['response']['choices'][0]['finish_reason'],
    schema_errors=schema_errors,rows=rows))
# Diagnostic in-memory schema only. No production edits or generated-answer repair.
stronger=copy.deepcopy(schema)
item=stronger['properties']['rows']['items']
def when(condition,body): return {'if':{'properties':condition,'required':list(condition)},'then':body}
item['allOf']=[
 when({'status':{'const':'unknown'}},{'properties':{'relation':{'const':'unknown'},'variants':{'maxItems':0},'unknown_reason':{'enum':['ambiguous','no_colour','insufficient_context']}}}),
 when({'status':{'const':'known'}},{'properties':{'relation':{'enum':['single','combination','alternatives']},'variants':{'minItems':1},'unknown_reason':{'const':'none'}}}),
 when({'relation':{'const':'single'}},{'properties':{'variants':{'minItems':1,'maxItems':1,'items':{'properties':{'colors':{'minItems':1,'maxItems':1}}}}}}),
 when({'relation':{'const':'combination'}},{'properties':{'variants':{'minItems':1,'maxItems':1,'items':{'properties':{'colors':{'minItems':2}}}}}}),
 when({'relation':{'const':'alternatives'}},{'properties':{'variants':{'minItems':2}}})]
Draft202012Validator.check_schema(stronger)
enhanced=Draft202012Validator(stronger)
for batch in results:
 record=json.loads((out/('пілот_mamay' if batch['model'].startswith('mamay') else 'пілот_lapa')/'requests'/batch['request']).read_text(encoding='utf-8'))
 answer=json.loads(record['response']['choices'][0]['message']['content'])
 for result,row in zip(batch['rows'],answer['rows']): result['diagnostic_stronger_schema_valid']=enhanced.is_valid({'rows':[row]})
summary=dict(source_sha='81f446f10523d555aa44fa8e7d24134992b80783',live_calls=0,production_changes=0,
 results=results,counts={model:{'rows':sum(len(b['rows']) for b in results if b['model']==model),
 'schema_pass':sum(r['schema_valid'] for b in results if b['model']==model for r in b['rows']),
 'validator_pass':sum(r['validator_error'] is None for b in results if b['model']==model for r in b['rows']),
 'quote_errors':sum(len(r['quote_errors']) for b in results if b['model']==model for r in b['rows'])} for model in {b['model'] for b in results}})
(out/'diagnostic_991.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary['counts'],ensure_ascii=False,indent=2))
print('Invalid rows:',[(r['raw'],r['relation'],r['variants'],r['colors_per_variant']) for b in results for r in b['rows'] if r['validator_error']])
print('Stronger schema agrees with cardinality validator:',all(r['diagnostic_stronger_schema_valid']==(r['validator_error'] is None) for b in results for r in b['rows']))
