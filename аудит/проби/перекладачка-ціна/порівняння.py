"""Кандидат (б) наряду «Перекладачка-ціна-вимір»: переклади Haiku 5.5 проти перекладів Sonnet 5.5 на справжньому мості 20.11
на тих самих 178 тілах перекладачки. Haiku — через `claude -p --model claude-haiku-5-5 --effort low` за підпискою
(`аудит/проби/модель-текст-claude/скрипти/повтор.py`; думки CLI не вимикає), журнал — `haiku_low.jsonl.gz`.

Автоперевірка зламаного (без судді):
- тексти й рядки: відповідь не JSON; ключів, які дав вхід, у відповіді нема; латинське слово, якого нема в перекладі
  Sonnet; літери ы э ъ ё;
- репліка: відповідь не тієї форми ({text: [{recorded, says}]}); набір `recorded` не той, що в Sonnet (речення каже
  записаним інше, ніж Sonnet на тому самому вході).
Пари «було — стало» — 20 випадкових текстів «тексти» довших за 40 знаків, де переклади різні (зерно 7).

Запуск з кореня: python3 -I аудит/проби/перекладачка-ціна/порівняння.py <вивід.md>"""
import glob, gzip, json, os, random, re, sys, collections

ТЕКА = 'аудит/проби/Живий-через-міст/стенд/службове'
ЖУРНАЛ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'haiku_low.jsonl.gz')
кандидат = {json.loads(л)['id']: json.loads(л) for л in gzip.open(ЖУРНАЛ, 'rt', encoding='utf-8')}
промпт, міст = {}, {}
for т in sorted(glob.glob(ТЕКА + '/с*')):
    с = os.path.basename(т)
    for і, л in enumerate(open(т + '/обміни.jsonl', encoding='utf-8')):
        x = json.loads(л); п = json.loads(x['запит'])['messages'][0]['content'][0]['text']
        if not п.startswith('Ти — перекладачка'):
            continue
        ід = f'{с}#{і:03d}'; промпт[ід] = п
        try:
            міст[ід] = ''.join(б.get('text', '') for б in json.loads(x['відповідь'])['content'] if б.get('type') == 'text')
        except Exception:
            pass


def вид(п):
    п = п[40:140]
    return 'репліка' if 'репліку' in п else 'рядки' if 'рядки' in п else 'тексти' if 'тексти' in п else '?'


def обʼєкт(т):
    т = re.sub(r'^```(?:json)?\s*|\s*```$', '', т.strip())
    try:
        о = json.loads(т)
    except Exception:
        м = re.search(r'\{.*\}', т, re.S)
        try:
            о = json.loads(м.group(0)) if м else None
        except Exception:
            о = None
    return о if isinstance(о, dict) else None


def пункти(о):
    if not о or not isinstance(о.get('text'), list):
        return None
    return [x for x in о['text'] if isinstance(x, dict)]


ЛАТ = re.compile(r'[A-Za-z][A-Za-z\'-]{2,}')
РОС = re.compile(r'[ыэъёЫЭЪЁ]')
лік = collections.Counter(); вади = []; пари = []
for ід in sorted(кандидат):
    if ід not in міст:
        лік['без відповіді моста'] += 1; continue
    в = вид(промпт[ід]); с, н = міст[ід], кандидат[ід]['текст']; лік[в] += 1
    if в == 'репліка':
        пс, пн = пункти(обʼєкт(с)), пункти(обʼєкт(н))
        if пс is None:
            лік['Sonnet не тієї форми'] += 1; continue
        if пн is None:
            вади.append((ід, в, 'не тієї форми', н[:160])); continue
        рс = sorted({р for x in пс for р in x.get('recorded', [])}); рн = sorted({р for x in пн for р in x.get('recorded', [])})
        if рс != рн:
            вади.append((ід, в, f'recorded: Sonnet {рс}, Haiku {рн}', ' / '.join(x.get('says', '') for x in пн)[:160]))
        continue
    пс, пн = обʼєкт(с), обʼєкт(н)
    if пс is None:
        лік['Sonnet не JSON'] += 1; continue
    if пн is None:
        вади.append((ід, в, 'не JSON', н[:160])); continue
    м = re.search(r'\nТЕКСТИ:\n(\{.*\})\s*$', промпт[ід], re.S)
    вхід = json.loads(м.group(1)) if м else {}
    if set(вхід) - set(пн):
        вади.append((ід, в, 'нема ключів ' + ', '.join(sorted(set(вхід) - set(пн), key=int)), ''))
    for к in пс:
        a, b = str(пс.get(к, '')), str(пн.get(к, ''))
        зайві = {w.lower() for w in ЛАТ.findall(b)} - {w.lower() for w in ЛАТ.findall(a)}
        if зайві:
            вади.append((ід, в, 'латинка: ' + ', '.join(sorted(зайві)), b[:160]))
        if РОС.search(b):
            вади.append((ід, в, 'літери ы э ъ ё', b[:160]))
        if в == 'тексти' and a != b and len(str(вхід.get(к, ''))) > 40:
            пари.append((ід, к, str(вхід.get(к, '')), a, b))
random.Random(7).shuffle(пари)
р = [f'# Haiku 5.5 (CLI) проти Sonnet 5.5 (міст 20.11) — автоперевірка й 20 пар', '',
     'Викликів: ' + ', '.join(f'{к} {з}' for к, з in sorted(лік.items())) + '.', '',
     f'## Зламане автоперевіркою — {len(вади)} у {len({в[0] for в in вади})} викликах з {sum(лік[к] for к in ("тексти", "рядки", "репліка"))}', '',
     '| виклик | клас | що | текст Haiku |', '|---|---|---|---|']
р += [f'| {а} | {б} | {в} | {г.replace(chr(10), " ⏎ ").replace("|", "/")} |' for а, б, в, г in вади]
р += ['', f'## 20 пар «тексти»: оригінал, Sonnet на мості, Haiku (з {len(пари)} різних текстів довших за 40 знаків)', '']
for ід, к, en, a, b in пари[:20]:
    р += [f'**{ід} · н={к}**', '', '- оригінал: ' + en.replace('\n', ' ⏎ '), '- Sonnet: ' + a.replace('\n', ' ⏎ '),
          '- Haiku: ' + b.replace('\n', ' ⏎ '), '']
open(sys.argv[1], 'w', encoding='utf-8').write('\n'.join(р) + '\n')
print(dict(лік), 'вад', len(вади), 'викликів з вадами', len({в[0] for в in вади}), 'пар', len(пари))
