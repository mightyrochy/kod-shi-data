import base64
import gzip
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

tree = pathlib.Path(sys.argv[1]).resolve()
tmp = pathlib.Path(sys.argv[2]).resolve()
tmp.mkdir(parents=True, exist_ok=True)
items = []
with gzip.open(tree / 'каталог_повний.xml.gz', 'rb') as stream:
    for _, offer in ET.iterparse(stream, events=('end',)):
        if offer.tag != 'offer':
            continue
        title = offer.findtext('name') or ''
        if 'сукн' not in title.lower() and 'човник' not in title.lower():
            offer.clear()
            continue
        photo = offer.findtext('picture')
        if not photo:
            continue
        try:
            request = urllib.request.Request(photo, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=15) as response:
                raw = response.read(4_000_000)
                image = 'data:' + response.headers.get_content_type() + ';base64,' + base64.b64encode(raw).decode()
        except Exception:
            continue
        items.append(dict(id=offer.get('id'), назва=title, ціна=offer.findtext('price'), фото=image,
                          слот='сукня' if 'сукн' in title.lower() else 'взуття'))
        if len(items) == 2:
            break
assert len(items) == 2
cards = [dict(рука=str(i), ітерацій=1, викликів=0, текст='Контроль відображення речей каталогу.',
              опис='Контроль відображення', підпис='образ', речі=items, мітки=[], знахідки=[], питання=[],
              етапи=dict(викликів=0, виклики=[]), свідомі=[], невиконано=None, різноманітність=None,
              мова=[], мова_спроб=0, мова_видано='так', фото_не_ті=[], дібрав_код_слоти=[]) for i in range(1, 5)]
packet = dict(в='ПОКАЗ-V1', збірка='cc59ce4838b024404e1cfd3ed121492e89839998',
              каталог='каталог_повний.xml', профіль='Контроль', розклад='1234', прогін='пр-перевірка-4041',
              випадок_рядок='Гостя на весіллі · контроль показу', пул=27525, картки=cards)
subprocess.run(['node', '-e', '''
const fs = require('fs');
const h = require('./показ_шаблон.js');
const html = h.підставитиШаблон(h.зібратиШаблонПоказу('показ.html'), {
  __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'cc59ce4838b024404e1cfd3ed121492e89839998',
  __ВІДБИТОК__: 'контроль', __ФІД_ПОКАЗУ__: 'каталог_повний.xml', __КАТАЛОГ_ПОКАЗУ__: '27525 речей',
  __ДОВІДНИК_ПОКАЗУ__: h.прочитатиДовідникJSON(process.cwd())
});
fs.writeFileSync('контроль-4041.html', html);
'''], cwd=tree / 'джерела', check=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=['--disable-gpu'])
    page = browser.new_page(viewport=dict(width=390, height=844), device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('https://**/*', lambda route: route.abort())
    page.goto((tree / 'джерела/контроль-4041.html').as_uri(), wait_until='load')
    page.wait_for_function("typeof рендер === 'function'")
    page.evaluate('(packet) => { П = packet; рендер(); }', packet)
    page.wait_for_selector('#картки .картка .список .річ')
    page.evaluate('() => document.fonts.ready')
    texts = []
    for i in range(4):
        page.evaluate('(i) => показатиОбраз(i)', i)
        page.locator(f'#к-{i}').scroll_into_view_if_needed()
        page.screenshot(path=str(tmp / f'картка-{i+1}-390x844.png'))
        texts.append(page.locator(f'#к-{i}').inner_text())
        if i == 0:
            page.locator('#к-0').screenshot(path=str(tmp / 'картка-1-повна.png'))
    (tmp / 'картки-тексти.json').write_text(json.dumps(texts, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(FOTO=os.environ.get('FOTO'), viewport='390x844', помилки=errors,
                          фото=page.locator('#картки img').count(), речі=[x['id'] for x in items]), ensure_ascii=False))
    browser.close()
