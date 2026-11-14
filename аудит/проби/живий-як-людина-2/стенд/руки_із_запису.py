#!/usr/bin/env python3
"""Руки образів — з ЗАПИСУ звернень до моделі (службове/<с>/обміни.jsonl), а не з того, що записав стенд про руку.
Рука: прозові руки 3–4 — виклик «personal stylist. Put together one outfit» (`person` непорожнє — 3, null — 4);
каталожні 1–2 — два виклики «Build outfits», рука 2 — той, чий `task.rules[2]` відрізняється від типового (K-CRA-01) або чий
пул відрізняється; образ каталожної руки — вибраний (`chosen`) образ виклику «Choose one», пов'язаний із збіркою збігом підписів.
Позиція на екрані: каталожний образ — за (слот, ціна) речей вибраного образу ↔ речі картки (ціна лише ключ зв'язку, не оцінка);
прозовий — за назвами речей українською з виклику-перекладу (вхід містить англійські назви з переліку речей руки).
Сід: ключ позицій = перемішатиП(['1','2','3','4'], сід) — той самий LCG, що в `стадії_збирання.js`.
Запуск: python3 руки_із_запису.py <тека службове/<с>> > руки_із_запису.json ; python3 руки_із_запису.py <тека> md  — рядки таблиці"""
import json, re, sys, os

def перемішати(а, сід):
    s = сід; б = list(а)
    for i in range(len(б) - 1, 0, -1):
        s = (s * 9301 + 49297) % 233280; j = int(s / 233280 * (i + 1)); б[i], б[j] = б[j], б[i]
    return б

def текст(з):
    m = з['messages'][-1]['content']
    return m if isinstance(m, str) else ''.join(b.get('text', '') for b in m if b.get('type') == 'text')

def відп(о):
    try: return json.loads(о['відповідь'])['content'][0]['text']
    except Exception: return ''

def json_з(т):
    п, к = т.find('{'), т.rfind('}')
    try: return json.loads(т[п:к + 1])
    except Exception: return None

def ціна_рядок(ц): return f"{int(ц):,}".replace(',', ' ') if ц is not None else ''

def розібрати(тека):
    import gzip
    ф = os.path.join(тека, 'обміни.jsonl')
    R = [json.loads(л) for л in (open(ф, encoding='utf8') if os.path.exists(ф) else gzip.open(ф + '.gz', 'rt', encoding='utf8'))]
    виклики = []
    for н, о in enumerate(R):
        if 'запит' not in о: continue
        з = json.loads(о['запит']); т = текст(з)
        виклики.append({'н': н, 'час': о['час'], 'т': т, 'в': відп(о)})
    for в in виклики:
        т = в['т']; в['рід'] = None; в['д'] = json_з(т) if т.startswith('{') else None
        д = в['д'] or {}; роль = ((д.get('task') or {}).get('role') or '')
        if роль.startswith('You are a personal stylist. Put together one outfit'):
            в['рід'] = 'проза'; в['рука'] = '3' if д.get('person') else '4'
        elif 'Build outfits' in роль: в['рід'] = 'збірка'
        elif 'Choose one' in роль: в['рід'] = 'вибір'
        elif роль.startswith('You read the description of an outfit'): в['рід'] = 'перелік'
    # прозові: у порядку часу; n-те збирання — n-та пара
    проза = sorted([в for в in виклики if в['рід'] == 'проза'], key=lambda в: в['час'])
    збирання = {}
    for в in проза:
        збирання.setdefault('3' if в['рука'] == '3' else '4', []).append(в)
    n = max(len(збирання.get('3', [])), len(збирання.get('4', [])), 0)
    # каталожні: збірки — парами за часом; вибір — за підписами
    збірки = sorted([в for в in виклики if в['рід'] == 'збірка'], key=lambda в: в['час'])
    вибори = sorted([в for в in виклики if в['рід'] == 'вибір'], key=lambda в: в['час'])
    def підписи_збірки(в):
        о = json_з(в['в']) or {}; return {x.get('caption') for x in (о.get('outfits') or []) if x.get('caption')}
    def правило(в): return ((в['д'] or {}).get('task') or {}).get('rules', [])[2:3]
    # групи збірок: (початок на хвилину раніше ± ) — парами за близьким часом
    групи = []
    for в in збірки:
        for г in групи:
            if abs(ord_t(в['час']) - ord_t(г[0]['час'])) < 150 and len(г) < 2: г.append(в); break
        else: групи.append([в])
    асемблі = []; використані = set()
    for г in групи:
        ру = {}
        if len(г) == 2:
            а, б = г; ра, рб = правило(а), правило(б)
            if ра != рб:
                типове = 'Besides the top' 
                ру[id(а)] = '1' if ра and ра[0].startswith('Besides the top') else '2'
                ру[id(б)] = '1' if рб and рб[0].startswith('Besides the top') else '2'
            else:
                ка, кб = set(а['д']), set(б['д'])  # слід поломки: зайвий ключ верхнього рівня (`kinds_missing`) або K-SIL-03
                ва = 'volume_top_and_bottom_no_anchor' in a_sc(а); вб = 'volume_top_and_bottom_no_anchor' in a_sc(б)
                if ка != кб: ру[id(а)], ру[id(б)] = ('2', '1') if ка > кб else ('1', '2')
                elif ва != вб: ру[id(а)], ру[id(б)] = ('2', '1') if ва else ('1', '2')
                else: ру[id(а)] = ру[id(б)] = 'кат.?'
        else:
            ру[id(г[0])] = 'кат.?'
        образи = []
        for в in г:
            підп = підписи_збірки(в)
            вільні = [х for х in вибори if х['час'] >= г[0]['час'] and id(х) not in використані]
            кращий = max(вільні, key=lambda х: len(підп & {y['your_outfit']['caption'] for y in (х['д'] or {}).get('verdict', []) if 'your_outfit' in y}), default=None)
            if кращий: використані.add(id(кращий))
            образи.append({'збірка': в['н'], 'рука': ру[id(в)], 'вибір': кращий})
        асемблі.append(образи)
    return виклики, збирання, асемблі

