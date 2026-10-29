# -*- coding: utf-8 -*-
"""Рядок 5617: чи годиться мапа сайту (sitemap) як дешевий щоденний свідок «річ ще на сайті» — один-два запити на крамницю
замість запиту на кожну річ. Та сама вибірка, що в `жниварка_логіка_зникли.py` (сід 17, порівну з крамниці). Мапа — з robots.txt
(Sitemap:) або /sitemap.xml, вкладені — до 20 файлів (спершу товарні), без мап зображень; 2 с між запитами хоста. Друкує: крамниць
із мапою й <lastmod>; «нема в мапі» для крамниць за JS-перевіркою; і, коли поруч /tmp/жниварка_зникли.json (пише проба «зникли»),
звірку мапи зі сторінкою речі. Запуск: cd джерела && python3 проби/жниварка_логіка_мапа.py [N]   (мережа до крамниць, ~3 хв)"""
import collections as C, concurrent.futures as КФ, gzip, json, os, random, re, sys, time, urllib.parse as У, urllib.request as Р  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф  # noqa: E402
прод, за = {str(р['id']).split('@')[0] for р in Ф._прочитати_каталог(Ф.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']}, C.defaultdict(list)
for о in Ф.читати_yml(Ф.каталог_на_диску())[0]:
    if о['id'].split('@')[0] in прод: за[о['магазин']].append(о)
random.seed(17); к = round((int(sys.argv[1]) if len(sys.argv) > 1 else 500) / len(за))
вибірка, шлях = {м: random.sample(л, min(к, len(л))) for м, л in sorted(за.items())}, lambda а: re.sub(r'^/(?:ua|uk|ru|en)(?=/)', '', У.unquote(У.urlparse(а).path)).rstrip('/').lower()
def взяти(адреса):
    """Текст відповіді ('' на збій); .gz розпаковує; пауза 2 с перед запитом — на хост працює один потік."""
    try: time.sleep(2); б = Р.urlopen(Р.Request(адреса, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36'}), timeout=60).read(40_000_000)
    except Exception: return ''
    return (gzip.decompress(б) if б[:2] == b'\x1f\x8b' else б).decode('utf-8', 'ignore')
def мапа(м):
    """(крамниця, шляхи сторінок мапи, чи є <lastmod>, файлів мапи)."""
    хост = У.urlparse(вибірка[м][0]['url']).netloc; шляхи, lastmod, файлів = set(), False, 0
    черга = re.findall(r'(?im)^\s*sitemap:\s*(\S+)', взяти('https://%s/robots.txt' % хост)) or ['https://%s/sitemap.xml' % хост]
    while черга and файлів < 20:
        т = взяти(черга.pop(0)); файлів += 1; lastmod |= '<lastmod>' in т
        for а in re.findall(r'<loc>\s*(?:<!\[CDATA\[)?\s*([^<\]\s]+)', т):
            if not re.search(r'\.xml(?:\.gz)?(?:\?|$)', а): шляхи.add(шлях(а))
            elif 'image' not in а: черга.append(а)
        черга.sort(key=lambda а: not re.search(r'product|catalog|tovar|goods|shop', а))
    return м, шляхи, lastmod, файлів
with КФ.ThreadPoolExecutor(len(вибірка)) as пул: мапи = {м: (ш, л, ф) for м, ш, л, ф in пул.map(мапа, вибірка)}
нема = {о['id']: шлях(о['url']) not in мапи[м][0] for м, л in вибірка.items() if мапи[м][0] for о in л}
print('крамниць %d · з мапою %d (з <lastmod> %d) · файлів мап %d · речей вибірки в крамницях з мапою %d, нема в мапі %d' % (len(мапи), sum(bool(ш) for ш, _, _ in мапи.values()), sum(bool(ш) and л for ш, л, _ in мапи.values()), sum(ф for _, _, ф in мапи.values()), len(нема), sum(нема.values())) + ' · без мапи: %s' % [м for м, (ш, _, _) in мапи.items() if not ш])
if os.path.exists('/tmp/жниварка_зникли.json'):
    прич = C.defaultdict(lambda: 'невідомо', json.load(open('/tmp/жниварка_зникли.json', encoding='utf-8'))); ЗНИКЛА = {'HTTP 404', 'HTTP 410', 'порожня сторінка', 'переадресація без товару', 'сторінка без товару'}
    кл = lambda п: 'зникла' if п in ЗНИКЛА else 'розпродана' if п == 'OutOfStock' else 'невідомо' if п.startswith(('HTTP', 'JS', 'невідомо')) else 'жива'  # noqa: E731
    таб = C.Counter((кл(прич[і]), н) for і, н in нема.items() if і in прич)
    print('сторінка → нема в мапі: ' + ' · '.join('%s %d/%d' % (с, таб[(с, True)], таб[(с, True)] + таб[(с, False)]) for с in ('зникла', 'розпродана', 'жива', 'невідомо')))
    print('JS-перевірка — нема в мапі: %s' % {м.split('.')[0]: '%d/%d' % (sum(нема[о['id']] for о in л), len(л)) for м, л in вибірка.items() if any(прич.get(о['id']) == 'JS-перевірка' for о in л) and мапи[м][0]})
    print('розбіжності за крамницями (зникла, але в мапі / жива, але нема): %s' % {м.split('.')[0]: (sum(кл(прич[о['id']]) == 'зникла' and not нема[о['id']] for о in л), sum(кл(прич[о['id']]) == 'жива' and нема[о['id']] for о in л)) for м, л in вибірка.items() if мапи[м][0] and any((кл(прич[о['id']]) == 'зникла') != нема[о['id']] and кл(прич[о['id']]) in ('зникла', 'жива') for о in л)})
