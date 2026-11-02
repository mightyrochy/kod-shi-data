"""Збирає збережені відповіді nvidia-smi за 30.10–01.11, без запуску моделей."""
import hashlib
import json
from pathlib import Path
import re
import sys


def main():
    """Пише обсяг читання й числові рядки первинних відповідей, не тексти агентів."""
    root, output = map(Path, sys.argv[1:3])
    current = '20261101-143938-813555205ce9'
    files = sorted(p for d in root.iterdir()
                   if d.is_dir() and re.match(r'2026(?:103[01]|1101)-', d.name) and d.name != current
                   for p in d.glob('*.jsonl'))
    result = {'обсяг': [], 'знімки': []}
    for path in files:
        raw = path.read_bytes()
        result['обсяг'].append({'файл': str(path.relative_to(root)), 'байтів': len(raw),
                               'sha256': hashlib.sha256(raw).hexdigest()})
        for number, line in enumerate(raw.decode('utf-8', errors='replace').splitlines(), 1):
            try:
                item = json.loads(line).get('item', {})
            except ValueError:
                continue
            if item.get('type') != 'command_execution' or item.get('exit_code') != 0:
                continue
            query = re.search(r'nvidia-smi\s+--query-gpu=([a-z.,_]+)', item.get('command', ''))
            if not query:
                continue
            columns = query[1].split(',')
            if 'memory.used' not in columns and 'utilization.gpu' not in columns:
                continue
            for row in item.get('aggregated_output', '').splitlines():
                fields = [x.strip() for x in row.split(',')]
                if len(fields) != len(columns):
                    continue
                values = {}
                for column, value in zip(columns, fields):
                    if column == 'name':
                        values[column] = value
                    elif re.fullmatch(r'\d+(?: MiB| %)?', value):
                        values[column] = int(value.split()[0])
                    else:
                        break
                else:
                    result['знімки'].append({'файл': str(path.relative_to(root)), 'рядок': number,
                                             'запит': query[1], 'відповідь': row, **values})
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    used = [r['memory.used'] for r in result['знімки'] if 'memory.used' in r]
    print(f'Журналів: {len(files)}; знімків: {len(result["знімки"])}; найбільше спостережене: {max(used)} MiB')


if __name__ == '__main__':
    main()
