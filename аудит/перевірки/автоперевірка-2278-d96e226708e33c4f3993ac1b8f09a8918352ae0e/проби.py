import json
import os
from pathlib import Path
import runpy
import sys
import tempfile

root = Path(sys.argv[1]).resolve()
module = runpy.run_path(str(root / 'джерела/прилади/корінь_е2_текст_жінці.py'), run_name='review_import')

def sinks(folder):
    program, entries, wrappers, dynamic, service = module['обчислити'](str(folder))
    return program, entries, wrappers

def result(program, entries):
    return [f"{module['відображене'](s.мод.шлях)}:{s.мод.рядок(s.і)} {s.чим} ранг={s.ранг} поріг={s.поріг} місце={module['є_місцем'](s)}" for s in entries if not s.обгортка]

with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    (folder / 'показ').mkdir()
    (folder / 'показ.html').write_text('<html></html>', encoding='utf-8')
    (folder / 'показ/мовний_шар.js').write_text('''
function назваЖінціП(е, т){ е.textContent = т; }
function їїСловаП(е, т){ е.textContent = т; }
function елНазваП(тег, клас, т){ const е = document.createElement(тег); назваЖінціП(е, т); return е; }
''', encoding='utf-8')
    cases = {
        'обгортка-входу': "function ф(дані){ елНазваП('b', null, String(дані.схема).replace(/_/g, ' ')); }",
        'ті-самі-дані-прямо': "function ф(дані){ назваЖінціП(document.body, String(дані.схема).replace(/_/g, ' ')); }",
        'її-слова-зі-сталим-написом': "function ф(файл){ їїСловаП(document.body, файл.name + ' · показано локально, нікуди не вантажиться'); }",
        'її-слова-з-назви-моделі': "async function ф(){ const дані = await (await fetch('/model')).json(); їїСловаП(document.body, дані.назва); }",
        'її-слова-з-тексту-моделі': "async function ф(){ const дані = await (await fetch('/model')).json(); їїСловаП(document.body, дані.текст); }",
        'вузли-childNodes': "function рендер(){ fetch('/model'); const вузол = document.createElement('div'); текстЖінціП(вузол, 'Перевірений текст'); return вузол; } function ф(){ document.body.replaceChildren(...рендер().childNodes); }",
    }
    for name, code in cases.items():
        (folder / 'показ/проба.js').write_text(code, encoding='utf-8')
        program, entries, wrappers = sinks(folder)
        found = [s for s in entries if not s.обгортка and module['є_місцем'](s)]
        filtered_b, _ = module['шлях_б'](program, found)
        all_b, _ = module['шлях_б'](program, [s for s in entries if not s.обгортка])
        print(name + ': ' + json.dumps({'місць': len(found), 'Б_поточний': len(filtered_b), 'Б_усі_стоки': len(all_b), 'стоки': result(program, entries)}, ensure_ascii=False))

program, entries, wrappers = sinks(root / 'джерела')
print('обгортки-голови: ' + ', '.join(sorted(wrappers)))
for s in entries:
    if module['відображене'](s.мод.шлях) == 'показ/картки.js' and s.мод.рядок(s.і) == 1376:
        print('голова-1376: ' + result(program, [s])[0])
for relative, line in [('показ/палітра.js', 463), ('показ/картки.js', 1147)]:
    present = [s for s in entries if module['відображене'](s.мод.шлях) == relative and s.мод.рядок(s.і) == line]
    print(f'голова-{relative}:{line}: стоків {len(present)}')
