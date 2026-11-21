"""Лічба клітинок «без входу» для полів сценарію на записаних прогонах: not_passed прямо і not_given при полі в паспорті."""
import json, sys, glob, collections
НЕВІД = (None, "", "невідомо", [], {})
def клітинки(o):
    if isinstance(o, dict):
        ч = o.get("чому")
        if isinstance(ч, str) and ч.startswith(("not_given:", "not_passed:")):
            yield ч
        for v in o.values(): yield from клітинки(v)
    elif isinstance(o, list):
        for v in o: yield from клітинки(v)
пр = collections.Counter(); вт = collections.Counter(); всього = collections.Counter(); файлів = 0
for ф in sys.argv[1:]:
    try: r = json.load(open(ф, encoding="utf8"))
    except Exception: continue
    if not isinstance(r, dict) or "прогони" not in r: continue
    файлів += 1
    п0 = ((r.get("спільне") or {}).get("паспорт") or {})
    if not isinstance(п0, dict): п0 = {}
    for прг in r["прогони"]:
        пп = ((прг.get("спільне") or {}).get("паспорт")) or {}
        п = dict(п0); п.update(пп if isinstance(пп, dict) else {})
        for ч in клітинки(прг):
            рід, поле = ч.split(":", 1)
            всього[ч] += 1
            if рід == "not_passed": пр[поле] += 1
            elif п.get(поле) not in НЕВІД: вт[(поле, json.dumps(п.get(поле), ensure_ascii=False)[:30])] += 1
print("файлів", файлів)
print("not_passed:", dict(пр))
print("not_given при полі в паспорті:", sum(вт.values()))
for k, n in вт.most_common(25): print(" ", n, k)
