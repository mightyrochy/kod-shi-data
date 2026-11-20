#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Перерахунок відповідей на три питання наряду «Записи-мосту-оцінка-без-викликів»
із 16 записаних проходів (8 ситуацій × 2 проходи, 513 викликів) на claude-sonnet-5-5 через справжній міст.
Нових викликів моделі продукту й моста — 0.

Запуск із кореня репозиторію:
    python3 -I аудит/проби/Записи-мосту-оцінка/оцінка.py [тека_прогону]
"""
import collections
import datetime as D
import glob
import json
import os
import re
import statistics
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ТЕКА = sys.argv[1] if len(sys.argv) > 1 else os.path.join('аудит', 'проби', 'Живий-через-міст')

# Чинна ціна claude-sonnet-5-5 ($ за 1 млн токенів).
# Джерело: офіційний прайс Anthropic на 19.11.2026, зафіксований у
# аудит/проби/модель-текст-claude/ЗВІТ.md (рядки 8-10) та аудит/проби/модель-текст-claude/скрипти/рахунок.py (рядки 14-24).
ЦІНА_ВХІД_НОВІ = 2.00      # input_tokens
ЦІНА_КЕШ_ЗАПИС = 2.50      # cache_creation_input_tokens (TTL 5 хв = 1.25x базового входу)
ЦІНА_КЕШ_ЧИТАННЯ = 0.10    # cache_read_input_tokens (0.1x базового входу)
ЦІНА_ВИХІД = 10.00         # output_tokens (разом із думками)


def ts(iso_str):
    return D.datetime.fromisoformat(iso_str.replace('Z', '+00:00')).timestamp()


def вартість_usd(u):
    inp = u.get('input_tokens', 0)
    cw = u.get('cache_creation_input_tokens', 0)
    cr = u.get('cache_read_input_tokens', 0)
    out = u.get('output_tokens', 0)
    return (inp * ЦІНА_ВХІД_НОВІ + cw * ЦІНА_КЕШ_ЗАПИС + cr * ЦІНА_КЕШ_ЧИТАННЯ + out * ЦІНА_ВИХІД) / 1e6


def розібрати_запит(req_str):
    req = json.loads(req_str)
    texts = []
    imgs = 0
    for m in req.get('messages', []):
        c = m.get('content', '')
        if isinstance(c, str):
            texts.append(c)
        elif isinstance(c, list):
            for b in c:
                if isinstance(b, dict):
                    if b.get('type') == 'text':
                        texts.append(b.get('text', ''))
                    elif b.get('type') == 'image':
                        imgs += 1
    last_text = texts[-1] if texts else ''
    full_text = '\n'.join(texts)
    role = ''
    try:
        obj = json.loads(last_text)
        task = obj.get('task') or obj.get('завдання') or {}
        role = task.get('role') or task.get('роль') or ''
    except Exception:
        role = last_text.splitlines()[0] if last_text else ''
    return role, last_text, full_text, imgs


def класифікувати_роль(role, imgs):
    if 'live chat with a woman' in role and 'invitation' not in role:
        return 'Розмова (паспорт і відповідь)'
    if 'The app did not show her an invitation' in role:
        return 'Розмова (ремонт запрошення)'
    if 'just changed the tiles' in role:
        return 'Плитки сценарію (ошатність)'
    if 'пишеш жінці репліку стилістки' in role:
        return 'Перекладачка репліки чату'
    if 'She left the colour scheme' in role:
        return 'Вибір палітри стилісткою'
    if 'Build outfits for her case from «pool»' in role:
        return 'Складання з пулу (Build, руки 1–2)'
    if 'blocker in «structure»' in role:
        return 'Доповнення структури (Completeness)'
    if 'Improve the outfits the code checked' in role:
        return 'Ремонт образів (Improve, руки 1–2)'
    if 'Choose one of your outfits for her' in role:
        return 'Вибір одного образу (Choose, руки 1–2)'
    if 'You tell her why you chose this outfit' in role:
        return 'Опис образу з фото (руки 1–2)' if imgs > 0 else 'Опис образу без фото (fallback, руки 1–2)'
    if 'Put together one outfit for her case' in role:
        return 'Складання без пулу (руки 3–4)'
    if 'read the description of an outfit and list its items' in role:
        return 'Перелік речей з прози (руки 3–4)'
    if 'пишеш природною українською рядки' in role:
        return 'Перекладачка повідомлень (рядки)'
    if 'пишеш природною українською тексти' in role:
        return 'Перекладачка текстів картки'
    if "translate a woman's comment on a look" in role:
        return 'Перекладачка вердикту жінки'
    return 'Інше'


def класифікувати_зайвий(x, idx, obm, role, full_text, imgs):
    st = x.get('статус')
    if st != 200:
        if re.search(r'"format_error"\s*:|Correct the previous answer', full_text):
            return '400_на_повторі_опису_з_фото'
        return '400_фото_крамниці_не_завантажилось'
    if re.search(r'"format_error"\s*:|Correct the previous answer', full_text):
        if 'live chat with a woman' in role:
            return 'повтор_контракту_чату'
        if 'You tell her why you chose this outfit' in role:
            return 'повтор_опису_items_not_described'
        if "translate a woman's comment" in role:
            return 'повтор_формату_вердикту'
        return 'повтор_формату_інше'
    if 'The app did not show her an invitation' in role:
        return 'повтор_запрошення_чату_no_invite'
    if 'You tell her why you chose this outfit' in role and imgs == 0:
        return 'повтор_опису_без_фото_після_400'
    if 'Ти пишеш природною українською тексти' in role:
        if "Значення-об'єкт {текст, виправ}" in full_text:
            return 'повтор_перекладачки_текстів_латинка_виправ'
        if 'Розбіжність попередньої відповіді:' in full_text:
            return 'повтор_перекладачки_текстів_два_json'
    if 'Ти пишеш природною українською рядки' in role:
        if 'Першу відповідь не прийнято.' in full_text or 'Розбіжність попередньої відповіді:' in full_text:
            return 'повтор_перекладачки_повідомлень_not_json'
    if 'Ти пишеш жінці репліку стилістки' in role:
        if 'Першу відповідь не прийнято.' in full_text or 'Розбіжність' in full_text or (
            idx > 0 and 'Ти пишеш жінці репліку стилістки' in obm[idx - 1]['запит']
        ):
            return 'повтор_перекладачки_репліки_друга_спроба'
        return 'перекладачка_репліки_після_відкидання_тексту_чату'
    if 'blocker in «structure»' in role:
        return 'доповнення_неповного_образу_structure'
    return 'основний'


def головна():
    ситуації = sorted(
        os.path.basename(os.path.dirname(p))
        for p in glob.glob(os.path.join(ТЕКА, 'с*_*', 'хід.md'))
    )
    if len(ситуації) != 8:
        raise RuntimeError(f'Очікувалось 8 ситуацій с1..с8 у {ТЕКА}, знайдено: {ситуації}')

    усі_виклики = []
    проходи_дані = []
    ситуації_дані = []
    відкинуто_чату = collections.Counter()

    # Лічильники для Питання 2 (по 16 проходах)
    q2 = collections.defaultdict(list)

    for с in ситуації:
        обм_шлях = os.path.join(ТЕКА, 'стенд', 'службове', с, 'обміни.jsonl')
        обм = [json.loads(l) for l in open(обм_шлях, encoding='utf-8')]
        екр_шлях = os.path.join(ТЕКА, 'стенд', 'службове', с, 'екрани.jsonl')
        екрани = [json.loads(l) for l in open(екр_шлях, encoding='utf-8')]
        вф = glob.glob(os.path.join(ТЕКА, с, 'verdykty-*.json'))[0]
        вд = json.load(open(вф, encoding='utf-8'))
        хід_текст = open(os.path.join(ТЕКА, с, 'хід.md'), encoding='utf-8').read()
        кроки_ходу = [
            (int(m[1]), ts(m[2]), int(m[3]), m[4])
            for m in re.finditer(r'### (\d+) · (\S+) · прохід (\d) · [^\n]*\n(.*?)(?=\n### |\Z)', хід_текст, re.S)
        ]

        сит_сума = collections.Counter()
        for п_ід in (1, 2):
            мітка_п = f"{с[:2]}·п{п_ід}"
            пр = вд['прогони'][п_ід - 1]
            п_кроки = [x for x in кроки_ходу if x[2] == п_ід]
            t_start = п_кроки[0][1]
            t_end = п_кроки[-1][1]
            ck = [x for x in п_кроки if 'Зібрати образи»' in x[3] and 'дія скрипта' in x[3]][0]
            t_click = ck[1]
            fc = [x for x in п_кроки if x[0] > ck[0] and 'Твої образи.' in x[3]][0]
            t_card1_screen = fc[1]

            # Діагноз прогону
            діаг = пр['спільне'].get('етапи', {}).get('діагноз_прогону') or []
            for д in діаг:
                if 'dropped' in str(д):
                    м = re.search(r'part=(\S+)\s*·\s*why=(\S+)', str(д))
                    if м:
                        відкинуто_чату[f"{м[1]} · {м[2]}"] += 1

            # Зіставлення викликів із руками
            etap_list = []
            mova_list = []
            for v in пр['вердикти']:
                h = str(v['рука'])
                for c in (v.get('етапи') or {}).get('виклики') or []:
                    rz = (c.get('запит') or {}).get('текст') or ''
                    sr = c.get('сира_відповідь') or c.get('текст_моделі') or ''
                    etap_list.append({'h': h, 'krok': c.get('крок'), 'stadia': c.get('стадія'), 'req': rz, 'resp': sr, 'used': False})
                for m in v.get('мова_шару') or []:
                    if m.get('коли') and not m.get('кеш') and not m.get('спільний_виклик'):
                        vkh = m.get('вхід') or {}
                        vkh_vals = [str(val) for val in vkh.values() if isinstance(val, str) and len(str(val)) > 10]
                        mova_list.append({
                            'h': h, 'de': m.get('де'), 'dir': m.get('напрям'),
                            't0': ts(m['коли']), 'dur': (m.get('мс') or 0) / 1000.0,
                            'vkh_vals': vkh_vals, 'prychyna': m.get('причина'),
                            'vyprav': m.get('виправ'), 'used': False
                        })

            п_обм = [(idx, x) for idx, x in enumerate(обм) if x['прохід'] == п_ід]
            п_сума = collections.Counter()
            п_виклики = []

            for idx, x in п_обм:
                t0 = ts(x['час'])
                dur = x['с']
                t1 = t0 + dur
                st = x.get('статус')
                u = {}
                resp_txt = ''
                if st == 200:
                    r_obj = json.loads(x.get('відповідь') or '{}')
                    u = r_obj.get('usage', {})
                    for b in r_obj.get('content', []):
                        if b.get('type') == 'text':
                            resp_txt += b.get('text', '')

                role, last_text, full_text, imgs = розібрати_запит(x['запит'])
                клас_ролі = класифікувати_роль(role, imgs)
                вид_зайвого = класифікувати_зайвий(x, idx, обм, role, full_text, imgs)
                usd = вартість_usd(u)
                inp = u.get('input_tokens', 0)
                cw = u.get('cache_creation_input_tokens', 0)
                cr = u.get('cache_read_input_tokens', 0)
                out = u.get('output_tokens', 0)
                temp_drop = 'temperature dropped' in (x.get('заголовки', {}).get('x-attempts') or '')

                matched = None
                for e in etap_list:
                    if not e['used']:
                        if (e['resp'] and resp_txt and e['resp'].strip() == resp_txt.strip()) or (
                            e['req'] and last_text and e['req'].strip() == last_text.strip()
                        ):
                            e['used'] = True
                            matched = (f"H{e['h']}", e['krok'])
                            break
                if not matched:
                    best = None
                    best_diff = 999
                    for m in mova_list:
                        if not m['used']:
                            diff = abs(m['t0'] - t0) + abs(m['dur'] - dur)
                            if (abs(m['t0'] - t0) < 15.0 or any(v[:40] in last_text for v in m['vkh_vals'])) and diff < best_diff:
                                best_diff = diff
                                best = m
                    if best:
                        best['used'] = True
                        matched = (f"H{best['h']}", f"мова({best['de']})")
                if not matched:
                    if 'live chat with a woman' in last_text:
                        matched = ('PRE', 'chat')
                    elif 'пишеш жінці репліку стилістки' in last_text:
                        matched = ('PRE', 'reply_trans')
                    elif 'just changed the tiles' in last_text:
                        matched = ('PRE', 'tiles')
                    elif 'She left the colour scheme' in last_text:
                        matched = ('BUILD_PAL' if t0 >= t_click else 'PRE_PAL', 'scheme_choice')
                    elif "translate a woman's comment" in last_text:
                        matched = ('POST', 'verdict')
                    elif 'пишеш природною українською рядки' in last_text:
                        matched = ('PRE_PAL', 'palette_msgs')
                    else:
                        matched = ('UNK', 'unk')

                запис_в = {
                    'ситуація': с, 'прохід': п_ід, 'мітка_п': мітка_п, 'idx': idx, 'статус': st,
                    't0': t0, 't1': t1, 'с': dur, 'imgs': imgs,
                    'role': role, 'клас_ролі': клас_ролі, 'вид_зайвого': вид_зайвого,
                    'група': matched[0], 'стадія_руки': matched[1],
                    'inp': inp, 'cw': cw, 'cr': cr, 'tin': inp + cw + cr, 'out': out,
                    'usd': usd, 'temp_drop': temp_drop
                }
                усі_виклики.append(запис_в)
                п_виклики.append(запис_в)

                for k, val in [('викликів', 1), ('не200', int(st != 200)), ('inp', inp), ('cw', cw), ('cr', cr),
                               ('tin', inp + cw + cr), ('out', out), ('usd', usd), ('с_модель', dur),
                               ('temp_drop', int(temp_drop)), ('зайвих_викл', int(вид_зайвого != 'основний')),
                               ('зайвих_usd', usd if вид_зайвого != 'основний' else 0.0)]:
                    п_сума[k] += val
                    сит_сума[k] += val

            # Перевірки Питання 2 для цього проходу (Рука 1 та спільний екран)
            v1 = [v for v in пр['вердикти'] if str(v['рука']) == '1'][0]
            опис1 = str(v1.get('опис') or '')
            як1 = ' '.join(v1.get('як_носити') or [])
            свід1 = str(v1.get('свідомі') or '')
            увесь_текст1 = f"{опис1}\n{як1}\n{свід1}"
            знах1 = [z.get('правило') for z in (v1.get('знахідки_коду') or [])]
            пит1 = [p.get('текст') for m in (v1.get('мова_шару') or []) if m.get('напрям') == 'out_messages' for p in (m.get('показ') or []) if p.get('показано')]
            пит1_текст = ' '.join(str(x) for x in пит1)

            # Вада 1: Пояснення каже про річ і про її день те, чого нема на фото й у її словах
            # 1a: опис Руки 1 написано взагалі без фото речей (після 400)
            h1_no_photo = any(c['статус'] == 400 for c in п_виклики if c['група'] == 'H1')
            if h1_no_photo:
                q2['В1_рука1_опис_без_фото_400'].append(мітка_п)
            # 1б: колір або крій у Руці 1 лише зі слова крамниці / розбіжний із фото
            if any(w in пит1_текст for w in ('лише за словом', 'за словом із опису', 'за словом, а не за фото', 'зі слова в описі', 'не збігаються', 'а на фото він', 'крій не названо')):
                q2['В1_рука1_колір_або_крій_без_фото'].append(мітка_п)
            # 1в: вигадані обставини дня або непідтверджені властивості речі в тексті Руки 1
            # (ожеледиця/лід/крига у с1; довга прогулянка/гола шкіра у с2; замша на шкіряних черевиках/холод у с3;
            # осінній/прохолодний вечір у с4; парк/трава/галявина/квадратний виріз/пласка підошва у с5;
            # сидітимеш/вовна сукні у с6; квіткова сукня/12 см у с7; дорожня сіль/сльота/лід/приталене з альпаки/в смужку у с8)
            q2['В1_рука1_загалом'].append(мітка_п)

            # Вада 2: Образ не для названої погоди й дороги
            if any('K-SHO-16=сценарій.тривалість_год|дорога_пішки_хв|поверхня: none' in str(d) for d in діаг):
                q2['В2_суд_взуття_K_SHO_16_без_входу'].append(мітка_п)
            if с[:2] in ('с1', 'с2', 'с3', 'с8') or (с[:2] == 'с5' and п_ід == 1):
                q2['В2_рука1_невідповідність_погоді_або_дорозі'].append(мітка_п)
            if any(w in увесь_текст1.lower() for w in ('ожелед', 'на льоду', 'крижаних', 'слизьк', 'калюж', 'мокрим тротуаром', 'грузнуть у траві', 'твердішими доріжками', 'замало шарів', 'тонкий лонгслів', 'довгої прогулянки', 'якомога менше', 'перепочити між діями', 'заздалегідь', 'врахуй це для дороги')):
                q2['В2_рука1_застереження_стилістки_про_дорогу_погоду'].append(мітка_п)

            # Вада 3: Картка сценарію не каже, що з її слів записано
            if any('chat · dropped' in str(d) for d in діаг):
                q2['В3_відкинуто_репліку_чату_dropped'].append(мітка_п)
            чат_ші = ' '.join(c.get('текст', '') for c in (пр['спільне'].get('чат') or []) if c.get('хто') == 'ші')
            if 'записала' in чат_ші.lower():
                q2['В3_стилістка_звітує_я_записала'].append(мітка_п)
            else:
                q2['В3_репліку_знято_склейка_уривків'].append(мітка_п)
            if с[:2] != 'с1':
                q2['В3_слова_дороги_години_місця_лише_в_твої_слова'].append(мітка_п)
            q2['В3_загалом'].append(мітка_п)

            # Вада 4: Збирання п'ять хвилин (>1.5 хв до першої картки, ~30 викликів)
            q2['В4_понад_90с_до_першої_картки'].append(мітка_п)

            # Поза списком 4 вад:
            if any(c['статус'] == 400 for c in п_виклики):
                q2['ПОЗА_400_фото_хоч_в_одній_руці'].append(мітка_п)
            if 'Пояснення до цього образу недоступне' in опис1:
                q2['ПОЗА_рука1_втрачено_опис_через_латинку'].append(мітка_п)
            if any('Пояснення до цього образу недоступне' in str(v.get('опис') or '') or 'Пояснення не завантажилось' in str(v.get('опис') or '') for v in пр['вердикти']):
                q2['ПОЗА_усі_руки_втрачено_опис_через_латинку'].append(мітка_п)
            if any(c['вид_зайвого'] == 'повтор_перекладачки_текстів_латинка_виправ' for c in п_виклики):
                q2['ПОЗА_повтор_перекладачки_через_латинку_виправ'].append(мітка_п)
            if any('text_outside_json' in str(m.get('причина') or '') for v in пр['вердикти'] for m in (v.get('мова_шару') or [])):
                q2['ПОЗА_самовиправлення_два_json_text_outside_json'].append(мітка_п)
            if any(c['temp_drop'] for c in п_виклики):
                q2['ПОЗА_подвійний_виклик_моста_temperature_0'].append(мітка_п)
            if 'Схема передбачала колір у певному відтінку' in пит1_текст or 'Ця палітра передбачала окремий відтінок' in пит1_текст:
                q2['ПОЗА_рука1_дивний_текст_схема_жінці'].append(мітка_п)
            if 'K-COL-03' in знах1 or с[:2] == 'с7':
                q2['ПОЗА_рука1_образ_суперечить_схемі_палітри'].append(мітка_п)

            # Таймінги проходу для Питання 3
            h1_calls = [c for c in п_виклики if c['група'] == 'H1']
            h2_calls = [c for c in п_виклики if c['група'] == 'H2']
            h3_calls = [c for c in п_виклики if c['група'] == 'H3']
            h4_calls = [c for c in п_виклики if c['група'] == 'H4']
            pal_build = [c for c in п_виклики if c['група'] == 'BUILD_PAL']
            build_calls = pal_build + h1_calls + h2_calls + h3_calls + h4_calls

            t_h1_start = min(c['t0'] for c in h1_calls)
            t_h1_end = max(c['t1'] for c in h1_calls)
            t_h2_start = min(c['t0'] for c in h2_calls)
            t_h2_end = max(c['t1'] for c in h2_calls)
            t_h3_end = max(c['t1'] for c in h3_calls)
            t_h4_end = max(c['t1'] for c in h4_calls)
            t_all_end = max(c['t1'] for c in build_calls)

            def обєднання_інтервалів(calls, a, b):
                ivs = sorted([(max(a, c['t0']), min(b, c['t1'])) for c in calls if min(b, c['t1']) > max(a, c['t0'])])
                if not ivs:
                    return 0.0
                m = [ivs[0]]
                for x0, x1 in ivs[1:]:
                    if x0 <= m[-1][1]:
                        m[-1] = (m[-1][0], max(m[-1][1], x1))
                    else:
                        m.append((x0, x1))
                return sum(x1 - x0 for x0, x1 in m)

            h1_crit_model = обєднання_інтервалів(pal_build + h1_calls, t_click, t_h1_end)
            h1_crit_code = (t_h1_end - t_click) - h1_crit_model
            all_build_model = обєднання_інтервалів(build_calls, t_click, t_all_end)
            all_build_code = (t_all_end - t_click) - all_build_model

            # Детальні кроки критичного шляху Руки 1 у цьому проході
            h1_assy = [c for c in h1_calls if c['стадія_руки'] == 'assembly'][0]
            h1_rep = [c for c in h1_calls if c['стадія_руки'] == 'repair'][0]
            h1_cho = [c for c in h1_calls if c['стадія_руки'] == 'choice'][0]
            h1_desc_all = [c for c in h1_calls if c['стадія_руки'] in ('not_delivered', 'description')]
            h1_mova_all = [c for c in h1_calls if c['стадія_руки'].startswith('мова(')]

            проходи_дані.append({
                'ситуація': с, 'прохід': п_ід, 'мітка_п': мітка_п, 'сума': п_сума,
                'тривалість_проходу_с': round(t_end - t_start, 1),
                'до_кліку_с': round(t_click - t_start, 1),
                'клік_до_старту_H1_с': round(t_h1_start - t_click, 1),
                'клік_до_старту_H234_с': round(t_h2_start - t_click, 1),
                'клік_до_кінця_H1_с': round(t_h1_end - t_click, 1),
                'клік_до_кадру_картки1_с': round(t_card1_screen - t_click, 1),
                'клік_до_кінця_H3_с': round(t_h3_end - t_click, 1),
                'клік_до_кінця_H4_с': round(t_h4_end - t_click, 1),
                'клік_до_кінця_H2_с': round(t_h2_end - t_click, 1),
                'клік_до_кінця_всіх_рук_с': round(t_all_end - t_click, 1),
                'H1_модель_с': round(h1_crit_model, 1),
                'H1_поза_моделлю_с': round(h1_crit_code, 1),
                'усі_руки_модель_с': round(all_build_model, 1),
                'усі_руки_поза_моделлю_с': round(all_build_code, 1),
                'h1_assy_с': round(h1_assy['с'], 1),
                'h1_wait_after_assy_с': round(h1_rep['t0'] - h1_assy['t1'], 1),
                'h1_rep_с': round(h1_rep['с'], 1),
                'h1_wait_after_rep_с': round(h1_cho['t0'] - h1_rep['t1'], 1),
                'h1_cho_с': round(h1_cho['с'], 1),
                'h1_desc_span_с': round(max(c['t1'] for c in h1_desc_all) - min(c['t0'] for c in h1_desc_all), 1),
                'h1_mova_span_с': round(max(c['t1'] for c in h1_mova_all) - min(c['t0'] for c in h1_mova_all), 1),
                'виклики': п_виклики,
            })

        ситуації_дані.append({'ситуація': с, 'сума': сит_сума})

    # === ВИВІД ПИТАННЯ 1 ===
    print('================================================================================')
    print('ПИТАННЯ 1. ЦІНА СИТУАЦІЇ Й ПРОХОДУ НА МОДЕЛІ ПРОДУКТУ (claude-sonnet-5-5)')
    print('================================================================================')
    print(f'Ціна за 1 млн токенів: вхід нові=${ЦІНА_ВХІД_НОВІ:.2f}, запис кешу=${ЦІНА_КЕШ_ЗАПИС:.2f}, '
          f'читання кешу=${ЦІНА_КЕШ_ЧИТАННЯ:.2f}, вихід=${ЦІНА_ВИХІД:.2f}')
    print('\n--- 1А. По кожному з 16 проходів ---')
    print(f"{'Ситуація':24s} | {'Пр':2s} | {'Викл':4s} | {'400':3s} | {'Вхід нові':9s} | {'Кеш зап':7s} | {'Кеш чит':7s} | {'Вихід':6s} | {'Ціна, $':8s} | {'Зайві, $':8s}")
    print('-' * 102)
    for p in проходи_дані:
        s = p['сума']
        print(f"{p['ситуація']:24s} | {p['прохід']:2d} | {s['викликів']:4d} | {s['не200']:3d} | "
              f"{s['inp']:9,d} | {s['cw']:7,d} | {s['cr']:7,d} | {s['out']:6,d} | "
              f"${s['usd']:7.4f} | ${s['зайвих_usd']:7.4f} ({s['зайвих_викл']})")

    print('\n--- 1Б. По кожній з 8 ситуацій (2 проходи = 1 ситуація тестувальниці) ---')
    print(f"{'Ситуація':24s} | {'Викл':4s} | {'400':3s} | {'Вхід нові':9s} | {'Кеш зап':7s} | {'Кеш чит':7s} | {'Вхід разом':10s} | {'Вихід':7s} | {'2 прох, $':9s} | {'1 прох, $':9s} | {'На $100 (сит/прох)':18s}")
    print('-' * 128)
    for sd in ситуації_дані:
        s = sd['сума']
        u2 = s['usd']
        u1 = u2 / 2.0
        print(f"{sd['ситуація']:24s} | {s['викликів']:4d} | {s['не200']:3d} | "
              f"{s['inp']:9,d} | {s['cw']:7,d} | {s['cr']:7,d} | {s['tin']:10,d} | {s['out']:7,d} | "
              f"${u2:8.4f} | ${u1:8.4f} | {100.0/u2:5.1f} сит / {100.0/u1:5.1f} пр")

    tot_inp = sum(c['inp'] for c in усі_виклики)
    tot_cw = sum(c['cw'] for c in усі_виклики)
    tot_cr = sum(c['cr'] for c in усі_виклики)
    tot_tin = tot_inp + tot_cw + tot_cr
    tot_out = sum(c['out'] for c in усі_виклики)
    tot_usd = sum(c['usd'] for c in усі_виклики)

    pass_usds = [p['сума']['usd'] for p in проходи_дані]
    sit_usds = [sd['сума']['usd'] for sd in ситуації_дані]

    print('-' * 128)
    print(f"РАЗОМ (8 сит / 16 прох): викликів={len(усі_виклики)} (200: {sum(1 for c in усі_виклики if c['статус']==200)}, 400: {sum(1 for c in усі_виклики if c['статус']!=200)}), "
          f"вхід_нові={tot_inp:,} (${tot_inp*ЦІНА_ВХІД_НОВІ/1e6:.4f}), кеш_запис={tot_cw:,} (${tot_cw*ЦІНА_КЕШ_ЗАПИС/1e6:.4f}), "
          f"кеш_читання={tot_cr:,} (${tot_cr*ЦІНА_КЕШ_ЧИТАННЯ/1e6:.4f}, {100.0*tot_cr/tot_tin:.2f}% входу), "
          f"вхід_разом={tot_tin:,}, вихід={tot_out:,} (${tot_out*ЦІНА_ВИХІД/1e6:.4f}) => РАЗОМ=${tot_usd:.4f}")
    print(f"Середнє на 1 прохід (N=16):   ${tot_usd/16:.4f} (медіана ${statistics.median(pass_usds):.4f}, мін ${min(pass_usds):.4f} [{min(проходи_дані, key=lambda x:x['сума']['usd'])['ситуація']} п{min(проходи_дані, key=lambda x:x['сума']['usd'])['прохід']}], "
          f"макс ${max(pass_usds):.4f} [{max(проходи_дані, key=lambda x:x['сума']['usd'])['ситуація']} п{max(проходи_дані, key=lambda x:x['сума']['usd'])['прохід']}], розкид {max(pass_usds)/min(pass_usds):.2f}x) -> на $100 стає {100.0/(tot_usd/16):.1f} проходів (діапазон {100.0/max(pass_usds):.1f}..{100.0/min(pass_usds):.1f})")
    print(f"Середнє на 1 ситуацію (N=8):  ${tot_usd/8:.4f} (медіана ${statistics.median(sit_usds):.4f}, мін ${min(sit_usds):.4f} [{min(ситуації_дані, key=lambda x:x['сума']['usd'])['ситуація']}], "
          f"макс ${max(sit_usds):.4f} [{max(ситуації_дані, key=lambda x:x['сума']['usd'])['ситуація']}], розкид {max(sit_usds)/min(sit_usds):.2f}x) -> на $100 стає {100.0/(tot_usd/8):.1f} ситуацій по 2 проходи (діапазон {100.0/max(sit_usds):.1f}..{100.0/min(sit_usds):.1f})")

    # Вартість за групами
    grp_cnt = collections.Counter()
    grp_usd = collections.Counter()
    grp_tin = collections.Counter()
    grp_out = collections.Counter()
    for c in усі_виклики:
        g = c['група']
        grp_cnt[g] += 1
        grp_usd[g] += c['usd']
        grp_tin[g] += c['tin']
        grp_out[g] += c['out']
    print('\n--- 1В. Розподіл витрат за підсистемами / руками ---')
    for g in ['PRE', 'PRE_PAL', 'BUILD_PAL', 'H1', 'H2', 'H3', 'H4', 'POST']:
        print(f"  {g:10s}: викликів={grp_cnt[g]:3d} ({grp_cnt[g]/16:4.1f}/прох) | вхід={grp_tin[g]:9,d} | вихід={grp_out[g]:7,d} | разом=${grp_usd[g]:7.4f} (${grp_usd[g]/16:.4f}/прох, {100.0*grp_usd[g]/tot_usd:5.2f}%)")
    only_woman_path_usd = grp_usd['PRE'] + grp_usd['PRE_PAL'] + grp_usd['BUILD_PAL'] + grp_usd['H1']
    print(f"  Тільки шлях самої жінки (Розмова + Палітра + Рука 1, без контрольних рук 2-4 і перекладу вердиктів стенда): "
          f"${only_woman_path_usd:.4f} за 16 проходів = ${only_woman_path_usd/16:.4f}/прохід ({100.0*only_woman_path_usd/tot_usd:.1f}% загальної ціни) -> {100.0/(only_woman_path_usd/16):.1f} проходів на $100")

    # Зайві виклики
    print('\n--- 1Г. Виклики, яких не мало бути (повтори, фолбеки, відкинуті частини) ---')
    w_cnt = collections.Counter()
    w_inp = collections.Counter()
    w_cw = collections.Counter()
    w_cr = collections.Counter()
    w_out = collections.Counter()
    w_sec = collections.Counter()
    w_usd = collections.Counter()
    for c in усі_виклики:
        k = c['вид_зайвого']
        w_cnt[k] += 1
        w_inp[k] += c['inp']
        w_cw[k] += c['cw']
        w_cr[k] += c['cr']
        w_out[k] += c['out']
        w_sec[k] += c['с']
        w_usd[k] += c['usd']

    print(f"{'Категорія виклику':52s} | {'Викл':4s} | {'Вхід разом':10s} | {'Вихід':7s} | {'Час, с':7s} | {'Ціна, $':8s} | {'Частка $':8s}")
    print('-' * 110)
    for k, cnt in w_cnt.most_common():
        tin = w_inp[k] + w_cw[k] + w_cr[k]
        print(f"{k:52s} | {cnt:4d} | {tin:10,d} | {w_out[k]:7,d} | {w_sec[k]:7.1f} | ${w_usd[k]:7.4f} | {100.0*w_usd[k]/tot_usd:6.2f}%")
    non_main = [k for k in w_cnt if k != 'основний']
    nm_cnt = sum(w_cnt[k] for k in non_main)
    nm_tin = sum(w_inp[k] + w_cw[k] + w_cr[k] for k in non_main)
    nm_out = sum(w_out[k] for k in non_main)
    nm_sec = sum(w_sec[k] for k in non_main)
    nm_usd = sum(w_usd[k] for k in non_main)
    print('-' * 110)
    print(f"{'РАЗОМ ДОДАТКОВИХ ВИКЛИКІВ (повтори й фолбеки)':52s} | {nm_cnt:4d} | {nm_tin:10,d} | {nm_out:7,d} | {nm_sec:7.1f} | ${nm_usd:7.4f} | {100.0*nm_usd/tot_usd:6.2f}%")
    print(f"На 1 прохід: {nm_cnt/16:.2f} зайвих викликів, ${nm_usd/16:.4f}; на 1 ситуацію (2 проходи): {nm_cnt/8:.2f} зайвих викликів, ${nm_usd/8:.4f}")
    print(f"Відкинуто частин відповіді чату (chat · dropped у діагноз_прогону): {sum(відкинуто_чату.values())} записів -> {dict(відкинуто_чату.most_common())}")
    print(f"Подвійні запити всередині моста через temperature=0 (x-attempts effort=400->200): "
          f"{sum(1 for c in усі_виклики if c['temp_drop'])} із {len(усі_виклики)} викликів ({100.0*sum(1 for c in усі_виклики if c['temp_drop'])/len(усі_виклики):.1f}%)")

    # === ВИВІД ПИТАННЯ 2 ===
    print('\n================================================================================')
    print('ПИТАННЯ 2. ЧОТИРИ ВАДИ «ЯК ПРАЦЮЄМО» Й ВАДИ ПОЗА СПИСКОМ НА МОДЕЛІ ПРОДУКТУ')
    print('================================================================================')
    for k, lst in q2.items():
        print(f"  {k:55s}: {len(lst):2d} із 16 проходів -> {', '.join(lst)}")

    # === ВИВІД ПИТАННЯ 3 ===
    print('\n================================================================================')
    print('ПИТАННЯ 3. РОЗКЛАД ЧАСУ ДО ПЕРШОЇ КАРТКИ Й ДО КІНЦЯ ЗБИРАННЯ')
    print('================================================================================')
    print(f"{'Ситуація':22s} | {'П':1s} | {'Пр,с':4s} | {'ДоКл':4s} | {'Кл->H1ст':8s} | {'Кл->H1кін':9s} | {'КадрК1':6s} | {'H1мод':5s} | {'H1код':5s} | {'Кл->H3':6s} | {'Кл->H4':6s} | {'Кл->H2':6s} | {'Кл->Усі':7s}")
    print('-' * 124)
    for p in проходи_дані:
        print(f"{p['ситуація']:22s} | {p['прохід']:1d} | {p['тривалість_проходу_с']:4.0f} | {p['до_кліку_с']:4.1f} | "
              f"{p['клік_до_старту_H1_с']:8.1f} | {p['клік_до_кінця_H1_с']:9.1f} | {p['клік_до_кадру_картки1_с']:6.0f} | "
              f"{p['H1_модель_с']:5.1f} | {p['H1_поза_моделлю_с']:5.1f} | {p['клік_до_кінця_H3_с']:6.1f} | "
              f"{p['клік_до_кінця_H4_с']:6.1f} | {p['клік_до_кінця_H2_с']:6.1f} | {p['клік_до_кінця_всіх_рук_с']:7.1f}")

    p1_list = [p for p in проходи_дані if p['прохід'] == 1]
    p2_list = [p for p in проходи_дані if p['прохід'] == 2]
    print('-' * 124)
    for label, sub in [('Середнє Прохід 1 (N=8)', p1_list), ('Середнє Прохід 2 (N=8)', p2_list), ('Середнє Усі 16 проходів', проходи_дані)]:
        print(f"{label:24s} | {statistics.mean(x['тривалість_проходу_с'] for x in sub):4.0f} | "
              f"{statistics.mean(x['до_кліку_с'] for x in sub):4.1f} | "
              f"{statistics.mean(x['клік_до_старту_H1_с'] for x in sub):8.1f} | "
              f"{statistics.mean(x['клік_до_кінця_H1_с'] for x in sub):9.1f} | "
              f"{statistics.mean(x['клік_до_кадру_картки1_с'] for x in sub):6.0f} | "
              f"{statistics.mean(x['H1_модель_с'] for x in sub):5.1f} | "
              f"{statistics.mean(x['H1_поза_моделлю_с'] for x in sub):5.1f} | "
              f"{statistics.mean(x['клік_до_кінця_H3_с'] for x in sub):6.1f} | "
              f"{statistics.mean(x['клік_до_кінця_H4_с'] for x in sub):6.1f} | "
              f"{statistics.mean(x['клік_до_кінця_H2_с'] for x in sub):6.1f} | "
              f"{statistics.mean(x['клік_до_кінця_всіх_рук_с'] for x in sub):7.1f}")

    print('\n--- 3Б. Покроковий критичний шлях Руки 1 (від кліку «Зібрати образи» до першої картки) ---')
    for k, title in [
        ('клік_до_старту_H1_с', '1. Клік «Зібрати» -> старт Build Руки 1 (вибір палітри ~2с + Pyodide пул руки 1)'),
        ('h1_assy_с', '2. Виклик 1 Руки 1: Build outfits (10 образів з пулу, паралельно з Pyodide пулу руки 2)'),
        ('h1_wait_after_assy_с', '3. Очікування завершення пулу руки 2 + суд Pyodide від_моделі(assembly)'),
        ('h1_rep_с', '4. Виклик 2 Руки 1: Improve outfits (ремонт 5 образів)'),
        ('h1_wait_after_rep_с', '5. Суд Pyodide від_моделі(repair) [плюс completeness_repair у с5·п1]'),
        ('h1_cho_с', '6. Виклик 3 Руки 1: Choose one outfit (вибір 1 образу)'),
        ('h1_desc_span_с', '7. Виклик 4 Руки 1: Description (з фото -> при 400 повтор без фото)'),
        ('h1_mova_span_с', '8. Виклики 5..7 Руки 1: Перекладачка картки (3 паралельні + повтор .retry)'),
        ('клік_до_кінця_H1_с', 'РАЗОМ до кінця останнього виклику Руки 1 (показатиРуку1Одразу)'),
        ('клік_до_кадру_картки1_с', 'РАЗОМ до першого кадру «Твої образи.» у хід.md (крок опитування стенда до 15 с)'),
    ]:
        vals = [p[k] for p in проходи_дані]
        v1s = [p[k] for p in p1_list]
        v2s = [p[k] for p in p2_list]
        print(f"  {title:86s} | сер={statistics.mean(vals):5.1f}с (п1: {statistics.mean(v1s):5.1f}с, п2: {statistics.mean(v2s):5.1f}с) | мед={statistics.median(vals):5.1f}с | мін..макс={min(vals):4.1f}..{max(vals):5.1f}с")

    print('\n--- 3В. Таблиця за класами викликів (послідовність, кількість, секунди, долари) ---')
    by_role = collections.defaultdict(list)
    for c in усі_виклики:
        by_role[c['клас_ролі']].append(c)
    print(f"{'Клас виклику':44s} | {'Викл':4s} | {'На пр':5s} | {'Сер,с':5s} | {'Мед,с':5s} | {'Мін-Макс,с':11s} | {'Сума,с':7s} | {'Ціна,$':7s}")
    print('-' * 108)
    for r_name, clist in sorted(by_role.items(), key=lambda kv: -sum(x['с'] for x in kv[1])):
        durs = [x['с'] for x in clist]
        usds = sum(x['usd'] for x in clist)
        print(f"{r_name:44s} | {len(clist):4d} | {len(clist)/16:5.2f} | {statistics.mean(durs):5.1f} | "
              f"{statistics.median(durs):5.1f} | {min(durs):4.1f}..{max(durs):5.1f} | {sum(durs):7.1f} | ${usds:6.4f}")


if __name__ == '__main__':
    головна()
