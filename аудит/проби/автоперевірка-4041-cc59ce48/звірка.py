"""Два виходи е3_формальність_знімок.py → зведення змін; сирі файли не редагуються."""
import collections
import gzip
import json
import sys

before, after = [json.load(gzip.open(p, 'rt', encoding='utf-8')) for p in sys.argv[1:3]]
assert len(before) == len(after)
changes = collections.Counter()
groups = collections.Counter()
unchanged = 0
for b, a in zip(before, after):
    assert b[:5] == a[:5], (b[:5], a[:5])
    changed = [i for i in range(5, 11) if b[i] != a[i]]
    if not changed:
        unchanged += 1
        continue
    for i in changed:
        changes[(a[2], i)] += 1
    groups[(a[2], b[5], a[5], b[8], a[8], b[9], a[9])] += 1
assert {k[0] for k in changes} <= {'K-KOH-05', 'K-KOH-08', 'K-OCC-01'}
summary = dict(знахідок=len(after), тотожних=unchanged,
               змін_сили=sum(v for (_, i), v in changes.items() if i == 5),
               змін_ваги=sum(v for (_, i), v in changes.items() if i == 9),
               поля=dict(сила=5, регістр=6, блокує=7, вага_конструктора=8, обмежена_вага=9, під_підлогою=10),
               зміни_полів=[[rule, i, n] for (rule, i), n in sorted(changes.items())],
               групи=[[*key, n] for key, n in sorted(groups.items(), key=str)])
print(json.dumps(summary, ensure_ascii=False, indent=2))
