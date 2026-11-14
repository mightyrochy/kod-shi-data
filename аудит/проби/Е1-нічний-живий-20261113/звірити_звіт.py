"""Перевірка цілісності доказів наряду без запуску моделей і без правки баз."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import subprocess

out = Path(__file__).resolve().parent
repo = out.parents[2]
plan_bytes = (out / 'ПЛАН.json').read_bytes()
plan = json.loads(plan_bytes)
assignment = (out / 'НАРЯД.md').read_text(encoding='utf-8')
original_line = next(line for line in assignment.splitlines() if line.startswith('{"reports":'))
checks = {'план_дослівно': plan_bytes.decode('utf-8').strip() == original_line,
          'призначена_збірка': plan['build'] == '2cfe2ab4226385c606e35dc4a45ea92c92034949'}
locations = {p.parent.name: p.parent for p in out.glob('*/результат.json')}
base = out / 'НОВА_БАЗА.md'
if base.exists():
    for name in re.findall(r'НОВА БАЗА: (\S+)', base.read_text(encoding='utf-8')):
        folder = Path(name)
        if (folder / 'результат.json').exists():
            result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
            assert result['сцена'] not in locations, result['сцена']
            locations[result['сцена']] = folder
checks['43_унікальні_записи'] = set(locations) == set(plan['scenes']) and len(locations) == 43
counts = Counter()
missing = []
raw_count = 0
for scene, folder in locations.items():
    result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
    checks['SHA_' + scene] = result['sha'] == result['дерево_стенда'] == 'c3d18d313e88a6199c3211d7984a492c4073a7a1'
    counts[str(result.get('rc'))] += 1
    for name in ('повтор.json', 'лог.txt', 'проксі.txt', 'VIDPOVIDI/обмін'):
        if not (folder / name).exists(): missing.append(str(folder / name))
    for raw in (folder / 'VIDPOVIDI/обмін').glob('*.json'):
        data = json.loads(raw.read_text(encoding='utf-8'))
        assert data['версія'] == 1 and 'запит' in data and 'відповідь' in data, raw
        raw_count += 1
checks['повні_файли_доказів'] = not missing
changes = subprocess.run(['git', '-c', 'core.quotepath=false', 'diff', '--name-only',
                          '06bfc0fd9fc6ba0b5887c0f08bf559be52cce9e4', '--'], cwd=repo, capture_output=True, text=True, encoding='utf-8', check=True).stdout.splitlines()
allowed = ('аудит/проби/Е1-нічний-живий-20261113/', 'аудит/проби/нічні/', 'аудит/дошка/gemini/Е1-нічний-живий-20261113.md')
foreign = [name for name in changes if not name.startswith(allowed)]
checks['змінено_лише_докази_наряду'] = not foreign
checks['немає_маркера_перевіреної_збірки'] = not re.search(r'^ПЕРЕВІРЕНО ЗБІРКУ:', (out / 'ЗВІТ.md').read_text(encoding='utf-8'), re.M)
summary = {'час_utc': datetime.now(timezone.utc).isoformat(), 'перевірки': checks,
           'план_sha256': hashlib.sha256(plan_bytes).hexdigest(), 'результатів': len(locations),
           'коди': dict(counts), 'сирих_обмінів': raw_count, 'відсутні_файли': missing, 'зайві_зміни': foreign}
(out / 'звірка_звіту.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
failed = [name for name, passed in checks.items() if not passed]
print('Записів:', len(locations), 'обмінів:', raw_count, 'помилки цілісності:', failed)
raise SystemExit(bool(failed))
