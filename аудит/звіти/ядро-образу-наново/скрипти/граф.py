# Замикання імпортів від bridge і найбільша група взаємної залежності (сильно зв'язна компонента).
# Ребра — усі import / from-import (зокрема всередині функцій) і import_module з рядковим літералом.
# Запуск з кореня репозиторію: python3 -I аудит/звіти/ядро-образу-наново/скрипти/граф.py джерела /tmp/граф.json
import ast, os, sys, json, warnings
warnings.simplefilter('ignore')
ДЖ, ВИХІД = sys.argv[1], sys.argv[2]
модулі = {f[:-3] for f in os.listdir(ДЖ) if f.endswith('.py')}
def імпорти(м):
    t = ast.parse(open(os.path.join(ДЖ, м + '.py'), encoding='utf-8').read()); вих = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import):
            вих |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            вих |= {n.module.split('.')[0]} if n.module else {a.name for a in n.names}
        elif isinstance(n, ast.Call) and getattr(n.func, 'attr', getattr(n.func, 'id', None)) in ('import_module', '__import__'):
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                вих.add(n.args[0].value.split('.')[0])
    return вих & модулі
ребра, стек = {}, ['bridge']
while стек:
    м = стек.pop()
    if м in ребра: continue
    ребра[м] = імпорти(м); стек.extend(ребра[м] - set(ребра))
рядки = {м: sum(1 for _ in open(os.path.join(ДЖ, м + '.py'), encoding='utf-8')) for м in ребра}
# Тар'ян без рекурсії
індекс, низ, на_стеку, ст, групи, лічба = {}, {}, set(), [], [], [0]
for корінь in ребра:
    if корінь in індекс: continue
    робота = [(корінь, iter(sorted(ребра[корінь])))]
    індекс[корінь] = низ[корінь] = лічба[0]; лічба[0] += 1; ст.append(корінь); на_стеку.add(корінь)
    while робота:
        в, діти = робота[-1]
        for д in діти:
            if д not in індекс:
                індекс[д] = низ[д] = лічба[0]; лічба[0] += 1; ст.append(д); на_стеку.add(д)
                робота.append((д, iter(sorted(ребра[д])))); break
            elif д in на_стеку: низ[в] = min(низ[в], індекс[д])
        else:
            робота.pop()
            if робота: низ[робота[-1][0]] = min(низ[робота[-1][0]], низ[в])
            if низ[в] == індекс[в]:
                г = []
                while True:
                    x = ст.pop(); на_стеку.discard(x); г.append(x)
                    if x == в: break
                групи.append(г)
найб = max(групи, key=len)
json.dump(dict(м=sorted(ребра), рядки=рядки, гр=sorted(найб)), open(ВИХІД, 'w'), ensure_ascii=False)
print('замикання від bridge: модулів', len(ребра), 'рядків', sum(рядки.values()))
print('найбільша група взаємної залежності: модулів', len(найб), 'рядків', sum(рядки[м] for м in найб))
