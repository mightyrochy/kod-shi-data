"""Факти з повних обмінів; відсутність фрази — дослівна перевірка, не суд над змістом."""
from collections import Counter
import json
from pathlib import Path

тека = Path(__file__).parent
фрази = [р['вона'] for р in json.loads((тека.parents[0] / 'е2_втрата_слова_розмова.json').read_text(encoding='utf-8'))]
звіт = {}
for сцена in ['ж2_довга_розмова_слова', 'ж1_оціни_образ_6б', 'б1_концерт_стримано']:
    шлях = тека / сцена
    if not (шлях / 'результат.json').exists():
        continue
    результат = json.loads((шлях / 'результат.json').read_text(encoding='utf-8'))
    журнал = шлях / 'знімки/модель_виклики.json'
    виклики = json.loads(журнал.read_text(encoding='utf-8')) if журнал.exists() else []
    if isinstance(виклики, dict):
        виклики = виклики.get('виклики', [])
    міри = []
    for і, файл in enumerate(sorted((шлях / 'VIDPOVIDI/обмін').glob('*.json'))):
        запис = json.loads(файл.read_text(encoding='utf-8'))
        запит = запис['запит']
        відповідь = json.loads(запис['відповідь']['body'])
        usage = відповідь.get('usage', {})
        м = {'файл': файл.name, 'модель': запит['model'], 'http': запис['відповідь']['status'],
             'стеля': запит.get('max_tokens'), 'usage': usage}
        if isinstance(виклики, list) and і < len(виклики):
            м['тип'] = виклики[і].get('тип')
        вхід = usage.get('input_tokens', usage.get('prompt_tokens'))
        if isinstance(вхід, int) and isinstance(м['стеля'], int):
            м['вхід_плюс_стеля'] = вхід + м['стеля']
        for повідомлення in запит.get('messages', []):
            вміст = повідомлення.get('content', [])
            if isinstance(вміст, str):
                вміст = [{'type': 'text', 'text': вміст}]
            for ч in вміст:
                if ч.get('type') != 'text':
                    continue
                текст = ч['text']
                try:
                    п = json.loads(текст)
                except ValueError:
                    п = None
                м['уточнення_дослівно'] = {ф: ф in текст for ф in фрази}
                if isinstance(п, dict):
                    м['ключі_промпта'] = list(п)
                    if 'case' in п:
                        м['випадок'] = п['case']
                    if isinstance(п.get('pool'), dict):
                        пул = п['pool']
                        м['колонки_пулу'] = пул.get('cols')
                        м['речей_пулу'] = len(пул.get('rows', []))
                        cols = пул.get('cols', [])
                        for ключ in ['kind', 'type', 'k', 't']:
                            if ключ in cols:
                                позиція = cols.index(ключ)
                                м['типи_пулу'] = dict(Counter(р[позиція] for р in пул['rows']))
                    if isinstance(п.get('task'), dict):
                        м['роль'] = п['task'].get('role')
        міри.append(м)
    звіт[сцена] = {'rc': результат.get('rc'), 'секунд': результат.get('секунд'), 'sha': результат.get('sha'),
        'виклики': міри}
(тека / 'ФАКТИ.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
for сцена, дані in звіт.items():
    print(сцена, 'rc=', дані['rc'], 'викликів=', len(дані['виклики']))
