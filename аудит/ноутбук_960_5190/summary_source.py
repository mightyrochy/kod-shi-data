from pathlib import Path
import json,subprocess,hashlib
out=Path(__file__).resolve().parent; root=out.parents[1]
models=[]
for name in ['пілот_mamay','пілот_lapa']:
 d=out/name; summary=json.loads((d/'звіт.json').read_text(encoding='utf-8'))
 requests=[json.loads(p.read_text(encoding='utf-8')) for p in (d/'requests').glob('*.json')]
 passed=[r for r in requests if r['state']=='validated']
 rows=sum(len(json.loads(r['request']['messages'][1]['content'])['rows']) for r in passed)
 seconds=sum(r['batch_elapsed_s'] for r in passed)
 failed=[{'request_sha256':p.stem,'error':r['error'],'rows':json.loads(r['request']['messages'][1]['content'])['rows'],'finish_reason':r.get('response',{}).get('choices',[{}])[0].get('finish_reason')}
         for p in (d/'requests').glob('*.json') if (r:=json.loads(p.read_text(encoding='utf-8')))['state']=='failed']
 models.append(dict(model=summary['identity']['model'],state=summary['state'],validated_rows=rows,
  validated_batch_wall_s=seconds,amortized_validated_row_s=seconds/rows if rows else None,
  mechanical_2401_hours=(seconds/rows)*2401/3600 if rows else None,
  estimate_kind='incomplete pilot; batch wall equal share; not a validated catalogue runtime estimate',
  failures=failed,semantic_review='pending',photo_review='not_performed',runtime_applied=False))
meta=dict(source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),models=models,
 controls81=81,frozen40=40,rows97=97,occurrences119=119,admitted_occurrences=0,
 protocol_tests='8/8 pass',models_unloaded=True,proxy_stopped=True,
 claim_38_of_40=False,independent_acceptance=False,
 lapa_method='same source module/validator/schema/prompt; in-memory MODEL identifier override only; declared prompt still names MamayLM')
(out/'summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print([(m['model'],m['validated_rows'],m['amortized_validated_row_s'],m['mechanical_2401_hours']) for m in models])
