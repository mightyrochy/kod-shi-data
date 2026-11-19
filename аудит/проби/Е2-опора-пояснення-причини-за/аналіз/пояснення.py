"""Наряд «причини-за»: пояснення руки 1 — причини й оголошені ходи у вході опису (reasons, your_declared), відповідь моделі
(about_items, text, how_to_wear), повтор `items_not_described` і текст на екрані. Копія `Тестовий-прогін-хмара-1711/аналіз/
пояснення.py` з причинами входу; лічба — та сама, що в оцінці #4205 (ЗВІТ.md)."""
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
        print(f'--- {Path(f).name} · речей {len(ід)} · кадрів {фото} · не дійшло {нед}' + (' · ПОВТОР ' + json.dumps(вх['format_error'].get('not_described'), ensure_ascii=False) if вх.get('format_error') else ''))
        print('    вхід речей:', json.dumps(вх['outfit']['items'], ensure_ascii=False))
        print('    day:', json.dumps(вх.get('day'), ensure_ascii=False)[:300])
        for н in ід:
            пр_н = [{к: v for к, v in р.items() if к != 'item'} for р in (вх.get('reasons') or []) if р.get('item') == н]
            for р in пр_н:
                if р.get('statements'): р['statements'] = [(з['code'], з.get('day_facts')) if з.get('day_facts') else з['code'] for з in р['statements']]
            св = [з['code'] for х in (вх.get('your_declared') or []) if х.get('item') == н for з in х.get('statements') or []]
            print(f'    REASONS {н}:', json.dumps(пр_н, ensure_ascii=False), '· DECLARED:', св)
        о = json.loads(відп[відп.index('{'):].strip())
        for а in о.get('about_items', []): print(f"    ABOUT {а['n']}: {а['text']}")
        print('    без запису:', [н for н in ід if н not in {а['n'] for а in о.get('about_items', [])}])
        print('    TEXT:', о.get('text')); print('    HOW:', о.get('how_to_wear'))
    print('    НА ЕКРАНІ (опис):', в1.get('опис'))
