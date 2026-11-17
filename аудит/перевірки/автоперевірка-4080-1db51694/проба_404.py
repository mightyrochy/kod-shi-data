"""Порівнює збережений HTTP 404 з класифікацією не_кадри на дереві PR #4080."""
import csv
import importlib.util
import json
from pathlib import Path
import sys

дерево = Path(sys.argv[1]).resolve()
проби = дерево / 'аудит/проби'
специфікація = importlib.util.spec_from_file_location(
    'порівняння4080', проби / 'кадр_варіант_кв2_один_колір_1611/порівняти.py')
модуль = importlib.util.module_from_spec(специфікація)
специфікація.loader.exec_module(модуль)
with (проби / 'кадр_варіант_кв1_очима_1511/кадри.tsv').open(encoding='utf-8') as потік:
    рядок = next(р for р in csv.DictReader(потік, delimiter='\t')
                 if р['крамниця'] == 'www.miraton.ua' and р['http_код'] == '404')
print(json.dumps(dict(ід=рядок['ід'], адреса=рядок['адреса_кадру'],
                     HTTP_у_кадрі_tsv=рядок['http_код'],
                     лічба_не_кадри=dict(модуль.не_кадри([рядок['адреса_кадру']]))),
                 ensure_ascii=False, indent=2))
