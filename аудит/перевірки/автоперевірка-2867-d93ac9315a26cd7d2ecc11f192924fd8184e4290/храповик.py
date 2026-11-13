"""Справжній храповик, обмежений одним паспортом; це не повний CI-храповик."""
import importlib.util
import os
from pathlib import Path
import sys

os.environ['PYTHONUTF8'] = '1'
дерево = Path(sys.argv[1]).resolve()
база = sys.argv[2]
sys.path.insert(0, str(дерево / 'джерела/прилади'))
spec = importlib.util.spec_from_file_location('храповик', дерево / 'джерела/прилади/храповик_кореня.py')
м = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = м
spec.loader.exec_module(м)
імя = 'Річ-примірка-та-сама-людина'
голови, бази = м.паспорти_голови, м.паспорти_бази
м.паспорти_голови = lambda *а: {к: в for к, в in голови(*а).items() if к == імя}
м.паспорти_бази = lambda *а: {к: в for к, в in бази(*а).items() if к == імя}
рядки, червоні, стенд = м.храповик(str(дерево), база)
print('\n'.join(рядки))
print('\n'.join(червоні))
print(f'червоних: {len(червоні)}; потрібен стенд: {стенд}')
raise SystemExit(bool(червоні))
