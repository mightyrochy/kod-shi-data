from pathlib import Path
import ast,copy,json,subprocess,importlib.util
from jsonschema import Draft202012Validator
root=Path(__file__).resolve().parents[1]
source=root/'джерела/прилади/рядки_кольору_5190.py'
spec=importlib.util.spec_from_file_location('pilot991',source)
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
schema,prompt,version,codes=p.контракт(); Draft202012Validator.check_schema(schema)
v=Draft202012Validator(schema)
old=subprocess.check_output(['git','show','81f446f10523d555aa44fa8e7d24134992b80783:джерела/прилади/рядки_кольору_5190.py'],cwd=root).decode('utf-8')
new=source.read_text(encoding='utf-8')
def functions(s): return {f.name:ast.get_source_segment(s,f) for f in ast.parse(s).body if isinstance(f,ast.FunctionDef)}
before,after=functions(old),functions(new)
unchanged=['_поля','_текст','_цитата','перевірити_відповідь','відповідь_пакета','виконати','перевірити_кеш']
assert all(before[n]==after[n] for n in unchanged)
branches=schema['properties']['rows']['items']['oneOf']
assert all('properties' not in x for x in [schema['properties']['rows']['items']])
assert all(b['properties']['variants']['items']['properties']['colors']['items']['properties']['code']['enum']==branches[0]['properties']['variants']['items']['properties']['colors']['items']['properties']['code']['enum'] for b in branches[:3])
results=[]
archive=Path('C:/Users/Admin/kod-shi-wt/pilot-960/аудит/ноутбук_960_5190')
for f in sorted(archive.glob('пілот_*/requests/*.json')):
 r=json.loads(f.read_text(encoding='utf-8')); response=p.читати_json(r['response']['choices'][0]['message']['content'])
 inputs=json.loads(r['request']['messages'][1]['content'])['rows']
 for row in response['rows']:
  x=next(x for x in inputs if x['row_id']==row['row_id'])
  try: p.перевірити_відповідь({'rows':[row]},[x],codes); accepted=True
  except ValueError: accepted=False
  matches=v.is_valid({'rows':[row]}); assert matches==accepted
  results.append(dict(raw=x['raw'],accepted=accepted))
# Positive boundaries and negative cardinality/status cases, no word interpretation.
examples=[]
for label,line in zip(['single','combination','alternatives','unknown'],[line for line in prompt.splitlines() if line.startswith('{"row_id":"demo-')]):
 row=json.loads(line); raw=prompt.split('raw=')[len(examples)+1].splitlines()[0].rstrip(':'); raw=json.loads(raw)
 incoming={'row_id':row['row_id'],'raw':raw}
 assert v.is_valid({'rows':[row]}); p.перевірити_відповідь({'rows':[row]},[incoming],codes)
 assert raw not in {r['raw'] for r in p.підготувати()['rows']}
 examples.append(row)
negative=[]
for row in examples:
 mutations=[]
 for status in ['known','unknown']:
  x=copy.deepcopy(row); x['status']=status; mutations.append(x)
 for relation in ['single','combination','alternatives','unknown']:
  x=copy.deepcopy(row); x['relation']=relation; mutations.append(x)
 x=copy.deepcopy(row); x['variants']=[]; mutations.append(x)
 for x in mutations:
  incoming={'row_id':x['row_id'],'raw':next(line for line in prompt.splitlines() if line.startswith('raw=') and ('Чорний' in line if x['row_id']=='demo-single' else 'Білий' in line if x['row_id']=='demo-combination' else 'Доступно' in line if x['row_id']=='demo-alternatives' else 'Декілька' in line))[4:-1]}
  try: p.перевірити_відповідь({'rows':[x]},[incoming],codes); accepted=True
  except ValueError: accepted=False
  # Here quote strings are JSON-quoted raw, so shape and exact quotation remain unchanged.
  incoming['raw']=json.loads(incoming['raw'])
  try: p.перевірити_відповідь({'rows':[x]},[incoming],codes); accepted=True
  except ValueError: accepted=False
  assert v.is_valid({'rows':[x]})==accepted
  negative.append(accepted)
summary=dict(validator_functions_unchanged=unchanged,recorded_rows=len(results),recorded_pass=sum(r['accepted'] for r in results),recorded_rejected=sum(not r['accepted'] for r in results),examples_pass=4,shape_mutations=len(negative),live_calls=0)
(root/'work/check_fix.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
