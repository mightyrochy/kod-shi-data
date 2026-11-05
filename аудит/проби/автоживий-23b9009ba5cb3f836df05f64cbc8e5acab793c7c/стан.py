"""Короткий огляд уже записаних файлів прогону, без втручання у стенд."""
from datetime import datetime, timezone
import json
from pathlib import Path

out = Path(__file__).resolve().parent
plan = json.loads((out / 'план.json').read_text(encoding='utf-8'))
print(datetime.now(timezone.utc).isoformat())
if (out / 'ДО_підготовка.txt').exists():
    print('ДО:', '\n'.join((out / 'ДО_підготовка.txt').read_text(encoding='utf-8').splitlines()[-2:]))
for scene in plan['scenes']:
    folder = out / scene
    if not folder.exists():
        continue
    if (folder / 'результат.json').exists():
        result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
        print(scene, 'rc=' + str(result.get('rc')), 'секунд=' + str(result.get('секунд')))
    else:
        print('ТРИВАЄ', scene)
        for name in ('лог.txt', 'проксі.txt'):
            if (folder / name).exists():
                lines = (folder / name).read_text(encoding='utf-8').splitlines()
                print(name, '\n'.join(line[:350] for line in lines[-3:]))
