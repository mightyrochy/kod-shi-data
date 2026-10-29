"""Зіставити вихід моста, а після стендів — точні невдалі звірки."""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
TEMP = Path('C:/Users/gemini/gemini-runs/20261028-171005-42cc673ca36e/e2-check')


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if 'промпт' not in k and k != 'порядок_запитів'}
    return [clean(v) for v in value] if isinstance(value, list) else value


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf8')).hexdigest()


before, after = [json.loads((TEMP / ('відповідь-моста-' + name + '.json')).read_text(encoding='utf8'))
                 for name in ('до', 'після')]
a, b = clean(before), clean(after)
result = dict(поля_моста_до=list(before), поля_моста_після=list(after),
              хеш_даних_до=digest(a), хеш_даних_після=digest(b),
              змінені_поля_даних=[k for k in a.keys() | b.keys() if a.get(k) != b.get(k)])
if (OUT / 'стенди.json').exists():
    stands = json.loads((OUT / 'стенди.json').read_text(encoding='utf8'))
    failures = [[line for line in r['звірки'] if line.lstrip().startswith('✗')] for r in stands]
    result['стенди'] = [dict(код=r['код'], успішних=sum(line.lstrip().startswith('✔') for line in r['звірки']),
                             провалів=len(fail), провали=fail) for r, fail in zip(stands, failures)]
    result['провали_байт_у_байт'] = failures[0] == failures[1]
(OUT / 'порівняння.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(result, ensure_ascii=False, indent=2))
