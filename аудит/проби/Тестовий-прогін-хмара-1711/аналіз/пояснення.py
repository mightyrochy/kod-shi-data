"""#4161: пояснення руки 1 — вхід опису (речі кодами, кадри) і відповідь моделі (about_items, text, how_to_wear) + текст на екрані."""
import json, re, sys, glob
from pathlib import Path
for сцена in sys.argv[1:]:
    d = json.loads(Path(сцена, 'вердикти.txt').read_text())
    в1 = [в for в in d['прогони'][0]['вердикти'] if str(в['рука']) == '1'][0]
    дов = в1['етапи'].get('довідник_речей') or {}
    номери = {(дов.get(р['id']) or {}).get('номер'): р['назва'] for р in в1['речі_образу']}
    print(f'##### {сцена} · рука 1 · речі на картці:', ', '.join(f'{н} «{т}»' for н, т in номери.items()))
    for f in sorted(glob.glob(f'{сцена}/VIDPOVIDI/*ОПИС_V1*.txt')):
        т = Path(f).read_text(); пр, _, відп = т.partition('── ВІДПОВІДЬ')
        try: вх = json.loads(пр[пр.index('{"version"'):].strip())
        except Exception: continue
        ід = [і['n'] for і in вх['outfit']['items']]
        if not set(ід) & set(номери): continue
        фото = len(re.findall(r'^Photo \d+', пр, re.M)); нед = пр.count('(image not delivered)')
        print(f'--- {Path(f).name} · речей {len(ід)} · кадрів {фото} · не дійшло {нед}')
        print('    вхід речей:', json.dumps(вх['outfit']['items'], ensure_ascii=False))
        print('    case.field_quotes:', json.dumps((вх.get('case') or {}).get('field_quotes'), ensure_ascii=False), '· day:', json.dumps(вх.get('day'), ensure_ascii=False)[:300])
        о = json.loads(відп[відп.index('{'):].strip())
        for а in о.get('about_items', []): print(f"    ABOUT {а['n']}: {а['text']}")
        print('    TEXT:', о.get('text')); print('    HOW:', о.get('how_to_wear'))
    print('    НА ЕКРАНІ (опис):', в1.get('опис'))
