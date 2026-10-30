import ast, importlib.util, json, os, sys
from pathlib import Path
from types import SimpleNamespace
sys.stdout.reconfigure(encoding='utf-8')
head = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
os.chdir(head)
spec = importlib.util.spec_from_file_location('прилад', head / 'джерела/прилади/корінь_е2_межі.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def count(code):
    f = ast.parse(code).body[0]
    s = p.Структура(SimpleNamespace(м={'приклад': SimpleNamespace(ім='приклад', функції={'прийняти': f})}))
    return len(s.відхилене_без_ходу({('приклад','прийняти')}))

base = '''def прийняти(дані):
    відкинуто = []
    if дані.get('помилка'):
        відкинуто.append(dict(чому='invalid', теми=[]))
        return None
    return дані
'''
checks = {
    'втрата з рядком звіту': count(base),
    'та сама втрата, додано невжиту змінну шаблон_даних': count(base.replace('    відкинуто = []', '    шаблон_даних = None\n    відкинуто = []')),
    'є запасна заява без спеціального імені': count(base.replace('        return None', "        return {'заява': 'Дозволені теми: ' + ', '.join(дані['теми'])}")),
}
for k,v in checks.items():
    print(k + ': ' + str(v))
js = p.ПоказJS()
print('JS нові п.3(г):', [(x[0], x[2]) for x in js.збій_без_ходу()])
for lo,hi in [(2418,2426),(2430,2437),(5065,5076),(5181,5191)]:
    print('\nмовний_шар.py:')
    lines=(head/'джерела/мовний_шар.py').read_text(encoding='utf-8').splitlines()
    for i in range(lo-1,hi): print(str(i+1)+': '+lines[i])
