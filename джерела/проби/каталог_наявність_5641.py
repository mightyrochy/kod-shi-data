"""Друкує наявність у каталозі й пулі та перевіряє три стани через producer."""
import copy, gzip, os, re, sys, tempfile, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф
from композитор_придатні import _придатні


def проба():
    """Звіряє структурне поле фіда із записом і чинним фільтром пулу."""
    шлях = sys.argv[1] if len(sys.argv) > 1 else 'каталог_повний.xml'
    каталог = Ф._прочитати_каталог(шлях, ліміт_фото=0)['каталог']
    пул, _ = _придатні(каталог, [], [], {})
    print('каталог / ключ / недоступні / недоступні у пулі:', len(каталог),
          sum('available' in р for р in каталог),
          sum(р.get('available') is False for р in каталог),
          sum(р.get('available') is False for р in пул))
    корінь = ET.parse(шлях).getroot(); офери = корінь.find('.//offers')
    ід = {str(р['id']).split('@')[0] for р in каталог}
    зразок = next(о for о in офери if о.get('id') in ід)
    for о in list(офери): офери.remove(о)
    for номер, стан in enumerate(('true', 'false', None)):
        о = copy.deepcopy(зразок); о.set('id', 'availability-' + str(номер))
        if стан is None: о.attrib.pop('available', None)
        else: о.set('available', стан)
        for залишок in о.findall('stock_quantity'): о.remove(залишок)
        офери.append(о)
    with tempfile.TemporaryDirectory() as тека:
        файл = os.path.join(тека, 'проба.xml'); ET.ElementTree(корінь).write(файл, encoding='utf-8')
        записи = Ф._прочитати_каталог(файл, ліміт_фото=0)['каталог']
        стани = {р['id'].split('@')[0]: р.get('available') for р in записи}
        assert стани == {'availability-0': True, 'availability-1': False, 'availability-2': None}, стани
        пул, _ = _придатні(записи, [], [], {})
        assert {р.get('available') for р in пул} == {True, None}
        print('true / false / unknown:', стани, 'пул:', [р.get('available') for р in пул])


if __name__ == '__main__':
    проба()
