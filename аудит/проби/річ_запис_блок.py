"""Звірити поля запису каталогу з блоком товару на збереженій сторінці (п.3 наряду Річ-запис-речі).

Запуск із кореня: python3 -X utf8 аудит/проби/річ_запис_блок.py [ТЕКА]
Читає ТЕКА/вибірка_п3.json і збережені HTML (без мережі), пише ТЕКА/блоки.json.
Блок товару — найвищий «чистий» предок заголовка товару (див. блок_товару): без колонтитулів, меню,
слайдерів і блоків інших товарів у піддереві.

Ознаки чужого тексту в самому записі (незалежно від сторінки) — мітки вкладок інтерфейсу, список інших
товарів, SEO-мета й хвіст заголовка вкладки; регулярні вирази в ОЗНАКИ.
Шматок поля «свій», якщо він є в JSON-LD / мета-описі сторінки або в тексті сторінки поза блоками
рекомендацій (ланцюжок предків без related/recommend/similar/slider/carousel/upsell/viewed/also);
«чужий» — шматок є на сторінці лише в такому блоці поза блоком товару; «нема» — шматка нема на
сторінці; поле порожнє в записі — «порожнє». Вердикт поля — за більшою часткою знаків: чужий >10 %
— «чужий», інакше нема >10 % — «нема», інакше «свій».
Це машинний огляд кандидатів; рішення очима по сумнівних записано в очі_п3.json і враховане
в річ_запис_частки.py.
"""
import collections
import gzip
import html
import json
from pathlib import Path
import re
import sys

from bs4 import BeautifulSoup

КОРІНЬ = Path(__file__).resolve().parents[2]
ТЕКА = КОРІНЬ / 'аудит/проби/річ_запис_каталог_2026_10_30'
КОШИК = re.compile(r'кошик|корзин|купити|придбати|додати|в кошик|add to cart|buy|замовити', re.I)


ОЗНАКИ = {
    'мітки_вкладок': r'(?:Характеристики|Оплата і доставка|Доставка і оплата|Доставка та оплата|Відгуки|Склад та догляд|Умови повернення|Доставка та повернення|Обміри виробу)\s+(?:Доставка|Відгуки|Умови|Склад|Новий|Обміри|[А-ЯІЇЄ])',
    'список_інших_товарів': r'Рекомендован\w+ для поєднання|З цим (?:товаром|виробом)|Вас може зацікавити|Схожі товари|Разом з цим',
    'SEO_мета': r'в\s+інтернет-магазині|за\s+ціною\s+[\d\s]+грн|Заходи і купи|^Купити\s|✅|⭐|❤|【',
}


def норма(т):
    """Звести текст до слів нижнього регістру без розділових знаків."""
    т = html.unescape(т or '').lower().replace('’', "'").replace('ʼ', "'").replace('`', "'")
    return ' '.join(re.sub(r"[^\w%']+", ' ', т).split())


def товари_ld(суп):
    """Зібрати об'єкти Product із JSON-LD."""
    знайдені = []
    for тег in суп.select('script[type="application/ld+json"]'):
        try:
            дані = json.loads(тег.get_text())
        except ValueError:
            continue
        черга = дані if isinstance(дані, list) else [дані]
        while черга:
            о = черга.pop()
            if isinstance(о, list):
                черга.extend(о)
            elif isinstance(о, dict):
                черга.extend(о.get('@graph') or [])
                тип = о.get('@type')
                if тип == 'Product' or (isinstance(тип, list) and 'Product' in тип):
                    знайдені.append(о)
    return знайдені


ЧУЖІ_КЛАСИ = re.compile(r'related|recommend|similar|also|upsell|cross-?sell|viewed|recent|carousel|swiper|footer|header|navbar|menu|popular|other|rekomen|vidpovid|reviews?-list|catalog-list|product-list|products-list|product-grid|collection', re.I)


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
    """Знайти блок товару: найвищий предок заголовка, у піддереві якого нема блоків інших товарів.

    Заголовок — h1, інакше елемент без дітей з ім'ям товару з JSON-LD. Піднімаємося, доки предок «чистий»
    (нема footer/header/nav/aside і класів related/recommend/slider/carousel/product-list тощо) і не
    корінь сторінки; блок — останній чистий предок. Не чистий жоден — сам заголовок і його найближчий
    предок із кошиком (запасний шлях) .
    """
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


def покриття_слів(шматок, текст):
    """Частка слів шматка, що є на сторінці (порядок і склад розділювачів не важливі)."""
    слова = шматок.split()
    сторінка = set(текст.split())
    return sum(с in сторінка for с in слова) / (len(слова) or 1)


def шматки(поле):
    """Розбити текстове поле запису на шматки для пошуку на сторінці."""
    частини = re.split(r'(?<=[.!?;])\s+|\s*[•·|]\s*|\n+', поле or '')
    return [ч.strip() for ч in частини if len(норма(ч)) >= 12] or ([поле.strip()] if поле and норма(поле) else [])


