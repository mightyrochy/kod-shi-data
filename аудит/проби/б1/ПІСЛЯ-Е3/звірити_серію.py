"""Звірка повноти записів серії; не запускає моделей і не оцінює образів."""
import collections
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


scenes = [line.split('|')[0] for line in (ROOT / 'аудит/проби/б1_доречність.md').read_text(encoding='utf-8-sig').splitlines() if line.startswith('б1_')]
paths = sorted(HERE.glob('*/результат.json'))
rows = [read(path) for path in paths]
assert sorted(row['номер'] for row in rows) == list(range(1, 31))
stamps, fingerprints, errors = set(), set(), collections.Counter()
for path, row in zip(paths, rows):
    assert row['сцена'] == scenes[row['номер'] - 1]
    assert row['rc'] in (0, 1)
    assert row['впало'] == len(row['звірки'])
    proof = read(path.parent / 'знімки/доказ.json')
    stamps.add(proof['код']['збірка'])
    fingerprints.add(proof['код']['відбиток'])
    mode = proof['режим']
    for key, value in {'MODEL': 'qwen/qwen3.5-9b', 'MODEL_MOVA': 'mamaylm-gemma-3-12b-it-v2.0', 'OTSINKA': '0', 'FOTO': '0', 'ODNOCHASNO': '1', 'сід': 3}.items():
        assert mode[key] == value, (row['номер'], key, mode[key])
    before, after = read(path.parent / 'моделі-до.json'), read(path.parent / 'прибирання.json')['моделі-після']
    assert not any(model['loaded_instances'] for model in before['models'])
    assert not any(model['loaded_instances'] for model in after['models'])
    observations = path.parent / 'спостереження-моделей.jsonl'
    if observations.exists():
        for line in observations.read_text(encoding='utf-8').splitlines():
            value = json.loads(line)['models']
            if 'помилка-GET' in value:
                errors[str(value['помилка-GET'])] += 1
assert fingerprints == {'04a19a1f0ed8'}, fingerprints
sha = (HERE / 'код-main.txt').read_text().strip()
for stamp in stamps | {'HEAD'}:
    subprocess.run(['git', 'diff', '--quiet', sha, stamp, '--', 'джерела', 'аудит/проби/рв6_стенд.js', 'аудит/ноутбук_стенд_2/проксі_почергове.js', '.github', 'аудит/адаптери/gemini'], cwd=ROOT, check=True)
summary = {
    'завершено': len(rows), 'повних-чотири-картки': sum(row['карток'] == 4 for row in rows),
    'без-✗': sum(row['rc'] == 0 and row['карток'] == 4 and not row['звірки'] for row in rows),
    'карток-разом': sum(row['карток'] for row in rows), 'ВПАЛО-разом': sum(row['впало'] for row in rows),
    'секунд-завершених': sum(row['секунди'] for row in rows),
    'неповні': [row['номер'] for row in rows if row['карток'] < 4],
    'профіль-збігається': sum(row['профіль-збігається'] is True for row in rows),
    'спільні-мірки-кольори-збігаються': sum(row.get('спільні-мірки-кольори-збігаються') is True for row in rows),
    'порівняння-складання-не-виміряно': [row['номер'] for row in rows if row.get('спільні-мірки-кольори-збігаються') == 'не виміряно'],
    'штампи-збірки': sorted(stamps), 'відбиток-коду': sorted(fingerprints),
    'помилки-GET-спостерігача-у-завершених': dict(errors), 'диф-продукту-стенда-проксі-заборонених-тек': 0,
}
(HERE / 'звірка-звіту.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
