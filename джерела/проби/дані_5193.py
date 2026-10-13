"""5193: усі назви й опорний текст — дослівні дані, без очищення або складання."""
import gzip, hashlib, json, sys, xml.etree.ElementTree as E
from collections import defaultdict
from pathlib import Path
def main():
    корінь = Path(__file__).resolve().parents[2]; тека = корінь / 'джерела/дані_5191_5194'
    речі = E.fromstring(gzip.decompress((корінь/'каталог_повний.xml.gz').read_bytes())).findall('.//offer')
    рядки, записи = defaultdict(list), defaultdict(set)
    for і, р in enumerate(речі):
        for к in ('name', 'description', 'vendor', 'опис', 'назва_сира'):
            вузли = р.findall(к) if к in ('name', 'description', 'vendor') else [п for п in р.findall('param') if п.get('name') == к]
            for п in вузли:
                з = ''.join(п.itertext())
                if з.strip():
                    рядки[к].append(з); записи[к].add(і)
    вхід = {к: sorted(set(з)) for к, з in sorted(рядки.items())}
    факти = {'raw': len(речі), 'поля': {к: [len(записи[к]), len(рядки[к]), len(з)] for к, з in вхід.items()},
             'name_порожні': len(речі)-len(записи['name']), 'name_частка_різних': len(вхід['name'])/len(речі),
             'offer_vendor_model': sum(р.get('type') == 'vendor.model' for р in речі),
             'name_ua': sum(р.find('name_ua') is not None for р in речі)}
    байти = (json.dumps(вхід, ensure_ascii=False, indent=2)+'\n').encode()
    print(json.dumps(факти, ensure_ascii=False, sort_keys=True)); print('вхід_sha256', hashlib.sha256(байти).hexdigest())
    if '--зберегти' in sys.argv:
        (тека / 'рядки_5193.json.gz').write_bytes(gzip.compress(байти, mtime=0))
if __name__ == '__main__':
    main()
