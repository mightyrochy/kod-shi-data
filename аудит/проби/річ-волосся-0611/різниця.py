"""Різниця виходу двох повторів (слід.py): записи, що різняться, і шляхи JSON, де різниця."""
import json, sys, collections
def шляхи(a, b, p=""):
    if type(a) != type(b): yield p; return
    if isinstance(a, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b: yield p + "/" + k
            else: yield from шляхи(a[k], b[k], p + "/" + k)
    elif isinstance(a, list):
        if len(a) != len(b): yield p + "[len]"; return
        for i, (x, y) in enumerate(zip(a, b)): yield from шляхи(x, y, p + "/" + str(i))
    elif a != b: yield p
for сцена in sys.argv[3:]:
    до = [json.loads(р) for р in open("%s-%s.jsonl" % (sys.argv[1], сцена), encoding="utf8")][1:]
    піс = [json.loads(р) for р in open("%s-%s.jsonl" % (sys.argv[2], сцена), encoding="utf8")][1:]
    л = collections.Counter(); різних = 0
    for x, y in zip(до, піс):
        ш = [s for s in шляхи(x, y) if "час" not in s and "мс" not in s]
        if ш: різних += 1; л.update((x.get("ендпойнт") or x.get("дія") or "?", s) for s in ш)
    print(сцена, "записів", len(до), len(піс), "різних", різних)
    for (е, s), n in л.most_common(25): print("  ", е, s, n)
