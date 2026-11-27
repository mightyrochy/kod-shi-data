# Пункт 2 наряду: які колонки кандидата стилістка використала. Вхід — теки проходів (як у `розбір.py`).
# «Використала» = у текстах її відповідей (складання, ремонт, вибір, пояснення: задум, підпис образу, «обрано чому»,
# знахідка/заміна) є слова цього поля, а в одній з названих у тексті речей поле має значення. Слова — англійські, бо
# модель відповідає англійською; це лексичне сито, а не доказ вибору: поле могло рухати вибір без слова в тексті
# («гіпотеза: що не видно в тексті» — перевіряє пункт 3 зняттям поля).
# Запуск: python3 поля.py <тека> [<тека> ...] > поля.json
import json, re, sys, collections

СЛОВА = {
    'price': r'price|cheap|expens|budget|afford|cost|₴',
    'kind': r'\b(top|bottom|dress|set|outerwear|shoes|bag|belt|headwear|scarf|jewel|earring|bead|necklace|bracelet|ring|brooch)\w*',
    'color': r'\b(black|white|grey|gray|brown|chocolate|navy|blue|red|green|olive|beige|cream|ivory|burgundy|cherry|camel|tan|pink|purple|lilac|yellow|orange|khaki|taupe|charcoal|cognac|ecru|milk|stone|pearl|silver|gold)\b',
    'hex': r'\bhex\b|#[0-9a-fA-F]{6}',
    'family': r'colour family|color family|\bfamily\b',
    'L': r'lightness|\bL value|\bL=',
    'branch_source': r'branch_source|colour source|color source',
    'in_arc': r'in_arc|\barc\b',
    'L_from': r'L_from',
    'palette_branch': r'palette branch|\bbranch\b',
    'type': r'\b(sweater|jumper|knit|blouse|shirt|t-shirt|tee|trousers|jeans|skirt|dress|jacket|blazer|coat|trench|boots?|sneakers|loafers|sandals|heels|bag|tote|shopper|scarf|belt|earrings|necklace|bracelet|ring|cardigan|vest|top|suit)\b',
    'length': r'\blength\b|\bmidi\b|\bmaxi\b|\bmini\b|knee|ankle|cropped',
    'garment_length': r'hip-length|thigh|hem|garment length|cm long|cropped|waist-length',
    'fabric': r'wool|cashmere|leather|cotton|silk|linen|knit|denim|suede|polyester|viscose|nylon|tweed|satin|fleece|cord|merino|fabric|material|textile',
    'fabric_season': r'season|warm enough|winter|summer|heavy|lightweight|breathable|insulat',
    'cut': r'\bcut\b|straight|slim|fitted|relaxed|wide|tailored|a-line|oversized|loose|tapered',
    'pattern': r'pattern|print|striped|stripe|check|floral|plaid|polka|solid',
    'shine': r'shine|matte|glossy|satin|sheen|shiny',
    'formality': r'formal|casual|smart|dressy|dress code|polished',
    'secondary_color': r'secondary|accent|trim|contrast',
    'heel': r'\bheel',
    'sole': r'\bsole\b|tread|grip',
    'sleeve': r'sleeve',
    'neckline': r'neckline|v-neck|round neck|crew|collar|scoop',
    'rise': r'\brise\b|high-waist|high waist|waistband|low-rise',
    'register': r'register|elegan|dressier|dressed up|dressed-down',
    'cut_tier': r'cut tier|tier',
    'metal': r'metal|\bgold\b|silver|brass|steel',
    'layer_warmth': r'warmth|warm layer|layer|insulat|cosy|cozy',
    'reason': r'\breason\b|why this item',
    'sources': r'provenance|source|stated by the shop|from the shop|catalogue says|inferred',
    'rank_facts': r'rank|wave|distance|window_share',
}
ТЕКСТОВІ = ('Build outfits', 'Improve the outfits', 'Choose one of the offered', 'Explain the chosen outfit')


def рядки(о, вих):
    if isinstance(о, str):
        вих.append(о)
    elif isinstance(о, dict):
        for к, в in о.items():
            if к not in ('items', 'item', 'n', 'id', 'pole', 'version'):
                рядки(в, вих)
    elif isinstance(о, list):
        for в in о:
            рядки(в, вих)


підсумок = collections.defaultdict(lambda: dict(згадок=0, текстів=0, проходи=set(), пул_значущих=0, пул_усього=0))
колонки_всі = []
for тека in sys.argv[1:]:
    ряди = {}
    відповіді = []
    for р in open(f'{тека.rstrip("/")}/обміни.jsonl', encoding='utf8'):
        д = json.loads(р)
        if 'с' not in д:
            continue
        з = д['запит']
        гол = з[:700] if not з.startswith('Catalogue photo') else з[з.find('"role"'):][:300]
        if not any(т in гол for т in ТЕКСТОВІ):
            continue
        try:
            q = json.loads(з[з.find('{"version"'):]) if з.startswith('Catalogue photo') else json.loads(з)
        except Exception:
            continue
        пул = q.get('pool')
        if 'Build outfits' in гол and пул:
            for ряд in пул['rows']:
                ряди[ряд[0]] = dict(zip(пул['cols'], ряд))
            for к in пул['cols']:
                if к not in колонки_всі:
                    колонки_всі.append(к)
            for к in пул['cols']:
                п = підсумок[к]
                п['пул_усього'] += len(пул['rows'])
                п['пул_значущих'] += sum(1 for ряд in пул['rows'] if dict(zip(пул['cols'], ряд))[к] not in ('unknown', None, [], {}))
        try:
            в = json.loads(д['відповідь'])
        except Exception:
            continue
        відповіді.append(в)
    for в in відповіді:
        оф = в.get('outfits') if isinstance(в, dict) else None
        вузли = оф if оф else [в]
        for ф in вузли:
            рядкиФ = []
            рядки(ф, рядкиФ)
            текст = ' '.join(рядкиФ)
            назви = set(ф.get('items', []) if isinstance(ф, dict) and isinstance(ф.get('items'), list) else [])
            назви |= set(re.findall(r'#\d+·\d+', json.dumps(ф, ensure_ascii=False)))
            for к, шаблон in СЛОВА.items():
                п = підсумок[к]
                п['текстів'] += 1
                if re.search(шаблон, текст, re.I):
                    п['згадок'] += 1
                    п['проходи'].add(тека)
вихід = {}
for к in колонки_всі:
    п = підсумок[к]
    вихід[к] = dict(згадок=п['згадок'], текстів=п['текстів'], проходів_зі_згадкою=len(п['проходи']),
                    частка_рядків_зі_значенням=round(п['пул_значущих'] / п['пул_усього'], 3) if п['пул_усього'] else None)
json.dump(вихід, sys.stdout, ensure_ascii=False, indent=1)
