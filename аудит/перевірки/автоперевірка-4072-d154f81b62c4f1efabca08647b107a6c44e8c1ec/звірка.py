"""Звірка старого приладу на голові та п.5 на первісній голові #4041.

Аргументи: дерево #4072, тека тимчасових даних, тека доказів. Запуск із репозиторію.
"""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

дерево, тимч, докази = (Path(x).resolve() for x in sys.argv[1:])
докази.mkdir(parents=True, exist_ok=True)
прилади = дерево / 'джерела' / 'прилади'
старий = тимч / '4072-базовий.py'
шлях = 'джерела/прилади/корінь_е3_сила_правила.py'
старий.write_bytes(subprocess.check_output(['git', 'show', '8c25789f40924bb4cb6056b645d44741557342be:' + шлях]))
запуск = "import sys,runpy;sys.path.insert(0,sys.argv.pop(1));sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name='__main__')"
до = subprocess.run([sys.executable, '-W', 'ignore', '-c', запуск, str(прилади),
                     str(старий), '--корінь', str(дерево)], capture_output=True, encoding='utf-8')
(докази / 'до.txt').write_text(до.stdout + до.stderr, encoding='utf-8')
assert до.returncode == 0, до.stderr
після = (тимч / '4072-докладно.txt').read_text(encoding='utf-16')
(докази / 'після.txt').write_text(після, encoding='utf-8')
рядки = lambda т: {x.replace('\\', '/') for x in т.splitlines() if x.startswith(('п1', 'п2', 'п3', 'п4'))}
print('База:', '\n'.join(до.stdout.splitlines()[-2:]), flush=True)
print('Зникло записів пп.1–4:', len(рядки(до.stdout) - рядки(після)), flush=True)
sha = '077b9ef11be52d3f7075a07a2e104a527156adb6'
архів = subprocess.check_output(['git', 'archive', sha, 'джерела/*.py', 'джерела/показ/*.js'])
первісне = тимч / 'первісна-4041'
первісне.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(архів)) as т:
    т.extractall(первісне, filter='data')
прогін = subprocess.run([sys.executable, '-W', 'ignore', str(прилади / 'корінь_е3_сила_правила.py'),
                         '--корінь', str(первісне)], capture_output=True, encoding='utf-8')
(докази / '4041.txt').write_text(прогін.stdout + прогін.stderr, encoding='utf-8')
assert прогін.returncode == 0, прогін.stderr
sys.path.insert(0, str(прилади))
spec = importlib.util.spec_from_file_location('прилад', прилади / 'корінь_е3_сила_правила.py')
п = importlib.util.module_from_spec(spec)
spec.loader.exec_module(п)


def константи(ревізія):
    текст = subprocess.check_output(['git', 'show', ревізія + ':джерела/реєстр_константи.py']).decode('utf-8')
    продукт = п.Продукт('/неіснує', модулі={'реєстр_константи': ('джерела/реєстр_константи.py', текст)}, js={})
    return {к['ключ']: к for к in п.константи(продукт)}


старі = константи('19bdefaa4f5192b65b04c7074fccbd242c62135c')
нові = константи(sha)
очікувані = sorted(к for к in нові.keys() - старі.keys() if not п._права(нові[к]))
спіймані = [к for к in очікувані if any(x.startswith('п5') and repr(к) in x for x in прогін.stdout.splitlines())]
підсумок = {'зникло_п1_4': len(рядки(до.stdout) - рядки(після)),
            'очікувані_4041': очікувані, 'спіймані_4041': спіймані}
(докази / 'звірка.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding='utf-8')
print('4041: спіймано %d з %d' % (len(спіймані), len(очікувані)))
print('\n'.join(прогін.stdout.splitlines()[-2:]))
