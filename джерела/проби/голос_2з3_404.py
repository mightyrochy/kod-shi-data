# -*- coding: utf-8 -*-
# Рядок 2688 (РОЗБІР-404): голосування 2 з 3 прогонів розбору → розбір.json, який читає еталон_поточний.py; друкує, скільки «вигадок» суду — not_applicable на полі «не застосовне».
# Запуск: python3 -I джерела/проби/голос_2з3_404.py вихід.json 404_а1/розбір.json 404_а2/розбір.json 404_а3/розбір.json   (~1 с; моделі й каталогу не треба)
import sys, os, ast, json, collections as C
Т = os.path.dirname(os.path.abspath(__file__)); Е = json.load(open(Т + '/еталон_розбору.json', encoding='utf-8')); ПОЛЯ = Е['поля']
д = ast.parse(open(Т + '/еталон_частки.py', encoding='utf-8').read()); exec(compile(ast.Module([в for в in д.body if isinstance(в, ast.FunctionDef)], []), 'x', 'exec'))
РЗ = [json.load(open(ф, encoding='utf-8')) for ф in sys.argv[2:]]; пусто = lambda v: v in (None, 'unknown', [])
def голос(зн):   # значення, яке дали ≥2 прогони; інакше None
    с = C.Counter(json.dumps(v) for v in зн if not пусто(v)); return json.loads(с.most_common(1)[0][0]) if с and с.most_common(1)[0][1] >= 2 else None
вих, рах = {}, C.Counter()
for р in Е['речі']:
    взуття = 'shoes' in р['правда']['slot']; з = [з_розбору(к[р['id']], взуття) for к in РЗ if р['id'] in к]
    г = {п: голос([x[п] for x in з]) for п in ПОЛЯ if п != 'set_parts'}; ч = голос([json.dumps(x['set_parts']) for x in з]); ч = json.loads(ч) if ч else []
    вих[р['id']] = dict(slot=г['slot'], item_type=г['item_type'], **{'shaft' if взуття else 'length': г['length']}, sleeve=г['sleeve'], neckline=г['neckline'], cut=г['cut'], fabric=г['fabric'], pattern=г['pattern'],
                        color_main=г['color'], metal=г['metal'], veto={'shine': г['shine']}, set_parts=[{'item_type': т} for т in ч])
    for п in ПОЛЯ:
        k = з_розбору(вих[р['id']], взуття)
        if not пусто(k[п]): в = суд(р['правда'][п], р['опора'].get(п, []), k[п], True); рах[в] += 1; рах['вигадано, не not_applicable'] += в == 'вигадано' and k[п] != 'not_applicable'
json.dump(вих, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False)
print('голос 2 з 3: ' + ' · '.join('%s %d' % к for к in рах.items()) + ' · вигадок на 720 без not_applicable %.1f %%' % (100 * рах['вигадано, не not_applicable'] / 720))
