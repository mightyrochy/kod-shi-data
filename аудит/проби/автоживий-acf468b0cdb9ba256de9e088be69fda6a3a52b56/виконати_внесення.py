"""Записує сцену пошкоджених полів; чекає дочірній записувач до завершення."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
env=dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
         NODE_PATH='C:/Users/gemini/kod-shi-test-node/node_modules')
env['NODE_OPTIONS']=env.get('NODE_OPTIONS','')+' --require "'+(OUT/'збій_перед_збиранням.cjs').as_posix()+'"'
cmd=[sys.executable,str(ROOT/'аудит/проби/записати_сцену.py'),str(ROOT.parent/'tmp/live'),
     'C:/Users/gemini/pyodide',str(OUT/'ж7_збій_правил_без_підборів'),'--сцена','ж7_збій_правил_без_підборів']
meta={'час_utc':datetime.now(timezone.utc).isoformat(),'команда':cmd,
      'оточення':{k:env.get(k) for k in ('NODE_OPTIONS','PYTHONPATH','NODE_PATH')},
      'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (OUT/'внести_збій.cjs',OUT/'збій_перед_збиранням.cjs',ROOT/'аудит/проби/рв6_стенд.js')},
      'підготовка':'Попередня команда PowerShell відхилена парсером до старту сцени; повтору сцени не було.',
      'метод':'Пошкодження даних у пам’яті; очікувані відмови в окремому обміні; потім цілий каталог.'}
(OUT/'внесення_середовище.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def note(text):
    line=datetime.now(timezone.utc).isoformat()+' '+text
    with (OUT/'done.txt').open('a',encoding='utf-8') as f:f.write(line+'\n')
    print(line,flush=True)
note('КОМАНДА: '+subprocess.list2cmdline(cmd))
with (OUT/'ж7_запуск.txt').open('w',encoding='utf-8') as log:
    rc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
note('ж7_збій_правил_без_підборів: код записувача='+str(rc))
raise SystemExit(rc)
