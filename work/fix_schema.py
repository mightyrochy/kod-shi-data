from pathlib import Path
import json,copy
root=Path(__file__).resolve().parents[1]
p=root/'джерела/прилади/рядки_5190/відповідь.schema.json'
s=json.loads(p.read_text(encoding='utf-8'))
base=s['properties']['rows']['items']
branches=[]
for relation in ['single','combination','alternatives','unknown']:
 branch=copy.deepcopy(base); props=branch['properties']
 props['status']={'const':'unknown' if relation=='unknown' else 'known'}
 props['relation']={'const':relation}
 props['unknown_reason']={'enum':['ambiguous','no_colour','insufficient_context']} if relation=='unknown' else {'const':'none'}
 variants=props['variants']
 if relation=='unknown':
  props['variants']={'type':'array','minItems':0,'maxItems':0,'items':{'type':'object','additionalProperties':False}}
 else:
  variants['minItems']=2 if relation=='alternatives' else 1
  if relation!='alternatives': variants['maxItems']=1
  colors=variants['items']['properties']['colors']
  if relation=='single': colors['maxItems']=1
  elif relation=='combination': colors['minItems']=2
 branches.append(branch)
s['properties']['rows']['items']={'oneOf':branches}
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
