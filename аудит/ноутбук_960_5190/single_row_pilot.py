"""Явний однорядковий повтор власника; жодного ремонту відповіді чи повтору POST."""
import datetime, importlib.util, json, pathlib, subprocess, sys, time

root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('C:/Users/Admin/kod-shi-wt/fix-991/джерела/прилади/рядки_кольору_5190.py')
sys.path.insert(0,str(source.parent))
spec=importlib.util.spec_from_file_location('single991',source)
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
model=sys.argv[1]
assert model in ('mamaylm-gemma-3-12b-it-v2.0','lapa-v0.1.3-instruct')
p.МОДЕЛЬ=model
label='mamay' if model.startswith('mamay') else 'lapa'
out=root/('однорядковий_'+label)
assert not out.exists(), 'Спроба вже має теку; автоматичний повтор заборонений'
out.mkdir()
if label=='lapa':
    prior=json.loads((root/'однорядковий_mamay/звіт.json').read_text(encoding='utf-8'))
    assert prior['state']!='completed' or prior.get('rejected_rows',0) or prior.get('unexpected_rows',0), 'Mamay пройшла: Lapa не дозволена'
history=p.попередні_спроби()
for directory in ('повтор_mamay_2','повтор_mamay_2b','повтор_mamay_3','повтор_lapa_3'):
    for path in (root/directory/'requests').glob('*.json'):
        record=p.читати_json(path.read_bytes())
        incoming=p.читати_json(record['request']['messages'][1]['content'])['rows']
        request_hash=p.відбиток(p.байти_json(record['request']))
        for row in incoming:
            history.append({**row,'attempts':[{'identity':record['identity'],'request_sha256':request_hash,'source_ref':str(path)}]})
schema,prompt,identity,codes=p.контракт()
manifest=p.походження(p.підготувати(),None)
assert len(manifest['rows'])==97 and len(manifest['occurrences'])==119
with p.Ж.відкрити(history) as ledger:
    authorization={'version':'5190-repeat-v1',
      'authorization_id':'власник-2026-10-13-один-рядок-'+label,
      'decision_ref':'Пряме повідомлення власника в поточній ноутбучній сесії Codex, 13.10.2026',
      'reason':'Повтори пілот MamayLM по одному рядку, щоб перевірити, чи проблема в змішуванні рядків пакета. Валідатор не послаблюй. Lapa — лише якщо MamayLM не пройде. Звіт — у #963.',
      'requires_all_provenance':False,
      'target_identity_sha256':p.Ж.відбиток(identity),
      'rows':{r['row_id']:sorted(a['request_sha256'] for a in ledger.попередні(r)) for r in manifest['rows'] if ledger.попередні(r)}}
    p.зберегти(out/'журнал_до.json',ledger.дані)
p.зберегти(out/'дозвіл.json',authorization)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source.parents[2],text=True).strip()
p.зберегти(out/'джерело.json',{'source_sha':sha,'batch_size':1,'model':model,'identity':identity,
    'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'validator_modified':False})
counter=0
def send(body):
    global counter
    counter+=1
    assert len(json.loads(body['messages'][1]['content'])['rows'])==1
    started=time.monotonic(); result=p.надіслати(body)
    print(f'{label}: {counter}/97, {time.monotonic()-started:.2f} с',flush=True)
    return result
try:
    result=p.виконати(manifest,out,пакет=1,транспорт=send,лише_переклад=True,дозвіл=authorization)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
except Exception as error:
    print('ЗБІЙ: '+str(error),flush=True)
    raise
finally:
    p.зберегти(out/'журнал_після.json',p.читати_json((p.Ж.тека_журналу()/'спроби.json').read_bytes()))
