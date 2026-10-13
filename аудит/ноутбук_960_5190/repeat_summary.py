"""Підсумок повторів #991 з незмінених сирих відповідей; без викликів моделі."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
sources = {'повтор_mamay_2': 'de437c2e26ef396a54376d54b24abbc6cc400d1b',
           'повтор_mamay_2b': '3512dfe0cbdd5036ce73d4d3bad512f69e3b224e',
           'повтор_mamay_3': '090feafc4cedf442df7ac9c6c473917469e585f9',
           'повтор_lapa_3': '090feafc4cedf442df7ac9c6c473917469e585f9'}
result = {'validator_unchanged_from': '81f446f10523d555aa44fa8e7d24134992b80783',
          'catalogue_applied': False, 'photo_acceptance_measured': False, 'runs': {}}
for name, source in sources.items():
    directory = root / name
    report = json.loads((directory / 'звіт.json').read_text(encoding='utf-8'))
    requests = []
    for path in sorted((directory / 'requests').glob('*.json')):
        item = json.loads(path.read_text(encoding='utf-8'))
        response = item.get('response', {})
        requests.append({'file': path.relative_to(root).as_posix(),
                         'started_utc': item.get('started_utc'), 'state': item['state'],
                         'elapsed_s': item.get('batch_elapsed_s'), 'error': item.get('error'),
                         'native_id': response.get('id'), 'usage': response.get('usage'),
                         'finish_reasons': [c.get('finish_reason') for c in response.get('choices', [])]})
    answers = [json.loads(p.read_text(encoding='utf-8'))['answer']
               for p in (directory / 'cache').glob('*.json')]
    result['runs'][name] = {'source': source, 'report': report,
                           'cached_rows': len(list((directory / 'cache').glob('*.json'))),
                           'statuses': dict(Counter(a['status'] for a in answers)),
                           'relations': dict(Counter(a['relation'] for a in answers)),
                           'requests': requests}
(root / 'repeat_summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({name: {'state': run['report']['state'], 'error': run['report'].get('error'),
                         'cached_rows': run['cached_rows'], 'requests': len(run['requests']),
                         'elapsed_s': sum(r['elapsed_s'] or 0 for r in run['requests'])}
                  for name, run in result['runs'].items()}, ensure_ascii=False, indent=2))
