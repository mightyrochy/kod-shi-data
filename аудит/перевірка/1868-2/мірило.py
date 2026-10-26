"""Переносний запуск мірила #1868 без зміни обчислень.

python -I -B мірило.py <робоча-копія> <зібраний.html> <речі.json>
"""
import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
корінь, індекс, вихід = (Path(п).resolve() for п in sys.argv[1:])
мірило = корінь / 'аудит/огляд_коду/мірило_картки.py'
код = мірило.read_text(encoding='utf-8').replace(
    "ДЖ = '/home/user/kod-shi-data/джерела'",
    'ДЖ = ' + repr(str(корінь / 'джерела')))
код = код.replace(
    "tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)), prefix='вантаж_')",
    "tempfile.mkdtemp(prefix='перевірка_1868_')")
sys.argv = [str(мірило), str(індекс), str(корінь / 'каталог_повний.xml.gz')]
простір = {'__file__': str(мірило), '__name__': '__main__'}
exec(compile(код, str(мірило), 'exec'), простір)
речі = простір['Б']
print('слот ≠ фото_слот', sum(bool(р.get('фото_слот'))
      and р['слот'] != р['фото_слот'] for р in речі))
вихід.write_text(json.dumps(речі, ensure_ascii=False, default=str), encoding='utf-8')
print('рядки збережено:', len(речі))
