import ast
import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('meter', root / 'джерела/прилади/корінь_е2_межі.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def analyze(src):
    return m.Аналіз({'probe': ast.parse(src)}, set(m.ПОЛЯ_МОДЕЛІ_ПАРАМ), set(m.СЛОВА_ЇЇ_ІМЕНА), {}).виконати()

cases = {
    'in': 'def f(уривок):\n    return "вечір" in уривок\n',
    'equality': 'def f(уривок):\n    return "night" if уривок.lower() == "вечір" else "day"\n',
    'field': 'def f(дані):\n    return "night" if дані.get("уривок", "").lower() == "вечір" else "day"\n',
    'sub': 'import re\ndef f(уривок):\n    return "night" if re.sub(r"\\s+", " ", уривок) == "вечір" else "day"\n',
}
for name, src in cases.items():
    a = analyze(src)
    print(name, [(e['рядок'], e['вид'], e['дія']) for e in a.події.values()])

# Гілки ремонту із записом діагностики й без нього.
for name, src in {
    'repair_with_notes': 'import json\ndef f(дані):\n    obj = json.loads(дані["відповідь_моделі"])\n    нотатки = []\n    if isinstance(obj, list):\n        obj = {"items": obj}\n        нотатки.append("wrapped list")\n    return obj\n',
    'repair_without_notes': 'import json\ndef f(дані):\n    obj = json.loads(дані["відповідь_моделі"])\n    if isinstance(obj, list):\n        obj = {"items": obj}\n    return obj\n',
}.items():
    a = analyze(src)
    print(name, 'p4=', m.Структура(a).нотатки() + m.Структура(a).знаки_json(), 'events=', [(e['вид'], e['дія']) for e in a.події.values()])

src = (root / 'джерела/картка_запиту.py').read_text(encoding='utf-8')
a = analyze(src)
print('actual_card_p7', [(e['функція'], e['рядок'], e['дія']) for e in a.події.values() if e['вид'] == 'слова'])

src = (root / 'джерела/протокол.py').read_text(encoding='utf-8')
a = analyze(src)
print('actual_protocol_notes', [(row, name) for mod, name, row, why in m.Структура(a).нотатки()])
import sys
sys.path.insert(0, str(root / 'джерела'))
import протокол
for schema, obj in [({'тип': 'рядок', 'значення': ['42']}, 42), ({'тип': 'рядок'}, ['a', 'b'])]:
    notes = []
    result = протокол._нормалізувати(schema, obj, '', notes)
    print('actual_protocol_conversion', repr(obj), '->', repr(result), notes)

src = (root / 'джерела/показ/збирання_руки.js').read_text(encoding='utf-8')
js = m.ПоказJS.__new__(m.ПоказJS)
js.ф = {name: {'файл':'джерела/показ/збирання_руки.js', 'рядок':line, 'тіло':m.без_коментарів_js(body)} for name,line,body in m.функції_js(src)}
print('actual_js_readers', js.читачі())

from types import SimpleNamespace
src = (root / 'джерела/каталог_розбір_прогін.py').read_text(encoding='utf-8')
func = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == '_спитати')
prompts=[]
def model(prompt, *args):
    prompts.append(prompt)
    return ('bad' if len(prompts) == 1 else 'good'), 0.0
ns = {'модель':model, 'ПОВТОРІВ_НА_НЕ_JSON':1,
      'КР':SimpleNamespace(з_відповіді=lambda text: (None, ['не JSON', 'missing required field']) if text == 'bad' else ({'ok':1}, [])),
      'СВ':SimpleNamespace(СХЕМИ_ВІДПОВІДІ={'КАТАЛОГ_РІЧ':SimpleNamespace(промпт_повтору=lambda prompt, error: prompt + ' | ' + error)})}
exec(compile(ast.Module(body=[func],type_ignores=[]), '<actual _спитати>', 'exec'), ns)
print('actual_catalog_retry', ns['_спитати']('original', 'offline'), prompts)
