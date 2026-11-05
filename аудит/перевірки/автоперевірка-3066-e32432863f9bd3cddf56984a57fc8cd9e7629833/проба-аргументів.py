import ast
import pathlib
import sys
import tempfile

sys.path.insert(0, sys.argv[1])
from ознаки_аналіз import Аналіз
from ознаки_основа import S, E

source = '''
def optional(x, ceiling=None):
    if ceiling is not None:
        return "high" if x * 2 > ceiling else "low"
    return None
'''
with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    (root / 'джерела').mkdir()
    (root / 'джерела' / 'probe.py').write_text(source, encoding='utf-8')
    for name, positional, named, expected in [
        ('не передано', [frozenset({S})], {}, 0),
        ('іменовано ceiling=10', [frozenset({S})], {'ceiling': E}, 1),
        ('позиційно 10', [frozenset({S}), E], {}, 1),
    ]:
        analysis = Аналіз(str(root))
        analysis.виклик(analysis.модулі['probe'].функції['optional'], positional, named)
        count = len(analysis.місця)
        print(f'{name}: місць {count}, очікувано {expected}')
        assert count == expected
