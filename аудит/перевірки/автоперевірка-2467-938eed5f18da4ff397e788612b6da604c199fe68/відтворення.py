import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

корінь = Path(sys.argv[1]).resolve()
шлях = корінь / 'джерела/прилади/корінь_е2_вікно.py'
опис = importlib.util.spec_from_file_location('прилад', шлях)
прилад = importlib.util.module_from_spec(опис)
опис.loader.exec_module(прилад)

def число(тека):
    місця, факти = прилад.місця(str(тека))
    return sum(bool(м['пункти']) for м in місця), факти

база, _ = число(корінь)
print('Голова: місць:', база)
випадки = {
    'новий виклик модельП зі змінним промптом': 'async function новий(дані){ return await модельП(JSON.stringify(дані)); }\n',
    'виклик повз лійку зі змінним промптом': '''async function новий(дані){
  return fetch('http://127.0.0.1:1234/v1/chat/completions', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body:JSON.stringify({model:'local', messages:[{role:'user',content:JSON.stringify(дані)}],max_tokens:4000})
  });
}\n''',
    'літеральний текст зі змінною історією': "async function новий(історія){ return await модельП('Продовжуй', null, історія); }\n",
}
with tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix='проби_2467_') as т:
    т = Path(т)
    for н, (назва, код) in enumerate(випадки.items()):
        дерево = т / str(н)
        shutil.copytree(корінь / 'джерела/показ', дерево / 'джерела/показ')
        (дерево / 'джерела/показ/новий.js').write_text(код, encoding='utf-8')
        вихід, _ = число(дерево)
        print(f'{назва}: {база} -> {вихід}; очікувано {база + 1}')
    дерево = т / 'діагностика'
    shutil.copytree(корінь / 'джерела/показ', дерево / 'джерела/показ')
    міст = дерево / 'джерела/показ/міст.js'
    текст = міст.read_text(encoding='utf-8')
    текст = текст.replace('  await вмістити_запит_П(повідомлення, вміщВих);',
                         "  await вмістити_запит_П(повідомлення, вміщВих);\n  console.log('token context_length splice');")
    міст.write_text(текст, encoding='utf-8')
    вихід, факти = число(дерево)
    print(f'Лише console.log, без вимірювання чи скорочення: {база} -> {вихід}; очікувано {база}')
    заміни = {
        'Наявна заміна речі через прямий HTTP': "(await fetch('http://127.0.0.1:1234/v1/chat/completions', {method:'POST', body:JSON.stringify({model:'local', messages:[{role:'user',content:з.текст}],max_tokens:4000})})).text()",
        'Наявна заміна речі: змінні дані в історії': "модельП('Продовжуй', null, [{role:'user',content:з.текст}])",
    }
    for н, (назва, заміна) in enumerate(заміни.items()):
        дерево = т / ('наявне_' + str(н))
        shutil.copytree(корінь / 'джерела/показ', дерево / 'джерела/показ')
        картки = дерево / 'джерела/показ/картки.js'
        текст = картки.read_text(encoding='utf-8')
        assert текст.count('модельП(з.текст)') == 1
        картки.write_text(текст.replace('модельП(з.текст)', заміна), encoding='utf-8')
        вихід, _ = число(дерево)
        print(f'{назва}: {база} -> {вихід}; очікувано {база}')

for ім, тека in прилад.СЕРІЇ:
    види, запитів, відмов = прилад.записи_серії(str(корінь), ім, тека)
    ремонт = види['ВЕРДИКТ_V1→ОБРАЗИ_V1']
    print(f"{ім}: запитів {запитів}; запитів з відмовою {відмов}; ремонт {прилад.форма(ремонт)}")
    всі = []
    for файл in (корінь / тека).glob('*/знімки/модель_виклики.json'):
        for в in json.loads(файл.read_text(encoding='utf-8')).get('виклики', []):
            if 'exceeds the available context size' in str(в.get('помилка', '')):
                всі.append((файл.parent.parent.name, в.get('тип'), в.get('помилка')))
    print('Незалежна вибірка відмов:', json.dumps(sorted(всі), ensure_ascii=False))

виводи = []
for _ in range(2):
    п = subprocess.run([sys.executable, str(шлях)], cwd=корінь, capture_output=True, encoding='utf-8', env=dict(os.environ, PYTHONUTF8='1'))
    assert п.returncode == 0, п.stderr
    виводи.append(п.stdout)
import hashlib
print('Два запуски Python', sys.version.split()[0], ': SHA256', *(hashlib.sha256(в.encode()).hexdigest() for в in виводи))
