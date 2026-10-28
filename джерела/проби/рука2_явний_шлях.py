"""Мірило Е3: нуль неявних читачів і незалежні явні шляхи в одному контексті."""
import ast, pathlib, sys
from concurrent.futures import ThreadPoolExecutor
КОРІНЬ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(КОРІНЬ))
import поломки as П, поломки_ядро as Я
читачі = []
for файл in КОРІНЬ.glob('*.py'):
    дерево = ast.parse(файл.read_text(encoding='utf-8-sig'))
    for вузол in ast.walk(дерево):
        if isinstance(вузол, ast.Name) and вузол.id in ('ПРОГІН', '_ПРОГІН', 'ПИТАЛИ_СТЕЖЕНІ'):
            читачі.append(f'{файл.name}:{вузол.lineno}')
        if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr == 'ContextVar':
            читачі.append(f'{файл.name}:{вузол.lineno}')
assert not читачі, читачі
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
assert not hasattr(Я, 'ПРОГІН')
print('Е3: модулів із неявним станом 0; 20 чергувань і 20 паралельних викликів незалежні')
