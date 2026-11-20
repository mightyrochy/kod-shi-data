"""Текст картки руки 1 з екранів стенда (екрани.jsonl): позиція руки 1 — з руки.jsonl, екрани — ті, де показано «N / 4»
цієї позиції; рядки без повторів, у порядку появи. Запуск: python3 картки_руки_1.py <тека службове/<ситуація>>"""
import json, gzip, sys, re
т = sys.argv[1]
def рядки(ф):
    try:
        return [json.loads(l) for l in open(ф)]
    except FileNotFoundError:
        return [json.loads(l) for l in gzip.open(ф + ".gz", "rt")]
руки = рядки(т + "/руки.jsonl"); екрани = рядки(т + "/екрани.jsonl")
for прохід in sorted({р["прохід"] for р in руки}):
    р = [x for x in руки if x["прохід"] == прохід][-1]
    поз = [п["позиція"] for п in р["позиції"] if п["рука"] == "1"]
    print(f"\n### прохід {прохід}: рука 1 на позиції {поз}")
    if not поз:
        continue
    бачено = set()
    for е in екрани:
        if е["прохід"] != прохід or not re.search(rf"(^|\n){поз[0]} / 4", е.get("текст") or ""):
            continue
        for рядок in (е["текст"] or "").split("\n"):
            if рядок not in бачено and len(рядок) > 2:
                бачено.add(рядок); print(рядок)
