"""Порівнює причини на базі й голові: python дріт.py <дерево голови PR #4161>."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

дерево = Path(sys.argv[1]).resolve()
база = '2fa468d20ee49091590e929f3b6d58f7e270a8c1'
річ = dict(н='#1·01', слот='сукня', тип='сукня', код_кольору='green',
           hex='#2e8b57', фото_номери=[1], ознаки=dict(cut='wide', fabric='silk'))
адреса = dict(item_id='#1·01', kind='dress', color='green', hex='#2e8b57')
вхід = dict(образ=dict(ід='о1', речі=[річ]),
            свідомі=[dict(н='#1·01', заяви=[dict(code='scarf_size_unknown',
                          values=dict(item=адреса, item_id='#1·01'))])],
            день=dict(temperature_c=18, provenance=dict(temperature_c='her_words')),
            тіло=dict(зріст=168), палітра=dict(метал='золото', axes=dict(source_hue='self_report')),
            неповний=['top'], заміна_запасні=dict(річ='#1·01', чому='wrong_photo', запасні=[річ]),
            рішення_заміни=dict(н='#1·01', стан='stays'))
обчислити = ('import sys,json; sys.path[:0]=json.loads(sys.argv[1]); '
             'import дріт_моделі as Д; '
             'print(json.dumps(Д.опис(json.loads(sys.stdin.read())),ensure_ascii=False))')


def виклик(шляхи):
    результат = subprocess.run(
        [sys.executable, '-c', обчислити, json.dumps([str(ш) for ш in шляхи])],
        input=json.dumps(вхід), capture_output=True, text=True, encoding='utf-8',
        check=True, cwd=дерево)
    return json.loads(результат.stdout)


def без_кольорів(значення):
    if isinstance(значення, dict):
        return {к: без_кольорів(в) for к, в in значення.items()
                if not (('item_id' in значення or 'n' in значення) and к in ('color', 'hex'))}
    if isinstance(значення, list):
        return [без_кольорів(в) for в in значення]
    return значення


with tempfile.TemporaryDirectory(prefix='перевірка-4161-дріт-') as тимчасова:
    модулі = Path(тимчасова)
    for імя in ('знання_речі.py', 'дріт_моделі.py', 'розбір_відповідей.py'):
        (модулі / імя).write_bytes(subprocess.check_output(
            ['git', 'show', база + ':джерела/' + імя], cwd=дерево))
    до = виклик([модулі, дерево / 'джерела'])
    після = виклик([дерево / 'джерела'])
assert без_кольорів(до) == після, (до, після)
assert після['body']['height_cm'] == 168
assert після['your_declared'][0]['statements'][0]['values']['item'] == dict(
    item_id='#1·01', kind='dress')
print('ПРОЙДЕНО: дріт речі образу, запасної й адреси заяви без color/hex; решта полів причин і значення не змінені.')
print(json.dumps(після, ensure_ascii=False, sort_keys=True))
