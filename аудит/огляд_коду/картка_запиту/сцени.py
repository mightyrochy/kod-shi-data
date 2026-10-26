import os, re, sys, json
L = sys.argv[1]
out = []
for root, dirs, files in sorted(os.walk(L)):
    if 'лог.txt' not in files or 'VIDPOVIDI' not in dirs:
        continue
    t = open(os.path.join(root, 'лог.txt'), encoding='utf8', errors='replace').read()
    rel = root[len(L)+1:]
    rel = re.sub(r'^zhyvi-[^/]+/аудит/', '', rel)
    out.append('### ' + rel)
    for line in t.split('\n'):
        s = line.strip()
        m = re.match(r'^(?:\S+ · )?(ВОНА|СТИЛІСТКА|ЯДРО|ВИМІРИ|НЕ ВЗЯТО)\s*:\s*(.*)$', s)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if k == 'ВИМІРИ':
            parts = [p.strip() for p in v.split(' · ')]
            keep = [p for p in parts if '(default)' not in p or re.match(r'(hour|part_of_day|temperature_c|formality)=', p)]
            v = ' · '.join(keep)
        if k == 'НЕ ВЗЯТО':
            try:
                arr = json.loads(v)
                v = ' | '.join(re.sub(r' · step=\w+', '', x)[:160] for x in arr)
            except Exception:
                v = v[:400]
        out.append('  %s: %s' % (k, v[:900]))
print('\n'.join(out))