def місце(суп, шматок, блок):
    """Описати місце шматка на сторінці: ланцюжок предків, найближчий заголовок, чи схоже на блок інших товарів."""
    ключ = норма(шматок)[:60]
    знайдено = None
    for тег in суп.find_all(True):
        if тег.name in ('script', 'style', 'head', 'title', 'meta', 'noscript'):
            continue
        if ключ in норма(тег.get_text(' ', strip=True)) and not any(ключ in норма(д.get_text(' ', strip=True)) for д in тег.find_all(True, recursive=False)):
            знайдено = тег
            break
    if знайдено is None:
        return dict(де='не локалізовано')
    ланцюг, предок = [], знайдено
    for _ in range(5):
        if предок is None or предок.name in ('[document]', 'body', 'html'):
            break
        ланцюг.append(предок.name + ('.' + '.'.join(предок.get('class') or [])[:40] if предок.get('class') else '') + ('#' + предок['id'][:20] if предок.get('id') else ''))
        предок = предок.parent
    заголовок = знайдено.find_previous(['h1', 'h2', 'h3', 'h4'])
    в_блоці = False
    вище = знайдено
    while вище is not None:
        if вище is блок:
            в_блоці = True
        вище = вище.parent
    весь = ' '.join(ланцюг)
    return dict(де=' < '.join(ланцюг), заголовок_перед=заголовок.get_text(' ', strip=True)[:60] if заголовок else None,
                у_блоці_товару=в_блоці, схоже_на_інші_товари=bool(re.search(r'related|recommend|similar|swiper|carousel|upsell|viewed|also', весь, re.I)))


def перевірити_поле(суп, блок, текст_блоку, текст_сторінки, ld_текст, поле, значення):
    """Віднести кожен шматок поля до свого блоку, чужого або відсутнього."""
    if not (значення or '').strip():
        return dict(вердикт='порожнє')
    підсумок = collections.Counter()
    приклади = []
    for ш in шматки(значення):
        н = норма(ш)
        if н in текст_блоку or н in ld_текст:
            підсумок['свій'] += len(н)
        elif н in текст_сторінки:
            де = місце(суп, ш, блок)
            чужий = де.get('схоже_на_інші_товари') and not де.get('у_блоці_товару')
            підсумок['чужий' if чужий else 'свій'] += len(н)
            if чужий:
                приклади.append(dict(шматок=ш[:160], **де))
        elif покриття_слів(н, текст_сторінки) >= 0.9:
            підсумок['свій'] += len(н)
        else:
            підсумок['нема'] += len(н)
            приклади.append(dict(шматок=ш[:160], де='нема на сторінці', покриття=round(покриття_слів(н, текст_сторінки), 2)))
    разом = sum(підсумок.values()) or 1
    if підсумок['чужий']:
        вердикт = 'чужий'
    elif підсумок['нема'] / разом > 0.1:
        вердикт = 'нема'
    else:
        вердикт = 'свій'
    return dict(вердикт=вердикт, частки={к: round(в / разом, 3) for к, в in підсумок.items()}, приклади=приклади[:4])


def крихти_сторінки(суп):
    """Зібрати слова крихт: BreadcrumbList у JSON-LD і елементи з класом breadcrumb."""
    назви = []
    for тег in суп.select('script[type="application/ld+json"]'):
        try:
            дані = json.loads(тег.get_text())
        except ValueError:
            continue
        черга = дані if isinstance(дані, list) else [дані]
        while черга:
            о = черга.pop()
            if isinstance(о, list):
                черга.extend(о)
            elif isinstance(о, dict):
                черга.extend(о.get('@graph') or [])
                if о.get('@type') == 'BreadcrumbList':
                    for е in о.get('itemListElement') or []:
                        ім = (е.get('item') or {}).get('name') if isinstance(е.get('item'), dict) else е.get('name')
                        if ім:
                            назви.append(норма(ім))
    for тег in суп.select('[class*="readcrumb"], [itemtype*="BreadcrumbList"], nav[aria-label*="read"]'):
        назви.append(норма(тег.get_text(' ', strip=True)))
    return назви


