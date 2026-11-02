"""Знімає одну картку 390×844 з index.html переданої голови без мережі й моделі."""
import base64
import gzip
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright


def головна():
    """Показує фікстуру з двома речами й зберігає знімок поруч зі звітом."""
    корінь = Path(sys.argv[1]).resolve()
    вихід = Path(__file__).with_name(Path(__file__).stem.removesuffix('_знімок') + '.png')
    пакет = {'в': 'ПОКАЗ-V1', 'збірка': 'перевірка2368', 'каталог': 'стенд', 'профіль': 'Оля', 'розклад': '3142',
             'прогін': 'перевірка2368', 'випадок': 'Робота · офіс', 'пул': 2, 'картки': [
                 {'рука': '1', 'ітерацій': 1, 'викликів': 0, 'текст': 'Світла сукня і тонкий пасок.',
                  'опис': 'Сукня з паском.', 'підпис': 'образ',
                  'речі': [{'id': 'перевірка-1', 'назва': 'Сукня', 'ціна': 3000, 'слот': 'сукня', 'фото': None},
                           {'id': 'перевірка-2', 'назва': 'Пасок', 'ціна': 500, 'слот': 'пояс', 'фото': None}],
                  'мітки': [], 'знахідки': [], 'питання': [], 'етапи': {'викликів': 0, 'виклики': []}, 'свідомі': [],
                  'невиконано': None, 'різноманітність': None, 'мова': [], 'мова_спроб': 0, 'мова_видано': 'так',
                  'фото_не_ті': [], 'дібрав_код_слоти': []}]}
    фрагмент = base64.urlsafe_b64encode(gzip.compress(json.dumps(пакет, ensure_ascii=False).encode())).decode().rstrip('=')
    with sync_playwright() as p:
        br = p.chromium.launch(args=['--disable-gpu'])
        try:
            page = br.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=1, is_mobile=True, has_touch=True)
            page.route('http://**/*', lambda route: route.abort())
            page.route('https://**/*', lambda route: route.abort())
            помилки = []
            page.on('pageerror', lambda e: помилки.append(str(e)))
            page.goto((корінь / 'index.html').as_uri() + '#' + фрагмент, wait_until='load')
            page.wait_for_selector('#картки .картка .список .річ', timeout=60000)
            page.locator('#картки .картка').first.scroll_into_view_if_needed()
            page.screenshot(path=str(вихід))
            print(json.dumps({'viewport': '390×844', 'карток': page.locator('#картки .картка').count(),
                              'помилки': помилки}, ensure_ascii=False))
        finally:
            br.close()


if __name__ == '__main__':
    головна()
