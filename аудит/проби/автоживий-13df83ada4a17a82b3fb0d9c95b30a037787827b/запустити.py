import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

root = Path.cwd()
out = root / 'аудит/проби/автоживий-13df83ada4a17a82b3fb0d9c95b30a037787827b'
os.environ['NODE_PATH'] = r'C:\Users\gemini\kod-shi-test-node\node_modules'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
commands = []

def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    commands.append({'команда': args, 'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    return p

models = json.load(urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=15))
(out / 'моделі_до.json').write_text(json.dumps(models, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
assert not any(m['loaded_instances'] for m in models['models'])
for key, ctx in [('qwen/qwen3.5-9b', 57344), ('mamaylm-gemma-3-12b-it-v2.0', 16384)]:
    assert any(m['key'] == key and m['max_context_length'] >= ctx for m in models['models'])
run(['git', 'merge-base', '--is-ancestor', '32736b6ea78ca066ff88cb5fd3f00dfd12e461cd', 'origin/main'])
run(['git', 'rev-parse', 'HEAD', 'origin/main'])
run(['git', '-C', '../tmp/збірка', 'rev-parse', 'HEAD'])
run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu', '--format=csv'])
run(['node', '-e', 'const {chromium}=require("playwright"); console.log(JSON.stringify({chromium:chromium.executablePath(),node:process.version,NODE_OPTIONS:process.env.NODE_OPTIONS||null}));'])
commands.append({'середовище': {k: os.environ.get(k) for k in ['NODE_PATH', 'NODE_OPTIONS', 'PYTHONPATH', 'TEMP', 'TMP', 'PYTHONUTF8', 'PYTHONIOENCODING']}, 'час_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
(out / 'передумови.json').write_text(json.dumps(commands, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
command = [sys.executable, 'аудит/проби/записати_сцену.py', '../tmp/збірка', r'C:\Users\gemini\pyodide', str(out / 'б1_концерт_стримано'), '--сцена', 'б1_концерт_стримано']
print('Запуск: ' + ' '.join(command), flush=True)
result = subprocess.run(command)
(out / 'команда_прогону.json').write_text(json.dumps({'команда': command, 'rc': result.returncode}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
raise SystemExit(result.returncode)
