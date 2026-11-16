#!/usr/bin/env python3
"""Факти про взуття в образах руки 1 — лише з запису звернень до моделі й зі сторінки, без оцінок (наряд Живий-як-людина-4, мірило 3).
Запуск (з теки стенд/): python3 погода_й_дорога_факти.py <мітка:тека службове/...> [ситуація ...] > ../погода_й_дорога_факти.md
Для кожного образу руки 1 (`рука стенда` = 1; запис каталожних рук 1 і 2 не розрізняє, див. `руки_із_запису.py`) беруться:
 · рядок взуття у вході стилістки — з виклику «Build outfits» (пул) і з виклику «Choose one» (кандидати), дослівно, JSON;
 · що про погоду й дорогу було у вході збірки: `day`, `case.field_quotes`, `style_rules` (код + значення), правила `task.rules`
   і `occasion_rules`, у яких є слова про погоду, дорогу, каблук, підошву; знахідки ремонту про цю річ (`verdict`);
 · кроки: взуття в образі збірки → після ремонту → вибране → в описі з фото (`swap`, `wrong_photos`) → на картці сторінки;
 · що написано жінці: опис і рядок про цю річ із запису (англійською й перекладом, який пішов на екран) і текст картки зі сторінки."""
import json, os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from руки_із_запису import розібрати, образ_вибору, json_з, ціна_рядок

СЛОВА = re.compile(r'weather|frost|snow|ice\b|icy|salt|slush|rain|wet|slip|grip|sole|heel|stiletto|walk|road|surface|boot|footwear|shoe|поверх|підошв|каблук|підбор|дорог|погод|ожеледиц', re.I)
ТОЧНІ = re.compile(r'\b(weather|frost|snow|ice|icy|salt|slush|rain|wet|slip|slippery|grip|sole|soles|heel|heels|stiletto|road|surface|boots?|shoes?|footwear|walk)\b', re.I)
КЛЮЧІ_РЯДКА = re.compile(r'heel|sole|grip|slip|shaft|platform|toe|waterproof|insul|lining|height', re.I)


def скл(т): return re.sub(r'[\s\u00a0\u202f\u2009]', '', str(т))


def j(о): return json.dumps(о, ensure_ascii=False, sort_keys=False)


def карта_сторінки(тека):
    записи = [json.loads(л) for л in open(os.path.join(тека, 'руки.jsonl'), encoding='utf8')]
    збирання = {}
    for з in записи:
        if not з.get('прогін'): continue
        ст = збирання.get(з['прогін'], {})
        збирання[з['прогін']] = {**ст, **{к: в for к, в in з.items() if в not in (None, '') and к != 'поломка_руки_2'}}
    return list(збирання.values())


def переклади(виклики):
    """англійський текст → український, який пішов на екран: пари вхід/вихід усіх викликів-перекладачок."""
    м = {}
    for в in виклики:
        if not (в['т'].startswith('Ти — перекладачка') or '"role": "You are a translator' in в['т'][:300]): continue
        п = в['т'].rfind('\n{')
        вхід = json_з(в['т'][п:]) if п >= 0 else None
        вих = json_з(в['в']) or {}
        if isinstance(вхід, dict) and 'task' not in вхід:
            for к, х in вхід.items():
                if к in вих and isinstance(х, str): м[х] = вих[к]
    return м


def рядок_пулу(д, ід):
    п = (d_ := д or {}).get('pool') or d_.get('candidates') or {}
    кол = п.get('cols') or []
    for р in п.get('rows') or []:
        if р and р[0] == ід:
            о = dict(zip(кол, р))
            if len(р) > len(кол): о['(додатково)'] = р[len(кол):]
            return о
    return None


def взуття_в_образі(вихід_збірки, ід_образу, ряди_пулу):
    """id речей образу `ід_образу` у відповіді збірки/ремонту."""
    відп = json_з(вихід_збірки) or {}
    for x in відп.get('outfits') or []:
        if x.get('id') == ід_образу: return x.get('items') or []
    return None


def вердикт_про(д, ід):
    """знахідки входу ремонту/вибору, що називають річ `ід`: у `items` знахідки або в `item_ids` її тверджень."""
    знахідки = []
    for в in (д or {}).get('verdict') or []:
        for ф in (в.get('findings') or []) if isinstance(в, dict) else []:
            ідс = set(ф.get('items') or []) | {i for ст in ф.get('statements') or [] for i in (ст.get('item_ids') or [])}
            if ід in ідс:
                знахідки.append({'finding': ф.get('id'), 'statements': [{'code': ст.get('code'), 'values': ст.get('values'), 'recipient': ст.get('recipient')} for ст in ф.get('statements') or []]})
    return знахідки


