"""Повторює лише сцени, відхилені до запису через зайняті моделі, після звільнення сервера."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
plan = json.loads((OUT / 'ПЛАН.json').read_text(encoding='utf-8-sig'))
retry = [name for name in plan['scenes'] if (OUT / name).is_dir()
         and not (OUT / name / 'код.txt').exists() and not (OUT / name / 'результат.json').exists()]
os.environ.update(NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules', PYTHONUTF8='1',
                  PYTHONIOENCODING='utf-8', TEKA_FOTO_SCENY=str(ROOT.parent / 'tmp/фото_сцен'))
failed = OUT / 'невдалі_спроби'
failed.mkdir(exist_ok=True)
with (OUT / 'повтор_середовища.jsonl').open('a', encoding='utf-8') as journal:
    def write(record):
        record['час'] = datetime.now(timezone.utc).isoformat()
        journal.write(json.dumps(record, ensure_ascii=False) + '\n')
        journal.flush()
        print(json.dumps(record, ensure_ascii=False), flush=True)

    write(dict(повторити=retry, причина='сцени мають теку, але не дійшли до код.txt; первинні відмови — у план-лог.txt'))
    for name in retry:
        while True:
            with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=15) as response:
                models = json.load(response)['models']
            loaded = [m['key'] for m in models if m['loaded_instances']]
            if not loaded:
                break
            write(dict(сцена=name, чекаю_звільнення=loaded))
            time.sleep(15)
        source, target = (OUT / name).resolve(), (failed / name).resolve()
        assert source.is_relative_to(OUT) and target.is_relative_to(OUT)
        source.rename(target)
        subset = dict(plan, scenes={name: plan['scenes'][name]}, cloud={}, bad=[])
        subset_file = failed / (name + '.json')
        subset_file.write_text(json.dumps(subset, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        command = [sys.executable, str(ROOT / 'аудит/проби/записати_план.py'), str(subset_file),
                   str(ROOT.parent / 'tmp/збірка'), r'C:\Users\gemini\pyodide', str(OUT)]
        with (failed / (name + '_лог.txt')).open('w', encoding='utf-8') as log:
            rc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
        write(dict(сцена=name, команда=command, rc=rc))
