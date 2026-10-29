"""Мірило Е3: нуль неявних читачів і незалежні явні шляхи в одному контексті."""
import ast, pathlib, sys
from concurrent.futures import ThreadPoolExecutor
КОРІНЬ = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent
дерева = {ф: ast.parse(ф.read_text(encoding='utf-8-sig')) for ф in КОРІНЬ.glob('*.py')}
ядро = дерева[КОРІНЬ / 'поломки_ядро.py']
неявний = any(isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
              and в.func.attr == 'ContextVar' for в in ast.walk(ядро))
читачі = []
for файл, дерево in дерева.items():
    for вузол in ast.walk(дерево):
        if неявний and ((isinstance(вузол, ast.Import) and any(і.name == 'поломки_ядро' for і in вузол.names))
                       or (isinstance(вузол, ast.ImportFrom) and вузол.module == 'поломки_ядро')):
            читачі.append(f'{файл.name}:{вузол.lineno}')
print('Модулів, залежних від неявного прогону поза ядром:', len(читачі), *читачі, sep='\n')
if len(sys.argv) > 1:
    sys.exit(0)
assert not читачі, читачі
sys.path.insert(0, str(КОРІНЬ))
import поломки as П, поломки_ядро as Я
справний, зламаний = П.прогін(), П.прогін(('K-KOH-02',))
def смуга(прогін_руки):
    """Рахує ту саму точку зламу лише з переданим станом."""
    return П.злам('K-KOH-02', 'смуга', (4, 5), прогін_руки=прогін_руки)
for _ in range(10):
    assert смуга(зламаний) == (3, 3) and смуга(справний) == (4, 5)
    assert П.злам('K-KOH-02', 'смуга', (4, 5)) == (4, 5)
with ThreadPoolExecutor(2) as пул:
    assert list(пул.map(смуга, (зламаний, справний) * 10)) == [(3, 3), (4, 5)] * 10
П.в_тінь('K-KOH-02', 'проба', прогін_руки=зламаний)
assert справний.тінь == [] and зламаний.тінь
assert not hasattr(Я, 'ПРОГІН') and not hasattr(Я, 'ПИТАЛИ_СТЕЖЕНІ')
print('Е3: модулів із неявним станом 0; 20 чергувань і 20 паралельних викликів незалежні')
