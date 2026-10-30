"""Повторює збережені незалежні фрагменти #2370 поточним приладом."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def головна():
    """Друкує ДО → ПІСЛЯ; фрагменти бере з історичного виміру, не переписує їх."""
    корінь = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / 'джерела/прилади'))
    п = importlib.import_module('корінь_річ_запис_речі')
    дж = корінь / 'аудит/проби/річ_запис_ланцюг_докази/проби.json'
    старі = json.loads(дж.read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory() as т:
        for до, після in zip(старі['ДО'], старі['ПІСЛЯ']):
            код = до['код']
            if до['проба'].startswith('JS'):
                ф = Path(т) / 'контроль.js'
                ф.write_text(код, encoding='utf8')
                р = subprocess.run(['node', '--expose-internals', str(корінь / 'джерела/прилади/корінь_річ_запис_речі_js.js'), str(ф)], capture_output=True, encoding='utf8', check=True)
                м = п.розібрати_js('джерела/контроль.js', json.loads(р.stdout)[str(ф)])
            else:
                м = п.розібрати_py('джерела/контроль.py', код)
            а = п.Аналіз([м], п.Реєстр(str(корінь)))
            а.пройти()
            пункти = sorted({к[2] for к in п.обчислити(а)})
            print(json.dumps(dict(проба=до['проба'], ДО=до['пункти'], попередній_ПІСЛЯ=після['пункти'], ПІСЛЯ=пункти), ensure_ascii=False))


if __name__ == '__main__':
    головна()
