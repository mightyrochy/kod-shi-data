"""Витяг фактів запису для питань плану; якість образів не оцінює."""
from collections import Counter
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
RULES = {'K-KOH-08', 'K-KOH-07', 'K-SHO-03', 'K-WEA-06'}


def walk(value, path=''):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + '.' + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + '[' + str(index) + ']')


def main():
    facts = {}
    for folder in OUT.iterdir():
        if not folder.is_dir() or not (folder / 'результат.json').exists():
            continue
        result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
        record = {'результат': result}
        logfile = folder / 'лог.txt'
        lines = logfile.read_text(encoding='utf-8').splitlines() if logfile.exists() else []
        record['червоні'] = [line.strip() for line in lines if '✗' in line]
        record['зелених'] = sum('✔' in line for line in lines)
        proof = folder / 'знімки/доказ.json'
        if proof.exists():
            record['доказ'] = json.loads(proof.read_text(encoding='utf-8'))
        verdicts = folder / 'вердикти.txt'
        if verdicts.exists():
            data = json.loads(verdicts.read_text(encoding='utf-8'))
            shared = data.get('спільне', {})
            record['паспорт'] = shared.get('паспорт')
            record['випадок_моделі'] = shared.get('випадок_моделі')
            record['правила'] = []
            for location, value in walk(data):
                if value.get('правило') in RULES:
                    record['правила'].append({'шлях': location, **{k: value[k] for k in
                        ['правило', 'сила', 'сила_нп', 'суть', 'де', 'значення', 'спрацювань', 'свідомий'] if k in value}})
        record['дріт'] = []
        for exchange in sorted((folder / 'VIDPOVIDI/обмін').glob('*.json')):
            data = json.loads(exchange.read_text(encoding='utf-8'))
            request = data.get('запит', {})
            texts = [part.get('text', '') for message in request.get('messages', [])
                     for part in message.get('content', []) if isinstance(part, dict)]
            for text in texts:
                try:
                    wire = json.loads(text)
                except (ValueError, TypeError):
                    continue
                if isinstance(wire, dict) and ('case' in wire or 'day' in wire):
                    record['дріт'].append({'файл': str(exchange.relative_to(OUT)),
                        'модель': request.get('model'), 'case': wire.get('case'), 'day': wire.get('day'),
                        'register': wire.get('register'),
                        'джерела': dict(Counter(value.get('kind') for _, value in walk(wire)
                                               if value.get('kind') in {'word', 'touch', 'reading', 'default', 'derived', 'photo'}))})
        facts[folder.name] = record
    (OUT / 'ФАКТИ.json').write_text(json.dumps(facts, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for scene, data in facts.items():
        print(scene, 'rc=' + str(data['результат'].get('rc')), 'зелених=' + str(data['зелених']),
              'червоних=' + str(len(data['червоні'])), 'ошатність=' + str((data.get('паспорт') or {}).get('ошатність')))


if __name__ == '__main__':
    main()
