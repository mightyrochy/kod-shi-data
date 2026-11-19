import ast, sys, importlib.util
шлях = sys.argv[1]
spec = importlib.util.spec_from_file_location("прилад", шлях)
п = importlib.util.module_from_spec(spec); sys.path.insert(0, шлях.rsplit("/",1)[0]); spec.loader.exec_module(п)
def код(повернути):
    return ("import json\n"
"def запит(d):\n    try:\n        об = json.loads(d['відповідь_моделі'])\n        return (об, d.get('usage', {}))\n    except Exception:\n        raise\n"
"def норм(о):\n    return {'опис': str(о.get('опис') or '')[:300], 'в': о.get('в')}\n"
"def спитати(d):\n    об, уж = запит(d)\n    return " + повернути + "\n"
"def описати(d):\n    try:\n        опис, _ = спитати(d)\n    except Exception:\n        return None\n    опис['фото'] = 1\n    return опис\n")
for н, р in [("як у продукті: (норм(об), уж)", "норм(об), уж"), ("без ужитку: (норм(об), {})", "норм(об), {}"), ("ужиток без норм: ({}, уж)", "{}, уж")]:
    а = п.Аналіз({"синтетика": ast.parse(код(р))}, {"відповідь_моделі"}, set(), {}).виконати()
    print(н, "→", [м[3][-30:] for м in п.Структура(а).зміни_обʼєкта()])
