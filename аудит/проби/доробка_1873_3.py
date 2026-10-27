"""Відтворити скидання фактів і змішану репліку без викликів моделі."""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[2]
БАЗА = 'daf1b93d462792bf66bd3c3d09ec0d2c6f0d7bc3'


def main():
    """Надрукувати ДО або ПІСЛЯ для обох напрямків заміни й джерел репліки."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--до', action='store_true')
    арг = парсер.parse_args()
    sys.path.insert(0, str(КОРІНЬ / 'джерела'))
    if арг.до:
        for ім in ('картка_запиту', 'мовний_шар'):
            шлях = КОРІНЬ / 'джерела' / (ім + '.py')
            модуль = importlib.util.module_from_spec(importlib.util.spec_from_file_location(ім, шлях))
            sys.modules[ім] = модуль
            код = subprocess.check_output(['git', 'show', f'{БАЗА}:джерела/{ім}.py'], cwd=КОРІНЬ)
            exec(compile(код, str(шлях), 'exec'), модуль.__dict__)
    import мовний_шар as м

    def хід(вхід, слова, досі=None):
        """Застосувати справжній шов і повернути паспорт."""
        return м.паспорт_з_шару(вхід, {}, паспорт_досі=досі, слова_ходу=слова)['паспорт']

    точний = dict(temperature_c=20, hour=11, minute=30,
                  quotes=dict(temperature_c='плюс 20', hour='о 11:30', minute='о 11:30'))
    відчуття = dict(weather_feel='cold', part_of_day='evening',
                    quotes=dict(weather_feel='холодно', part_of_day='увечері'))
    рівно = хід(dict(temperature_c=20, hour=11, quotes=dict(temperature_c='плюс 20', hour='о 11:00')),
                 'плюс 20, о 11:00')
    рівно = хід(відчуття, 'насправді холодно, увечері', рівно)
    п = хід(точний, 'плюс 20, о 11:30')
    п = хід(відчуття, 'насправді холодно, увечері', п)
    назад = хід(точний, 'плюс 20, о 11:30', п)
    незмінний = хід(dict(place='inside', quotes=dict(place='у приміщенні')), 'у приміщенні', назад)
    поля = ('темп_c', 'погода_відчуття', 'година', 'хвилини', 'пора')
    результат = dict(версія='ДО' if арг.до else 'ПІСЛЯ', паспорт={к: п.get(к) for к in поля},
                     назад={к: назад.get(к) for к in поля},
                     скинуті_факти=[к for к in ('темп_c', 'година', 'хвилини') if к in п.get('картка_запиту', {})],
                     скинуті_цитати=[к for к in ('темп_c', 'година', 'хвилини') if к in п.get('цитати_полів', {})],
                     репліки={})
    запис = dict(occasion=dict(label='театр', quote='театр'))
    випадки = [
        ('answer', 'Записала: театр. Бордо тобі личить.', dict(answer=dict(free_text='Бордо тобі личить.'))),
        ('довга_відповідь', 'Записала: театр. Бордо тобі личить. Обирай його сміливо.',
         dict(answer=dict(free_text='Бордо тобі личить. Обирай його сміливо.'))),
        ('item_verdicts', 'Записала: театр. Твої чоботи пасують.',
         dict(item_verdicts=[dict(item='Твої чоботи', verdict=dict(statements=[dict(
             code='item_source', values=dict(why=dict(free_text='Твої чоботи пасують.')))]))])),
        ('added', 'Записала: театр. Додала твої чоботи.', dict(added=dict(own_items=['твої чоботи']))),
        ('без_опори', 'Записала: театр. Записала: басейн.', dict(answer=dict(free_text='Бордо тобі личить.'))),
        ('чуже_число', 'Записала: театр. Бордо тобі личить у 25 років.',
         dict(answer=dict(free_text='Бордо тобі личить у 25 років.'))),
        ('саме_число', 'Записала: театр о 19:00.', {}),
        ('порожні_поля', 'Записала: театр. Записала: басейн.', dict(answer={}, item_verdicts=[], added={})),
        ('відоме_число', 'Записала: театр о 19:00.', dict(recorded=dict(occasion=запис['occasion'], hour=dict(label='19:00')))),
    ]
    for ім, текст, додатки in випадки:
        вихід, відмови = м.суд_репліки(текст, dict(dict(recorded=запис), **додатки))
        результат['репліки'][ім] = dict(прийнято=bool(вихід), причини=[в['чому'] for в in відмови])
    print(json.dumps(результат, ensure_ascii=False, indent=2))
    очікувані = ('answer', 'довга_відповідь', 'item_verdicts', 'added', 'відоме_число') if not арг.до else ('відоме_число',)
    assert all(в['прийнято'] == (ім in очікувані) for ім, в in результат['репліки'].items())
    if арг.до:
        assert рівно.get('темп_c') == 20 and рівно.get('година') == 11
        assert п.get('темп_c') == 20 and п.get('година') == 11
    else:
        assert рівно.get('темп_c') is None and рівно.get('година') is None
        assert п.get('темп_c') is None and п.get('година') is None and п.get('хвилини') is None
        assert not результат['скинуті_факти'] and not результат['скинуті_цитати']
        assert назад.get('погода_відчуття') is None and not назад.get('пора')
        assert not any(назад.get('картка_запиту', {}).get(к) for к in ('погода_відчуття', 'пора'))
        assert незмінний.get('темп_c') == 20 and незмінний.get('година') == 11


if __name__ == '__main__':
    main()