def главa(мітка, тека, ситуації):
    виклики, проза, асемблі = розібрати(тека)
    за_н = {в['н']: в for в in виклики}
    пер = переклади(виклики)
    сторінка = карта_сторінки(тека)
    вих = []
    for номер, образи in enumerate(асемблі):
        з = сторінка[номер] if номер < len(сторінка) else None
        if not з: continue
        карт = {п['позиція']: п for п in з['позиції']}
        for образ in образи:
            if not образ['вибір']: continue
            речі, ід_образу = образ_вибору(образ['вибір'])
            найкращий, збіг = None, 0
            for поз, п in карт.items():
                зб = sum(1 for р in речі if any(f"{int(р['price'])}₴" in скл(к['назва']) for к in п['речі']))
                if зб > збіг: найкращий, збіг = поз, зб
            if not найкращий: continue
            рука_стенда = карт[найкращий]['рука']
            if рука_стенда != '1': continue
            вих.append((номер + 1, найкращий, образ, речі, ід_образу, карт[найкращий], з))
    return виклики, за_н, пер, вих


def опис_з_фото(виклики, ід_речей, після_н):
    """виклик «Photo 1 — …» (опис образу із фото), у якому є речі вибраного образу; рядки типу «#id (kind, type)»."""
    найкр, збіг = None, 0
    for в in виклики:
        if в['н'] <= після_н or not в['т'].startswith('Photo 1 —'): continue
        ід = set(re.findall(r'photo of (#\d+·\d+) \(([^)]*)\)', в['т'])) if False else {m[0] for m in re.findall(r'photo of (#\d+·\d+) \(([^)]*)\)', в['т'])}
        з = len(ід & ід_речей)
        if з > збіг: найкр, збіг = в, з
    return найкр


