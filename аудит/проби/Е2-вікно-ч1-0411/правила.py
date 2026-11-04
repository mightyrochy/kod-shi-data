"""Перевіряє правила вміщення на функціях поточного дерева без мережі."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела/прилади'))
import корінь_е2_вікно as П


def main():
    """Передає справжні функції JS у VM для перевірки збереження даних."""
    назви = {
        'блокиЗадачіП', 'даніЗадачіП', 'вміститиБлокиЗадачіП', 'фотоЗБлоківЗадачіП',
        'модельЗадачіП', 'скоротитиДовідкуП', 'скоротитиОсновиП',
        'скоротитиОцінкуП', 'оцінкаТокенівП', '_текстиПовідомленьП', '_оцінкаПромптаП',
        'токениФотоП', 'стадіяВикликуП', 'вмістити_у_вікно_П', '_скоротитиВердиктиП',
    }
    функції = {}
    for шлях in ('міст.js', 'приміряння.js', 'випадок.js', 'палітра.js', 'оцінка.js'):
        код = (КОРІНЬ / 'джерела/показ' / шлях).read_text(encoding='utf-8')
        for н, _, т in П.М.функції_js(код):
            if н in назви:
                чистий, _ = П.очистити(т)
                функції[н] = т[:П.дужка(чистий, чистий.index('{')) + 1]
    assert функції.keys() == назви
    запис = None
    сцена = КОРІНЬ / 'аудит/проби/б1/ПІСЛЯ-Е3/01_б1_концерт_стримано/VIDPOVIDI'
    for файл in sorted(сцена.glob('*.txt')):
        збіг = re.search(r'── ПРОМПТ \(\d+ симв\.\) ──\n(.*?)\n\n── ВІДПОВІДЬ',
                         файл.read_text(encoding='utf-8'), re.S)
        if not збіг:
            continue
        try:
            дані = json.loads(збіг[1])
        except json.JSONDecodeError:
            continue
        if isinstance(дані, dict) and дані.get('bases') and дані.get('schemes'):
            запис = dict(промпт=збіг[1], джерело=файл.relative_to(КОРІНЬ).as_posix())
            break
    assert запис, 'Нема записаного промпта палітри б1/01'
    with tempfile.TemporaryDirectory(dir=os.environ['TEMP']) as тека:
        файл = Path(тека) / 'функції.json'
        файл.write_text(json.dumps(dict(функції=функції, запис=запис), ensure_ascii=False), encoding='utf-8')
        return subprocess.run(['node', str(Path(__file__).with_suffix('.js')), str(файл)], cwd=КОРІНЬ).returncode


if __name__ == '__main__':
    sys.exit(main())
