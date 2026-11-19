# -*- coding: utf-8 -*-
"""Порівнює рядки приладу на тих самих записах і тотожних збережених виходах стенда.

Це перевірка незмінності рішень, не заміна браузерного виміру часу.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from виміряти import ВХІД, ДО, КОРІНЬ, НІЧНІ, ПРИЛАД, ПЯТЬ, ТИМЧАСОВА, видалити


def виконати():
    звіт = Path(__file__).resolve().parent
    обгортка = ТИМЧАСОВА / 'same-output.cjs'
    обгортка.write_text("""const fs = require('fs'), path = require('path'), Module = require('module'), zlib = require('zlib');
const [source, original, input, root, capture] = process.argv.slice(2);
const m = new Module(original, module);
m.filename = original; m.paths = Module._nodeModulePaths(path.dirname(original));
m._compile(fs.readFileSync(source, 'utf8'), original);
const saved = JSON.parse(zlib.gunzipSync(fs.readFileSync(capture)));
process.exitCode = m.exports.виконати([input, '--main', 'origin/main'], root,
  {відтворити: (folder) => saved[path.basename(folder)]});
""", encoding='utf-8')
    дані = []
    for сцена in ПЯТЬ:
        # Повний вимір захоплює виходи всіх фактично запущених стендів.
        знімок = звіт / 'повний-1-стенд.json.gz'
        if not знімок.exists():
            raise FileNotFoundError('Спершу завершіть повний вимір')
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
                                    str(КОРІНЬ), str(знімок)], cwd=КОРІНЬ,
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
        дані.append({'сцена': сцена, 'однаково': однаково, 'запуски': результати})
    (звіт / 'тотожні_рішення.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({р['сцена']: р['однаково'] for р in дані}, ensure_ascii=False))
    if not all(р['однаково'] for р in дані):
        raise AssertionError('Рішення приладу різні на тотожному виході стенда')


if __name__ == '__main__':
    виконати()
