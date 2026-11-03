"""Межа вибірки: метод PR #2514, аудит/проби/річ_запис_блок.py@8cdf2d8e.

Це запасна межа незалежного виміру 30.10; рецепт і Product мають перевагу.
Не переписує розбір жнив і не вважає відсутність межі успішним звуженням.
"""
import html
import re

КОШИК = re.compile(r'кошик|корзин|купити|придбати|додати|в кошик|add to cart|buy|замовити', re.I)
ЧУЖІ_КЛАСИ = re.compile(r'related|recommend|similar|also|upsell|cross-?sell|viewed|recent|carousel|swiper|footer|header|navbar|menu|popular|other|rekomen|vidpovid|reviews?-list|catalog-list|product-list|products-list|product-grid|collection', re.I)


def норма(т):
    """Зводить текст до слів для пошуку заголовка з JSON-LD."""
    т = html.unescape(т or '').lower().replace('’', "'").replace('ʼ', "'").replace('`', "'")
    return ' '.join(re.sub(r"[^\w%']+", ' ', т).split())


def брудний(тег):
    """Чи містить піддерево блок інших товарів, меню, колонтитул чи слайдер."""
    for д in тег.find_all(True):
        if д.name in ('footer', 'header', 'nav', 'aside'):
            return True
        ознака = ' '.join(д.get('class') or []) + ' ' + (д.get('id') or '')
        if ЧУЖІ_КЛАСИ.search(ознака):
            return True
    return False


def блок_товару(суп, імена):
    """Знаходить найвищого чистого предка заголовка за методом вихідного виміру."""
    ціль = суп.find('h1')
    if not ціль:
        for тег in суп.find_all(True):
            if тег.name not in ('script', 'style', 'title', 'meta') and not тег.find(True) and норма(тег.get_text()) in імена and норма(тег.get_text()):
                ціль = тег
                break
    if not ціль:
        return None, None
    вузол, чистий = ціль, None
    while вузол.parent is not None and вузол.parent.name not in ('[document]', 'html', 'body'):
        вузол = вузол.parent
        if брудний(вузол):
            break
        чистий = вузол
    if чистий is not None and len(чистий.get_text(' ', strip=True)) > 200:
        return чистий, ціль
    вузол = ціль
    while вузол.parent is not None and вузол.parent.name not in ('[document]', 'html', 'body'):
        вузол = вузол.parent
        текст = вузол.get_text(' ', strip=True)
        if len(текст) > 300 and КОШИК.search(текст):
            return вузол, ціль
    return вузол, ціль
