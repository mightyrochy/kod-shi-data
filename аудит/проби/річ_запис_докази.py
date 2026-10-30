"""Зберегти докази проби каталогу: сирі жнива, HTML, контекст полів і 20 кадрів.

--доступ читає наявні журнали лише для читання, потім відкриває недоступні
сторінки звичайним Chromium без профілю, паролів, зміни адрес чи обходу CAPTCHA.
Без цього прапорця працює винятково із зафіксованими файлами.
"""
import argparse
import asyncio
import collections
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3
import sys

from річ_запис_каталог import КОРІНЬ, записати, стиснути, поля_вибірки, сертифікати


def читати(шлях):
    """Прочитати зафіксований JSON."""
    return json.loads(шлях.read_text(encoding='utf-8'))


def архів(вихід, мета):
    """Шукати тільки ту саму адресу в збережених HTTP-тілах журналу 5.3."""
    зразки = {р['id']: р for р in читати(вихід / 'вибірка.json')}
    журнал = Path.home() / '.cache/liusterko/harvest-5.3-20261029'
    for р in мета:
        if р.get('стан') == 200:
            continue
        дом = зразки[р['id']]['крамниця']
        база = журнал / 'проходи' / дом / 'черга.sqlite3'
        if not база.is_file():
            continue
        with sqlite3.connect(база.as_uri() + '?mode=ro', uri=True) as з:
            ряд = з.execute('SELECT час,код,sha256,файл FROM відповіді WHERE url=? AND код=200 ORDER BY ід DESC LIMIT 1', (р['url'],)).fetchone()
        if not ряд:
            continue
        шлях = база.parent / ряд[3]
        if not шлях.is_file():
            continue
        дані = шлях.read_bytes()
        if hashlib.sha256(дані).hexdigest() != ряд[2]:
            raise ValueError('Не збігається SHA256 збереженої відповіді: ' + str(шлях))
        стиснути(вихід / р['файл'], дані)
        р.update(перший_HTTP=р.get('стан', р.get('помилка')), стан=200,
                 джерело='збережена відповідь жнив 5.3', час=ряд[0], sha256=ряд[2],
                 архівний_файл=str(шлях), кодування='utf-8')
        р.pop('помилка', None)


async def браузер(вихід, мета):
    """Відкрити решту адрес звичайним браузером і зберегти DOM без обходу захистів."""
    from playwright.async_api import async_playwright
    async with async_playwright() as рушії:
        рушій = await рушії.chromium.launch(headless=True)
        контекст = await рушій.new_context(locale='uk-UA')
        семафор = asyncio.Semaphore(4)

        async def одна(р):
            """Одна спроба стандартної навігації на вихідну адресу."""
            async with семафор:
                сторінка = await контекст.new_page()
                try:
                    відповідь = await сторінка.goto(р['url'], wait_until='domcontentloaded', timeout=25000)
                    await сторінка.wait_for_timeout(1500)
                    дані = (await сторінка.content()).encode()
                    код = відповідь.status if відповідь else None
                    р['браузер_HTTP'] = код
                    if код == 200:
                        стиснути(вихід / р['файл'], дані)
                        р.update(перший_HTTP=р.get('стан', р.get('помилка')), стан=код,
                            кінцева=сторінка.url, sha256=hashlib.sha256(дані).hexdigest(),
                            кодування='utf-8', джерело='DOM звичайного Chromium')
                        р.pop('помилка', None)
                except Exception as помилка:
                    р['браузер_помилка'] = type(помилка).__name__ + ': ' + str(помилка).split('\n')[0]
                finally:
                    await сторінка.close()

        await asyncio.gather(*(одна(р) for р in мета if р.get('стан') != 200))
        await рушій.close()


def контекст(вихід):
    """Зберегти текстові контексти для читання очима разом зі шляхами DOM."""
    from bs4 import BeautifulSoup
    зразки = {р['id']: р for р in читати(вихід / 'вибірка.json')}
    огляд = []
    for м in читати(вихід / 'сторінки.json'):
        р = dict(зразки[м['id']], HTTP=м.get('стан'), доказ=м.get('файл'))
        if м.get('стан') != 200:
            огляд.append(р)
            continue
        дані = gzip.decompress((вихід / м['файл']).read_bytes())
        суп = BeautifulSoup(дані, 'html.parser')
        р['title'] = суп.title.get_text(' ', strip=True) if суп.title else ''
        р['h1'] = [т.get_text(' ', strip=True) for т in суп.select('h1')]
        р['структуровані'] = []
        for тег in суп.select('script[type="application/ld+json"]'):
            try:
                р['структуровані'].append(json.loads(тег.get_text()))
            except (ValueError, TypeError):
                pass
        for тег in суп(['script', 'style', 'noscript', 'svg']):
            тег.decompose()
        текст = суп.get_text(' ', strip=True)
        h1 = суп.find('h1')
        п = текст.find(h1.get_text(' ', strip=True)) if h1 else -1
        р['після_h1'] = текст[max(0, п):max(0, п) + 6000]
        р['склад_контексти'] = [текст[max(0, з.start() - 70):з.start() + 240]
                                for з in list(re.finditer(r'склад|состав|composition', текст, re.I))[:10]]
        р['крихти'] = [т.get_text(' ', strip=True) for т in суп.select('[class*="breadcrumb"], [class*="Breadcrumb"], [itemtype*="BreadcrumbList"]')][:8]
        огляд.append(р)
    записати(вихід / 'контекст.json', огляд)
    print('HTTP:', dict(collections.Counter(р['HTTP'] for р in огляд)))


