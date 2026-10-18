"""Ф2/2.6: слот і тип із коду зберігаються в кінцевому записі каталогу."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import фід_каталог as К


def main():
    """Провести суперечливі назви крізь читання та збагачення трьох записів."""
    дані = [('a', 'Костюм білий', 'leggings', 'низ', 'легінси'),
            ('b', 'Сукня біла', 'suit', 'комплект', 'костюм'),
            ('c', 'Топ білий', 'gloves', 'рукавички', 'рукавички'),
            ('e', 'Костюм зі штанами і кардиганом білий', 'костюм', 'комплект', 'костюм_повсякденний')]
    offers = ''.join('<offer id="%s"><name>%s</name><price>100</price>'
                     '<currencyId>UAH</currencyId><categoryId>1</categoryId>'
                     '<param name="Колір">Білий</param><param name="слот">пояс</param>'
                     '<param name="тип">%s</param></offer>' % р[:3] for р in дані)
    offers += '<offer id="d"><name>Каблучка біла</name><price>100</price>' \
              '<categoryId>1</categoryId><param name="Колір">Білий</param>' \
              '<param name="слот">комплект</param><param name="тип">unknown</param></offer>'
    xml = '<yml_catalog><shop><categories><category id="1">пояс</category>' \
          '</categories><offers>' + offers + '</offers></shop></yml_catalog>'
    with tempfile.TemporaryDirectory() as т:
        шлях = Path(т) / 'каталог.xml'
        шлях.write_text(xml)
        результат = К._прочитати_каталог(str(шлях), ліміт_фото=0,
                                          кеш=str(Path(т) / 'кеш.json'), збагачення={})
        факт = {str(р['id']).split('@')[0]: (р['слот'], р['тип'])
                for р in результат['каталог']}
        очікувано = {р[0]: р[3:] for р in дані}
        очікувано['d'] = ('комплект', None)
        assert факт == очікувано, факт
    print('ПРОЙДЕНО: три коди, unknown і старий грубий тип без нової підміни підтипу')


if __name__ == '__main__':
    main()
