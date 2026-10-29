"""Знімає точну збірку у Chromium з фото та заглушками моделей."""
import datetime
import json
import os
import pathlib
import subprocess
import sys

тека = pathlib.Path(__file__).resolve().parent
корінь = pathlib.Path(sys.argv[1]).resolve()
сайт = pathlib.Path(sys.argv[2]).resolve()
знімки = pathlib.Path(sys.argv[3]).resolve()
знімки.mkdir(parents=True, exist_ok=True)
оточення = {к: в for к, в in os.environ.items()
            if not к.startswith(('MODEL', 'ZHYVA', 'REPLAY', 'COMFY'))}
оточення.update(NODE_PATH=r'C:/Users/gemini/kod-shi-test-node/node_modules',
    CHROMIUM=r'C:/Program Files/Google/Chrome/Application/chrome.exe',
    ZNIMKY=str(знімки), ZVIT_OUT=str(знімки / 'вердикти.txt'),
    FOTO='1', OTSINKA='0', FORMY='0', PYTHONUTF8='1')
команда = ['node', str(корінь / 'аудит/проби/рв6_стенд.js'),
           'http://127.0.0.1:8765', str(сайт), r'C:/Users/gemini/pyodide', '3']
with (тека / 'знімки.log').open('w', encoding='utf-8') as журнал:
    результат = subprocess.run(команда, cwd=корінь, env=оточення,
                              stdout=журнал, stderr=subprocess.STDOUT)
факт = dict(код=результат.returncode, команда=команда, моделі='заглушки',
            FOTO='1', знімки=str(знімки), utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(тека / 'знімки.json').write_text(json.dumps(факт, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(факт, ensure_ascii=False))
sys.exit(результат.returncode)
