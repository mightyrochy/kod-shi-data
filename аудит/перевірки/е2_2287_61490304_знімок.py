from pathlib import Path
import subprocess
import sys
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
output.mkdir(parents=True, exist_ok=True)
js = '''
const fs = require('fs'), path = require('path');
const root = process.argv[1], out = process.argv[2];
const t = require(path.join(root, 'джерела/показ_шаблон.js'));
const html = t.підставитиШаблон(path.join(root, 'джерела/показ.html'), {
  __МОДУЛІ_ПОКАЗУ__: 'offline', __ЗБІРКА_ПОКАЗУ__: 'review-2287', __ВІДБИТОК__: 'review-2287',
  __ФІД_ПОКАЗУ__: 'offline', __КАТАЛОГ_ПОКАЗУ__: 'offline', __ДОВІДНИК_ПОКАЗУ__: fs.readFileSync(path.join(out, 'dictionary.json'), 'utf8'),
  __ПРОМПТ_КОЛІР_ПОКАЗУ__: '', __ВИБІРКА_ПОКАЗУ__: '{}'
});
fs.writeFileSync(path.join(out, 'e2-page.html'), html);
'''
dictionary = subprocess.run(['python', '-X', 'utf8', '-c', "import json,sys; sys.path.insert(0,'прилади'); from експорт_показу import довідник; print(json.dumps(довідник(),ensure_ascii=False))"], cwd=root / 'джерела', capture_output=True, text=True, encoding='utf-8', check=True).stdout.strip().splitlines()[-1]
(output / 'dictionary.json').write_text(dictionary, encoding='utf-8')
subprocess.run(['node', '-e', js, str(root), str(output)], check=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-gpu'])
    page = browser.new_page(viewport={'width':390, 'height':844}, device_scale_factor=1)
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('**/*', lambda r: r.fulfill(content_type='text/html', body=(output / 'e2-page.html').read_text(encoding='utf-8')) if r.request.url == 'http://offline.local/' else r.abort())
    page.goto('http://offline.local/')
    page.wait_for_function("typeof застосуватиСценарій === 'function'")
    page.evaluate("""() => {
        застосуватиСценарій({поля:{'сц-нагода':'робота','сц-година':'9'}, паспорт:{нагода:'робота',година:9,подія:'робочий день в офісі'}});
        режим('сценарій'); малюватиКарткуСценарію();
    }""")
    page.screenshot(path=str(output / 'e2-390x844.png'), animations='disabled')
    print('viewport=390x844; pageerrors=', errors)
    browser.close()
