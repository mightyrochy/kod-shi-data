# -*- coding: utf-8 -*-
"""Порівнює рядки приладу на тих самих записах і тотожних збережених виходах стенда.

Це перевірка незмінності рішень, не заміна браузерного виміру часу.
"""
import json
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

from виміряти import ВХІД, ДО, КОРІНЬ, НІЧНІ, ПРИЛАД, ПЯТЬ, ТИМЧАСОВА, видалити


def виконати():
    звіт = Path(__file__).resolve().parent
    ТИМЧАСОВА.mkdir(parents=True, exist_ok=True)
    (ТИМЧАСОВА / 'before.js').write_bytes(subprocess.check_output(
        ['git', 'show', ДО + ':аудит/проби/нова_база.js'], cwd=КОРІНЬ))
    main = json.loads((звіт / 'вимір.json').read_text(encoding='utf-8'))['main']
    попередні = звіт / 'тотожні_рішення.json'
    if попередні.exists() and not all(р.get('main') == main for р in json.loads(попередні.read_text(encoding='utf-8'))):
        with zipfile.ZipFile(звіт / 'порівняння-origin-main.zip', 'w', zipfile.ZIP_DEFLATED) as архів:
            for файл in list(звіт.glob('тотожний-*')) + [попередні]:
                if файл.is_file():
                    архів.write(файл, файл.name)
    обгортка = ТИМЧАСОВА / 'same-output.cjs'
    обгортка.write_text("""const fs = require('fs'), path = require('path'), Module = require('module'), zlib = require('zlib');
const [source, original, input, root, capture, main] = process.argv.slice(2);
const m = new Module(original, module);
m.filename = original; m.paths = Module._nodeModulePaths(path.dirname(original));
m._compile(fs.readFileSync(source, 'utf8'), original);
const saved = JSON.parse(zlib.gunzipSync(fs.readFileSync(capture)));
process.exitCode = m.exports.виконати([input, '--main', main], root,
  {відтворити: (folder) => saved[path.basename(folder)]});
""", encoding='utf-8')
    збережені, джерела = {}, {}
    файли = list(звіт.glob('ДО-*-стенд.json.gz')) + list(звіт.glob('ПІСЛЯ-*-стенд.json.gz')) + sorted(звіт.glob('повний-*-стенд.json.gz')) + list(звіт.glob('дознімок-стенд.json.gz'))
    for файл in файли:
        for сцена, вихід in json.loads(gzip.decompress(файл.read_bytes())).items():
            if сцена in ПЯТЬ:
                збережені[сцена] = вихід
                джерела[сцена] = {'файл': файл.name, 'sha256': hashlib.sha256(файл.read_bytes()).hexdigest()}
    if set(збережені) != set(ПЯТЬ):
        raise ValueError('Нема збереженого виходу стенда: ' + ', '.join(set(ПЯТЬ) - set(збережені)))
    знімок = звіт / 'тотожний-стенд.json.gz'
    знімок.write_bytes(gzip.compress(json.dumps(збережені, ensure_ascii=False).encode('utf-8')))
    (звіт / 'тотожний-стенд-джерела.json').write_text(json.dumps(джерела, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    дані = []
    for сцена in ПЯТЬ:
        результати = []
        for назва, код in [('ДО', ТИМЧАСОВА / 'before.js'), ('ПІСЛЯ', ПРИЛАД)]:
            тека = ТИМЧАСОВА / ('тотожний-' + назва + '-' + сцена)
            if тека.exists():
                видалити(тека, ТИМЧАСОВА)
            тека.mkdir()
            shutil.copytree(ВХІД / сцена, тека / сцена)
            було = {ф.resolve() for ф in НІЧНІ.rglob('*')}
            початок = time.perf_counter()
            try:
                р = subprocess.run(['node', str(обгортка), str(код), str(ПРИЛАД), str(тека),
                                    str(КОРІНЬ), str(знімок), main], cwd=КОРІНЬ,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
                секунд = time.perf_counter() - початок
                (звіт / f'тотожний-{назва}-{сцена}.log').write_bytes(р.stdout)
                рядки = (тека / 'НОВА_БАЗА.md').read_text(encoding='utf-8').replace(
                    os.path.relpath(тека, КОРІНЬ), '<вхід>')
                (звіт / f'тотожний-{назва}-{сцена}-НОВА_БАЗА.md').write_text(рядки, encoding='utf-8')
                результати.append({'код': ДО if назва == 'ДО' else 'нова_база.js у цьому PR',
                                  'rc': р.returncode, 'секунд': секунд, 'рядки': рядки})
            finally:
                створено = {ф.resolve() for ф in НІЧНІ.rglob('*')} - було
                for ф in sorted(створено, key=lambda ф: len(ф.parts)):
                    if ф.is_dir() and ф.exists():
                        видалити(ф, НІЧНІ)
        однаково = (результати[0]['rc'], результати[0]['рядки']) == (результати[1]['rc'], результати[1]['рядки'])
        дані.append({'сцена': сцена, 'main': main, 'однаково': однаково, 'запуски': результати})
    (звіт / 'тотожні_рішення.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({р['сцена']: р['однаково'] for р in дані}, ensure_ascii=False))
    if not all(р['однаково'] for р in дані):
        raise AssertionError('Рішення приладу різні на тотожному виході стенда')


if __name__ == '__main__':
    виконати()
