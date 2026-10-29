import base64
import gzip
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

root = Path(sys.argv[1]).resolve()
packet = {'в': 'ПОКАЗ-V1', 'збірка': 'перевірка-2271', 'каталог': 'офлайн-фікстура',
          'профіль': 'Оля', 'розклад': '3142', 'прогін': 'перевірка-2271',
          'випадок': 'Робота · офіс', 'пул': 100, 'картки': []}
for hand in ('3', '1', '4', '2'):
    packet['картки'].append({'рука': hand, 'ітерацій': 1, 'викликів': 1,
        'текст': 'Світла сукня і тонкий пасок.', 'опис': 'Образ руки ' + hand,
        'підпис': 'образ', 'речі': [
            {'id': f'сукня-{hand}', 'назва': 'Сукня', 'ціна': 3000, 'слот': 'сукня', 'фото': None},
            {'id': f'пасок-{hand}', 'назва': 'Пасок', 'ціна': 500, 'слот': 'пояс', 'фото': None}],
        'мітки': [], 'знахідки': [], 'питання': [], 'етапи': {'викликів': 1, 'виклики': []},
        'свідомі': [], 'невиконано': None, 'різноманітність': None, 'мова': [],
        'мова_спроб': 0, 'мова_видано': 'так', 'фото_не_ті': [], 'дібрав_код_слоти': []})
fragment = base64.urlsafe_b64encode(gzip.compress(json.dumps(packet, ensure_ascii=False).encode())).decode().rstrip('=')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--disable-gpu'])
    page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('http://**/*', lambda r: r.abort())
    page.route('https://**/*', lambda r: r.abort())
    page.goto((root / 'index.html').as_uri() + '#' + fragment)
    page.wait_for_selector('#картки .картка .список .річ', timeout=30000)
    page.locator('#картки .картка').first.scroll_into_view_if_needed()
    page.screenshot(path=str(root.parent / '2271-390x844.png'))
    print(json.dumps({'viewport': page.viewport_size, 'cards': page.locator('#картки .картка').count(), 'errors': errors}, ensure_ascii=False))
    browser.close()
