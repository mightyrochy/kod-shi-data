import json, re, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
probes = root / 'аудит/проби'
records = sorted({p.parent for p in probes.glob('б1/ПІСЛЯ-Е3/*/вердикти.txt')} |
                 {p.parent for p in probes.glob('автоживий-*/**/вердикти.txt')})
old_green = new_red = items = addresses = loaded = network_off = 0
for record in records:
    log = (record / 'лог.txt').read_text(encoding='utf8')
    network_off += 'без FOTO=1 мережі нема' in log
    old_green += any('✔ руки 1–2: речі з фото й цінами' in line for line in log.splitlines())
    photos = (record / 'знімки/фото_карток.txt').read_text(encoding='utf8')
    visible = {m[0]: int(m[1]) for m in re.findall(r'рука (\d) · картинок \d+, прийшло (\d+)', photos)}
    failed = False
    for run in json.loads((record / 'вердикти.txt').read_text(encoding='utf8'))['прогони']:
        for card in run['вердикти']:
            hand = str(card['рука'])
            if hand not in ('1', '2'):
                continue
            own = sum(bool(item.get('фото')) for item in card.get('речі_образу') or [])
            items += len(card.get('речі_образу') or [])
            addresses += own
            loaded += visible.get(hand, 0)
            failed |= visible.get(hand, 0) < own
    new_red += failed
print(f'Записів {len(records)}; речей {items}; адрес {addresses}; завантажено {loaded}')
print(f'ДО: стара звірка зелена {old_green}/{len(records)}; ПІСЛЯ: нова червона {new_red}/{len(records)}')
assert (len(records), items, addresses, loaded, old_green, new_red) == (41, 416, 416, 0, 35, 41)
print(f'Без FOTO=1 мережі нема: {network_off}/{len(records)} записів')
assert network_off == len(records)
names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], cwd=root).decode('utf8').splitlines()
names = [name for name in names if name.endswith('/фото_карток.txt')]
counts = {'без позначки FOTO=1': [0, 0, 0], 'FOTO=1': [0, 0, 0]}
for name in names:
    text = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=root).decode('utf8')
    key = 'FOTO=1' if 'FOTO=1' in text and 'без FOTO=1' not in text else 'без позначки FOTO=1'
    if key:
        counts[key][0] += 1
        for total, ok in re.findall(r'картинок (\d+), прийшло (\d+)', text):
            counts[key][1] += int(total)
            counts[key][2] += int(ok)
print('Усі файли фото_карток.txt:', len(names), counts)
