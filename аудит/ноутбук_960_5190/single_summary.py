"""Офлайн-перевірка однорядкових доказів; без нових викликів."""
import ast,collections,importlib.util,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path('C:/Users/Admin/kod-shi-wt/fix-991/джерела/прилади/рядки_кольору_5190.py')
sys.path.insert(0,str(source.parent))
spec=importlib.util.spec_from_file_location('single_proof',source)
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def functions(text):
    return {f.name:ast.get_source_segment(text,f) for f in ast.parse(text).body if isinstance(f,ast.FunctionDef)}
old=functions(subprocess.check_output(['git','show','81f446f10523d555aa44fa8e7d24134992b80783:'+source.relative_to(source.parents[2]).as_posix()],cwd=source.parents[2]).decode('utf-8'))
current=functions(source.read_text(encoding='utf-8'))
unchanged=['_поля','_текст','_цитата','перевірити_відповідь']
assert all(old[n]==current[n] for n in unchanged)
result={'strict_validation_unchanged_from':'81f446f10523d555aa44fa8e7d24134992b80783','functions':unchanged,'runs':{}}
for label in ('mamay','lapa'):
    directory=root/('однорядковий_'+label)
    if not (directory/'звіт.json').exists():continue
    report=p.читати_json((directory/'звіт.json').read_bytes())
    p.МОДЕЛЬ=report['identity']['model']
    schema,prompt,identity,codes=p.контракт()
    assert identity==report['identity']
    manifest=p.читати_json((directory/'маніфест.json').read_bytes())
    records=[]
    statuses=collections.Counter();reasons=collections.Counter()
    for cache_path in (directory/'cache').glob('*.json'):
        cache=p.читати_json(cache_path.read_bytes())
        incoming=next(r for r in manifest['rows'] if r['row_id']==cache['row_id'])
        checked=p.перевірити_кеш(cache,incoming,identity,directory,codes,schema,prompt)
        statuses[checked['answer']['status']]+=1
        reasons[checked['answer']['unknown_reason']]+=1
    for path in (directory/'requests').glob('*.json'):
        record=p.читати_json(path.read_bytes())
        rows=p.читати_json(record['request']['messages'][1]['content'])['rows']
        assert len(rows)==1
        response=record.get('response',{})
        records.append({'file':path.name,'row_id':rows[0]['row_id'],'raw':rows[0]['raw'],'state':record['state'],
            'elapsed_s':record.get('batch_elapsed_s'),'native_id':response.get('id'),'usage':response.get('usage'),
            'finish_reasons':[c.get('finish_reason') for c in response.get('choices',[])],
            'validation':record.get('validation'),'error':record.get('error')})
    result['runs'][label]={'report':report,'source':p.читати_json((directory/'джерело.json').read_bytes()),
        'verified_cache_rows':sum(statuses.values()),'statuses':dict(statuses),'unknown_reasons':dict(reasons),
        'requests':records}
(root/'single_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({label:{'report':r['report'],'statuses':r['statuses'],'unknown_reasons':r['unknown_reasons']} for label,r in result['runs'].items()},ensure_ascii=False,indent=2))
