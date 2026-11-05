import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / 'джерела'))
import мовний_шар as М, паспорт_нагоди as П, дріт_моделі as Д, сценарій as С
for code in ['morning', 'day', 'evening', 'night', None]:
    passport = П.паспорт_з_json(json.dumps({'подія': 'зустріч', 'пора': code}), {}, '', чекати_відповідь=False)
    assert 'година' not in passport and 'хвилини' not in passport
    if code is not None:
        assert Д.випадок(passport).get('part_of_day') == code
результат = []
старий = {'година': 19, 'хвилини': 30, 'пора': 'вечір'}
for code in ['morning', 'day', 'evening', 'night', 'unknown']:
    raw = json.dumps({'update': {'part_of_day': code, 'occasion': {'quote': 'зустріч', 'value': 'date'}}})
    parsed = М.прийняти_розмову(raw)
    passport = М.паспорт_з_шару(parsed['внутрішня'], {}, паспорт_досі=старий, частини=parsed.get('частини'))['паспорт']
    scene = П.з_показу({}, passport)[0]
    day = С.день_кодами(scene)
    for wire in [Д.випадок(passport), Д.випадок(passport, day)]:
        assert 'start_hour' not in wire
    assert 'година' not in passport and 'хвилини' not in passport
    if code != 'unknown':
        assert Д.випадок(passport)['part_of_day'] == code
        assert day['part_of_day'] == code
    результат.append({'код': code, 'паспорт': passport, 'дріт': Д.випадок(passport), 'шматки': П.паспорт_шматками_людині(passport)})
print(json.dumps(результат, ensure_ascii=False))
