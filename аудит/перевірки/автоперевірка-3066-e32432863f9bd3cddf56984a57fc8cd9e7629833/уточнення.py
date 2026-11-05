import ast
from pathlib import Path
import sys
import tempfile

root = Path(__file__).parent
tree = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'pr3066'
sys.path.insert(0, str(tree / 'джерела' / 'прилади'))
from ознаки_аналіз import Аналіз
from ознаки_основа import S, E

source = (tree / 'джерела' / 'face_contrast.py').read_text(encoding='utf-8')
module = ast.parse(source)
nodes = [node for node in module.body if
         isinstance(node, ast.FunctionDef) and node.name == 'світле_біля_глибокої' or
         isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ГЛИБОКІ_СМУГИ' for t in node.targets)]
extracted = ast.unparse(ast.Module(body=nodes,type_ignores=[]))
namespace = {}
exec(extracted, namespace)
function = namespace['світле_біля_глибокої']
print('Той самий код продукту: brown,30,80 →', function('brown',30,80))
print('Той самий код продукту: light,30,80 →', function('light',30,80))
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory)
    (path / 'джерела').mkdir()
    (path / 'джерела' / 'probe.py').write_text(extracted,encoding='utf-8')
    analysis = Аналіз(str(path))
    analysis.виклик(analysis.модулі['probe'].функції['світле_біля_глибокої'], [frozenset({S}),E,E], {})
    print('Мітка S лише на смузі шкіри: місць',len(analysis.місця))
    assert not analysis.місця

sys.path.insert(0, str(tree / 'джерела'))
from колір_простір_шкіра import вісь_підтону_двостороння
from колір_простір_риси import температура_шкіри
print('Двосторонність на голові:',вісь_підтону_двостороння()['двостороння'])
for lab in [(60,10,15),(60,20,35)]:
    data = температура_шкіри(lab)
    print('Температура',lab,':',data['тепло_клас'],';',data['undertone'])
