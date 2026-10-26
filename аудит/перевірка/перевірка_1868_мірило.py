"""Мірило #1868 з переносним шляхом джерел і вивантаженням речей для дифу.

python -I -B перевірка_1868_мірило.py <worktree> <index.html> <вихід.json>
Збірку робить штатний build_артефакт.py; мірило й дані не підміняються.
"""
import json
import os
from pathlib import Path
import sys

корінь, індекс, вихід = map(lambda п: Path(п).resolve(), sys.argv[1:])
мірило = корінь / 'аудит/огляд_коду/мірило_картки.py'
код = мірило.read_text(encoding='utf-8').replace(
    "ДЖ = '/home/user/kod-shi-data/джерела'",
    'ДЖ = ' + repr(str(корінь / 'джерела')))
sys.argv = [str(мірило), str(індекс), str(корінь / 'каталог_повний.xml.gz')]
простір = {'__file__': str(мірило), '__name__': '__main__'}
exec(compile(код, str(мірило), 'exec'), простір)
речі = простір['Б']
print('слот ≠ фото_слот', sum(bool(р.get('фото_слот'))
      and р['слот'] != р['фото_слот'] for р in речі))
вихід.write_text(json.dumps(речі, ensure_ascii=False), encoding='utf-8')
os.chdir(корінь)