def a_sc(в): return ((в['д'] or {}).get('task') or {}).get('statement_codes') or {}

def ord_t(ч): 
    from datetime import datetime
    return datetime.fromisoformat(ч.replace('Z', '+00:00')).timestamp()

def образ_вибору(вибір):
    д = вибір['д']; о = json_з(вибір['в']) or {}; ід = о.get('chosen')
    вихід = next((y['your_outfit'] for y in д.get('verdict', []) if y.get('your_outfit', {}).get('id') == ід), None)
    ряди = {р[0]: dict(zip(д['candidates']['cols'], р)) for р in д['candidates']['rows']}
    return [ряди[н] for н in (вихід or {}).get('items', []) if н in ряди], ід

def зіставити(тека):
    виклики, проза, асемблі = розібрати(тека)
    записи = [json.loads(л) for л in open(os.path.join(тека, 'руки.jsonl'), encoding='utf8')]
    збирання = {}
    for з in записи:
        if not з.get('прогін'): continue
        ст = збирання.get(з['прогін'], {})
        збирання[з['прогін']] = {**ст, **{к: в for к, в in з.items() if в not in (None, '') and к != 'поломка_руки_2'}}
    вихід = []
    for номер, (пр, з) in enumerate(збирання.items()):
        # ті збірки, що йдуть у цьому проході: за порядком часу
        ас = асемблі[номер] if номер < len(асемблі) else []
        карт = {п['позиція']: п for п in з['позиції']}
        незалежно = {}
        # каталожні: за (слот, ціна)
        for образ in ас:
            if not образ['вибір']: continue
            речі, ід = образ_вибору(образ['вибір'])
            ключ = {(р['type'], ціна_рядок(р['price'])) for р in речі}
            найкращий, збіг = None, 0
            for поз, п in карт.items():
                зб = sum(1 for р in речі if any(ціна_рядок(р['price']) + ' ₴' in к['назва'].replace(' ', ' ') or ціна_рядок(р['price']) in к['назва'].replace(' ', ' ') for к in п['речі']))
                if зб > збіг: найкращий, збіг = поз, зб
            if найкращий: незалежно[найкращий] = (образ['рука'], f'вибір {ід}: {збіг} з {len(речі)} речей за ціною')
        # прозові: українські рядки перекладу, що містять назви речей картки
        for рука in ('3', '4'):
            виклики_р = проза.get(рука, [])
            if номер >= len(виклики_р): continue
            в = виклики_р[номер]; англ = в['в']
            пер = None
            for к in виклики:
                if к['рід'] is None and 'перекладачка' in к['т'][:40] and к['час'] >= в['час']:
                    ім = [р['name'] for р in ((json_з(next((x['в'] for x in виклики if x['рід'] == 'перелік' and x['час'] >= в['час'] and англ[:60] in x['т']), '')) or {}).get('items') or [])]
                    if ім and all(н in к['т'] for н in ім[:3]): пер = к; break
            if not пер: continue
            укр = json_з(пер['в']) or {}; рядки = ' '.join(str(х) for х in укр.values())
            найкращий, збіг = None, 0
            for поз, п in карт.items():
                if п['рука'] is None: continue
                зб = sum(1 for к in п['речі'] if к['назва'] and к['назва'] in рядки)
                if зб > збіг and зб >= max(3, len(п['речі']) - 1): найкращий, збіг = поз, зб
            if найкращий and найкращий not in незалежно: незалежно[найкращий] = (рука, f'переклад: {збіг} з {len(карт[найкращий]["речі"])} назв речей')
        вихід.append({'прогін': пр, 'сід': з.get('сід'), 'ключ_стенда': з.get('ключ'),
                      'ключ_із_сіду': ''.join(перемішати(['1', '2', '3', '4'], з['сід'])) if з.get('сід') else None,
                      'позиції': [{'позиція': i, 'рука_стенда': (карт.get(i) or {}).get('рука'), 'рука_із_запису': незалежно.get(i, (None, ''))[0], 'підстава': незалежно.get(i, (None, 'не зіставлено'))[1]} for i in range(1, 5)]})
    return вихід

if __name__ == '__main__':
    р = зіставити(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == 'md':
        for п in р:
            print(f"| {п['прогін']} | {п['сід']} | {п['ключ_стенда']} / {п['ключ_із_сіду']} | " + ' | '.join(f"{x['рука_стенда']}={x['рука_із_запису']}" for x in п['позиції']) + ' |')
    else: print(json.dumps(р, ensure_ascii=False, indent=1))
