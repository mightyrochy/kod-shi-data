"""Відтворює підміну товару: python -X utf8 цей_файл.py <дерево_голови>."""
import json
from pathlib import Path
import subprocess
import sys
import types
from playwright.sync_api import sync_playwright

дерево = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(дерево / 'zhnyvarka'))
import жниварка
from виконавець import ЗЛІПОК_DOM

html = '''<article class="product"><h1>Своя сукня</h1>
<div itemprop="description">Свій опис сукні</div>
<aside class="related"><section class="product"><h1>Чужа сумка</h1>
<div itemprop="description">Чужий опис сумки</div></section></aside></article>'''
рецепт = {'блок': '.product'}
до = types.ModuleType('жниварка_до')
до.__file__ = str(дерево / 'zhnyvarka/жниварка.py')
код = subprocess.check_output(['git', 'show',
    'da74a751ea07d72191c690a1f68e9338c11b85ca:zhnyvarka/жниварка.py'], cwd=дерево)
exec(compile(код, до.__file__, 'exec'), до.__dict__)
for крок, модуль in [('ДО', до), ('ПІСЛЯ', жниварка)]:
    ф = модуль.факти_з_картки(html, 'https://shop.test/product/1', рецепт)
    print(json.dumps(dict(крок=крок, **{к: ф.get(к) for к in ('назва', 'опис', 'межа_блоку')}), ensure_ascii=False))
with sync_playwright() as p:
    браузер = p.chromium.launch(headless=True, args=['--disable-gpu'])
    сторінка = браузер.new_page(viewport={'width': 390, 'height': 844})
    сторінка.set_content(html)
    dom = сторінка.evaluate(ЗЛІПОК_DOM, рецепт)
    print(json.dumps(dict(крок='Chromium ПІСЛЯ', назва=dom['h1'], текст=dom['text']), ensure_ascii=False))
    браузер.close()
