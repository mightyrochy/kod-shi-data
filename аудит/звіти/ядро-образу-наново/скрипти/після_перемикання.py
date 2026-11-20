# Що з модулів, які нове ядро заміняє, ще потрібне іншим функціям продукту (оцінка, приміряння, пошук речі, річ з фото,
# стилістка, помічниця, палітри, помади): замикання імпортів від їхніх модулів ∩ ЗАМІНЯЄ з коло_без_шляху.py.
# Запуск з кореня: python3 -I аудит/звіти/ядро-образу-наново/скрипти/після_перемикання.py джерела
import os, sys, re, ast, warnings
warnings.simplefilter('ignore')
ДЖ = sys.argv[1]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'коло_без_шляху.py'), encoding='utf-8').read()
ЗАМІНЯЄ = set(re.search(r"ЗАМІНЯЄ = set\('''(.*?)'''", src, re.S).group(1).split())
модулі = {f[:-3] for f in os.listdir(ДЖ) if f.endswith('.py')}
def імпорти(м):
    t = ast.parse(open(os.path.join(ДЖ, м + '.py'), encoding='utf-8').read()); вих = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import): вих |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom): вих |= {n.module.split('.')[0]} if n.module else {a.name for a in n.names}
        elif isinstance(n, ast.Call) and getattr(n.func, 'attr', getattr(n.func, 'id', None)) in ('import_module', '__import__'):
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str): вих.add(n.args[0].value.split('.')[0])
    return вих & модулі
ІНШІ = ['міст_основи', 'приміряння', 'помада', 'міст_річ', 'міст_оцінка', 'міст_стилістка', 'міст_помічниця', 'пошук_речі']
бачено, стек = set(), list(ІНШІ)
while стек:
    м = стек.pop()
    if м in бачено: continue
    бачено.add(м); стек.extend(імпорти(м) - бачено)
рядки = lambda мм: sum(sum(1 for _ in open(os.path.join(ДЖ, м + '.py'), encoding='utf-8')) for м in мм)
треба = sorted(бачено & ЗАМІНЯЄ); вільні = sorted(ЗАМІНЯЄ - бачено)
print('потрібні іншим функціям:', len(треба), 'модулів,', рядки(треба), 'рядків —', ' '.join(треба))
print('видаляються з перемиканням:', len(вільні), 'модулів,', рядки(вільні), 'рядків —', ' '.join(вільні))
for вхід in ІНШІ:
    б, ст = set(), [вхід]
    while ст:
        м = ст.pop()
        if м in б: continue
        б.add(м); ст.extend(імпорти(м) - б)
    print(f'  {вхід}: замінених у замиканні {len(б & ЗАМІНЯЄ)}, рядків {рядки(б & ЗАМІНЯЄ)}')
