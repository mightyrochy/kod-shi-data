import json, os, subprocess, urllib.request
from pathlib import Path
from datetime import datetime, timezone

root = Path.cwd()
out = root / 'аудит/проби/Е1-нічний-живий-20261104'
log = {'час_utc': datetime.now(timezone.utc).isoformat(), 'перевірки': []}
os.environ['NODE_PATH'] = r'C:\Users\gemini\kod-shi-test-node\node_modules'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
def api(path='', data=None):
    request = urllib.request.Request('http://127.0.0.1:1234/api/v1/models'+path,
        data=None if data is None else json.dumps(data).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=300) as r:
        value = json.load(r)
        log['перевірки'].append({'шлях':path,'запит':data,'status':r.status,'відповідь':value})
        return value

browser = subprocess.run(['node','-'], input='''const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({headless:true}); console.log(JSON.stringify({chromium:b.version(),executable:chromium.executablePath()}));await b.close();})().catch(e=>{console.error(e);process.exitCode=2});''',
    text=True, encoding='utf-8', capture_output=True)
log['chromium']={'rc':browser.returncode,'stdout':browser.stdout,'stderr':browser.stderr}
assert browser.returncode==0, browser.stderr
log['pyodide']=json.loads(Path(r'C:\Users\gemini\pyodide\pyodide-lock.json').read_text(encoding='utf-8'))['info']
try:
    models=api()['models']
    assert not any(m['loaded_instances'] for m in models), 'Чужа модель завантажена'
    for name,ctx in [('qwen/qwen3.5-9b',57344),('mamaylm-gemma-3-12b-it-v2.0',16384)]:
        result=api('/load',{'model':name,'context_length':ctx,'parallel':1,'echo_load_config':True})
        instance=result.get('instance_id')
        assert instance, result
        try:
            instances=[i for m in api()['models'] if m['key']==name for i in m['loaded_instances'] if i['id']==instance]
            assert len(instances)==1 and instances[0]['config']['context_length']==ctx and instances[0]['config']['parallel']==1, instances
        finally:
            api('/unload',{'instance_id':instance})
        print(name+': контекст '+str(ctx)+', parallel=1 підтверджено',flush=True)
finally:
    out.joinpath('підготовка.json').write_text(json.dumps(log,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print('Chromium і Pyodide готові',flush=True)
