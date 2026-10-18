"""Ф2/2.6: слот і тип із коду зберігаються в кінцевому записі каталогу."""
import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import фід_каталог as К


def main():
    """Провести суперечливі назви крізь читання та збагачення трьох записів."""
    дані = [('a', 'Костюм білий', 'leggings', 'низ', 'легінси'),
            ('b', 'Сукня біла', 'suit', 'комплект', 'костюм'),
            ('c', 'Топ білий', 'gloves', 'рукавички', 'рукавички')]
    offers = ''.join('<offer id="%s"><name>%s</name><price>100</price>'
                     '<currencyId>UAH</currencyId><categoryId>1</categoryId>'
                     '<param name="Колір">Білий</param><param name="слот">пояс</param>'
                     '<param name="тип">%s</param></offer>' % р[:3] for р in дані)
    xml = '<yml_catalog><shop><categories><category id="1">пояс</category>' \
          '</categories><offers>' + offers + '</offers></shop></yml_catalog>'
    with tempfile.TemporaryDirectory() as т:
        шлях = Path(т) / 'каталог.xml'
        шлях.write_text(xml)
        результат = К._прочитати_каталог(str(шлях), ліміт_фото=0,
                                          кеш=str(Path(т) / 'кеш.json'), збагачення={})
        факт = {str(р['id']).split('@')[0]: (р['слот'], р['тип'])
                for р in результат['каталог']}
        assert факт == {р[0]: р[3:] for р in дані}, факт
    print('ПРОЙДЕНО: три коди пройшли до кінцевого каталогу; назва не змінила слот/тип')


if __name__ == '__main__':
    main()
