"""Рахує власників і довірені пари на повному каталозі без мережі та вимірів."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
import feed
import фід_розбір as ФР
import фід_збагачення as ФЗ
import фід_фото as ФФ
import фід_власник_кадру as ФВ
import колір_річ as КР
import verify as В


def main():
    """Повторює умови довіреної пари, не виконуючи --записати проби вжитку."""
    каталог = КОРІНЬ / 'каталог_повний.xml.gz'
    розпакований = КОРІНЬ.parent / 'tmp/каталог-лічба.xml'
    with gzip.open(каталог, 'rb') as вхід:
        розпакований.write_bytes(вхід.read())
    офери = ФР.читати_yml(str(розпакований))[0]
    збагачення = ФЗ.читати_збагачення()
    спільні = ФФ.спільні_фото(офери)
    стани, варіанти, дизайни = Counter(), Counter(), set()
    пар = 0
    токени = re.compile(r"[a-zа-яёєіїґ']+")
    for о in офери:
        з = збагачення.get(о['id'])
        власник = ФВ.запис(о, з) if з else None
        if власник:
            стани[власник['стан']] += 1
        частини = [ч.strip() for ч in ФР.СЕП_КОЛЬОРУ.split(о.get('колір_сирий') or о.get('колір_назва') or '') if ч.strip()]
        if not ФЗ.збагачення_придатне(з) or (з.get('версія') or 1) < 2 or len(частини) != 1:
            continue
        ч = частини[0]
        if re.search(r'[\[(]', ч) or sum(bool(В.назва_кольору(т) or В.слово_крамниці(т))
                                          for т in токени.findall(ч.lower().replace('-', ' '))) > 1:
            continue
        lab = ФЗ.lab_з_hex(КР.hex_кольору(з['колір_основний']))
        слово = В.слово_крамниці(ч)
        if lab is None or not слово or not власник or власник['стан'] != 'свій':
            continue
        if ФФ.чужий_кадр(з.get('фото'), спільні.get(о.get('магазин') or о['id'].split('@')[-1]) or {}):
            continue
        пар += 1
        варіанти[власник.get('варіант') or 'невідомо'] += 1
        дизайни.add((слово['ім'], ФФ.файл_фото(з['фото'])))
    шляхи = ['каталог_повний.xml.gz', 'каталог_маніфест_кадрів.json.gz',
             'джерела/каталог_збагачення.json.gz', 'джерела/каталог_власник_кадру.json.gz']
    основа = subprocess.check_output(['git', 'merge-base', 'HEAD', 'origin/main'], cwd=КОРІНЬ).decode().strip()
    хеші = {ш: hashlib.sha256((КОРІНЬ / ш).read_bytes()).hexdigest() for ш in шляхи}
    for ш in шляхи:
        сирі = subprocess.check_output(['git', 'show', основа + ':' + ш], cwd=КОРІНЬ)
        assert hashlib.sha256(сирі).hexdigest() == хеші[ш], (основа, ш, 'відмінний вхід')
    звіт = dict(main=основа,
                 оферів=len(офери), власність_товару=dict(sorted(стани.items())),
                 довірених_пар=пар, варіанти_пар=dict(sorted(варіанти.items())), дизайнів=len(дизайни),
                 sha256=хеші)
    шлях = Path(__file__).with_suffix('.json')
    шлях.write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(звіт, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
