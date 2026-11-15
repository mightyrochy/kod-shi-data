"""Короткий стан запущеного повтору без звернень до моделей."""
from pathlib import Path
import json
import re

base = Path(__file__).resolve().parent.parent
state = json.loads((base / 'спроба_6/стан.json').read_text(encoding='utf-8'))
remaining = [x for x in state['лишилось'] if re.match(r'^с[1-8]_', x['ситуація'])]
print('Завершено в цій спробі:', len(state['завершено']), '; лишилось:', len(remaining))
paths = list(base.glob('gemini-*/стенд/службове/*/екрани.jsonl'))
latest = max(paths, key=lambda p: p.stat().st_mtime)
frame = json.loads(latest.read_text(encoding='utf-8').splitlines()[-1])
print(latest.parents[3].name, latest.parent.name, '· прохід', frame['прохід'],
      '· крок', frame['крок'], '·', frame['опис'][:150])
print(frame['текст'].replace('\n', ' ')[:250])