def сирі(вихід):
    """Зафіксувати сирі рядки вибірки з доступної смуги 5.3 без змін журналів."""
    зразки = {р['url']: р for р in читати(вихід / 'вибірка.json')}
    журнал = Path.home() / '.cache/liusterko/harvest-5.3-20261029/сирі'
    знайдені = {}
    джерела = {}
    from журнал_карток import прочитати
    for файл in sorted(журнал.glob('*.jsonl')):
        рядки, помилки = прочитати(файл)
        if помилки:
            raise ValueError('Пошкоджений журнал: ' + str(файл))
        джерела[файл.name] = hashlib.sha256(файл.read_bytes()).hexdigest()
        for ряд in рядки:
            if ряд.get('url') in зразки and ряд.get('картка'):
                знайдені[ряд['url']] = dict(джерело=файл.name, рядок=ряд)
    стиснути(вихід / 'сирі_вибірки.json.gz', json.dumps(знайдені, ensure_ascii=False, sort_keys=True, indent=2).encode())
    записати(вихід / 'джерела_жнив.json', dict(шлях=str(журнал), sha256=джерела,
        вибірка_всього=len(зразки), вибірка_знайдено=len(знайдені)))
    print('Сирі жнива:', len(знайдені), 'з', len(зразки))


def кадри(вихід):
    """Зберегти 20 кадрів прикладів і контактний аркуш для огляду."""
    import concurrent.futures
    import requests
    from PIL import Image, ImageDraw, ImageFont
    зразки = читати(вихід / 'приклади_20.json')
    тека = вихід / 'кадри'
    тека.mkdir(exist_ok=True)
    довіра = сертифікати()
    def один(р):
        """Отримати незмінений кадр, вказаний каталогом."""
        шлях = тека / (р['id'].replace('@', '_') + '.jpg')
        if not шлях.exists():
            try:
                відповідь = requests.get(р['кадр'], verify=довіра, timeout=25)
                відповідь.raise_for_status()
                Image.open(io.BytesIO(відповідь.content)).verify()
                шлях.write_bytes(відповідь.content)
            except (requests.RequestException, OSError) as помилка:
                return dict(id=р['id'], помилка=str(помилка))
        return dict(id=р['id'], файл=str(шлях.relative_to(вихід)).replace('\\', '/'), sha256=hashlib.sha256(шлях.read_bytes()).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as пул:
        мета = list(пул.map(один, зразки))
    записати(вихід / 'кадри.json', мета)
    аркуш = Image.new('RGB', (1200, 1600), 'white')
    малюнок = ImageDraw.Draw(аркуш)
    шрифт = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    for і, (р, м) in enumerate(zip(зразки, мета)):
        x, y = (і % 4) * 300, (і // 4) * 320
        if 'файл' in м:
            знімок = Image.open(вихід / м['файл']).convert('RGB')
            знімок.thumbnail((290, 260))
            аркуш.paste(знімок, (x + (300 - знімок.width) // 2, y))
        малюнок.text((x + 5, y + 262), р['id'], fill='black', font=шрифт)
        малюнок.text((x + 5, y + 281), р['назва_суду'][:31], fill='black', font=шрифт)
        малюнок.text((x + 5, y + 300), ' / '.join(str(р['читачі'][к].get('слот')) for к in ['вид_офера', 'жниварка_повтор']), fill='black', font=шрифт)
    аркуш.save(вихід / 'приклади_20.png')


def main():
    """Виконати явно вибрані дії зі свідченнями."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--вихід', type=Path, default=КОРІНЬ / 'аудит/проби/річ_запис_каталог_2026_10_30')
    парсер.add_argument('--доступ', action='store_true')
    парсер.add_argument('--сирі', action='store_true')
    парсер.add_argument('--кадри', action='store_true')
    а = парсер.parse_args()
    записати(а.вихід / 'вибірка.json', поля_вибірки(читати(а.вихід / 'вибірка.json')))
    if а.доступ:
        мета = читати(а.вихід / 'сторінки.json')
        архів(а.вихід, мета)
        asyncio.run(браузер(а.вихід, мета))
        записати(а.вихід / 'сторінки.json', мета)
    if а.сирі:
        сирі(а.вихід)
    if а.кадри:
        кадри(а.вихід)
    контекст(а.вихід)


if __name__ == '__main__':
    main()
