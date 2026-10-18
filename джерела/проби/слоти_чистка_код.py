"""Ф2/2.6: підготовка каталогу не маскує вгадування слота з назви."""
import gzip, os, sys, tempfile, xml.etree.ElementTree as E
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import чистка_каталогу as Ч

def main():
    """Перевірити кодову правку та незмінність невідомого слота до читання фідом."""
    xml = '<yml_catalog><shop><categories><category id="1">пояс</category>' \
          '</categories><offers>'
    for і, назва, тип in [('a', 'Пояс білий', 'leggings'),
                          ('b', 'Штани з поясом білі', 'unknown')]:
        xml += '<offer id="%s"><name>%s</name><price>100</price><categoryId>1</categoryId>' \
               '<param name="слот">пояс</param><param name="тип">%s</param>' \
               '<param name="Колір">Білий</param></offer>' % (і, назва, тип)
    xml = xml.replace('<param name="слот">пояс</param>', '', 1)
    xml += '</offers></shop></yml_catalog>'
    with tempfile.TemporaryDirectory() as т:
        вх, вих = Path(т)/'вх.xml', Path(т)/'вих.xml'
        вх.write_text(xml)
        звіт = Ч.почистити(str(вх), str(вих))
        assert звіт['слотів_виправлено'] == 1, звіт
        rows = E.parse(вих).findall('.//offer')
        слоти = {o.get('id'): next(п.text for п in o.findall('param')
                                  if п.get('name') == 'слот') for o in rows}
        assert слоти == {'a':'низ', 'b':'пояс'}, слоти
        assert Ч.класифікувати(str(вих))[4] == []
        архів = Path(т)/'сирий.gz'
        архів.write_bytes(gzip.compress(вх.read_bytes()))
        старий = Ч._МАРКЕР_СЛОТІВ.sub('', вих.read_text()).replace('<param name="слот">пояс', '<param name="слот">низ')
        вих.write_text(старий)
        стан = Ч.забезпечити_чистим(_шлях=str(вих), _архів=str(архів))
        assert стан['розпаковано_наново']
        b = E.parse(вих).find('.//offer[@id="b"]/param[@name="слот"]')
        assert b.text == 'пояс', b.text
    print('ПРОЙДЕНО: чистка виправляє слот за кодом і не вгадує невідомий із назви')

if __name__ == '__main__':
    main()
