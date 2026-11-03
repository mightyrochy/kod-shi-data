"""Витяги фактів із збережених записів, без повторного звернення до моделей."""
import json
from pathlib import Path
import re

ТЕКА = Path(__file__).resolve().parent


def пройти(обєкт, шлях=''):
    if isinstance(обєкт, dict):
        for ключ, значення in обєкт.items():
            новий = шлях + '/' + str(ключ)
            yield новий, ключ, значення
            yield from пройти(значення, новий)
    elif isinstance(обєкт, list):
        for номер, значення in enumerate(обєкт):
            новий = шлях + '/' + str(номер)
            yield новий, номер, значення
            yield from пройти(значення, новий)


підсумок = {}
for тека in sorted(ТЕКА.iterdir()):
    if not тека.is_dir() or not (тека / 'результат.json').exists():
        continue
    р = json.loads((тека / 'результат.json').read_text(encoding='utf-8'))
    лог = (тека / 'лог.txt').read_text(encoding='utf-8')
    факти = {к: р[к] for к in ['sha', 'сцена', 'rc', 'початок', 'кінець', 'секунд']}
    факти['зелених'] = len(re.findall(r'^  ✔ ', лог, flags=re.M))
    факти['червоних'] = len(re.findall(r'^  ✗ ', лог, flags=re.M))
    факти['червоні'] = [р.strip() for р in лог.splitlines() if '✗' in р]
    факти['моделей_після'] = sum(len(м['loaded_instances']) for м in р['моделі_після'])
    for файл in ['знімки/ng4_rozmova_seed3.txt', 'вердикти.txt']:
        ф = тека / файл
        if not ф.exists():
            continue
        текст = ф.read_text(encoding='utf-8')
        дані, _ = json.JSONDecoder().raw_decode(текст)
        if файл.endswith('ng4_rozmova_seed3.txt'):
            факти['розмова'] = дані
        else:
            факти['вердиктів'] = дані['вердиктів']
            факти['схема'] = {к: з for к, з in дані['спільне'].items() if к.startswith('пал_')}
            факти['знахідки_суду'] = [
                {'рука': в['рука'], 'запис': з} for п in дані['прогони'] for в in п['вердикти']
                for з in (в.get('етапи') or {}).get('суд', {}).get('знахідки', [])]
            факти['провенанс'] = [
                {'шлях': ш, 'значення': з} for ш, к, з in пройти(дані)
                if 'провенанс' in str(к).lower() or 'provenance' in str(к).lower()]
            факти['картки'] = [{к: в.get(к) for к in ['рука', 'склад', 'текст', 'опис', 'фото_речей', 'схема_вийшла']}
                               for п in дані['прогони'] for в in п['вердикти']]
    факти['запити'] = []
    for файл in sorted((тека / 'VIDPOVIDI/обмін').glob('*.json')):
        обмін = json.loads(файл.read_text(encoding='utf-8'))
        for повідомлення in обмін['запит'].get('messages', []):
            вміст = повідомлення.get('content', '')
            тексти = [вміст] if isinstance(вміст, str) else [ч.get('text', '') for ч in вміст]
            for текст in тексти:
                try:
                    пакет = json.loads(текст)
                except (ValueError, TypeError):
                    continue
                поля = list(пройти(пакет))
                факти['запити'].append({
                    'файл': str(файл.relative_to(ТЕКА)), 'модель': обмін['запит'].get('model'),
                    'поля': list(пакет) if isinstance(пакет, dict) else [],
                    'провенанс': [{'шлях': ш, 'значення': з} for ш, к, з in поля
                                  if any(п in str(к).lower() for п in ['provenance', 'провенанс', 'сила_нп_джерело'])],
                    'схеми': [{'шлях': ш, 'значення': з} for ш, к, з in поля if к in ['scheme', 'branches', 'schemes']],
                    'джерела': sorted({str(з) for _, к, з in поля if к == 'source'}),
                })
    підсумок[тека.name] = факти

(ТЕКА / 'ФАКТИ.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
for сцена, р in підсумок.items():
    print(сцена, 'rc=' + str(р['rc']), str(р['секунд']) + ' с',
          'зелених=' + str(р['зелених']), 'червоних=' + str(р['червоних']),
          'знахідок_суду=' + str(len(р.get('знахідки_суду', []))),
          'провенанс=' + str(len(р.get('провенанс', []))))
