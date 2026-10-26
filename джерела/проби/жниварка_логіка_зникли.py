# -*- coding: utf-8 -*-
"""Рядок 5617, перший вимір: частка речей каталогу, що зникли з сайтів від жнив (07.09 — 38 днів, 18.09 — 27). Вибірка порівну з крамниць (500, сід 17), потік на хост, 2 с
перед запитом. Зникла — 404/410, порожня, переадресація без товару, сторінка без товару в крамниці, що розмічує товар (≥ 3 з Product/og); розпродана — лише OutOfStock;
403/5xx/збій/JS-перевірка (не обходимо) — невідомо. Зважено речами крамниці, 95 % Вілсона з ефективним n; пише /tmp/жниварка_зникли.json. Мережа, ~2 хв; аргумент — N."""
import collections as C, concurrent.futures as КФ, json, math, os, random, re, sys, tempfile, time, urllib.parse as У, urllib.request as Р  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import feed as Ф  # noqa: E402
прод, за = {str(р['id']).split('@')[0] for р in Ф._прочитати_каталог(Ф.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']}, C.defaultdict(list)
for о in Ф.читати_yml(Ф.каталог_на_диску())[0]:
    if о['id'].split('@')[0] in прод: за[о['магазин']].append(о)
random.seed(17); к = round((int(sys.argv[1]) if len(sys.argv) > 1 else 500) / len(за)); ВСЬОГО = sum(map(len, за.values()))
вибірка, шлях = {м: random.sample(л, min(к, len(л))) for м, л in sorted(за.items())}, lambda а: re.sub(r'^/(?:ua|uk|ru|en)(?=/)', '', У.urlparse(а).path).rstrip('/').lower()
ДОСТ = re.compile(r'(?:schema\.org\\?/|"availability"\s*:\s*"|availability"\s+content=")([A-Za-z ]{2,24})', re.I)
ТОВАР = re.compile(r'"@type"\s*:\s*\[?\s*"Product(?:Group)?"|schema\.org\\?/Product\b|og:type"\s+content="product', re.I)
def взяти(адреса):
    """(код, кінцева адреса, текст); пауза 2 с перед запитом — на хост працює один потік."""
    try: time.sleep(2); в = Р.urlopen(Р.Request(адреса, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 Safari/537.36'}), timeout=30); return в.status, в.geturl(), в.read(4_000_000).decode('utf-8', 'ignore')
    except Р.HTTPError as п: return п.code, адреса, ''
    except Exception: return 'збій', адреса, ''
def крамниця(м):
    """Причина стану кожної речі вибірки однієї крамниці."""
    сирі = [(о,) + взяти(о['url']) for о in вибірка[м]]; розмічує = sum(код == 200 and bool(ТОВАР.search(т)) for _, код, _, т in сирі) >= 3
    def причина(о, код, кін, т):
        if код != 200 or len(т) < 3000: return 'HTTP %s' % код if код != 200 else 'JS-перевірка' if '<script' in т else 'порожня сторінка'
        переадр, д = шлях(кін) != шлях(о['url']), {x.lower().replace(' ', '') for x in ДОСТ.findall(т)}; наяв = 'InStock' if д & {'instock', 'limitedavailability', 'preorder', 'presale', 'backorder'} else 'OutOfStock' if д & {'outofstock', 'soldout', 'discontinued', 'oos'} else 'товар без наявності'
        if not ТОВАР.search(т): return 'переадресація без товару' if переадр else 'сторінка без товару' if розмічує else 'без розмітки'
        return 'переадресація на товар' if переадр and наяв != 'OutOfStock' else наяв  # розпродане після переадресації — розпродане
    return м, [(р[0], причина(*р)) for р in сирі]
with КФ.ThreadPoolExecutor(len(вибірка)) as пул: рез = dict(пул.map(крамниця, вибірка))
ЗНИКЛА, РОЗПР, ЖИВА = {'HTTP 404', 'HTTP 410', 'порожня сторінка', 'переадресація без товару', 'сторінка без товару'}, {'OutOfStock'}, {'InStock', 'товар без наявності', 'без розмітки', 'переадресація на товар'}
ВИЗН, все = ЗНИКЛА | РОЗПР | ЖИВА, [(о, п) for р in рез.values() for о, п in р]; json.dump({о['id']: п for о, п in все}, open(os.path.join(tempfile.gettempdir(), 'жниварка_зникли.json'), 'w'), ensure_ascii=False)
def частка(клас, умова=lambda о: True):
    """Зважена речами крамниці частка класу серед визначених, 95 % Вілсона з ефективним n (Korn–Graubard), покриття каталогу."""
    стр = {м: в for м, в in ((м, [п in клас for о, п in р if п in ВИЗН and умова(о)]) for м, р in рез.items()) if в}; Ч = sum(len(за[м]) for м in стр); n = sum(map(len, стр.values()))
    p = sum(len(за[м]) / Ч * sum(в) / len(в) for м, в in стр.items()); v = sum((len(за[м]) / Ч) ** 2 * sum(в) / len(в) * (1 - sum(в) / len(в)) / len(в) * (1 - len(в) / len(за[м])) for м, в in стр.items())
    н = (min(n, p * (1 - p) / v) if v else n) or 1; ц, r = (p + 1.92 / н) / (1 + 3.84 / н), 1.96 * math.sqrt(p * (1 - p) / н + 0.96 / н ** 2) / (1 + 3.84 / н)
    return '%.1f %% [%.1f–%.1f] ≈ %d речей; визначено %d у %d крамницях = %.0f %% каталогу' % (100 * p, 100 * max(0, ц - r), 100 * (ц + r), p * Ч, n, len(стр), 100 * Ч / ВСЬОГО)
лік = lambda клас, умова: '%d/%d' % (sum(п in клас for о, п in все if умова(о) and п in ВИЗН), sum(п in ВИЗН for о, п in все if умова(о)))  # noqa: E731
print('каталог %d речей, %d крамниць · вибірка %d (по %d) · причини %s\nЗНИКЛИ з сайту: %s\nНЕ КУПИТИ (зникли + розпродані): %s' % (ВСЬОГО, len(за), len(все), к, dict(C.Counter(п for _, п in все).most_common()), частка(ЗНИКЛА), частка(ЗНИКЛА | РОЗПР)))
print('  серед «є» в день жнив не купити зараз: %s\n  зникли (з визначених): знято 07.09 — %s, 18.09 — %s · InStock серед available=false %s' % (частка(ЗНИКЛА | РОЗПР, lambda о: о['available']), лік(ЗНИКЛА, lambda о: (о['параметри'] or {}).get('знято') == '2026-09-07'), лік(ЗНИКЛА, lambda о: (о['параметри'] or {}).get('знято') == '2026-09-18'), лік({'InStock'}, lambda о: о['available'] is False)))
print('крамниці, зникла/розпродана/невідомо з вибірки: %s' % ' '.join('%s %d/%d/%d' % (м.split('.')[0], *(sum(п in кл for _, п in р) for кл in (ЗНИКЛА, РОЗПР)), sum(п not in ВИЗН for _, п in р)) for м, р in рез.items() if any(п not in ЖИВА for _, п in р)))
