"""Зберігає завершені результати стендів і вихідні часові лінії 6/8 слотів."""
from pathlib import Path
import json
import re
import sys


def main():
    """Перевіряє коди, підраховує підсумок і незалежно читає часові лінії процесів."""
    tree = Path(sys.argv[1]).resolve()
    folder = Path(__file__).resolve().parent
    results = json.loads((folder / 'журнали/результати.json').read_text(encoding='utf-8'))
    expected = {p.name for p in (tree / 'аудит/адаптери/gemini/перевірка').glob('сценарії_*.sh')}
    assert {r['стенд'] for r in results} == expected | {'перевірити_хеші.py'}
    assert all(r['код'] == 0 for r in results)
    total = 0
    table = ['| Стенд | ✓ | ✗ | Код |', '|---|---:|---:|---:|']
    for row in results:
        if row['стенд'].endswith('.sh'):
            match = re.search(r'✓ (\d+) / ✗ (\d+)', row['підсумок'])
            assert match and int(match[2]) == 0
            total += int(match[1])
            table.append(f"| `{row['стенд']}` | {match[1]} | {match[2]} | {row['код']} |")
    hashes = (folder / 'журнали/перевірити_хеші.py.txt').read_text(encoding='utf-8').splitlines()
    assert len(hashes) == 9 and all(line.startswith('✓ ') for line in hashes)
    lanes = []
    for count in (6, 8):
        run = tree.parent / 'd1969-suite/smuhy' / f'slots-{count}'
        raw = (run / 'timeline.txt').read_bytes().replace(b'\r\n', b'\n')
        (folder / f'паралельність-{count}.txt').write_bytes(raw)
        events = []
        for line in raw.decode('utf-8').splitlines():
            kind, slug, stamp = line.split()
            events.append((int(stamp), 0 if kind == 'end' else 1, slug))
        current = peak = ended = 0
        for stamp, kind, slug in sorted(events):
            current += 1 if kind else -1
            ended += not kind
            peak = max(peak, current)
        config = json.loads((run / 'seed/аудит/адаптери/gemini/смуги.json').read_text(encoding='utf-8'))
        assert config['slots']['codex'] == peak == ended == count and current == 0
        lanes.append({'задано': config['slots'], 'водночас': peak, 'закінчено': ended})
    summary = {'стендів': len(expected), 'успішних-перевірок': total, 'провалів': 0,
               'хешів': len(hashes), 'паралельність': lanes}
    (folder / 'підсумок.json').write_bytes((json.dumps(summary, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    (folder / 'стенди.txt').write_bytes(('\n'.join(table) + '\n').encode('utf-8'))
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
