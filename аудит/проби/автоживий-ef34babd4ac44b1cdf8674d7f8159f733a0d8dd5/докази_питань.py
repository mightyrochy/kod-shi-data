"""Вибірка фактів для питань наряду, без повторних викликів моделі."""
import json
from pathlib import Path
import re

ТЕКА = Path(__file__).resolve().parent
план = json.loads(next(x for x in (ТЕКА / 'НАРЯД.md').read_text(encoding='utf-8').splitlines()
                       if x.startswith('{"since":')))


def читати(файл):
    return json.loads(файл.read_text(encoding='utf-8-sig'))


def ключі_часу(значення, шлях=''):
    знайдено = []
    if isinstance(значення, dict):
        for к, в in значення.items():
            далі = шлях + '.' + к
            if к in ['hour', 'minute', 'start_hour', 'start_minute', 'година', 'хвилина']:
                знайдено.append({'шлях': далі, 'значення': в})
            знайдено.extend(ключі_часу(в, далі))
    elif isinstance(значення, list):
        for і, в in enumerate(значення):
            знайдено.extend(ключі_часу(в, шлях + '[' + str(і) + ']'))
    return знайдено


результати = {}
for сцена, питання in план['scenes'].items():
    т = ТЕКА / сцена
    if not (т / 'результат.json').exists():
        continue
    р = читати(т / 'результат.json')
    лог = (т / 'лог.txt').read_text(encoding='utf-8')
    д = {'питання': питання, 'rc': р['rc'], 'секунд': р['секунд'],
         'завершення': читати(т / 'знімки/доказ.json') if (т / 'знімки/доказ.json').exists() else None,
         'червоні': [x.strip() for x in лог.splitlines() if '✗' in x],
         'час_у_знімках_тексту': [], 'руки': [], 'входи_стилістки': [],
         'розмова_лог': [x.strip() for x in лог.splitlines() if any(
             слово in x for слово in ['СТИЛІСТКА:', 'КАРТКА:', 'ВИМІРИ:', 'KARTKA ·'])]}
    текст_екранів = т / 'знімки/текст_екранів.txt'
    розмова = т / 'знімки/ng4_rozmova_seed3.txt'
    if розмова.exists():
        д['розмова'] = json.JSONDecoder().raw_decode(розмова.read_text(encoding='utf-8').lstrip())[0]
    if текст_екранів.exists():
        д['час_у_знімках_тексту'] = [x for x in текст_екранів.read_text(encoding='utf-8').splitlines()
                                   if re.search(r'\b\d{1,2}:\d{2}\b|[Вв]вечері|[Зз]ранку|[Вв]ранці|[Вв]день', x)]
    файл = т / 'вердикти.txt'
    if файл.exists():
        ж = читати(файл)
        п = ж['спільне'].get('паспорт') or {}
        д['паспорт'] = {к: п.get(к) for к in ['пора', 'ошатність', 'нагода', 'поля_шару', 'цитати_полів']}
        д['структурний_час_паспорта'] = ключі_часу(п)
        д['випадок_моделі'] = ж['спільне'].get('випадок_моделі')
        д['чат'] = ж['спільне'].get('чат')
        for прогін in ж['прогони']:
            for к in прогін['вердикти']:
                е = к.get('етапи') or {}
                с = е.get('суд') or {}
                д['руки'].append({'рука': к['рука'], 'склад': к['склад'],
                    'день': с.get('день'), 'повнота': с.get('повнота'), 'блокує': с.get('блокує'),
                    'знахідки': с.get('знахідки'),
                    'слід': [з for з in (с.get('слід_правил') or []) if з.get('правило') in
                             ['K-CRA-04', 'K-OUT-06', 'K-KOH-06', 'K-KOH-10']],
                    'діагноз': [з for з in (е.get('діагноз_руки') or []) if
                                any(слово in з for слово in ['completeness', 'code_added', 'replacement'])],
                    'кроки': [{'крок': з.get('крок'), 'слід': [в for в in з.get('слід_правил', [])
                               if в.get('правило') in ['K-CRA-04', 'K-OUT-06']]} for з in е.get('виклики', [])]})
    for ф in sorted((т / 'VIDPOVIDI/обмін').glob('*.json')):
        о = читати(ф)
        з = о['запит']
        if з.get('model') != 'qwen/qwen3.5-9b':
            continue
        for м in з.get('messages', []):
            content = м.get('content', [])
            for б in content if isinstance(content, list) else [{'text': content}]:
                текст = б.get('text', '')
                try:
                    тіло = json.loads(текст)
                except (ValueError, TypeError):
                    continue
                д['входи_стилістки'].append({'обмін': ф.name, 'роль': м.get('role'),
                    'структурний_час': ключі_часу(тіло),
                    'день': тіло.get('day'), 'стиль': тіло.get('style_rules'),
                    'типи': {к: в for к, в in тіло.get('kind_notes', {}).items()
                             if к in ['outerwear', 'bag']},
                    'згадки_годин': sorted(set(re.findall(r'\b\d{1,2}:\d{2}\b', текст)))})
    результати[сцена] = д
(ТЕКА / 'ДОКАЗИ_ПИТАНЬ.json').write_text(json.dumps(результати, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
for сцена, д in результати.items():
    print(сцена, 'rc=' + str(д['rc']), 'пора=' + str(д.get('паспорт', {}).get('пора')),
          'червоних=' + str(len(д['червоні'])))
