"""Стисла вибірка доказів із завершених записів; не змінює записи або бази."""
import json
import re
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
ПЛАН = json.loads(next(x for x in (ТЕКА / 'НАРЯД.md').read_text(encoding='utf-8').splitlines()
                      if x.startswith('{"since":')))
ВИМІРИ = {}
for сцена, питання in ПЛАН['scenes'].items():
    тека = ТЕКА / сцена
    if not (тека / 'результат.json').exists():
        continue
    р = json.loads((тека / 'результат.json').read_text(encoding='utf-8'))
    лог = (тека / 'лог.txt').read_text(encoding='utf-8')
    в = {'питання': питання, 'rc': р['rc'], 'секунд': р['секунд'],
         'червоні': [x.strip() for x in лог.splitlines() if '✗' in x],
         'фото_моделі': [x.strip() for x in лог.splitlines() if 'не дійшло' in x],
         'заміни': [x.strip() for x in лог.splitlines() if 'ЗАМІНА руки' in x or 'NE_TSIA' in x]}
    перший = тека / 'VIDPOVIDI/обмін/00001.json'
    if перший.exists():
        обмін = json.loads(перший.read_text(encoding='utf-8'))
        тіло = json.loads(обмін['відповідь']['body'])
        текст = ''.join(б.get('text', '') for б in тіло.get('content', []))
        збіг = re.search(r'\{[\s\S]*\}', текст)
        if збіг:
            try:
                в['перший_хід_моделі'] = json.loads(збіг[0])
            except json.JSONDecodeError:
                в['перший_хід_моделі'] = {'не_розібрано': текст}
    доказ = тека / 'знімки/доказ.json'
    if доказ.exists():
        д = json.loads(доказ.read_text(encoding='utf-8'))
        в['доказ'] = {к: д[к] for к in ['код', 'факт', 'вердикт']}
    файл = тека / 'вердикти.txt'
    if файл.exists():
        ж = json.loads(файл.read_text(encoding='utf-8-sig'))
        в['паспорт'] = ж['спільне'].get('паспорт')
        в['випадок_моделі'] = ж['спільне'].get('випадок_моделі')
        в['руки'] = []
        for прогін in ж['прогони']:
            for к in прогін['вердикти']:
                е = к.get('етапи', {})
                с = е.get('суд', {})
                в['руки'].append({'рука': к['рука'], 'склад': к['склад'],
                    'діагноз': [д for д in (е.get('діагноз_руки') or []) if 'code_unknown=' not in д],
                    'слід_питань': [з for з in (с.get('слід_правил') or []) if з.get('правило') in
                        ['K-CRA-04', 'K-OUT-06', 'K-KOH-06', 'K-KOH-10']],
                    'суд': {п: с.get(п) for п in
                    ['день', 'блокує', 'повнота', 'знахідки', 'структура']},
                    'кроки': [{п: з.get(п) for п in ['крок', 'стадія', 'помилка', 'повнота',
                        'блокує', 'структура', 'дні']}
                        for з in е.get('виклики', [])]})
    ВИМІРИ[сцена] = в
(ТЕКА / 'ВИМІРИ.json').write_text(json.dumps(ВИМІРИ, ensure_ascii=False, indent=1), encoding='utf-8')
for сцена, в in ВИМІРИ.items():
    print(сцена, 'rc=' + str(в['rc']), 'червоних=' + str(len(в['червоні'])), 'секунд=' + str(в['секунд']))
