"""Штучний шлях HTML → запис → XML для перевірки походження, незалежний від продукту."""
import json
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup


def рецепт_селекторів(_крамниця):
    """Залишає межу штучного товару спостерігачеві; крамниця не впливає на вхід."""
    return {}


def факти_з_картки(тіло, _url, _селектори=None):
    """Читає JSON-LD поза товаром і власний h1; адреса й рецепт не міняють штучної сторінки."""
    суп = BeautifulSoup(тіло, 'html.parser')
    вузол = суп.select_one('script[type="application/ld+json"]')
    дані = json.loads(вузол.get_text()) if вузол else {}
    return dict(є_товар=True, назва=дані.get('name', ''),
                заголовок=суп.select_one('#товар h1').get_text())


def канонічний_запис(факти, _крамниця, _канал):
    """Незмінно передає поля до записувача; метадані транспорту тут не потрібні."""
    return dict(факти)


def записати_каталог(записи, файл, _назва):
    """Серіалізує обидва джерела в XML; службова назва каталогу поза перевіркою."""
    корінь = ET.Element('offers')
    for запис in записи:
        офер = ET.SubElement(корінь, 'offer')
        ET.SubElement(офер, 'name').text = запис['назва']
        ET.SubElement(офер, 'param', name='заголовок').text = запис['заголовок']
    ET.ElementTree(корінь).write(файл, encoding='utf-8')
