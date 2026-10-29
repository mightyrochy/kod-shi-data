"""5192: наявність кодів фото, чисел фіда й незмінених рядків по точних ключах."""
import gzip, hashlib, json, math, sys, xml.etree.ElementTree as E
from collections import defaultdict
from pathlib import Path
def main():
    корінь = Path(__file__).resolve().parents[2]; тека = корінь / 'джерела/дані_5191_5194'
    сх = json.loads((тека / 'поля.json').read_text()); пер = сх['переліки']
    речі = E.fromstring(gzip.decompress((корінь/'каталог_повний.xml.gz').read_bytes())).findall('.//offer')
    архів = (корінь/'джерела/каталог_збагачення.json.gz').read_bytes(); зб = json.loads(gzip.decompress(архів))
    форми = [з.get('з_v1') if з.get('колір_р3') else з for з in зб.values()]
    форми = [з for з in форми if isinstance(з, dict) and 'помилка' not in з and (з.get('впевненість') or 0) >= .5]
    def число(з):
        try:
            return math.isfinite(float(з))
        except ValueError:
            return False
    ключі = set(сх['текстові_ключі_5192']); числові = set(сх['числові_ключі_5192'])
    рядки, записи, числа, інші = defaultdict(list), defaultdict(set), defaultdict(set), defaultdict(int)
    for і, р in enumerate(речі):
        for п in р.findall('param'):
            к, з = п.get('name'), ''.join(п.itertext())
            if not з.strip(): continue
            if к in числові and число(з): числа[к].add(і)
            elif к in ключі or к in числові: рядки[к].append(з); записи[к].add(і)
            else: інші[к] += 1
    вхід = {к: sorted(set(з)) for к, з in sorted(рядки.items())}; фото = {}
    for к, п in (('крій','cut'), ('довжина','length'), ('матеріал','fabric'), ('візерунок','pattern')):
        відомі = [з[к] for з in форми if з.get(к) in пер[п]]
        фото[к] = {'код': len(відомі), 'null': sum(з.get(к) is None for з in форми),
                   'поза_enum': sum(з.get(к) is not None and з[к] not in пер[п] for з in форми), 'різні': sorted(set(відомі))}
    факти = {'raw': len(речі), 'enriched': len(зб), 'форма_ворота_0_5': len(форми), 'фото': фото,
             'числа_синтаксис': {к: len(з) for к, з in sorted(числа.items())},
             'поля': {к: [len(записи[к]), len(рядки[к]), len(з)] for к, з in вхід.items()},
             'поза_вибіркою_ключів': len(інші), 'поза_вибіркою_входжень': sum(інші.values()),
             'enriched_sha256': hashlib.sha256(архів).hexdigest()}
    байти = (json.dumps(вхід, ensure_ascii=False, indent=2)+'\n').encode()
    print(json.dumps(факти, ensure_ascii=False, sort_keys=True)); print('вхід_sha256', hashlib.sha256(байти).hexdigest())
    if '--зберегти' in sys.argv: (тека / 'рядки_5192.json.gz').write_bytes(gzip.compress(байти, mtime=0))
if __name__ == '__main__':
    main()
