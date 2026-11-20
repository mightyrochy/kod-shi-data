# Чи тримає коло залежностей шлях (мости, пакет, розбір, паспорт, повнота) чи знання (суд, колір, каталог)?
# Вилучаємо з графа модулі, які нове ядро заміняє (ЗАМІНЯЄ нижче — розділ 3 ОПИС.md; фасади, `trace`,
# `внутрішня_мова` і `statements` — словник знання, лишаються), і міряємо найбільшу групу
# взаємної залежності серед решти; ще — скільки ребер іде від решти до вилучених (їх ріже видалення старого шляху).
# Запуск з кореня: python3 -I аудит/звіти/ядро-образу-наново/скрипти/коло_без_шляху.py джерела
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ДЖ = sys.argv[1]
ЗАМІНЯЄ = set('''мовний_шар паспорт_нагоди паспорт_поля паспорт_основи міст_вхід картка_запиту її_входи conversation_tools
language_contract пакет_моделі міст_пакет міст_запити композитор_збирання композитор_слоти композитор_полюси композитор_оцінка
композитор_реєстр композитор_річ композитор_придатні семплер різноманітність_пулу уважний_вибір порядок_запиту brief знання_дріт
дріт_моделі збирач_промптів спільні_вимоги фрази_формату кеш_входу розбір_відповідей протокол схема_відповіді схеми_розбору
міст_відповіді руки_без_коду міст_рука2 знахідка людський_вихід суд_від_моделі вердикт_моделі
перевірка_образу суд_огляд суд_чеклісти суд_образу повнота_образу selection_policy міст_опис пропозиція_заміни заміна_речі
причини_речі bridge покроковик'''.split())
import ast, warnings; warnings.simplefilter('ignore')
модулі = {f[:-3] for f in os.listdir(ДЖ) if f.endswith('.py')}
def імпорти(м):
    t = ast.parse(open(os.path.join(ДЖ, м + '.py'), encoding='utf-8').read()); вих = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Import): вих |= {a.name.split('.')[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom): вих |= {n.module.split('.')[0]} if n.module else {a.name for a in n.names}
        elif isinstance(n, ast.Call) and getattr(n.func, 'attr', getattr(n.func, 'id', None)) in ('import_module', '__import__'):
            if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str): вих.add(n.args[0].value.split('.')[0])
    return вих & модулі
ребра, стек = {}, ['bridge']
while стек:
    м = стек.pop()
    if м in ребра: continue
    ребра[м] = імпорти(м); стек.extend(ребра[м] - set(ребра))
рядки = {м: sum(1 for _ in open(os.path.join(ДЖ, м + '.py'), encoding='utf-8')) for м in ребра}
def найбільша(вузли):
    вузли = set(вузли); р = {м: ребра[м] & вузли for м in вузли}
    індекс, низ, на, ст, групи, n = {}, {}, set(), [], [], [0]
    for к in sorted(вузли):
        if к in індекс: continue
        роб = [(к, iter(sorted(р[к])))]; індекс[к] = низ[к] = n[0]; n[0] += 1; ст.append(к); на.add(к)
        while роб:
            в, діти = роб[-1]
            for д in діти:
                if д not in індекс:
                    індекс[д] = низ[д] = n[0]; n[0] += 1; ст.append(д); на.add(д); роб.append((д, iter(sorted(р[д])))); break
                elif д in на: низ[в] = min(низ[в], індекс[д])
            else:
                роб.pop()
                if роб: низ[роб[-1][0]] = min(низ[роб[-1][0]], низ[в])
                if низ[в] == індекс[в]:
                    г = []
                    while True:
                        x = ст.pop(); на.discard(x); г.append(x)
                        if x == в: break
                    групи.append(г)
    return max(групи, key=len)
з = ЗАМІНЯЄ & set(ребра); решта = set(ребра) - з
print('нове ядро заміняє: модулів', len(з), 'рядків', sum(рядки[м] for м in з))
print('лишаються знанням: модулів', len(решта), 'рядків', sum(рядки[м] for м in решта))
г = найбільша(ребра); print('коло зараз: модулів', len(г), 'рядків', sum(рядки[м] for м in г))
г2 = найбільша(решта); print('коло серед решти: модулів', len(г2), 'рядків', sum(рядки[м] for м in г2), '—', ' '.join(sorted(г2)))
назад = sorted((м, x) for м in решта for x in ребра[м] & з)
print('ребер від решти до замінених:', len(назад), 'у модулях', len({м for м, _ in назад}))
for м, x in назад: print('  ', м, '→', x)
# Склад замінених модулів: коментарі й докстрінги проти коду; з покриттям (другий аргумент — вихід покриття_аналіз.py)
# — скільки рядків їхніх функцій виконав тест живого шляху.
док = ком = порож = 0
for м in з:
    src = open(os.path.join(ДЖ, м + '.py'), encoding='utf-8').read(); t = ast.parse(src); рр = src.splitlines()
    д = set()
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            д.update(range(n.body[0].lineno, n.body[0].end_lineno + 1))
    док += len(д); ком += sum(1 for i, l in enumerate(рр, 1) if l.strip().startswith('#') and i not in д)
    порож += sum(1 for i, l in enumerate(рр, 1) if not l.strip() and i not in д)
всього = sum(рядки[м] for м in з)
print(f'замінені: докстрінги {док}, коментарі {ком}, порожні {порож}, код {всього - док - ком - порож} з {всього}')
if len(sys.argv) > 2:
    п = json.load(open(sys.argv[2]))
    print('замінені: рядків у функціях', sum(п[м]['фун'] for м in з), 'у виконаних функціях', sum(п[м]['фун_вик'] for м in з))
