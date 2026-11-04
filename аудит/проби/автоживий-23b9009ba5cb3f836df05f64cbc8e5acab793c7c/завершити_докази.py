"""Зберігає висновок приладу баз та очищення тимчасових дерев після блокера."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import urllib.request

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
TEMP_ROOT = (ROOT.parent / 'tmp').resolve()
command = ['node', 'аудит/проби/нова_база.js', str(OUT.relative_to(ROOT))]
with (OUT / 'нова_база_запуск.txt').open('w', encoding='utf-8') as log:
    print('Команда: ' + ' '.join(command), file=log, flush=True)
    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    print('Код виходу: ' + str(result.returncode), file=log, flush=True)
(OUT / 'нова_база_rc.txt').write_text(str(result.returncode) + '\n', encoding='utf-8')
print('Прилад баз: rc=' + str(result.returncode), flush=True)
if (OUT / 'НОВА_БАЗА.md').exists():
    print((OUT / 'НОВА_БАЗА.md').read_text(encoding='utf-8'), flush=True)
with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=30) as response:
    models = json.load(response)
(OUT / 'моделі_після.json').write_text(json.dumps(models, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
loaded = [(model['key'], model['loaded_instances']) for model in models['models'] if model['loaded_instances']]
print('Завантажені моделі після очищення:', loaded, flush=True)
cleanup = []
for name in ('збірка', 'до'):
    tree = (TEMP_ROOT / name).resolve()
    if not tree.is_relative_to(TEMP_ROOT) or tree == TEMP_ROOT:
        raise RuntimeError('Тимчасове дерево поза дозволеною текою: ' + str(tree))
    command = ['git', 'worktree', 'remove', '--force', str(tree)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, encoding='utf-8')
    cleanup.append({'час': datetime.now(timezone.utc).isoformat(), 'перевірена_межа': str(TEMP_ROOT),
        'шлях': str(tree), 'команда': command, 'rc': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr})
    print('Очищення', name, 'rc=' + str(result.returncode), flush=True)
(OUT / 'очищення_дерев.json').write_text(json.dumps(cleanup, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
