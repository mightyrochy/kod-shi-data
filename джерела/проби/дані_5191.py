"""5191: точні коди фіда й залишок тексту; не виконує читачів слів продукту."""
import gzip, hashlib, json, sys, xml.etree.ElementTree as E
from collections import Counter, defaultdict
from pathlib import Path
def main():
    корінь = Path(__file__).resolve().parents[2]; тека = корінь / 'джерела/дані_5191_5194'
    схема = json.loads((тека / 'поля.json').read_text())['переліки']
    xml = (корінь / 'каталог_повний.xml.gz').read_bytes()
    дерево = E.fromstring(gzip.decompress(xml)); речі = дерево.findall('.//offer')
    def значення(р, к):
        return [''.join(п.itertext()) for п in р.findall('param') if п.get('name') == к]
    def має_код(р, к, перелік):
        return any(з in перелік for з in значення(р, к))
    неповні = [р for р in речі if not має_код(р, 'тип', схема['item_type'])]
    кат = {к.get('id') for к in дерево.findall('.//category')}
    рядки, записи = defaultdict(list), defaultdict(set)
    for і, р in enumerate(неповні):
        for к in ('name', 'description', 'опис', 'категорія_магазину', 'тип'):
            знач = [''.join(п.itertext()) for п in р.findall(к)] if к in ('name', 'description') else значення(р, к)
            for з in знач:
                if з.strip():
                    рядки[к].append(з); записи[к].add(і)
    комплекти = [р for р in речі if має_код(р, 'тип', ('костюм','комплект')) or має_код(р, 'слот', ('комплект',))]
    for к in ('name', 'description', 'опис'):
        рядки['частини:'+к] = [''.join(п.itertext()) for р in комплекти for п in (р.findall(к) if к != 'опис' else р.findall("param[@name='опис']")) if ''.join(п.itertext()).strip()]
        записи['частини:'+к] = {і for і, р in enumerate(комплекти) if (р.findtext(к) if к != 'опис' else р.findtext("param[@name='опис']"))}
    вхід = {к: sorted(set(з)) for к, з in sorted(рядки.items())}
    факти = {'raw': len(речі), 'categoryId_посилання': sum(р.findtext('categoryId') in кат for р in речі),
             'слот_enum': sum(має_код(р, 'слот', схема['slot']) for р in речі),
             'тип_raw': sum(bool(значення(р, 'тип')) for р in речі), 'тип_enum': len(речі)-len(неповні),
             'тип_неповний': len(неповні), 'різні_тип_raw': sorted({з for р in речі for з in значення(р, 'тип')}),
             'поля_частин': sum(bool(значення(р, 'частини') or значення(р, 'частини_комплекту')) for р in речі),
             'поля': {к: [len(записи[к]), len(рядки[к]), len(з)] for к, з in вхід.items()},
             'name_весь': len({р.findtext('name') for р in речі}), 'raw_sha256': hashlib.sha256(xml).hexdigest()}
    байти = (json.dumps(вхід, ensure_ascii=False, indent=2)+'\n').encode()
    print(json.dumps(факти, ensure_ascii=False, sort_keys=True))
    print('вхід_sha256', hashlib.sha256(байти).hexdigest())
    if '--зберегти' in sys.argv: (тека / 'рядки_5191.json.gz').write_bytes(gzip.compress(байти, mtime=0))
if __name__ == '__main__':
    main()
