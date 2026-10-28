"""Повна проба 300 образів; еквівалентне індексування лише діагностичного сліду.

Запуск із кореня: python аудит/проби/тип_кольору_213_нейтраль.py
На першому справжньому сліді звіряє весь результат зі штатним збиранням.
Суд, вхід, сід, кількість образів і записи сліду не змінює (знахідка 9704).
"""
import os
from pathlib import Path
import runpy
import sys
import time

root = Path(__file__).resolve().parents[2] / 'джерела'
os.chdir(root)
sys.path[:0] = [str(root), str(root / 'проби')]
import trace as T
import pal_вердикт as P

old_collect, old_find = T.зібрати, P.знахідки
checked, count, start = False, 0, time.perf_counter()


def collect():
    global checked
    rows = {}
    for row in T.ЗАПИСИ:
        key = (row['правило'], row['де'], row['рука'], str(row['значення']))
        if key in rows:
            rows[key]['спрацювань'] += 1
        else:
            rows[key] = dict(row, спрацювань=1)
    result = list(rows.values())
    if not checked:
        t = time.perf_counter()
        assert result == old_collect()
        checked = True
        print('Слід тотожний штатному:', len(T.ЗАПИСИ), 'записів;',
              'штатне збирання секунд', round(time.perf_counter() - t, 2), flush=True)
    return result


def find(*a, **kw):
    global count
    result = old_find(*a, **kw)
    count += 1
    if count % 25 == 0:
        print('Суд', count, '/300; секунд', round(time.perf_counter() - start, 1), flush=True)
    return result


T.зібрати, P.знахідки = collect, find
print('Повна проба нейтралей; лише індекс сліду замість повторного пошуку', flush=True)
try:
    runpy.run_path(str(root / 'проби' / 'колір_нейтраль.py'), run_name='__main__')
    assert count == 300 and checked
    print('Пробу завершено:', count, 'судів', flush=True)
finally:
    T.зібрати, P.знахідки = old_collect, old_find
