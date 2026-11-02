import json, os, pathlib, platform, shutil, socket, subprocess, urllib.request
from datetime import datetime, timezone

repo = pathlib.Path(r'C:\Users\gemini\gemini-runs\w\20261030-173120-b3f17293e57f\repo')
out = repo / 'аудит/проби/автоживий-1c96595b8da30f14c90e84054b024d1aaab0e634'
build = pathlib.Path(os.environ['TEMP']) / 'збірка'
result = {'час_utc': datetime.now(timezone.utc).isoformat(), 'система': platform.platform(),
          'середовище': {k: os.environ.get(k) for k in ['NODE_OPTIONS','PYTHONPATH','NODE_PATH','PYTHONUTF8','PYTHONIOENCODING','TEMP']},
          'контексти_проксі': {'qwen/qwen3.5-9b': 57344, 'mamaylm-gemma-3-12b-it-v2.0': 16384}, 'команди': []}
def run(args, cwd=repo):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    result['команди'].append({'команда':args, 'rc':r.returncode, 'stdout':r.stdout, 'stderr':r.stderr})
    return r
run(['git','merge-base','--is-ancestor','1ad12ec380d1ece6838231c132828c4a34e30227','origin/main'])
run(['git','rev-parse','HEAD','origin/main'])
run(['git','rev-parse','HEAD'], build)
run(['node','--version'])
run(['python','--version'])
run(['node','-e',"const {chromium}=require('playwright'); const fs=require('fs'); console.log(JSON.stringify({playwright:require('playwright/package.json').version,chromium:chromium.executablePath(),exists:fs.existsSync(chromium.executablePath())}))"])
gpu = shutil.which('nvidia-smi')
if gpu:
    run([gpu,'--query-gpu=name,memory.used,memory.total,utilization.gpu','--format=csv'])
else:
    result['nvidia-smi'] = 'Команди немає у PATH; зайнятість моделей перевірено через REST API.'
url = 'http://127.0.0.1:1234/api/v1/models'
with urllib.request.urlopen(url, timeout=30) as r:
    models = json.load(r)
    result['сервер'] = {'url':url,'status':r.status,'відповідь':models}
for port in [1235]:
    with socket.socket() as s:
        s.bind(('127.0.0.1',port))
    result[f'порт_{port}'] = 'вільний'
result['штамп_build.txt'] = (build/'build.txt').read_text(encoding='utf-8').strip()
result['кеш_Pyodide'] = str(pathlib.Path.home()/'pyodide')
(out/'передстарт.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(r['rc']==0 for r in result['команди']), 'Помилка перевірки середовища'
assert not any(m['loaded_instances'] for m in models['models']), 'Сервер тримає чужу модель'
for name, ctx in result['контексти_проксі'].items():
    assert any(m['key']==name and m['max_context_length']>=ctx for m in models['models']), name
print('Передстарт пройдено; обидві моделі доступні, екземплярів немає; порт 1235 вільний.')
