"""Прицільні відтворення п.5; аргумент — дерево перевіреної голови PR."""
import importlib.util
import json
from pathlib import Path
import sys

корінь = Path(sys.argv[1]).resolve()
прилади = корінь / 'джерела' / 'прилади'
sys.path.insert(0, str(прилади))
spec = importlib.util.spec_from_file_location('прилад', прилади / 'корінь_е3_сила_правила.py')
п = importlib.util.module_from_spec(spec)
spec.loader.exec_module(п)


def вимір(зміни):
    модулі = dict(п._СТЕНД)
    модулі.update(зміни)
    продукт = п.Продукт('/неіснує', модулі={
        м: ('джерела/' + м + '.py', т) for м, т in модулі.items()
    }, js=п._JS)
    місця, відкинуті = п.п5(продукт, п.П1(продукт).прогін(), п.емісії(продукт))
    return {
        'місця': [рядок for рядок, _, _ in місця if 'реєстр_п5' in рядок],
        'відкинуті': [рядок for рядок, _ in відкинуті if 'реєстр_п5' in рядок],
    }


база = вимір({})
аліас = вимір({'суд_п5а': п._СТЕНД['суд_п5а'].replace(
    'РЕЄСТР5 as Р', 'РЕЄСТР5 as УНІКАЛЬНИЙ_АЛІАС').replace("Р[", "УНІКАЛЬНИЙ_АЛІАС[")})
print(json.dumps({'база': база, 'імпортний_аліас': аліас},
                 ensure_ascii=False, indent=2))
