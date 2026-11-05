import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.mkdtemp(prefix='перевірка-2933-очі-'))
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root / 'zhnyvarka'))
import жниварка

входи = root / 'аудит/проби/річ_запис_каталог_2026_10_30'
вибірка = json.loads((входи / 'вибірка_п3.json').read_text(encoding='utf8'))
items = []
for номер, збіг in enumerate(('minimal-pudra', 'bodi_leo')):
    row = next(r for r in вибірка if збіг in r['url'])
    html = gzip.decompress((входи / row['файл']).read_bytes()).decode('utf8')
    facts = жниварка.факти_з_картки(html, row['url'])
    soup = жниварка.BeautifulSoup(html, 'html.parser')
    base = soup.find('base', href=True)
    url = urljoin(base['href'] if base else row['url'], facts['фото'][0])
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as r:
        data, mime = r.read(), r.headers.get_content_type()
    (out / f'фото-{номер}.bin').write_bytes(data)
    items.append(dict(id=row['id'], назва=facts['назва'], опис=facts['опис'],
                      ціна=facts['ціна'], фото=f'http://offline.local/фото-{номер}',
                      урл=row['url'], слот='верх', фото_джерело=url,
                      фото_sha256=hashlib.sha256(data).hexdigest(), mime=mime))
(out / 'очі-входи.json').write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf8')
subprocess.run(['node', str(Path(__file__).with_name('шаблон.js')), str(root), str(out/'показ.html')], check=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True, args=['--disable-gpu'])
    for i, item in enumerate(items):
        page = br.new_page(viewport={'width':390,'height':844}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        def route(r):
            if r.request.url == 'http://offline.local/':
                r.fulfill(content_type='text/html; charset=utf-8', body=(out/'показ.html').read_bytes())
            elif r.request.url.startswith('http://offline.local/%D1%84%D0%BE%D1%82%D0%BE-') or '/фото-' in r.request.url:
                r.fulfill(content_type=item['mime'], body=(out/f'фото-{i}.bin').read_bytes())
            else:
                r.abort()
        page.route('**/*', route)
        page.goto('http://offline.local/', wait_until='domcontentloaded')
        page.wait_for_function("typeof (document.getElementById('сцн-новий') || {}).onclick === 'function'")
        card = dict(рука='1', ітерацій=1, викликів=0, текст=item['опис'], опис=item['опис'], підпис='образ',
                    речі=[item], мітки=[], знахідки=[], питання=[], етапи={'викликів':0,'виклики':[]},
                    свідомі=[], невиконано=None, різноманітність=None, мова=[], мова_спроб=0,
                    мова_видано='так', фото_не_ті=[], дібрав_код_слоти=[])
        packet = dict(в='ПОКАЗ-V1', збірка='перевірка-2933', каталог='офлайн-вибірка', профіль='Проба',
                      розклад='1', прогін='проба-2933', випадок_рядок='Повтор текстів жнив', пул=1, картки=[card])
        page.evaluate("packet => { П=packet; рендер(); if(window.показатиОбраз) window.показатиОбраз(0); }", packet)
        page.wait_for_selector('#картки .картка .список .річ')
        page.locator('#к-0').scroll_into_view_if_needed()
        page.wait_for_function("[...document.querySelectorAll('#к-0 img')].every(i=>i.complete&&i.naturalWidth>0)")
        page.screenshot(path=str(out/f'390x844-{i}.png'), animations='disabled')
        print(json.dumps({'номер':i,'назва':item['назва'],'помилки':errors,'FOTO':os.environ.get('FOTO')}, ensure_ascii=False))
        page.close()
    br.close()
