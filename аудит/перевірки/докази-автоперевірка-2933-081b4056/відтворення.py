"""Відтворює втрату group_id з незмінного HTML через факти, запис і XML.

Запуск: python -X utf8 <цей файл> <дерево голови PR> [--повна-вибірка]
Дерево має бути викладене з 081b40567257c48b578763f5ec0641aca5f13055.
Базу читає через git, тимчасові файли кладе в TEMP; мережі та моделей немає.
"""
import argparse
from collections import defaultdict, Counter
import gzip
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

БАЗА = 'da74a751ea07d72191c690a1f68e9338c11b85ca'
URL = 'https://cooshwear.com/product/open-toe-suede-ankle-boots-safari-chocolate'


def головна():
    """Порівнює штатні читачі голови й бази та друкує фактичний результат."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('дерево', type=Path)
    парсер.add_argument('--повна-вибірка', action='store_true')
    арг = парсер.parse_args()
    дерево = арг.дерево.resolve()
    репо = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(дерево / 'zhnyvarka'))
    import жниварка as після
    корпус = дерево / 'аудит/проби/річ_запис_каталог_2026_10_30'
    вибірка = json.loads((корпус / 'вибірка_п3.json').read_text(encoding='utf8'))
    лічба = defaultdict(Counter)
    результат = {'база': БАЗА, 'url': URL}
    with tempfile.TemporaryDirectory(prefix='перевірка2933-') as тимчасова:
        тека = Path(тимчасова)
        for ім in ('жниварка.py', 'рецепти.tsv'):
            (тека / ім).write_bytes(subprocess.check_output(
                ['git', 'show', f'{БАЗА}:zhnyvarka/{ім}'], cwd=репо))
        специфікація = importlib.util.spec_from_file_location('жниварка_до_2933', тека / 'жниварка.py')
        до = importlib.util.module_from_spec(специфікація)
        специфікація.loader.exec_module(до)
        до.РЕЦЕПТИ_TSV = str(тека / 'рецепти.tsv')
        for рядок in вибірка:
            if not арг.повна_вибірка and рядок['url'] != URL:
                continue
            html = gzip.decompress((корпус / рядок['файл']).read_bytes()).decode('utf8')
            поля = {}
            for мітка, модуль in (('до', до), ('після', після)):
                ф = модуль.факти_з_картки(html, рядок['url'], модуль.рецепт_селекторів(рядок['крамниця']))
                ф['url'] = рядок['url']
                поля[мітка] = ф
                if рядок['url'] == URL:
                    запис = модуль.канонічний_запис(ф, {'домен': рядок['крамниця'], 'платформа': 'невідомо'}, 'html')
                    запис['id'] = 'проба'
                    вихід = io.BytesIO()
                    модуль.записати_каталог([запис], вихід, 'перевірка')
                    результат[мітка] = dict(факти=ф.get('group_id'), запис=запис.get('group_id'),
                                           xml=ET.fromstring(вихід.getvalue()).find('.//offer').get('group_id'))
            for поле in ('назва', 'опис', 'бренд', 'артикул', 'id_магазину', 'group_id', 'розміри', 'розміри_в_наявності'):
                for мітка in ('до', 'після'):
                    лічба[поле][мітка] += bool(поля[мітка].get(поле))
                лічба[поле]['втрачено'] += bool(поля['до'].get(поле)) and not bool(поля['після'].get(поле))
    if арг.повна_вибірка:
        результат['покриття'] = dict(лічба)
    print(json.dumps(результат, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(головна())
