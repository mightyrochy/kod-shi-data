"""Зведення ПІСЛЯ-1211.md: таблиця 30 запитів, два числа, причини ✗, порівняння з ПІСЛЯ-Е3 (30.10)."""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ДО = ROOT / 'аудит/проби/б1/ПІСЛЯ-Е3'


def fails(log):
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    return [re.sub(r'\s+', ' ', f)[:95] for f in re.findall(r'^ {2}✗ (.+?)(?:  →|$)', text, re.M)]


def старий(folder):
    log = folder / 'лог.txt'
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    hands = [json.loads(v) for v in re.findall(r'^\s+рука [1-4] (\{.*\})$', text, re.M)]
    hands = [h for h in hands if 'речей' in h and 'збій' in h]
    cards = sum(h['речей'] > 0 and not h['збій'] for h in hands)
    tot = re.findall(r'^ВПАЛО (\d+)', text, re.M)
    return cards, int(tot[-1]) if tot else len(fails(log)), fails(log)


ТАБЛИЦЯ_ДО = {int(m[1]): (int(m[3]), int(m[4])) for m in re.finditer(
    r'^\| (\d\d) \| \S+ \| (\d) \| \d+ \| (\d) \| (\d+) \|', (ДО.parent / 'ПІСЛЯ-Е3.md').read_text(encoding='utf-8'), re.M)}
rows = []
for p in sorted(HERE.glob('*/результат.json')):
    r = json.loads(p.read_text(encoding='utf-8'))
    d = [x for x in sorted(ДО.glob(f"{r['номер']:02}_*")) if (x / 'лог.txt').exists()][0]
    _, _, dfl = старий(d)
    dc, dv = ТАБЛИЦЯ_ДО[r['номер']]
    nf = fails(p.parent / 'лог.txt')
    r.update(до_карток=dc, до_впало=dv, до_f=dfl, f=nf)
    rows.append(r)


def оцінка(r):
    a = (r['карток'] == 4, r['впало'] == 0, r['карток'], -r['впало'])
    b = (r['до_карток'] == 4, r['до_впало'] == 0, r['до_карток'], -r['до_впало'])
    return 'так само' if a == b else ('краще' if a > b else 'гірше')


for r in rows:
    r['оц'] = оцінка(r)
n4 = sum(r['карток'] == 4 for r in rows)
n0 = sum(r['впало'] == 0 for r in rows)
d4 = sum(r['до_карток'] == 4 for r in rows)
d0 = sum(r['до_впало'] == 0 for r in rows)
c = collections.Counter(o for r in rows for o in r['оц'].split())
out = [f"Усі чотири картки — {n4} з 30 (30.10: {d4}); без жодної `✗` — {n0} з 30 (30.10: {d0}).", '',
       '| № | запит | rc | с | карток | ВПАЛО | 30.10: карток / ВПАЛО | проти 30.10 | запис |', '|---|---|---|---|---|---|---|---|---|']
for r in rows:
    out.append(f"| {r['номер']:02} | {r['сцена']} | {r['rc']} | {r['секунди']} | {r['карток']} | {r['впало']} | {r['до_карток']} / {r['до_впало']} | {r['оц']} | `{r['запис']}/` |")
out += ['', f"Проти 30.10: краще — {c['краще']}, так само — {c['так само']}, гірше — {c['гірше']}.", '',
        '## Причини `✗` (запитів, де звірка впала)', '', '| причина | 30.10 | 1311 |', '|---|---|---|']
now = collections.Counter(x for r in rows for x in set(r['f']))
old = collections.Counter(x for r in rows for x in set(r['до_f']))
for k in sorted(set(now) | set(old), key=lambda k: -(now[k] + old[k])):
    out.append(f"| {k} | {old[k]} | {now[k]} |")
ok = [r for r in rows if r['карток'] > 0]
сто = collections.Counter(x for r in ok for x in set(r['f']))
out += ['', f'## Причини `✗` лише там, де збирання дійшло до карток ({len(ok)} запитів)', '', '| причина | запитів |', '|---|---|']
out += [f'| {k} | {v} |' for k, v in сто.most_common()]
worker = [r['номер'] for r in rows if 'мовчить 300' in (ROOT / r['запис'] / 'лог.txt').read_text(encoding='utf-8')]
nagoda = [r['номер'] for r in rows if r['rc'] == 1 and r['карток'] == 0]
out += ['', f'Обрив «worker: мовчить 300 с, виклик запити» (збирання не дало жодної картки): {len(worker)} запитів — '
        + ', '.join(f'{n:02}' for n in worker) + '.',
        f'Збирання не стартувало, бо стоїть «питання нагоди»: {len(nagoda)} — ' + ', '.join(f'{n:02}' for n in nagoda) + '.']
print('\n'.join(out))
