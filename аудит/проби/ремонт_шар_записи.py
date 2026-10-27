"""Порівняти розбір записаних відповідей серії 2 з базою; без моделі й мережі."""
import json
import re
import subprocess
import sys
import types
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
import мовний_шар as після


def main():
    """Надрукувати походження й лічбу кожного розбору, включно з відхиленнями."""
    база = sys.argv[1] if len(sys.argv) > 1 else '2c107632bdb24ac170c715ed181499abe1dbc67c'
    до = types.ModuleType('мовний_шар_до')
    сир = subprocess.run(['git', 'show', база + ':джерела/мовний_шар.py'],
                         cwd=КОРІНЬ, encoding='utf-8', capture_output=True, check=True).stdout
    exec(compile(сир, 'мовний_шар_до.py', 'exec'), до.__dict__)
    записи = []
    for ф in sorted((КОРІНЬ / 'аудит/проби/б1/ДО-2710').glob('*/VIDPOVIDI/*.txt')):
        текст = ф.read_text(encoding='utf-8')
        частини = re.split(r'\n── ВІДПОВІДЬ[^\n]*──\n', текст, maxsplit=1)
        if len(частини) != 2 or '\nПОВІДОМЛЕННЯ:\n' not in частини[0]:
            continue
        заяви = json.loads(частини[0].split('\nПОВІДОМЛЕННЯ:\n')[1].strip())
        розмітка = [dict(ключ=з['key'], повідомлення=str(і), вид='card_unchecked', заяви=[з])
                    for і, з in enumerate(заяви)]
        результати = [м.прийняти_повідомлення(розмітка, частини[1]) for м in (до, після)]
        записи.append(dict(джерело=str(ф.relative_to(КОРІНЬ)).replace('\\', '/'),
                           заяв=len(розмітка),
                           до=sum(з['стан'] == 'translated' for з in результати[0]['заяви']),
                           після=sum(з['стан'] == 'translated' for з in результати[1]['заяви']),
                           без_тексту=sum(з['стан'] != 'translated' for з in результати[1]['заяви']),
                           помилки={к: sum(п['що'] == к for п in результати[1].get('помилки', []))
                                    for к in sorted({п['що'] for п in результати[1].get('помилки', [])})}))
    підсумок = dict(база=база, викликів=len(записи),
                   **{к: sum(з[к] for з in записи) for к in ('заяв', 'до', 'після', 'без_тексту')},
                   непрочитаних_без_стану=sum(з['заяв'] - з['після'] - з['без_тексту'] for з in записи))
    print(json.dumps(dict(підсумок=підсумок, записи=записи), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
