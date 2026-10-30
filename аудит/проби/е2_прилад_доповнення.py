# -*- coding: utf-8 -*-
"""Проба З1–З3: той самий код фікстури з приладом ДО та ПІСЛЯ."""
import importlib.util
from pathlib import Path
import sys
import tempfile

корінь = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(корінь / 'джерела' / 'прилади'))
шлях = Path(sys.argv[1]) if len(sys.argv) > 1 else корінь / 'джерела/прилади/корінь_е2_промпти.py'
спека = importlib.util.spec_from_file_location('лічба', шлях)
п = importlib.util.module_from_spec(спека)
спека.loader.exec_module(п)
код = '''РЕЄСТР = {"крок": {"норма": "Never mention " + "internal ranking " + "numbers in the answer."}}
ШАБЛОН = "<offer id='{id}'><name>{назва}</name><price>{ціна}</price><picture>{фото}</picture><vendor>{бренд}</vendor><stock>{сток}</stock></offer>"
ПОЧАТОК = "You are the stylist.\\n"
def скласти(дані):
    return ПОЧАТОК + "\\n".join(р["норма"] for р in РЕЄСТР.values()) + "\\nReturn " + "only one JSON object " + "without explanations."
def транспорт(текст):
    return {"role": "user", "content": текст}
def робота(дані):
    лист = скласти(дані)
    return транспорт(лист)
'''
with tempfile.TemporaryDirectory(prefix='е2_проба_') as тека:
    дж = Path(тека) / 'джерела'
    дж.mkdir()
    (дж / 'приклад.py').write_text(код, encoding='utf-8')
    модулі = п.модулі_py(тека, п.файли_коду(тека))
    if hasattr(п, 'зібрати_функції'):
        тексти, неповні, операції = п.зібрати_функції(модулі, п.є_вимогою)
        довжини = {к: len(в) for к, в in тексти.items()}
    else:
        довжини, тексти = п.довжини_сталих(тека, модулі), {}
    очікуване = 'You are the stylist.\nNever mention internal ranking numbers in the answer.\nReturn only one JSON object without explanations.'
    факти = [очікуване in тексти.values(), not any('ШАБЛОН' in к for к in довжини), any('Never mention internal ranking numbers' in т for т in тексти.values()), not п.речення_вимог('The occasion is not known yet.', True)]
    for ім, ок in zip(('З1 повний виклик', 'З2 фікстура поза довжинами', 'реєстр і склеєний формат', 'З3 опис входу'), факти):
        print('%s: %s' % (ім, 'так' if ок else 'НІ'))
    print('проба: %d з %d' % (sum(факти), len(факти)))
    sys.exit(0 if all(факти) else 1)
