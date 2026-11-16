import ast, sys, importlib.util
def завант(ш, ім):
    s = importlib.util.spec_from_file_location(ім, ш); м = importlib.util.module_from_spec(s); s.loader.exec_module(м); return м
sys.path.insert(0, "/tmp/w/H/джерела/прилади")
Г = завант("/tmp/w/H/джерела/прилади/корінь_е2_межі.py", "г")
Б = завант("/tmp/w/B/джерела/прилади/корінь_е2_межі.py", "б")
for ім, м in (("база", Б), ("голова", Г)):
    добре = 0
    for н, к, ч in Г.ВИПАДКИ_ВАД_ВИМІРУ:
        а = м.Аналіз({"синтетика": ast.parse(к)}, {"відповідь_моделі"}, set(), {}).виконати()
        добре += len(м.Структура(а).зміни_обʼєкта()) == ч
    print(ім, добре, "з", len(Г.ВИПАДКИ_ВАД_ВИМІРУ))
