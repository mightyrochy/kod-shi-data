"""Відтворюваний знімок доступності середовища без секретів."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import urllib.request

тека = Path(__file__).parent
команди = [
 ['git', 'merge-base', '--is-ancestor', '1b77b2048ad1896b660c1f562a32145847f06563', 'origin/main'],
 ['git', 'rev-parse', 'HEAD', 'origin/main'],
 ['git', 'ls-remote', 'origin', 'refs/heads/gemini/автоживий-263404595a84dcfd369ba67ff7a0c3e471897034'],
 ['git', 'diff', '--name-only', '1b77b2048ad1896b660c1f562a32145847f06563', '--',
  'аудит/проби/рв6_стенд.js', 'аудит/проби/записати_сцену.py',
  'аудит/ноутбук_стенд_2/проксі_почергове.js', 'джерела/міст_помічниця.py'],
 ['node', '--version'], ['node', '-e', "console.log(require('playwright/package.json').version);console.log(require('playwright').chromium.executablePath())"],
 ['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader']]
дані = {'час_utc': datetime.now(timezone.utc).isoformat(), 'канал': 'останній рядок відповіді обгортці',
 'збірка': '1b77b2048ad1896b660c1f562a32145847f06563',
 'код_штампа': '263404595a84dcfd369ba67ff7a0c3e471897034',
 'змінні': {к: os.environ.get(к) for к in ['NODE_OPTIONS','PYTHONPATH','NODE_PATH','TEMP','TMP']}, 'команди': []}
for команда in команди:
    р = subprocess.run(команда, capture_output=True, encoding='utf-8')
    дані['команди'].append({'команда': команда, 'rc': р.returncode, 'stdout': р.stdout, 'stderr': р.stderr})
with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=10) as р:
    моделі = json.load(р)
дані['моделі'] = [м for м in моделі['models'] if м['key'] in ['qwen/qwen3.5-9b','mamaylm-gemma-3-12b-it-v2.0']]
(тека / 'СЕРЕДОВИЩЕ.json').write_text(json.dumps(дані, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
print('Середовище збережено; кодів команд:', [к['rc'] for к in дані['команди']])