def перевірити_розділ(суп, розділ, назва, текст_сторінки):
    """Порівняти розділ запису з крихтами сторінки.

    З розділу вилучені службові ланки («Головна», «/», перша ланка довгого шляху — назва крамниці)
    і остання ланка, якщо це назва товару. Решта має бути в крихтах сторінки («свій»), лише деінде
    на сторінці («інший блок»: меню, сусідній товар) або нема взагалі.
    """
    ланки = [норма(л) for л in re.split(r'\s*>\s*', розділ or '') if норма(л)]
    if not ланки or ланки == ['без розділу']:
        return dict(вердикт='порожнє')
    ім = норма(назва)
    якщо_довгий = ланки[1:] if len(ланки) >= 3 else ланки
    ядро = [л for л in якщо_довгий if л not in ('головна', 'home', 'каталог', 'catalog') and not (ім and (л == ім or ім.startswith(л[:25]) and len(л) > 20))]
    if not ядро:
        return dict(вердикт='порожнє', примітка='лише службові ланки')
    сторінка = крихти_сторінки(суп)
    повні = ' | '.join(сторінка)
    у_крихтах = [л for л in ядро if л in повні]
    деінде = [л for л in ядро if л not in повні and л in текст_сторінки]
    вердикт = 'свій' if len(у_крихтах) == len(ядро) else 'інший блок' if len(у_крихтах) + len(деінде) == len(ядро) else 'нема'
    return dict(вердикт=вердикт, ланки_запису=ядро, крихти_сторінки=сторінка[:3], лише_деінде=деінде)


def перевірити_назву(імена_сторінки, назва):
    """Назва запису проти h1 / ім'я JSON-LD / заголовка сторінки."""
    н = норма(назва)
    if н in імена_сторінки['власні']:
        return dict(вердикт='свій')
    for власна in імена_сторінки['власні']:
        if власна and н.startswith(власна) and len(н) > len(власна):
            return dict(вердикт='чужий', вид='власна назва плюс хвіст: ' + назва[len(власна):][:120])
        if власна and власна.startswith(н) and len(н) >= 8:
            return dict(вердикт='свій', примітка='запис коротший за заголовок')
    if імена_сторінки['title'] and н in імена_сторінки['title']:
        return dict(вердикт='чужий', вид='назва — текст заголовка вкладки/мета, а не заголовка товару')
    return dict(вердикт='нема', вид='ні h1, ні ім’я JSON-LD, ні title не містять назви запису')


def огляд_сторінки(х, тека):
    """Повний машинний огляд однієї збереженої сторінки."""
    суп = BeautifulSoup(gzip.decompress((тека / х['файл']).read_bytes()), 'html.parser')
    ld = товари_ld(суп)
    h1 = [норма(т.get_text(' ', strip=True)) for т in суп.find_all('h1')]
    og = суп.find('meta', property='og:title')
    ld_імена = [норма(о.get('name')) for о in ld if о.get('name')]
    title = норма(суп.title.get_text()) if суп.title else ''
    імена = dict(власні=[і for і in h1 + ld_імена + [норма(og.get('content'))] if і] if og else [і for і in h1 + ld_імена if і], title=title)
    мета = [норма(м.get('content')) for м in суп.find_all('meta') if (м.get('name') or м.get('property') or '') in ('description', 'og:description', 'twitter:description')]
    ld_текст = ' '.join([норма(о.get('description')) for о in ld] + мета)
    блок, ціль = блок_товару(суп, set(імена['власні']))
    for тег in суп(['script', 'style', 'noscript', 'svg']):
        тег.decompose()
    текст_сторінки = норма(суп.get_text(' ', strip=True))
    текст_блоку = норма(блок.get_text(' ', strip=True)) if блок is not None else ''
    результат = dict(id=х['id'], крамниця=х['id'].split('@')[1], url=х['url'], файл=х['файл'],
        блок=(блок.name + '.' + '.'.join(блок.get('class') or [])[:60]) if блок is not None else None,
        блок_знаків=len(текст_блоку), заголовок=ціль.get_text(' ', strip=True)[:120] if ціль is not None else None)
    результат['назва'] = перевірити_назву(імена, х['назва'])
    for поле in ('назва', 'опис', 'склад'):
        збіги = [к for к, р in ОЗНАКИ.items() if re.search(р, х.get(поле) or '', re.M)]
        результат.setdefault(поле, {})
        if збіги:
            результат[поле + '_ознаки'] = збіги
    результат['опис'] = перевірити_поле(суп, блок, текст_блоку, текст_сторінки, ld_текст, 'опис', х.get('опис'))
    результат['склад'] = перевірити_поле(суп, блок, текст_блоку, текст_сторінки, ld_текст, 'склад', х.get('склад'))
    результат['розділ'] = перевірити_розділ(суп, х.get('розділ'), х['назва'], текст_сторінки)
    return результат


def main():
    """Обійти всю вибірку й записати блоки.json."""
    тека = Path(sys.argv[1]) if len(sys.argv) > 1 else ТЕКА
    вибірка = json.loads((тека / 'вибірка_п3.json').read_text(encoding='utf-8'))
    результати = [огляд_сторінки(х, тека) for х in sorted(вибірка, key=lambda х: х['id'])]
    (тека / 'блоки.json').write_text(json.dumps(результати, ensure_ascii=False, sort_keys=True, indent=1) + '\n', encoding='utf-8')
    for поле in ['назва', 'опис', 'склад', 'розділ']:
        print(поле, dict(collections.Counter(р[поле]['вердикт'] for р in результати)))
    print('блок не знайдено:', sum(р['блок'] is None for р in результати))


if __name__ == '__main__':
    main()
