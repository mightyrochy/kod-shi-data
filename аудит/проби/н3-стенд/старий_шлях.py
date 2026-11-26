"""(г): чи є в обмінах прогону виклик старого шляху образу. Запит ядра (Ч4) несе `version_of_day` і роль із
`ядро/дані/запити.json`; старий шлях — ні. Решта викликів — розмова (паспорт), палітра, мовний шар, фото, руки 3–4."""
import json
import sys
from collections import Counter
from pathlib import Path

ролі_ядра = {з["role"] for к, з in json.loads(Path('/home/user/kod-shi-data/джерела/ядро/дані/запити.json').read_text()).items()
             if isinstance(з, dict) and "role" in з}
for тека in sys.argv[1:]:
    види = Counter()
    for л in Path(тека, 'обміни.jsonl').read_text().splitlines():
        о = json.loads(л)
        q = о.get('запит') or ''
        try:
            т = json.loads(q)
        except ValueError:
            види['не JSON: ' + (о.get('тип') or '?')] += 1
            continue
        роль = (т.get('task') or {}).get('role', '') if isinstance(т.get('task'), dict) else ''
        if роль in ролі_ядра:
            види['ядро' if 'version_of_day' in т else 'роль ядра без version_of_day (!)'] += 1
        elif роль.startswith('You are a personal stylist') or роль.startswith('You read the description'):
            види['руки 3–4 (Ч4 без_коду)'] += 1
        elif 'her_new_message' in т:
            види['розмова'] += 1
        elif 'schemes' in т:
            види['палітра'] += 1
        elif any(к in т for к in ('pool', 'candidates', 'items', 'groups')):
            види['СТАРИЙ ШЛЯХ? ' + роль[:60]] += 1
        else:
            види['інше: ' + роль[:60]] += 1
    print(тека.rstrip('/').split('/')[-1], dict(види))
