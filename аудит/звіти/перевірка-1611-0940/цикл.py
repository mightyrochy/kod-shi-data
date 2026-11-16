import ast, sys, importlib.util
шлях = sys.argv[1]
spec = importlib.util.spec_from_file_location("прилад", шлях)
п = importlib.util.module_from_spec(spec); sys.path.insert(0, шлях.rsplit("/",1)[0]); spec.loader.exec_module(п)
к = "import json\ndef ф(сп):\n    об = {}\n    for d in сп:\n        об = json.loads(d['відповідь_моделі'])\n        break\n    об['x'] = 1\n    return об\n"
а = п.Аналіз({"с": ast.parse(к)}, {"відповідь_моделі"}, set(), {}).виконати()
print("цикл без try, break:", len(п.Структура(а).зміни_обʼєкта()))
