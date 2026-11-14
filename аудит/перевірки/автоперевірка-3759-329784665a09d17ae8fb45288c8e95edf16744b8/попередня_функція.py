import ast
import os
from pathlib import Path
import runpy
import subprocess
import sys

src = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'pr3759') / 'джерела'
os.chdir(src)
sys.path.insert(0, str(src))
import паспорт_нагоди as passport
source = subprocess.check_output(['git', 'show', '8dafc1113ba09cdc5459cead2c0878fbc14b2b37:джерела/паспорт_нагоди.py'])
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'паспорт_шматками_людині')
exec(compile(ast.Module(body=[function], type_ignores=[]), str(src / 'паспорт_нагоди.py'), 'exec'), passport.__dict__)
runpy.run_path(str(src / 'проби/паспорт_один_опис_8740.py'), run_name='__main__')
