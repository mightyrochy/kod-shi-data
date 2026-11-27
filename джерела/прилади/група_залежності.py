"""Лічба для наряду Код-фасади-геть: прохідні модулі (без власних def/class), імпорти через них і найбільша група
взаємної залежності (сильно зв'язна компонента) серед модулів `джерела/*.py`. Запуск: python3 прилади/група_залежності.py
з теки `джерела`; друкує «прохідних N · імпортів через них M · група K (на рівні модуля L)»."""
import ast, glob, os, sys
sys.setrecursionlimit(10000)
МОД = {os.path.basename(f)[:-3]: f for f in glob.glob("*.py")}
ДЕРЕВА = {}
for м, ф in МОД.items():
    try:
        ДЕРЕВА[м] = ast.parse(open(ф, encoding="utf-8-sig").read())
    except SyntaxError:
        pass

def імпорти(дерево, _):
    for в in ast.walk(дерево):
        if isinstance(в, ast.Import):
            for а in в.names:
                yield а.name.split(".")[0]
        elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
            yield в.module.split(".")[0]

def верхні(дерево):
    for в in дерево.body:
        if isinstance(в, ast.Import):
            for а in в.names:
                yield а.name.split(".")[0]
        elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
            yield в.module.split(".")[0]

def найбільша_група(граф):
    індекс, низ, стек, на, лічба, найб = {}, {}, [], set(), [0], 0
    def йти(в):
        nonlocal найб
        індекс[в] = низ[в] = лічба[0]; лічба[0] += 1; стек.append(в); на.add(в)
        for н in граф[в]:
            if н not in індекс:
                йти(н); низ[в] = min(низ[в], низ[н])
            elif н in на:
                низ[в] = min(низ[в], індекс[н])
        if низ[в] == індекс[в]:
            n = 0
            while True:
                х = стек.pop(); на.discard(х); n += 1
                if х == в: break
            найб = max(найб, n)
    for в in граф:
        if в not in індекс: йти(в)
    return найб

def без_власних(д):
    return (not any(isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for в in ast.walk(д))
            and any(isinstance(в, (ast.Import, ast.ImportFrom)) for в in д.body))

прохідні = [м for м, д in ДЕРЕВА.items() if без_власних(д)]
через = sum(1 for м, д in ДЕРЕВА.items() for ім in set(імпорти(д, False)) if ім in прохідні and ім != м)
повний = {м: {і for і in імпорти(д, False) if і in ДЕРЕВА and і != м} for м, д in ДЕРЕВА.items()}
верх = {м: {і for і in верхні(д) if і in ДЕРЕВА and і != м} for м, д in ДЕРЕВА.items()}
print(f"прохідних {len(прохідні)} · модулів, що імпортують їх, {через} · група {найбільша_група(повний)} "
      f"(на рівні модуля {найбільша_група(верх)})")
