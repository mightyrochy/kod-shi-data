import json, re, sys, glob
from pathlib import Path
Р = re.compile(r"солон|солян|\bсол[іяиьюей]|\bсіл[ьіл]|реаген|\bsalt|\bde-?icing|road_salt|salted", re.I)
for сцена in sys.argv[1:]:
    d = json.loads(Path(сцена, 'вердикти.txt').read_text())
    for пр in d['прогони']:
        for в in пр['вердикти']:
            знайдено = []
            def обійти(x, шлях):
                if isinstance(x, str):
                    if Р.search(x): знайдено.append((шлях, x))
                elif isinstance(x, dict):
                    for к, v in x.items(): обійти(v, шлях + '.' + к)
                elif isinstance(x, list):
                    for i, v in enumerate(x): обійти(v, шлях + f'[{i}]')
            for к in ('опис', 'текст', 'коментар', 'для_мене', 'питання_поля', 'склад'):
                if к in в: обійти(в[к], к)
            print(сцена, 'рука', в.get('рука'), 'полів із сіллю:', len(знайдено))
            for ш, т in знайдено:
                м = Р.search(т); print('   ', ш, '…' + т[max(0, м.start()-150):м.end()+150].replace('\n', ' ') + '…')
