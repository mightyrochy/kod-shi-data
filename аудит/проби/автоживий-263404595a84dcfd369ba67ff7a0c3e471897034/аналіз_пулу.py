"""Зіставлення початкових пулів з фактично надісланими запитами; жодних викликів моделі."""
from collections import Counter
import json
from pathlib import Path
import re

тека = Path(__file__).parent
записи = [json.loads(р) for р in (тека / 'пул_до_скорочення.jsonl').read_text(encoding='utf-8').splitlines()]
початкові = next(р['результат']['руки'] for р in записи if р.get('ім') == 'запити')
cpy = [json.loads(р) for р in (тека / 'ремонт_до_скорочення.jsonl').read_text(encoding='utf-8').splitlines()]
cpy_початкові = next(р['результат']['руки'] for р in cpy if р.get('ім') == 'запити')
assert початкові == cpy_початкові, 'Початкові промпти Pyodide та CPython різні'
входи_моста = [json.loads(р) for р in (тека / 'б1_концерт_стримано/виклики_моста.jsonl').read_text(encoding='utf-8').splitlines()]
ремонти_до = []
def промпти(в):
    if isinstance(в, dict):
        for з in в.values():
            промпти(з)
    elif isinstance(в, list):
        for з in в:
            промпти(з)
    elif isinstance(в, str) and в.startswith('{'):
        try:
            п = json.loads(в)
        except ValueError:
            return
        if isinstance(п, dict) and isinstance(п.get('candidates'), dict):
            п['_джерело_виклик'] = поточний_номер
            ремонти_до.append(п)
for запис in cpy:
    поточний_номер = запис.get('н')
    промпти(запис.get('результат'))
факти = json.loads((тека / 'ФАКТИ.json').read_text(encoding='utf-8'))['б1_концерт_стримано']['виклики']

def таблиця(п):
    т = п.get('pool') or п.get('candidates')
    if not isinstance(т, dict):
        return None
    к = т['cols']
    return {р[к.index('n')]: р for р in т['rows']}, Counter(р[к.index('type')] for р in т['rows'])

def оцінка(текст):
    # Точні коефіцієнти оцінкаТокенівП зі збірки; JavaScript Math.round для додатного числа.
    кир = цифр = лат = решта = 0
    for з in текст:
        if 0x400 <= ord(з) <= 0x4ff or з == 'ʼ':
            кир += 1
        elif '0' <= з <= '9':
            цифр += 1
        elif 'A' <= з <= 'Z' or 'a' <= з <= 'z':
            лат += 1
        else:
            решта += 1
    import math
    return math.floor(кир*.475 + цифр*1.375 + лат*.34 + решта*.186 + .5)

