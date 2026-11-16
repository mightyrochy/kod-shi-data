import ast, sys, importlib.util
шлях = sys.argv[1]
spec = importlib.util.spec_from_file_location("прилад", шлях)
п = importlib.util.module_from_spec(spec); sys.path.insert(0, шлях.rsplit("/",1)[0]); spec.loader.exec_module(п)
H = "import json\n"
В = [
 ("append виведеного у список, що повертається", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = []\n    вих.append(dict(об, x=1))\n    return вих\n", 1),
 ("json.dumps виведеного — текст далі", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    return json.dumps(dict(об, x=1))\n", 1),
 ("update результату виведеним", H+"def ф(d, р):\n    об = json.loads(d['відповідь_моделі'])\n    р.update(dict(об, x=1))\n    return р\n", 1),
 ("присвоєно імені, далі append", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    о2 = dict(об, x=1)\n    вих = []\n    вих.append(о2)\n    return вих\n", 1),
 ("присвоєно імені, далі лише звірка (контроль)", H+"def зв(р, с):\n    return {'п': 1}\ndef ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    о2 = dict(об, x=1)\n    return зв({}, о2)\n", 0),
]
for н, к, ч in В:
    а = п.Аналіз({"с": ast.parse(к)}, {"відповідь_моделі"}, set(), {}).виконати()
    є = [м[3][-40:] for м in п.Структура(а).зміни_обʼєкта()]
    print("ОК " if len(є)==ч else "ХИБА", len(є), "/", ч, "—", н)