def друк(мітка, тека, ситуації):
    виклики, за_н, пер, вих = главa(мітка, тека, ситуації)
    ремонти = [в for в in виклики if в['д'] and 'Improve' in ((в['д'].get('task') or {}).get('role') or '')]
    for номер, поз, образ, речі, ід_образу, картка, збирання in вих:
        збірка = за_н[образ['збірка']]; вибір = образ['вибір']
        ід_речей = [р['n'] for р in речі]
        слот = {}
        # взуття: тип із рядків «Photo» опису (kind=shoes), інакше за переліком типів
        опис = опис_з_фото(виклики, set(ід_речей), вибір['н'])
        види = dict(re.findall(r'photo of (#\d+·\d+) \(([^)]*)\)', опис['т'])) if опис else {}
        взуття = [р for р in речі if (види.get(р['n'], '').split(',')[0].strip() == 'shoes') or (р['n'] not in види and re.search(r'boots?|sneakers|sandals|heels|pumps|loafers|flats|shoes|mules|oxfords|brogues|clogs|slippers', str(р.get('type') or ''), re.I))]
        print(f"\n### {мітка} · {ситуації} · прохід {номер} · позиція {поз} на екрані · рука 1 (стенд: {картка['рука']}) · образ {ід_образу}")
        print(f"- виклики запису (№ у `обміни.jsonl.gz`): збірка {збірка['н']}, вибір {вибір['н']}" + (f", опис із фото {опис['н']}" if опис else ", опису із фото в записі нема"))
        # ремонт цього образу: той, чий вхід збігається з речами збірки за id
        ід_збірки = {i for x in (json_з(збірка['в']) or {}).get('outfits', []) for i in x.get('items', [])}
        рем = None; найк = 0
        for р in ремонти:
            if not (збірка['н'] < р['н'] < вибір['н']): continue
            ід_р = set(re.findall(r'#\d+·\d+', р['т'])); з = len(ід_р & ід_збірки)
            if з > найк: рем, найк = р, з
        print(f"- ремонт (Improve): " + (f"виклик {рем['н']}" if рем else "виклику не знайдено"))
        день_д = (збірка['д'] or {})
        for р in взуття:
            ід = р['n']
            print(f"\n**Пара {ід}** — тип у записі: `{р.get('type')}`")
            рс = рядок_пулу(збірка['д'], ід); рк = рядок_пулу(вибір['д'], ід)
            print(f"\n1. Рядок стилістки.")
            print(f"   - вхід збірки (пул, виклик {збірка['н']}), колонки пулу `{j((збірка['д'].get('pool') or {}).get('cols'))}`: `{j(рс) if рс is not None else 'рядка в пулі нема'}`")
            print(f"   - вхід вибору (кандидати, виклик {вибір['н']}): `{j(рк) if рк is not None else 'рядка нема'}`")
            ключі = {}
            for х in ((рс or {}).get('(додатково)') or []):
                if isinstance(х, dict): ключі.update(х)
            print(f"   - усе, що в рядку пулу поза колонками (`(додатково)`): `{j(ключі) if ключі else 'нічого'}`")
            print(f"   - висота чи клас каблука й підошва: `heel`: `{j(ключі.get('heel', 'ключа нема'))}` · `heel_height`: `{j(ключі.get('heel_height', 'ключа нема'))}` · `sole`: `{j(ключі.get('sole', 'ключа нема'))}`; інші ключі з `heel`/`sole`/`grip`/`slip`: `{j({к: х for к, х in ключі.items() if re.search(r'heel|sole|grip|slip', к, re.I) and к not in ('heel', 'heel_height', 'sole')}) }`")
            print(f"\n2. Що про погоду й дорогу знав код (вхід збірки, виклик {збірка['н']}).")
            print(f"   - `day`: `{j(день_д.get('day'))}`")
            print(f"   - `case.field_quotes`: `{j((день_д.get('case') or {}).get('field_quotes'))}`")
            print(f"   - `style_rules`: `{j([{'code': x.get('code'), 'values': x.get('values'), 'recipient': x.get('recipient'), 'item_ids': x.get('item_ids')} for x in день_д.get('style_rules') or []])}`")
            for ряд in ((день_д.get('task') or {}).get('rules') or []):
                if isinstance(ряд, str) and ТОЧНІ.search(ряд): print(f"   - `task.rules`: «{ряд}»")
            for ряд in (день_д.get('occasion_rules') or []):
                if isinstance(ряд, str) and ТОЧНІ.search(ряд): print(f"   - `occasion_rules`: «{ряд[:600]}»")
            if рем:
                print(f"   - ремонт (виклик {рем['н']}) про цю річ: `{j(вердикт_про(рем['д'], ід)) if вердикт_про(рем['д'], ід) else 'знахідок про неї у вході ремонту нема'}`")
            print(f"   - вибір (виклик {вибір['н']}) про цю річ: `{j(вердикт_про(вибір['д'], ід)) if вердикт_про(вибір['д'], ід) else 'знахідок про неї у вході вибору нема'}`")
            print(f"\n3. Заміна.")
            бо = взуття_в_образі(збірка['в'], ід_образу, None); ро = взуття_в_образі(рем['в'], ід_образу, None) if рем else None
            def взув(л):
                return [i for i in (л or []) if i in {x['n'] for x in взуття} or i == ід or ((види.get(i, '').split(',')[0].strip() == 'shoes'))] if л is not None else None
            print(f"   - взуття в образі {ід_образу}: після збірки `{j(взув(бо))}` · після ремонту `{j(взув(ро)) if ро is not None else 'образу в ремонті нема'}` · вибране `{j([x['n'] for x in взуття])}`")
            оп = json_з(опис['в']) if опис else None
            if оп is not None:
                print(f"   - опис із фото (виклик {опис['н']}): `swap`: `{j(оп.get('swap', 'ключа нема'))}` · `wrong_photos`: `{j(оп.get('wrong_photos'))}` · ключі відповіді: `{j(list(оп.keys()))}`")
            ціна = ціна_рядок(р['price'])
            наст = [к for к in картка['речі'] if f"{int(р['price'])}₴" in скл(к['назва']) or (к.get('слот') or '') in ('shoes', 'взуття')]
            print(f"   - на картці сторінки (позиція {поз}), річ за ціною {ціна} ₴ чи слотом взуття: " + (j([{'назва': к['назва'], 'слот': к.get('слот')} for к in наст]) if наст else 'не знайдено') + f"; усі речі картки: `{j([{'назва': к['назва'], 'слот': к.get('слот')} for к in картка['речі']])}`")
            print(f"\n4. Що написано жінці.")
            if оп:
                про = [x for x in оп.get('about_items') or [] if x.get('n') == ід]
                print(f"   - рядок про річ у описі (EN): `{j(про[0]['text']) if про else 'рядка про цю річ нема'}`" + (f"\n     переклад: `{j(пер.get(про[0]['text'], 'переклад не знайдено'))}`" if про else ''))
                print(f"   - текст опису образу (EN): «{оп.get('text')}»")
                print(f"     переклад: «{пер.get(оп.get('text'), 'переклад не знайдено')}»")
                for н_, ряд in enumerate(оп.get('how_to_wear') or [], 1):
                    print(f"   - як носити {н_} (EN): «{ряд}»; переклад: «{пер.get(ряд, 'переклад не знайдено')}»")
            else:
                print("   - опису із фото в записі нема")
            тк = картка.get('текст_картки')
            if тк: print(f"   - текст картки на екрані (зі сторінки, дослівно):\n\n```\n{тк}\n```")
            else: print("   - текст картки зі сторінки в записі цього прогону не збережено")


if __name__ == '__main__':
    print("# Взуття в образах руки 1 — факти із запису (без оцінок)\n")
    print("Джерело — `стенд/погода_й_дорога_факти.py` (читає `обміни.jsonl.gz` і `руки.jsonl` кожної ситуації). Рука 1 — за рукою, яку записав стенд зі сторінки (`руки.jsonl`); запис звернень каталожних рук 1 і 2 не розрізняє (`руки.md`).")
    for арг in sys.argv[1:]:
        мітка, тека = арг.split(':', 1)
        print(f"\n## {мітка} — {os.path.basename(тека)}")
        друк(мітка, тека, os.path.basename(тека))
