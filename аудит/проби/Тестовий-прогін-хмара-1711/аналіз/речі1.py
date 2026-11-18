"""Пояснення руки 1 з вердикти.txt: about_items, text, how_to_wear (сирий EN) — для ручної лічби класу 16321."""
import json, sys
for с in sys.argv[1:]:
    d = json.load(open(f'{с}/вердикти.txt'))
    for в in d['прогони'][0]['вердикти']:
        if str(в['рука']) != '1': continue
        t = json.loads(в['текст']) if в['текст'].lstrip().startswith('{') else {'text': в['текст']}
        print('=====', с, '· речей', len(t.get('about_items', [])))
        for a in t.get('about_items', []): print(' ', a['n'], '|', a['text'])
        print('  TEXT |', t.get('text'))
        print('  HOW  |', t.get('how_to_wear'))
