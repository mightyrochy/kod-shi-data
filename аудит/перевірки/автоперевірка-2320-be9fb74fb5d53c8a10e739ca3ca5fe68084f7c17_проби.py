# -*- coding: utf-8 -*-
"""Прицільні проби автоперевірки #2320. Аргументи: дерево бази, дерево голови."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

tool = Path('джерела/прилади/корінь_е2_межі.py')
base, head = (Path(p).resolve() for p in sys.argv[1:3])
cases = {
 'повтор_у_викликачі': ('import json\ndef читати(вхід):\n    return json.loads(вхід["відповідь_моделі"])\ndef викликач(вхід):\n    розбір = читати(вхід)\n    if розбір is None:\n        промпт_повтору(вхід, "не пройшло перевірку")\n    return розбір\n', ''),
 'немає_повтору': ('import json\ndef читати(вхід):\n    return json.loads(вхід["відповідь_моделі"])\ndef викликач(вхід):\n    return читати(вхід)\n', ''),
 'слова_дорівнюють': ('def вибрати(уривок):\n    return уривок == "вечір"\n', ''),
 'слова_у_переліку': ('def вибрати(уривок):\n    return уривок in ("вечір", "ранок")\n', ''),
 'ключі_словника': ('def вибрати(уривок):\n    for к, з in уривок.items():\n        if к != "formality":\n            return з\n', ''),
 'ремонт_return': ('def читати(об, нотатки):\n    if isinstance(об, list):\n        нотатки.append("склеєно")\n        return "\\n".join(об)\n', ''),
 'відхилення_return': ('def читати(об, нотатки):\n    if not isinstance(об, str):\n        нотатки.append("відхилено: очікувався рядок")\n        return False\n', ''),
 'js_вкладене_const': ('', 'async function читати(){\n  const т = await модельП();\n  const локальна = () => {\n    const т = "звичайний текст";\n    return т.replace("а", "б");\n  };\n  return т;\n}\n'),
 'js_параметр': ('', 'async function читати(){\n  const т = await модельП();\n  const локальна = т => т.replace("а", "б");\n  return т;\n}\n'),
 'js_параметр_і_справжній_читач': ('', 'async function читати(){\n  const локальна = т => т.replace("а", "б");\n  {\n    const т = await модельП();\n    return JSON.parse(т);\n  }\n}\n'),
 'js_справжній_читач': ('', 'async function читати(){\n  const т = await модельП();\n  return JSON.parse(т);\n}\n'),
}
env = dict(os.environ, PYTHONIOENCODING='utf-8')
with tempfile.TemporaryDirectory(prefix='перевірка_2320_') as temp:
    for name, (python, js) in cases.items():
        root = Path(temp) / name
        (root/'джерела/показ').mkdir(parents=True)
        (root/'джерела/status.py').write_text('МОДУЛІ_ПРОДУКТУ = ["приклад"]\n', encoding='utf-8')
        (root/'джерела/приклад.py').write_text(python, encoding='utf-8')
        (root/'джерела/показ/приклад.js').write_text(js, encoding='utf-8')
        results = {}
        for label, tree in [('ДО', base), ('ПІСЛЯ', head)]:
            run = subprocess.run([sys.executable, str(tree/tool), '--корінь', str(root), '--json'], cwd=root,
                                 env=env, capture_output=True, encoding='utf-8', check=True)
            data = json.loads(run.stdout)
            results[label] = {k:data[k] for k in ['місць', 'за_пунктами']}
        print(name, json.dumps(results, ensure_ascii=False), flush=True)