пули = []
пакетів = 0
for м in факти:
    if м.get('тип') not in ['ПАКЕТ_V1→ОБРАЗИ_V1', 'ВЕРДИКТ_V1→ОБРАЗИ_V1']:
        continue
    обмін = json.loads((тека / 'б1_концерт_стримано/VIDPOVIDI/обмін' / м['файл']).read_text(encoding='utf-8'))
    п = json.loads(next(ч['text'] for пв in обмін['запит']['messages'] for ч in пв['content'] if ч['type']=='text'))
    т = таблиця(п)
    if not т:
        continue
    if м['тип'] == 'ПАКЕТ_V1→ОБРАЗИ_V1':
        пакетів += 1
        рука = str(пакетів)
    else:
        # Руку ремонту нижче визначаємо з фактичного входу моста: донор=True — рука 2.
        рука = None
    до_промпт = json.loads(початкові[рука]) if рука else {}
    if м['тип'] == 'ВЕРДИКТ_V1→ОБРАЗИ_V1':
        сумісні = [р for р in ремонти_до if р.get('break_kind') == п.get('break_kind')]
        assert сумісні, ('Промпт ремонту не знайдено', м['файл'])
        сумісні = [р for р in сумісні if р.get('case') == п.get('case') and р.get('day') == п.get('day')]
        кінцеві_рядки = таблиця(п)[0]
        сумісні = [р for р in сумісні if р['candidates']['cols'] == п['candidates']['cols']
            and all(н in таблиця(р)[0] and таблиця(р)[0][н] == з for н, з in кінцеві_рядки.items())]
        унікальні = {json.dumps(р['candidates'], sort_keys=True, ensure_ascii=False): р for р in сумісні}
        assert len(унікальні) == 1, ('Не єдиний початковий пул ремонту', м['файл'], len(унікальні))
        до_промпт = next(iter(унікальні.values()))
        вхід_ремонту = json.loads(входи_моста[до_промпт['_джерело_виклик']]['вхід'])
        рука = '2' if вхід_ремонту.get('донор') else '1'
    до, типи_до = таблиця(до_промпт)
    після, типи_після = т
    мірка = {'файл': м['файл'], 'тип': м['тип'], 'рука': рука,
        'до': len(до), 'після': len(після), 'типів_до': len(типи_до), 'типів_після': len(типи_після),
        'втрачені_типи': sorted(set(типи_до) - set(типи_після)),
        'кандидати_за_типом_до': dict(типи_до), 'кандидати_за_типом_після': dict(типи_після),
        'вхід_плюс_стеля': м['вхід_плюс_стеля'], 'break_kind': п.get('break_kind')}
    if '_джерело_виклик' in до_промпт:
        мірка['початковий_ремонт_виклик_моста'] = до_промпт['_джерело_виклик']
    if м['тип'] == 'ПАКЕТ_V1→ОБРАЗИ_V1':
        мірка['нові_ід'] = sorted(set(після)-set(до))
        мірка['зміна_рядків'] = [н for н, р in після.items() if н in до and р != до[н]]
        import math
        мірка['оцінка_початкового_промпта_з_1_1'] = math.ceil(оцінка(початкові[рука])*1.1)
        мірка['оцінка_до_плюс_стеля'] = мірка['оцінка_початкового_промпта_з_1_1'] + м['стеля']
    пули.append(мірка)

журнал = json.loads((тека / 'б1_концерт_стримано/знімки/виклики_стадії.json').read_text(encoding='utf-8'))
спроби = []
def знайти(в):
    if isinstance(в, dict):
        if isinstance(в.get('скорочено'), list):
            спроби.append(в)
        for з in в.values():
            знайти(з)
    elif isinstance(в, list):
        for з in в:
            знайти(з)
знайти(журнал)
вердикти = json.loads((тека / 'б1_концерт_стримано/вердикти.txt').read_text(encoding='utf-8'))
картки = {}
for в in вердикти['прогони'][0]['вердикти']:
    картки.setdefault(в['рука'], {'склад': в['склад'], 'речей': len(в['склад'].split('+')), 'ітерацій': в['ітерацій']})
усі = {'пули': пули, 'картки': картки, 'початкові_промпти_pyodide_cpython_ідентичні': True,
 'усі_http': sorted(set(м['http'] for м in факти)),
 'макс_qwen_вхід_плюс_стеля': max(м['вхід_плюс_стеля'] for м in факти if м['модель']=='qwen/qwen3.5-9b'),
 'макс_mamay_вхід_плюс_стеля': max(м['вхід_плюс_стеля'] for м in факти if м['модель']=='mamaylm-gemma-3-12b-it-v2.0'),
 'спроби_зі_скороченням': спроби}
(тека / 'ПУЛ_ФАКТИ.json').write_text(json.dumps(усі, ensure_ascii=False, indent=1)+'\n',encoding='utf-8')
print(json.dumps({к: з for к,з in усі.items() if к not in ['пули','спроби_зі_скороченням']}, ensure_ascii=False))
for п in пули:
    print({к: з for к,з in п.items() if not к.startswith('кандидати_за_типом')})
print('Записів спроб зі скороченням:', len(спроби))
