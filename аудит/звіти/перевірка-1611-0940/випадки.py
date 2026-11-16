import ast, sys, importlib.util
шлях = sys.argv[1]
spec = importlib.util.spec_from_file_location("прилад", шлях)
п = importlib.util.module_from_spec(spec); sys.path.insert(0, шлях.rsplit("/",1)[0]); spec.loader.exec_module(п)
H = "import json\n"
В = [
 # 15902 кортеж/zip
 ("вкладене розпакування: власний запис поруч — не місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = {}\n    (а, (вузол, сире)) = (1, (вих, об))\n    вузол['x'] = 1\n    return вузол\n", 0),
 ("вкладене розпакування: обʼєкт — місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = {}\n    (а, (вузол, сире)) = (1, (вих, об))\n    сире['x'] = 1\n    return вузол\n", 1),
 ("обмін а,б=б,а: після обміну сире — власний — не місце", H+"def ф(d):\n    сире = json.loads(d['відповідь_моделі'])\n    вузол = {}\n    вузол, сире = сире, вузол\n    сире['x'] = 1\n    return сире\n", 0),
 ("ланцюг цілей а,б = в,г = х,о: г — обʼєкт — місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = {}\n    а, б = в, г = вих, об\n    г['x'] = 1\n    return а\n", 1),
 ("for вкладене enumerate(zip(...)): власний — не місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = [{}]\n    for і, (ч, г) in enumerate(zip(об.get('p'), вих)):\n        г['x'] = ч.get('x')\n    return вих\n", 0),
 ("for вкладене enumerate(zip(...)): елемент обʼєкта — місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    вих = [{}]\n    for і, (ч, г) in enumerate(zip(об.get('p'), вих)):\n        ч['x'] = 1\n    return вих\n", 1),
 ("розпакування виклику, що повертає (обʼєкт, ужиток): ужиток — не обʼєкт", H+"def з():\n    об = json.loads('{}')\n    return об, {'t': 1}\ndef ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    return об, {'t': 1}\ndef г(d):\n    _, уж = ф(d)\n    уж['x'] = 1\n    return уж\n", 0),
 # 15903 try
 ("try, except теж присвоює обʼєкт іншої відповіді — місце", H+"def ф(d):\n    try:\n        об = json.loads(d['відповідь_моделі'])\n    except ValueError:\n        об = json.loads(d['відповідь_моделі'].strip())\n    об['x'] = 1\n    return об\n", 1),
 ("try в циклі, break у тілі, мітка — після циклу — місце", H+"def ф(сп):\n    об = {}\n    for d in сп:\n        try:\n            об = json.loads(d['відповідь_моделі'])\n            break\n        except ValueError:\n            continue\n    об['x'] = 1\n    return об\n", 1),
 ("try/else: мітка в else, перекрита у тілі — не місце", H+"def ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    try:\n        об = {}\n    except ValueError:\n        return None\n    об['x'] = 1\n    return об\n", 0),
 ("try/finally: присвоєння у finally перекриває — не місце", H+"def ф(d):\n    try:\n        об = json.loads(d['відповідь_моделі'])\n    finally:\n        об = {}\n    об['x'] = 1\n    return об\n", 0),
 ("try: except raise, мітка з тіла — місце", H+"def ф(d):\n    try:\n        об = json.loads(d['відповідь_моделі'])\n    except ValueError:\n        raise\n    об.pop('x')\n    return об\n", 1),
 # 15910 звірка
 ("обʼєкт для звірки, присвоєний і потім записаний — місце", H+"def читач(р, с):\n    return dict(р)\ndef ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    о2 = dict(об, x=1)\n    р = читач({}, о2)\n    о2['y'] = 2\n    return р\n", 1),
 ("виведений обʼєкт — аргумент виклику, що його повертає вкладено (кортеж) — місце", H+"def пара(а, о):\n    return а, о\ndef ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    return пара(1, dict(об, x=1))\n", 1),
 ("виведений обʼєкт у звірці, але присвоєно читачем у атрибут self — місце?", H+"class К:\n    def ф(self, d):\n        об = json.loads(d['відповідь_моделі'])\n        о2 = dict(об, x=1)\n        self.з = о2\n        return 1\n", 1),
 ("обʼєкт для звірки: два читачі — не місце", H+"def ч1(р, с):\n    return {'a': 1}\ndef ч2(р, с):\n    return {'b': 1}\ndef ф(d):\n    об = json.loads(d['відповідь_моделі'])\n    о2 = dict(об, x=1)\n    return ч1({}, о2), ч2({}, о2)\n", 0),
]
for н, к, ч in В:
    а = п.Аналіз({"синтетика": ast.parse(к)}, {"відповідь_моделі"}, set(), {}).виконати()
    є = [м[3] for м in п.Структура(а).зміни_обʼєкта()]
    print("ОК " if len(є)==ч else "ХИБА", len(є), "/", ч, "—", н, є if len(є)!=ч else "")
