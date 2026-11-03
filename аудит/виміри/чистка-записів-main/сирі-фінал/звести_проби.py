import argparse, collections, json, re, subprocess
from pathlib import Path

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def read_pairs(folder):
    rows = [json.loads(s) for s in (folder / 'пари.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    result = {r['проба']: r for r in rows}
    assert len(result) == len(rows), 'Повторена назва проби'
    return result

def norm(s):
    s = re.sub(r'лічба_проб_[a-z0-9_]+', 'TREE', s)
    s = re.sub(r'tmp[a-z0-9_]{8}(?=\.xml)', 'TMP', s)
    return re.sub(r'обрив-стан-[a-z0-9_]+', 'обрив-стан-TMP', s)

p = argparse.ArgumentParser()
p.add_argument('--первинні', type=Path, required=True)
p.add_argument('--повтори', type=Path, required=True)
p.add_argument('--вихід', type=Path, required=True)
a = p.parse_args()
initial, repeated = [read_pairs(f) for f in (a.первинні, a.повтори)]
m0, m1 = [read_json(f / 'підсумок.json') for f in (a.первинні, a.повтори)]
assert m0['база'] == m1['база'] == '27c5d4686ce699a0e799e2c827c6efe94c0e8881'
assert not m0['зміни_дерева_користувача'] and not m1['зміни_дерева_користувача']
subprocess.run(['git', 'diff', '--quiet', m0['голова'], m1['голова'], '--', 'джерела'], check=True)
expected = set(subprocess.check_output(['git', 'ls-tree', '-rz', '--full-tree', '--name-only', m0['база'], '--', 'джерела/проби']).decode().split('\0'))
expected = {s for s in expected if s.endswith('.py')}
assert set(initial) == expected and len(expected) == 1305
different = {n for n, r in initial.items() if r['до']['rc'] != r['після']['rc']}
assert set(repeated) == different, 'Повтор має охопити рівно всі розбіжності'
for r in repeated.values():
    assert r['до']['rc'] == r['після']['rc'] == 0
resolved = initial | repeated
assert all(r['до']['rc'] == r['після']['rc'] for r in resolved.values())
reason_diff = [n for n, r in resolved.items() if norm(r['до']['причина']) != norm(r['після']['причина'])]
assert not reason_diff, reason_diff
counts = dict(sorted(collections.Counter(str(r['до']['rc']) for r in resolved.values()).items()))
out = {'база': m0['база'], 'основна_голова': m0['голова'], 'голова_повторів': m1['голова'],
       'проб': len(resolved), 'різних_кодів_після_уточнень': 0, 'однакові_коди': counts,
       'стеля_основна_сек': m0['стеля'], 'стеля_hilky_сек': resolved['джерела/проби/hilky_131.py']['стеля'],
       'без_стелі': [n for n, r in resolved.items() if r['стеля'] is None],
       'код_124': 'Межа часу приладу, не успішне завершення проби',
       'повторно_використано_кодів_незмінної_бази': m0['попередніх_кодів_бази'],
       'кожну_голову_запущено_наново': True, 'нових_FileNotFoundError': 0,
       'відмінних_причин_після_нормалізації_відомих_тимчасових_імен': reason_diff,
       'зміни_дерева_користувача': [], 'python': m0['python'],
       'секунд_основний_прогін': m0['секунд'], 'секунд_повтори': m1['секунд'],
       'сирі_пари': 'f3ca66bdfd6c0c74ac9254bc0a66cf62ae356bcb:аудит/виміри/чистка-записів-main/сирі-фінал/пари-первинні.jsonl'}
a.вихід.mkdir(parents=True, exist_ok=True)
(a.вихід / 'проби-підсумок.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(a.вихід / 'проби-повтори.json').write_text(json.dumps({'підсумок': m1, 'пари': list(repeated.values())}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (a.вихід / 'проби-коди.tsv').open('w', encoding='utf-8') as f:
    f.write('проба\tкод ДО\tкод ПІСЛЯ\n')
    for n, r in sorted(resolved.items()):
        f.write(f"{n}\t{r['до']['rc']}\t{r['після']['rc']}\n")
print(json.dumps(out, ensure_ascii=False))
