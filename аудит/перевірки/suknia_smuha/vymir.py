# Рядки 1412 і 1427: обрана сукня зі смугою ≥6 щаблів і «вибір за тобою» на картках рук 1–2
import json, gzip, os, re, sys
R = sys.argv[1]
РЕ = re.compile(r'вибір за тобою|тобі вирішувати|на твій розсуд|твоє рішення|вирішуєш ти|вирішувати тобі|вирішиш ти', re.I)
ш6 = фраз = карток = обр = 0
for run in sorted(os.listdir(R)):
    p = os.path.join(R, run, 'вердикти.txt.gz')
    if not os.path.exists(p): continue
    for v in json.load(gzip.open(p, 'rt'))['прогони'][0]['вердикти']:
        ch = [s for s in v['етапи']['виклики'] if s['крок'] == 'choice']
        if v['рука'] not in ('1', '2') or not ch: continue
        pj = json.loads(ch[0]['запит']['текст']); cid = ch[0]['вибір']['обрано'].replace('о', 'o')
        f = (pj.get('day') or {}).get('formality') or {}
        for x in pj['verdict']:
            if x['your_outfit']['id'] != cid: continue
            for it in x['your_outfit']['items']:
                if it.get('type') == 'dress_generic' or 'сукн' in it['name'].lower():
                    fo = it.get('formality'); обр += 1
                    w = fo[1] - fo[0] if fo else None
                    ш6 += bool(w is not None and w >= 6)
                    print('%-26s р%s смуга %s–%s · сукня formality=%s · %s' % (run, v['рука'], f.get('from'), f.get('to'), fo, it['name'][:50]))
    for blk in re.split(r'═══ картка', open(os.path.join(R, run, 'картки.txt')).read())[1:]:
        m = re.match(r' \d з \d · рука (\d)', blk)
        if not m or m.group(1) not in '12': continue
        карток += 1; mm = РЕ.search(blk)
        if mm:
            фраз += 1; print('   «%s» … %s' % (mm.group(0), blk[max(0, mm.start()-140):mm.end()].replace('\n', ' ')))
print('%s: обраних суконь %d · смуга ≥6 — %d · карток рук 1–2 %d · з фразою «вибір за тобою» — %d' % (os.path.basename(R.rstrip('/')), обр, ш6, карток, фраз))
