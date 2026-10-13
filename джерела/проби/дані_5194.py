"""5194: числа ошатності/блиску та текстові входи, без нових вердиктів."""
import gzip, hashlib, json, sys, xml.etree.ElementTree as E
from collections import defaultdict, Counter
from pathlib import Path
корінь = Path(__file__).resolve().parents[2]; тека = корінь / 'джерела/дані_5191_5194'
речі = E.fromstring(gzip.decompress((корінь/'каталог_повний.xml.gz').read_bytes())).findall('.//offer')
зб = json.loads(gzip.decompress((корінь/'джерела/каталог_збагачення.json.gz').read_bytes()))
форми = {к: з.get('з_v1') if з.get('колір_р3') else з for к, з in зб.items()}
форми = {к: з for к, з in форми.items() if isinstance(з, dict) and 'помилка' not in з and (з.get('впевненість') or 0) >= .5}
def чинне(з, к, мін, макс):
    return type(з.get(к)) is int and мін <= з[к] <= макс
відомі = {к for к, з in форми.items() if чинне(з, 'формальність', 1, 10)}
рядки, записи = defaultdict(list), defaultdict(set)
for і, р in enumerate(речі):
    пар = р.findall('param')
    магазин = next((''.join(п.itertext()) for п in пар if п.get('name') in ('магазин','Магазин')), '')
    ід = р.get('id')+'@'+магазин.strip().lower()
    for к in ('name', 'description', 'опис', 'Декор', '~Декор', 'декор', '~Стиль', '~Теги'):
        вузли = р.findall(к) if к in ('name', 'description') else [п for п in пар if п.get('name') == к]
        for п in вузли:
            з = ''.join(п.itertext())
            if з.strip():
                рядки[к].append(з); записи[к].add(і)
                if ід not in відомі and к in ('name','description','опис'):
                    рядки['без_числа:'+к].append(з); записи['без_числа:'+к].add(і)
вхід = {к: sorted(set(з)) for к, з in sorted(рядки.items())}
факти = {'raw': len(речі), 'форма_ворота_0_5': len(форми),
         'формальність_число': len(відомі), 'блиск_число': sum(чинне(з,'блиск',0,3) for з in форми.values()),
         'формальність_розподіл': dict(Counter(з['формальність'] for з in форми.values() if чинне(з,'формальність',1,10))),
         'поля': {к: [len(записи[к]), len(рядки[к]), len(з)] for к, з in вхід.items()},
         'код_трауру_raw': sum(any(п.get('name') == 'траурний_регістр' for п in р.findall('param')) for р in речі)}
байти = (json.dumps(вхід, ensure_ascii=False, indent=2)+'\n').encode()
print(json.dumps(факти, ensure_ascii=False, sort_keys=True)); print('вхід_sha256', hashlib.sha256(байти).hexdigest())
if '--зберегти' in sys.argv:
    (тека / 'рядки_5194.json.gz').write_bytes(gzip.compress(байти, mtime=0))
