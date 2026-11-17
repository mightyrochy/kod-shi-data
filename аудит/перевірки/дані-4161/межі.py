"""Контроль меж: python межі.py <дерево голови> [SHA бази для трьох змінених модулів]."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

дерево = Path(sys.argv[1]).resolve()
тимчасова = tempfile.TemporaryDirectory(prefix='перевірка-4161-межі-')
шляхи = [str(дерево / 'джерела')]
if len(sys.argv) > 2:
    модулі = Path(тимчасова.name)
    for імя in ('знання_речі.py', 'дріт_моделі.py', 'розбір_відповідей.py'):
        (модулі / імя).write_bytes(subprocess.check_output(
            ['git', 'show', sys.argv[2] + ':джерела/' + імя], cwd=дерево))
    шляхи.insert(0, str(модулі))
sys.path[:0] = шляхи
import bridge as Б
import мовний_шар as МШ
import міст_вхід as МВ
import дріт_моделі as Д

слова = 'робочий день в офісі, дрес-код business casual, без підборів'
давній = json.loads(Б.виклик('паспорт', json.dumps(dict(
    сценарій={}, вимоги=слова, json_моделі=json.dumps(dict(
        подія='робочий день в офісі', нагода='робота', місце='офіс_корпоративний',
        дрес_код='business_casual', намір='conventional',
        вето=dict(типи=['підбори'], тканини=[], принти=[], кольори=[], зони=[])),
        ensure_ascii=False)), ensure_ascii=False)))['паспорт']
вхід = dict(occasion=dict(quote='робочий день', value='work'),
            place=dict(quote='в офісі', value='office_corporate'),
            dress_code=dict(quote='дрес-код business casual', code='business_casual'),
            vetoes=[dict(quote='без підборів', feature='heels')])
внутрішня = МШ.прийняти_вхід('scenario', json.dumps(вхід, ensure_ascii=False))['внутрішня']
чинний = МШ.паспорт_з_шару(внутрішня, {}, None, None, слова_ходу=слова)['паспорт']
for назва, паспорт, очікуване in (
        ('стара проба', давній, None), ('чинний мовний шар', чинний, ['heels'])):
    дані = МВ.застосувати_паспорт(dict(паспорт=паспорт, сценарій={}, вимоги=слова))
    межі = дані.get('межі')
    опис = Д.опис(dict(образ=dict(речі=[]), межі=межі)).get('she_refuses')
    вибір = Д.вердикт({}, межі=межі, вибір=True).get('she_refuses')
    assert опис == вибір == очікуване, (назва, опис, вибір)
    print(назва, json.dumps(dict(перекладено_шаром=паспорт.get('перекладено_шаром'),
                                межі=межі, опис=опис, вибір=вибір), ensure_ascii=False))
тимчасова.cleanup()
