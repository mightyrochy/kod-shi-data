"""Міряє код виходу справжньої PAL-12 без сусідніх речей: запуск із кореня.

Стенд і добір підмінено контрольованим входом; це перевірка мірила Д2,
не живий прогін моделі чи перевірка продуктового суду. --до SHA читає стару пробу.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

парсер = argparse.ArgumentParser()
парсер.add_argument('--до')
а = парсер.parse_args()
корінь = Path.cwd()
sys.path[:0] = [str(корінь / 'джерела/проби'), str(корінь / 'джерела')]
import pal_вердикт as ПВ

ПВ.стенд = lambda **_: ({}, {}, {}, {'палітра_практична': {
    'прийоми': [{'прийом': 'драматизація_м_якої', 'активний': True}],
    'осі': {'позиція': {'chroma': -1}}}})
ПВ.з_каталогу = lambda кат, слот, умова: {'id': 'акцент'} if слот == 'верх' else None
ПВ.взяти = lambda *арг: None
ПВ.lch = lambda *арг: (50, 60, 30)
файл = корінь / 'джерела/проби/pal_K-PAL-12.py'
код = (subprocess.check_output(['git', 'show', а.до + ':джерела/проби/pal_K-PAL-12.py'])
       if а.до else файл.read_bytes())
try:
    exec(compile(код, str(файл), 'exec'), {'__name__': '__main__', '__file__': str(файл)})
except SystemExit as вихід:
    print(json.dumps({'сценарій': 'PAL-12: акцент є, сусідніх речей нема',
                      'rc': вихід.code}, ensure_ascii=False))
    raise SystemExit(вихід.code)
raise SystemExit('Проба не завершилася на відсутньому вході')
