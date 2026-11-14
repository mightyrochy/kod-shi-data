"""Відтворення сусідньої проби з функцією голови або бази, без зміни файлів продукту."""
import ast
import os
from pathlib import Path
import runpy
import subprocess
import sys

src = Path(sys.argv[1]).resolve() / 'джерела'
side = sys.argv[2]
os.chdir(src)
sys.path.insert(0, str(src))
import паспорт_нагоди as passport

if side == 'база':
    source = subprocess.check_output(['git', 'show', '8dafc1113ba09cdc5459cead2c0878fbc14b2b37:джерела/паспорт_нагоди.py'])
    function = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'паспорт_шматками_людині')
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(src / 'паспорт_нагоди.py'), 'exec'), passport.__dict__)
else:
    assert side == 'голова'

text = 'Зустріч з подругами у старовинній бібліотеці після презентації нашої нової книжки'
import json
p = passport.паспорт_з_json(json.dumps({'місце': 'кафе', 'місце_слова': text, 'подія': text}), {}, '', шар=True)
chunks = passport.паспорт_шматками_людині(p)
print('Варіант:', side, flush=True)
print('Шматки:', json.dumps(chunks, ensure_ascii=False), flush=True)
print('Повний текст збережений:', any(x['текст'] == text for x in chunks), flush=True)
sys.argv = [str(src / 'проби/е2_втрата_слова.py')]
runpy.run_path(sys.argv[0], run_name='__main__')
