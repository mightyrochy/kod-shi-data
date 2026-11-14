from pathlib import Path
import json
import os
import sys
from playwright.sync_api import sync_playwright

out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'evidence3759'
os.environ['FOTO'] = '1'
rows = json.loads((out / 'rows.json').read_text(encoding='utf-8'))
cases = [('restaurant', next(x for x in rows if x['сцена'] == 'с4 живий рядок')),
         ('cafe', next(x for x in rows if x['сцена'] == 'кафедра / мовний шар'))]
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(args=['--disable-gpu'])
    page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('http://**/*', lambda r: r.abort())
    page.route('https://**/*', lambda r: r.abort())
    page.goto((out / 'head.html').as_uri(), wait_until='load')
    page.wait_for_function("typeof малюватиРядокВипадку === 'function' && typeof режим === 'function'")
    for name, item in cases:
        for side in ['до', 'після']:
            state = page.evaluate('''({chunks, side}) => {
                П = {в: 'ПОКАЗ-V1', прогін: 'перевірка-3759-' + side, картки: [], випадок_шматки: chunks};
                рендер();
                const row = document.getElementById('обр-випадок');
                row.scrollIntoView({block: 'center'});
                return {текст: row.innerText, svg: row.querySelectorAll('svg').length,
                        піктограми: ІКОНКА_ПОЛЯ_ВИПАДКУ,
                        слова: [...row.children].map(e => e.textContent)};
            }''', {'chunks': item[side], 'side': side})
            page.screenshot(path=str(out / f'{name}-{side}.png'), animations='disabled')
            results.append({'сцена': item['сцена'], 'бік': side, **state})
    browser.close()
(out / 'screens.json').write_text(json.dumps({'знімки': results, 'помилки_сторінки': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(results, ensure_ascii=False))
print('Помилок сторінки:', len(errors))
